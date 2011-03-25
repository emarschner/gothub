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

COLLECTION = 'commits'

conn = Connection(slave_okay=True)
processed = conn[INPUT_DB]
coll = processed[COLLECTION]

time_ranges = [
    ['april_month', [datetime(2010, 4, 1), datetime(2010, 5, 1)]],
    ['october_month', [datetime(2010, 10, 1), datetime(2010, 11, 1)]],
    ['november_week', [datetime(2010, 11, 1), datetime(2010, 11, 8)]]
]

geo_box_ranges = [
    ['world', [[-89.0, -179.9], [89.9, 179.9]]],
    #['bayarea', [[37.2, -123.0], [38.0, -121.0]]],
    ['cali', [[32.81, -125.0], [42.0, -114.0]]],
    ['america', [[25.0, -125.0], [50.0, -65.0]]],
    ['europe', [[33.0, 40.0], [71.55, 71.55]]],
    ['australia', [[-48.0, 113.1], [-10.5, 179.0]]]
]

project_ranges = [
    ['rails', 'rails'],
    ['homebrew', 'homebrew'],
    ['node', 'node']
]

combined_ranges = [
    #['rails_bay_apr', ["rails", [datetime(2010, 4, 1), datetime(2010, 5, 1)], [[37.2, -123.0], [38.0, -121.0]] ]],
    #['homebrew_bay_2010', ["homebrew", [datetime(2010, 1, 1), datetime(2011, 1, 1)], [[37.2, -123.0], [38.0, -121.0]] ]]
    ['node_australia_2010', ["node", [datetime(2010, 1, 1), datetime(2011, 1, 1)], [[-48.0, 113.1], [-10.5, 179.0]]]]
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
    #print "miles = %s" % miles
    
    geo_near = [center, radius]
    test = [desc, geo_near]
    print "Test = %s" % test
    #geo_circle_ranges.append(test)

def time_match(range):
    # range is [start_time, end_time]
    return {"date": {"$gte": range[0], "$lt": range[1]}}

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

def geo_split_box_match(range):
    # range is [center, radius]
    return {
        "long": {"$gt": range[0][1], "$lt": range[1][1]},
        "lat": {"$gt": range[0][0], "$lt": range[1][0]}
    }
    
def project_match(range):
    return {
        "project": range
    }

def combined_match(range):
    query = {}
    project_query = {"project": range[0]}
    time_query = time_match(range[1])
    geo_query = geo_split_box_match(range[2])
    query.update(project_query)
    query.update(time_query)
    query.update(geo_query)
    return query

def run_queries(tests, match_fcn, process_fcn = None):
    # Test are 2-element lists of descriptions and range specs.
    # Match fcn takes a range spec and generates a match input.
    # Process fcn takes a cursor arg.
    for entry in tests:
        desc, range = entry
        print "--------------------------------------------"
        print "desc: %s\nrange: %s" % (desc, range)
        match = match_fcn(range)
        print "match: %s" % match
        start = time.time()
        matching = coll.find(match)
        matched = matching.count()
        if process_fcn:
            process_fcn(matching)
        elapsed = float(time.time() - start)
        print "matched: %i" % matched
        print "time: %0.6f" % elapsed

def process_loc_str(matching):
    for m in matching:
        x = m['sha1']
        #x = str(m['sha1']) + str(m['lat'])

def process_loc_str_err(matching):
    for m in matching:
        if 'location' in m:
            print "%s, %s, %s, %s" % (m['author'], m['location'], m['lat'], m['long'])
        #x = m['sha1']
        #x = str(m['sha1']) + str(m['lat'])

def process_loc_list(matching):
    shas = []
    for m in matching:
        shas.extend(m['sha1'])

def process_loc_gettimes(matching):
    dates = []
    i = 0
    commits = processed['commits']
    for m in matching:
        shas = m['sha1']
        i += len(shas)
        for sha in shas:
            dates += sha
            c = commits.find_one({'sha1': sha})
            #print c
            i += 1
            #dates.append(c['committed_date_native'])

    print "total commits matched: %i" % i

# Benchmark suite for paper inclusion:
#run_queries(time_ranges, time_match, process_loc_str)

# Query to identify Yahoo bug
geo_box_ranges2 = [
    ['whoknows', [[-60, -20], [-30, 0]]]
]
run_queries(geo_box_ranges2, geo_split_box_match, process_loc_str_err)

#run_queries(geo_box_ranges, geo_split_box_match, process_loc_str)
#run_queries(project_ranges, project_match, process_loc_str)
#run_queries(combined_ranges, combined_match, process_loc_str)

#run_queries(geo_box_ranges, geo_box_match)
#run_queries(geo_circle_ranges, geo_circle_match)
#run_queries(geo_circle_ranges, geo_near_match)

#run_queries(geo_box_ranges, geo_box_match, process_loc_list)
#run_queries(geo_box_ranges, geo_box_match, process_loc_gettimes)

#run_queries([['null', {}]], lambda x: x)
#run_queries([['null', {}]], lambda x: x, process_loc_str)