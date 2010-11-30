#!/usr/bin/env python
# Brandon Heller
#
# Process commits from raw into a form that will hopefully work well
# for generating tableau small multiples displays.

from optparse import OptionParser
import os
import time
from os.path import isfile
from datetime import datetime

from pymongo import Connection, ASCENDING

# Mode.  Non-normal modes are used only for performance testing.
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

# Default DB names
DEF_INPUT_DB_NAME = 'raw'
DEF_OUTPUT_DB_NAME = 'processed'

# Default collection names
DEF_INPUT_COLL = 'commits'
DEF_OUTPUT_COLL = 'commits'


class CommitProcessor:

    def __init__(self):
        self.parse_args()
        conn = Connection()
        self.input_db = conn[self.options.input_db]
        self.output_db = conn[self.options.output_db]
        if self.options.clear:
            self.output_db.drop_collection(self.options.output_coll)
        self.input_coll = self.output_db[self.options.input_coll]
        self.output_coll = self.output_db[self.options.output_coll]

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
        opts.add_option("--output_coll", type = 'string',
                        default = DEF_OUTPUT_COLL,
                        help = "name of output collection")
        opts.add_option('--mode', type='choice', choices = MODES,
                        default = DEF_MODE,
                        help='one of [' + ', '.join(MODES) + ']')
        options, arguments = opts.parse_args()
        self.options = options

    def build_commit(self, commit):

        c = {}  # key/val pairs of interest
        sha1 = commit['id']
        c['sha1'] = sha1
        author = commit['author']['login']
        if not author:
            author = commit['author']['name']

        if author:
            c['author'] = author
            user = self.input_db.users.find_one({'name' : author})
            if user:
                if 'location' in user:
                    c['location'] = user['location']
                if 'geo' in user:
                    c['lat'] = float(user['geo']['latitude'])
                    c['long'] = float(user['geo']['longitude'])
            else:
                #print "could not find user: %s" % author
                pass

            # Example URL: "url" : "/hone/twittershoes/commit/"
            # Extract repo name, removing starting slash
            # This is a necessary step to do a fast lookup in db.repos,
            # which is indexed by both owner _and_ name.
            url = commit['url'][1:]
            project = url.split('/')[1]
            c['project'] = project
#            # uncomment to restore branch data
#            key = {'owner' : author, 'name': }
#            repo = self.db.repos.find_one(key)
#            if repo:
#                if 'branches' in repo:
#                    c['branches'] = repo['branches'].keys()
#                else:
#                    #print "could not find branches in repo:", repo
#                    pass

            c['parents'] = [parent['id'] for parent in commit['parents']]
            # Example datetime from github:
            # 2008-01-20T14:49:00-08:00
            base_fmt = "%Y-%m-%dT%H:%M:%S"
            str = commit['committed_date']
            base = str[:str.rfind('-')]
            tz = str_tz = str[str.rfind('-'):]
            global_date = datetime.strptime(base, base_fmt)
            # TODO: figure out how to correct for the UTC offset...
            c['date'] = global_date

            return c
        else:
            # For now, ignore these commits; who knows why they're there?
            return None
            #print commit
            #raise Exception("no author login or name found")

    def process_commits(self):
        # Create processed rows
        print "[time] [commits parsed]"
        start = time.time()

        i = 0
        s = ''
        cursor = self.input_db.commits.find()
        for c in cursor:
            i += 1
            if self.options.mode == 'normal':
                if self.options.build:
                    commit = self.build_commit(c)
                    if commit:
                        if self.options.clear:
                            self.output_coll.insert(commit)
                        else:
                            sha1 = commit['sha1']
                            self.output_coll.update({'sha1': sha1}, commit, True)
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
        print "index info before: ", self.output_db.commits.index_information()

        # Create primary lat/long index.
        index_params = [("long", ASCENDING),
                        ("lat", ASCENDING),
                        ("date", ASCENDING),
                        ("project", ASCENDING)]
        self.generate_index(self.output_coll, 'lat, long', index_params)

        # setup sha-1 index, useful for future updates to the collection.
        # otherwise, deleting and building from scratch is faster than a linear
        # lookup for modify operations.
        # http://api.mongodb.org/python/1.6%2B/examples/geo.html
        # http://www.mongodb.org/display/DOCS/Geospatial+Indexing
        self.generate_index(self.output_coll, 'sha1', [("sha1", ASCENDING)])


if __name__ == "__main__":
    CommitProcessor()

# vim: tabstop=4 expandtab shiftwidth=4 softtabstop=4
