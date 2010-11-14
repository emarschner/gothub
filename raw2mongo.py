#!/usr/bin/python

import os
import time
import pymongo
import json

conn = pymongo.Connection()

db = conn.raw
queue = conn.queue

#WARNING: THIS WILL DELETE ALL DATA IN RAW
db.users.drop()
db.commits.drop()
db.repos.drop()
queue.users.drop()
queue.repos.drop()
queue.commits.drop()
db.users.ensure_index("name", pymongo.ASCENDING)
db.repos.ensure_index([("owner", pymongo.ASCENDING), ("name", pymongo.ASCENDING)])

def import_raw():
	to_run = [
				["/home/cs448b/gothub/raw/user/search/", user_search],
				["/home/cs448b/gothub/raw/user/geocode/", user_geocode]
			]
	for proc in to_run:
		print "Processing: " + str(proc[0])
		process_dir(proc[0], proc[1])
		
	print "Processing commits"
	commit_dir = "/home/cs448b/gothub/raw/commits/list/"
	users = os.listdir(commit_dir)
	for user in users:
		user_dir = commit_dir + "/" + user
		try:
			projs = os.listdir(user_dir)
			for proj in projs:
				proj_dir = user_dir + "/" + proj
				process_dir(proj_dir, commits_list)
		except:
			pass

	print "Processing repos"
	repos_dir = "/home/cs448b/gothub/raw/repos/show/"
	users = os.listdir(repos_dir)
	for user in users:
		user_dir = repos_dir + '/' + user
		try:
			repos = os.listdir(user_dir)
			for repo in repos:
				repo_dir = user_dir + "/" + repo
				process_dir(repo_dir, repos_show)
		except:
			pass
		
	
	
def process_dir(dir, func):
	files = os.listdir(dir)
	ctr = 0
	for fname in files:
		ctr = ctr + 1
		if ctr % 1000 == 0:
			print "Processed: " + str(ctr)
		try:
			file_path = dir + "/" + fname
			f = open(file_path, "r")
			jsonstr = f.read()
			f.close()
			obj = json.loads(jsonstr)
			func(file_path, obj)
		except:
			pass
			
	
def user_search(path, obj):
	for user in obj["users"]:
		existing = db.users.find_one({"name" : user["name"]})
		if not existing:
			id = db.users.insert(user)
			queue.users.insert({"id" : id})

def user_geocode(path, obj):
	fname = path.split('/')[-1]
	results = obj["ResultSet"]["Results"]
	if len(results) == 1:
                existing = db.users.find_one({"name" : fname})
                if not existing:
                        id = db.users.insert({"name": fname, "geo" : results[0]})
                        queue.users.insert({"id" : id})
		else:
			db.users.update({"name":fname}, {"$set" : {"geo" : results[0]}})
	
def commits_list(path, obj):
	cmts = obj["commits"]
	for cmt in cmts:
		id = db.commits.insert(cmt)
		queue.commits.insert({"id" : id})
		
def repos_show(path, obj):
	spl = path.split('/')
	repo_name = spl[-2]
	owner = spl[-3]
	key = obj.keys()[0]
	existing = db.repos.find({"name" : repo_name, "owner" : owner})
	if existing:
		db.repos.update({"name": repo_name, "owner" : owner}, {"$set" : {key : obj[key]}})
	else:
		id = db.repos.insert({"name": repo_name, "owner" : owner, key : obj[key]})
		queue.repos.insert({"id" : id})
	
	
			
			

	

if __name__ == '__main__':
	import_raw()

# vim: tabstop=4 expandtab shiftwidth=4 softtabstop=4

