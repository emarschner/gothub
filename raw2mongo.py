#!/usr/bin/python

import os
import time
import pymongo
import json
import optparse
import codecs

conn = pymongo.Connection()

db = conn.raw
queue = conn.queue


def import_raw():
	
	usage = "usage: %prog [options]"
	parser = optparse.OptionParser(usage)
	parser.add_option("-d", "--drop", dest="should_drop", 
		action="store_true", help="drop existing collections")
	parser.add_option("-t", "--test", dest="test_mode", action="store_true",
				help="Use a test database")
	
	options, args = parser.parse_args()
	
	if options.should_drop:
		db.users.drop()
		db.commits.drop()
		db.repos.drop()
		queue.users.drop()
		queue.repos.drop()
		queue.commits.drop()
	
	if options.test_mode:
		print "Test Mode"
		global db, queue
		db = conn.rawtest
		queue = conn.queuetest

	db.users.ensure_index("name", pymongo.ASCENDING)
	db.repos.ensure_index("name", pymongo.ASCENDING)
	
	base_dir = "/home/cs448b/gothub/raw/full/"
	to_run = [
				["user_search", user_search],
				["geocode", user_geocode],
				["repos_show", repos_show],
				["commits", commits_list]
				
			]
	for proc in to_run:
		print "Processing: " + str(proc[0])
		process_file(base_dir + proc[0], proc[1])
	
	
def process_file(file_path, func):
		f = codecs.open(file_path, encoding='utf-8', mode='r')
		ctr = 0
		for line in f:
			ctr = ctr + 1
			if ctr % 1000 == 0:
				print "Processed: " + str(ctr)
			obj = json.loads(line)
			func(file_path, obj)
		f.close()
			
	
def user_search(path, obj):
	for user in obj["users"]:
		existing = db.users.find_one({"name" : user["name"]})
		if not existing:
			id = db.users.insert(user)
			queue.users.insert({"id" : id})

def user_geocode(path, obj):
	#{"emarschner" : data}
	user_name = obj.keys()[0]
	obj = obj[user_name]
	results = obj["ResultSet"]["Results"]
	if len(results) == 1:
		existing = db.users.find_one({"name" : user_name})
		if not existing:
			id = db.users.insert({"name": user_name, "geo" : results[0]})
			queue.users.insert({"id" : id})
		else:
			db.users.update({"name":user_name}, {"$set" : {"geo" : results[0]}})
	
def commits_list(path, obj):
	#{"emarschner/gothub/master" : {"commits" : []}}
	key = obj.keys()[0]
	owner, repo_name, branch = key.split('/')
	obj = obj[key]
	cmts = obj["commits"]
	for cmt in cmts:
		existing = db.commits.find_one({"id" : cmt["id"]})
		long_name = owner + '/' + repo_name
		if not existing:
			cmt["repo_n"] = [repo_name]
			cmt["repo_l"] = [long_name]
			id = db.commits.insert(cmt)
			queue.commits.insert({"id" : id})
		else:
			changed = False
			if cmt.has_key("repo_n"):
				if not (repo_name in cmt["repo_n"]):
					cmt["repo_n"].append(repo_name)
					changed = True
			else:
				cmt["repo_n"] = [repo_name]
				changed = True
			if cmt.has_key("repo_l"):
				if not (long_name in cmt["repo_l"]):
					cmt["repo_l"].append(long_name)
					changed = True
			else:
				cmt["repo_l"] = [long_name]
				changed = True
			if changed:
				db.commits.update({"id": cmt["id"]}, {"$set" : {"repo_l" : cmt["repo_l"], "repo_n" : cmt["repo_n"]}})
				queue.commits.insert({"id": existing["_id"]})
		
def repos_show(path, obj):
	#{"emarschner/gothub" : { "contributors" : blah}}
	key = obj.keys()[0]
	owner, repo_name = key.split('/')
	obj = obj[key]
	key = obj.keys()[0]
	for sub_key in obj[key].keys():
		clean_key = sub_key.replace(".", "_")
		if clean_key != sub_key:
			obj[key][clean_key] = obj[key][sub_key]
			del obj[key][sub_key]
	existing = db.repos.find_one({"name" : repo_name, "owner" : owner})
	if existing:
		db.repos.update({"name": repo_name, "owner" : owner}, {"$set" : {key : obj[key]}})
		queue.repos.insert({"id" : existing["_id"]})
	else:
		id = db.repos.insert({"name": repo_name, "owner" : owner, key : obj[key]})
		queue.repos.insert({"id" : id})
	
	
			
			

	

if __name__ == '__main__':
	import_raw()

# vim: tabstop=4 expandtab shiftwidth=4 softtabstop=4

