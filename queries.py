#!/usr/bin/env python
# Brandon Heller
#
# Run geo, time, and combined queries to get an early idea of how interactive
# this might be.

import time
from datetime import datetime

from pymongo import Connection

INPUT_DB = 'processed'

conn = Connection(slave_okay=True)
processed = conn[INPUT_DB]

def time_queries():
    
    time_ranges = [
        ['april_month', [datetime(2010, 4, 1), datetime(2010, 5, 1)]],
        ['october_month', [datetime(2010, 10, 1), datetime(2010, 11, 1)]],
        ['november_week', [datetime(2010, 11, 1), datetime(2010, 11, 8)]]
    ]
    
    for entry in time_ranges:
        desc, range = entry
        print "--------------------------------------------"
        print "desc: %s\nrange: %s" % (desc, range)
        match = {"committed_date_native": {"$gte": range[0], "$lt": range[1]}}
        start = time.time()
        matching = processed.commits.find(match)
        matched = matching.count()
        elapsed = float(time.time() - start)
        print "matched: %i" % matched
        print "time: %0.4f" % elapsed

def geo_queries():
    #http://www.mongodb.org/display/DOCS/Geospatial+Indexing
    # mongodb geo bounds queries are represented by lower-left and upper-right
    # corners.
    geo_ranges = [
        ['bayarea', [[37.2, -123.0], [38.0, -121.0]]],
        ['cali', [[32.81, -125.0], [42.0, -114.0]]],
        ['america', [[25.0, -125.0], [50.0, -65.0]]]
        ['europe', [[33.0, 40.0], [71.55, 71.55]]]
        ['australia', [[-48.0, 113.1], [-10.5, 179.0]]]
    ]
    
    for entry in geo_ranges:
        desc, box = entry
        print "--------------------------------------------"
        print "desc: %s\nrange: %s" % (desc, box)
        match = {'loc': {"$within": {"$box": box}}}
        start = time.time()
        matching = processed.commits.find(match)
        matched = matching.count()
        elapsed = float(time.time() - start)
        print "matched: %i" % matched
        print "time: %0.4f" % elapsed

time_queries()
#geo_queries()
