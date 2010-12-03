#!/usr/bin/env python
#
# On OSX, this script seems to work better with the built-in
# Apache server, not web.py.
# To enable Apache, go to System Preferences > Sharing and enable Web Sharing.
# Then add a link from the Apache serving directory to the html page
# for gothub:
# cd /Library/WebServer/Documents
# <example location>
# ln -s ~/src/gothub .

from selenium import selenium

import os

# Server map files
BASE_DIR = "http://localhost/gothub/web/static/"
HTML_FILE = "map.html"


class ScreenshotGen():

	def __init__(self):
		self.base_dir = BASE_DIR
		self.selenium = selenium("localhost", 4444, "*firefox", self.base_dir)
		self.selenium.start()

	def generate(self, path, name, query = {}):
		# query is a set of key/val string pairs to forward to the mapper
		sel = self.selenium
		base_path = self.base_dir + HTML_FILE + "?"
		i = 0
		query_str = ""
		for key, val in query.iteritems():
			# add ampersand if not last:
			query_str += key + "=" + val
			if i < len(query) - 1:
				query_str += "&"
			i += 1
		print "query string: %s" % query_str
		sel.open(base_path + query_str)
		filename = os.path.join(path, name + ".png")
		sel.capture_entire_page_screenshot(filename, None)

	def __del__(self):
		self.selenium.stop()
