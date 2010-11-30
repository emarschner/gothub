#!/usr/bin/env python
# Brandon Heller
#
# Parse processed mongo DB to output CSV suitable for Tableau exploration.
#
# See CommitCSVWriter for the fields and their ordering.

from optparse import OptionParser
import os
import time
from os.path import isfile
from datetime import datetime

from pymongo import Connection, ASCENDING, GEO2D

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

# Default DB names
DEF_INPUT_DB_NAME = 'raw'
DEF_OUTPUT_DB_NAME = 'processed'


class CommitProcessor:

    def __init__(self):
        self.fields = ['sha1', 'author', 'location', 'lat', 'long',
                       'committed_date', 'authored_date', 'parents_total',
                       'parents_str', 'branches_total', 'branches_str']
        self.crlf = '\r\n' # yes, add Windows line ending
        self.parse_args()
        conn = Connection()
        self.db = conn[self.options.input_db]
        self.processed = conn[self.options.output_db]
        if self.options.clear:
            self.processed.drop_collection('commits')
        if self.options.build:
            self.build_commits()
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
                        help = "name of input database (raw)")
        opts.add_option("--output_db", type = 'string', 
                        default = DEF_OUTPUT_DB_NAME,
                        help = "name of output database (processed)")
        opts.add_option('--mode', type='choice', choices = MODES,
                        default = DEF_MODE,
                        help='one of [' + ', '.join(MODES) + ']')
        options, arguments = opts.parse_args()
        self.options = options

    def build_commit(self, commit):

        #print commit
        c = {}  # key/val pairs of interest
        sha1 = commit['id']
        author = commit['author']['login']
        if author:
            user = self.db.users.find_one({'name' : author})
            if user:
                if 'location' in user:
                    c['location'] = user['location']
                if 'geo' in user:
                    lat = float(user['geo']['latitude'])
                    long = float(user['geo']['longitude'])
                    # mongo is particular about geo formatting
                    # see http://www.mongodb.org/display/DOCS/Geospatial+Indexing
                    # another option would be to use an ordered dict, rather
                    # than a list
                    c['loc'] = [lat, long]
            else:
                #print "could not find user: %s" % author
                pass

            # Example URL: "url" : "/hone/twittershoes/commit/"
            # Extract repo name, removing starting slash
            # This is a necessary step to do a fast lookup in db.repos,
            # which is indexed by both owner _and_ name.
            url = commit['url'][1:]
            repo_name = url.split('/')[1]
            key = {'owner' : author, 'name': repo_name}
            repo = self.db.repos.find_one(key)
            if repo:
                if 'branches' in repo:
                    c['branches'] = repo['branches'].keys()
                else:
                    #print "could not find branches in repo:", repo
                    pass

        c['parents'] = [parent['id'] for parent in commit['parents']]
        c.update({
             'sha1': sha1,
             'author': author,
             'committed_date': commit['committed_date'], 
             'authored_date': commit['authored_date']
        })
        # Example datetime from github:
        # 2008-01-20T14:49:00-08:00
        base_fmt = "%Y-%m-%dT%H:%M:%S"
        # c['committed_date_native'] = datetime(2010, 4, 1)
        str = c['committed_date']
        base = str[:str.rfind('-')]
        tz = str_tz = str[str.rfind('-'):]
        global_date = datetime.strptime(base, base_fmt)
        # TODO: figure out how to correct for the UTC offset...
        c['committed_date_native'] = global_date

        return c

    def build_commits(self):
        # Create processed rows
        print "[time] [commits parsed]"
        start = time.time()

        i = 0
        s = ''
        cursor = self.db.commits.find()
        for c in cursor:
            i += 1
            if self.options.mode == 'normal':
                commit = self.build_commit(c)
                sha1 = commit['sha1']
                if self.options.write:
                    if self.options.clear:
                        self.processed.commits.insert(commit)
                    else:
                        self.processed.commits.update({'sha1': sha1}, commit, True)
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

    def generate_index(self, name, params_list):
        print "params_list: %s" % params_list
        print ("generating %s index..." % name), 
        start = time.time()
        created = self.processed.commits.ensure_index(params_list)
        elapsed = float(time.time() - start)
        print " took %0.3f seconds, created %s" % (elapsed, created)

    def setup_indices(self):
        print "index info before: ", self.processed.commits.index_information()

        # setup sha-1 index, useful for future updates to the collection.
        # otherwise, deleting and building from scratch is faster than a linear
        # lookup for modify operations.
        # http://api.mongodb.org/python/1.6%2B/examples/geo.html
        # http://www.mongodb.org/display/DOCS/Geospatial+Indexing
        self.generate_index('sha1', [("sha1", ASCENDING)])

        # setup geo index:
        # http://api.mongodb.org/python/1.6%2B/examples/geo.html
        # http://www.mongodb.org/display/DOCS/Geospatial+Indexing
        self.generate_index('geo', [("loc", GEO2D)])

        # setup time index:
        # http://cookbook.mongodb.org/patterns/date_range/
        self.generate_index('datetime', [('committed_date_native', ASCENDING)])
        print "index info after: ", self.processed.commits.index_information()

if __name__ == "__main__":
    CommitProcessor()

# vim: tabstop=4 expandtab shiftwidth=4 softtabstop=4
