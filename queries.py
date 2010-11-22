#!/usr/bin/env python
# Brandon Heller
#
# Run geo, time, and combined queries to get an early idea of how interactive
# this might be.

import time
from datetime import datetime
from math import sqrt, radians

from pymongo import Connection

#INPUT_DB = 'processed100k'
INPUT_DB = 'processed'

conn = Connection(slave_okay=True)
processed = conn[INPUT_DB]

time_ranges = [
    ['april_month', [datetime(2010, 4, 1), datetime(2010, 5, 1)]],
    ['october_month', [datetime(2010, 10, 1), datetime(2010, 11, 1)]],
    ['november_week', [datetime(2010, 11, 1), datetime(2010, 11, 8)]]
]

geo_box_ranges = [
    ['bayarea', [[37.2, -123.0], [38.0, -121.0]]],
    #['cali', [[32.81, -125.0], [42.0, -114.0]]],
    #['america', [[25.0, -125.0], [50.0, -65.0]]],
    #['europe', [[33.0, 40.0], [71.55, 71.55]]],
    #['australia', [[-48.0, 113.1], [-10.5, 179.0]]]
]

geo_circle_ranges = []
for entry in geo_box_ranges:
    desc, range = entry
    lower_left = range[0]
    upper_right = range[1]
    long_center = (lower_left[0] + upper_right[0]) / 2
    lat_center = (lower_left[1] + upper_right[1]) / 2
    long_diff = upper_right[0] - lower_left[0]
    lat_diff = upper_right[1] - lower_left[1]
    center = [long_center, lat_center]
    # diag is roughly an angle in degrees.
    diag = sqrt(long_diff * long_diff + lat_diff * lat_diff)
    # convert to radians - NOT YET, only for sphere w/1.7+
    #diag = radians(diag)
    # http://stackoverflow.com/questions/3878702/mongodb-bound-queries-how-do-i-convert-mile-to-radian
    radius = diag / 2
    EARTH_RADIUS_MILES = 3959
    miles = radius * EARTH_RADIUS_MILES
    print "miles = %s" % miles
    
    geo_near = [center, radius]
    test = [desc, geo_near]
    print "Test = %s" % test
    geo_circle_ranges.append(test)

def time_match(range):
    # range is [start_time, end_time]
    return {"committed_date_native": {"$gte": range[0], "$lt": range[1]}}

def geo_box_match(range):
    # range is [lowerleft, upperright]
    # lowerleft and upperright are [long, lat]
    return {'loc': {"$within": {"$box": range}}}

def geo_circle_match(range):
    # range is [center, radius]
    return {"loc": {"$within": {"$center" : range}}}

def geo_near_match(range):
    # range is [center, radius]
    return {"loc": {"$near": range[0], "$maxDistance": range[1]}}

def run_queries(tests, match_fcn):
    # Test are 2-element lists of descriptions and range specs.
    # Match fcn takes a range spec and generates a match input.
    for entry in tests:
        desc, range = entry
        print "--------------------------------------------"
        print "desc: %s\nrange: %s" % (desc, range)
        match = match_fcn(range)
        print "match: %s"
        start = time.time()
        matching = processed.commits.find(match)
        matched = matching.count()
        elapsed = float(time.time() - start)
        print "matched: %i" % matched
        print "time: %0.6f" % elapsed


#run_queries(time_ranges, time_match)
#run_queries(geo_box_ranges, geo_box_match)
#run_queries(geo_circle_ranges, geo_circle_match)
#run_queries(geo_circle_ranges, geo_near_match)