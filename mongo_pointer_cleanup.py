#!/usr/bin/python

import pymongo

conn = pymongo.Connection()

db = conn.raw
queue = conn.queue

def cleanup_pointers():
	
	usage = "usage: %prog [options]"
	parser = optparse.OptionParser(usage)
	parser.add_option("-a", "--all", dest="all", 
		action="store_true", help="cleanup all")
	parser.add_option("-r", "--repos", dest="repos", 
		action="store_true", help="cleanup repos")
	parser.add_option("-c", "--commits", dest="commits", 
		action="store_true", help="cleanup commits")
	parser.add_option("-u", "--users", dest="users", 
		action="store_true", help="cleanup users")		
	
	options, args = parser.parse_args()
	
	if options.repos or options.all:
		cleanup('repos')
	if options.commits or options.all:
		cleanup('commits')
	if options.users or options.all:
		cleanup('users')

def cleanup(collection):
	for record in queue[collection].find():
		a = db[collection].find_one({"_id" : record["id"]})
		if not a:
			queue[collection].remove(record)


if __name__ == '__main__':
	cleanup_pointers()
	

# vim: tabstop=4 expandtab shiftwidth=4 softtabstop=4