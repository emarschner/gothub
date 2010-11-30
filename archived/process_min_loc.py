#!/usr/bin/env python
# Brandon Heller
#
# Processing functions to create DBs that may yield faster geo queries.

from optparse import OptionParser
import os
import time
from os.path import isfile
from datetime import datetime

from pymongo import Connection, ASCENDING, GEO2D

#RED = True
#MIN = True
#LOC = True
RED = False  # Reduced commit set: no-location commits removed.
MIN = False  # Reduced, + only add sha1s to db entries.
LOC = False  # Same as min, only for checking if loc writes can be
             # sped up by ensuring an index first.
SPLIT = True  # Store a compound index of long and lat to compare against
              # geo searches.

# Mode, used for performance testing:
MODES = ['normal', 'null', 'access', 'string']
DEF_MODE = 'normal'

# Hard # of max commits: 10M for now
HARD_MAX_COMMITS = 1e7

# Default max number of commits to parse before outputting csv
# Set to None to read all.
DEF_MAX_COMMITS = None

# Create indices after processing commits?
DEF_CREATE_INDICES = False

# Clear commits collection at start of script?
DEF_CLEAR = False

# Write processed commit rows to database?
DEF_WRITE = True

# Build commits?  Useful for indexing-only runs.
DEF_BUILD = True

# Commits to read until printing out current commit
PRINT_INTERVAL = 1000

# If set, use 40B sha1 string, otherwise use index pointer. 
USE_FULL_SHA = True

# Default DB names
DEF_INPUT_DB_NAME = 'processed'
DEF_OUTPUT_DB_NAME = 'processed'

# Default collection names
DEF_INPUT_COLL = 'commits'
DEF_RED_COLL = 'commits_red'
DEF_MIN_COLL = 'commits_min'
DEF_LOC_COLL = 'loc'
DEF_SPLIT_COLL = 'split'


class CommitMinProcessor:

    def __init__(self):
        self.parse_args()
        conn = Connection()
        self.db = conn[self.options.input_db]
        self.processed = conn[self.options.output_db]
        if self.options.clear:
            #self.processed.drop_collection(self.options.input_coll)
            if RED: self.processed.drop_collection(self.options.red_coll)
            if MIN: self.processed.drop_collection(self.options.min_coll)
            if LOC: self.processed.drop_collection(self.options.loc_coll)
            if SPLIT: self.processed.drop_collection(self.options.split_coll)
        self.input = self.processed[self.options.input_coll]
        if RED: self.red = self.processed[self.options.red_coll]
        if MIN: self.min = self.processed[self.options.min_coll]
        if LOC:
            self.loc = self.processed[self.options.loc_coll]
            # check if loc updates can be sped up w/an index?
            self.loc.ensure_index([("loc", GEO2D)])
        if SPLIT: self.split = self.processed[self.options.split_coll]

        if self.options.build:
            self.process_commits()
        if self.options.indices:
            self.setup_indices()

    def parse_args(self):
        opts = OptionParser()
        opts.add_option("-m", "--max_commits", type = "int",
                        default = DEF_MAX_COMMITS,
                        help = "max commits to parse; default is all")
        opts.add_option("-i", "--indices", action = "store_true", 
                        default = DEF_CREATE_INDICES,
                        help = "create indices?")
        opts.add_option("-c", "--clear", action = "store_true", 
                        default = DEF_CLEAR,
                        help = "clear commits collection at start?")
        opts.add_option("-n", "--no-write", action = "store_false",
                        dest = "write", default = DEF_WRITE,
                        help = "don't write to processed database?")
        opts.add_option("-b", "--no-build", action = "store_false",
                        dest = "build", default = DEF_BUILD,
                        help = "don't build commits?")
        opts.add_option("--input_db", type = 'string', 
                        default = DEF_INPUT_DB_NAME,
                        help = "name of input database (processed)")
        opts.add_option("--output_db", type = 'string',
                        default = DEF_OUTPUT_DB_NAME,
                        help = "name of output database (processed)")
        opts.add_option("--input_coll", type = 'string',
                        default = DEF_INPUT_COLL,
                        help = "name of input collection")
        opts.add_option("--min_coll", type = 'string',
                        default = DEF_MIN_COLL,
                        help = "name of min collection")
        opts.add_option("--red_coll", type = 'string',
                        default = DEF_RED_COLL,
                        help = "name of red collection")
        opts.add_option("--loc_coll", type = 'string',
                        default = DEF_LOC_COLL,
                        help = "name of loc collection")
        opts.add_option("--split_coll", type = 'string',
                        default = DEF_SPLIT_COLL,
                        help = "name of split collection")
        opts.add_option('--mode', type='choice', choices = MODES,
                        default = DEF_MODE,
                        help='one of [' + ', '.join(MODES) + ']')
        options, arguments = opts.parse_args()
        self.options = options

    def process_commit(self, c, i):
        if 'loc' in c:
            if RED:
                self.red.insert(c)
            min = {'loc': c['loc'], 'sha1': c['sha1']}
            if MIN:
                self.min.insert(min)
            loc = {'loc': c['loc']}
            if LOC:
                self.loc.update(loc, {"$push": {'sha1': c['sha1']}}, True)
            if SPLIT:
                lat = c['loc'][0]
                long = c['loc'][1]
                sha1 = None
                if USE_FULL_SHA:
                    sha1 = c['sha1']
                else:
                    sha1 = i
                split = {'lat': lat, 'long': long, 'sha1': sha1}
                self.split.insert(split)

    def process_commits(self):
        # Create processed rows
        print "[time] [commits parsed]"
        start = time.time()

        i = 0
        s = ''
        cursor = self.processed.commits.find()
        for c in cursor:
            i += 1
            if self.options.mode == 'normal':
                if self.options.build:
                    self.process_commit(c, i)
            elif self.options.mode == 'string':
                s = str(c)
            elif self.options.mode == 'null':
                pass
            elif self.options.mode == 'access':
                s = c['id']
            else:
                raise Exception("invalid mode")

            if i == HARD_MAX_COMMITS:
                break
            if self.options.max_commits and (i == self.options.max_commits):
                break

            if i % PRINT_INTERVAL == 0:
                elapsed = float(time.time() - start)
                print '%0.3f %i' % (elapsed, i)

        elapsed = float(time.time() - start)
        print "read %i commits in %0.3f seconds" % (i, elapsed)
        print "%0.2f commits per second" % (i / elapsed)

    def generate_index(self, coll, name, params_list):
        print "params_list: %s" % params_list
        print ("generating %s index... for collection %s" % (name, coll)), 
        start = time.time()
        created = coll.ensure_index(params_list)
        elapsed = float(time.time() - start)
        print " took %0.3f seconds, created %s" % (elapsed, created)

    def setup_indices(self):
        print "index info before: ", self.processed.commits.index_information()

        if SPLIT:
            index_params = [("long", ASCENDING), ("lat", ASCENDING)]
            self.generate_index(self.split, 'lat, long', index_params)

        colls = []
        if MIN: colls.append(self.min)
        if RED: colls.append(self.red)
        if LOC: colls.append(self.loc)
        for coll in colls:

            # setup sha-1 index, useful for future updates to the collection.
            # otherwise, deleting and building from scratch is faster than a linear
            # lookup for modify operations.
            # http://api.mongodb.org/python/1.6%2B/examples/geo.html
            # http://www.mongodb.org/display/DOCS/Geospatial+Indexing
            self.generate_index(coll, 'sha1', [("sha1", ASCENDING)])
    
            # setup geo index:
            # http://api.mongodb.org/python/1.6%2B/examples/geo.html
            # http://www.mongodb.org/display/DOCS/Geospatial+Indexing
            self.generate_index(coll, 'geo', [("loc", GEO2D)])

            # setup time index:
            # http://cookbook.mongodb.org/patterns/date_range/
            #self.generate_index('datetime', [('committed_date_native', ASCENDING)])
            #print "index info after: ", self.processed.commits.index_information()

if __name__ == "__main__":
    CommitMinProcessor()

# vim: tabstop=4 expandtab shiftwidth=4 softtabstop=4
