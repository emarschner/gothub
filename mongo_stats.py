#!/usr/bin/env python
# Dump stats for raw and queue.

import os
import time
import pymongo
import json

conn = pymongo.Connection()

# db -> collections
dbs = {
       'raw' : ['commits', 'repos', 'users'],
       'queue' : ['commits', 'repos', 'users'],
       'processed' : ['commits']
}

for db, collections in dbs.iteritems():
    for collection in collections:
        count = conn[db][collection].count()
        print "%s.%s: %i" % (db, collection, count)