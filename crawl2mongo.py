#!/usr/bin/python

import os
import time
import pymongo
import json
import sys
import optparse

def main():
	usage = "usage: %prog [options]"
	parser = optparse.OptionParser(usage)
	parser.add_option("-u", "--user", dest="user_name", action="store", type="string", help="username")
	parser.add_options("-r", "--repo", dest="repo_name", action="store", type="string", help="repo name")
	parser.add_option("--geocode", action="store_true", dest="geocode")
	parser.add_option("--user-search", action="store_true", dest="user_search")
	parser.add_option("--commits", action="store_true", dest="commits")
	parser.add_option("--repos-show", action="store_true", dest="repos_show")
	
	options, args = parser.parse_args()
	
	conn = pymongo.Connection()

	db = conn.raw
	queue = conn.queue

	data = sys.stdin.read()
	obj = json.loads(data)
	if options.geocode and options.user_name:
		results = obj["ResultSet"]["Results"][0]
		db.users.update({"name":options.user_name}, {"$set" : {"geo" : results}}, upsert=True)
	elif options.user_search:
		for user in obj["users"]:
			id = db.users.insert(user)
			queue.users.insert({"id" : id})
	elif options.commits:
		cmts = obj["commits"]
		for cmt in cmts:
			id = db.commits.insert(cmt)
			queue.commits.insert({"id" : id})
	elif options.repos_show and options.repo_name and options.user_name:
		key = obj.keys()[0]
		db.repos.update({"name": options.repo_name}, {"$set" : {"owner" : options.user_name, key : obj[key]}}, upsert=True)
		queue.repos.update({"name": options.repo_name}, {"$set" : {"name" : options.repo_name}}, upsert=True)

if __name__ == '__main__':
	main()

