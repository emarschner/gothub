#!/usr/bin/python

import os
import time
import pymongo
import json

conn = pymongo.Connection()

db = conn.raw

def import_raw():
	to_run = [
				["raw/user/search/", user_search],
				["raw/user/geocode/", user_geocode]
			]
	for proc in to_run:
		print "Processing: " + dir
		process_dir(proc[0], proc[1])
		
	commit_dir = "raw/commits/list/"
	users = os.listdir(commit_dir)
	for user in users:
		user_dir = commit_dir + "/" + user
		projs = os.listdir(user_dir)
		for proj in projs:
			proj_dir = user_dir + "/" + proj
			process_dir(proj_dir, commits_list)

	repos_dir = "raw/repos/show/"
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
			print "Processed: " + ctr
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
		db.users.insert(user)


def user_geocode(path, obj):
	fname = path.split('/')[-1]
	results = obj["ResultSet"]["Results"][0]
	db.users.update({"name":fname}, {"$set" : {"geo" : results}}, upsert=True)
	
def commits_list(path, obj):
	cmts = obj["commits"]
	for cmt in cmts:
		db.commits.insert(cmt)
		
def repos_show(path, obj):
	spl = path.split('/')
	repo_name = spl[-2]
	owner = spl[-3]
	key = obj.keys()[0]
	db.repos.update({"name": repo_name}, {"$set" : {"owner" : owner, key : obj[key]}}, upsert=True)
	
	
			
			

	

if __name__ == '__main__':
	import_raw()