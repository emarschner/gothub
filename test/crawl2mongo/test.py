#!/usr/bin/python

import os
import time
import pymongo
import json
import sys
import optparse

def main():
	
	conn = pymongo.Connection()

	db = conn.rawtest
	queue = conn.queuetest

	print "Testing user import"
	obj = db.users.find_one({"name" : "EVANTEST"})
	pointer = queue.users.find_one()
	if pointer:
		testobj = db.users.find_one({"_id" : pointer["id"]})
		if testobj:
			print "Working"
		else:
			print "Error!"

	print "Testing repo import"
	obj = db.repos.find_one({"name" : "FAKEREPO", "owner": "EVANTEST"})
	pointer = queue.repos.find_one()
	if pointer:
		testobj = db.repos.find_one({"_id" : pointer["id"]})
		if testobj:
			print "Working"
		else:
			print "Error!"

	db.users.drop()
	db.commits.drop()
	db.repos.drop()
	queue.users.drop()
	queue.commits.drop()
	queue.repos.drop()

if __name__ == '__main__':
	main()

