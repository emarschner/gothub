#!/usr/bin/python

import os
import time
import pymongo
import json
import sys
import optparse
import codecs

def main():
	usage = "usage: %prog [options]"
	parser = optparse.OptionParser(usage)
	parser.add_option("-t", "--test", dest="testing", action="store_true", help="Enable testing mode")
	parser.add_option("-u", "--user", dest="user_name", action="store", type="string", help="username")
	parser.add_option("-r", "--repo", dest="repo_name", action="store", type="string", help="repo name")
	parser.add_option("--geocode", action="store_true", dest="geocode")
	parser.add_option("--user-search", action="store_true", dest="user_search")
	parser.add_option("--commits", action="store_true", dest="commits")
	parser.add_option("--repos-show", action="store_true", dest="repos_show")
	
	options, args = parser.parse_args()
	
	conn = pymongo.Connection()

	db = conn.raw
	queue = conn.queue
	if options.testing:
		db = conn.rawtest
		queue = conn.queuetest

	char_stream = codecs.getreader("utf-8")(sys.stdin)
	data = char_stream.read()
	obj = json.loads(data)
	if options.geocode and options.user_name:
		if obj["ResultSet"]["Found"] == 1:
			existing = db.users.find_one({"name" : options.user_name})
			if not existing:
				id = db.users.insert({"name" : options.user_name, "geo" : obj["ResultSet"]["Results"][0]})
				queue.users.insert({"id" : id})
			else:
				db.users.update({"name":options.user_name}, {"$set" : {"geo" : obj["ResultSet"]["Results"][0]}})
				queue.users.insert({"id" : existing["_id"]})
	elif options.user_search:
		for user in obj["users"]:
			existing = db.users.find_one({"name" : user["name"]})
			if not existing:
				id = db.users.insert(user)
				queue.users.insert({"id" : id})
	elif options.commits and options.repo_name and options.user_name
		cmts = obj["commits"]
		for cmt in cmts:
			existing = db.commits.find_one({"id" : cmt["id"]})
			long_name = options.user_name + '/' + options.repo_name
			if not existing:
				cmt["repo_n"] = [options.repo_name]
				cmt["repo_l"] = [long_name]
				id = db.commits.insert(cmt)
				queue.commits.insert({"id" : id})
			else:
				changed = False
				if cmt.has_key("repo_n"):
					if not (options.repo_name in cmt["repo_n"]):
						cmt["repo_n"].append(options.repo_name)
						changed = True
				else:
					cmt["repo_n"] = [options.repo_name]
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
	elif options.repos_show and options.repo_name and options.user_name:
		key = obj.keys()[0]
		for sub_key in obj[key].keys():
			clean_key = sub_key.replace(".", "_")
			if clean_key != sub_key:
				obj[key][clean_key] = obj[key][sub_key]
				del obj[key][sub_key]
		existing = db.repos.find_one({"name" : options.repo_name, "owner" : options.user_name})
		if existing:
			db.repos.update({"name": options.repo_name, "owner" : options.user_name}, {"$set" : {key : obj[key]}})
			queue.repos.insert({"id" : existing["_id"]})
		else:
			id = db.repos.insert({"name": options.repo_name, "owner" : options.user_name, key : obj[key]})
			queue.repos.insert({"id" : id})

if __name__ == '__main__':
	main()


