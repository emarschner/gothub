#!/usr/bin/env python
# Brandon Heller
# Parse processed mongo DB to output CSV suitable for Tableau exploration.
#
# See CommitCSVWriter for the fields and their ordering.

from optparse import OptionParser
import os
import time
from os.path import isfile

import pymongo

# Mode, used for performance testing: [normal, null, access, string]
MODE = 'mode' 

# Default output filename
DEF_OUTPUT_FILENAME = 'gothub'

# Path for output files
DEF_OUTPUT_PATH = './'

# Output filename extension
OUTPUT_EXT = '.csv'

# Hard # of max commits: 10M for now
HARD_MAX_COMMITS = 1e7

# Default max number of commits to parse before outputting csv
# Set to None to read all.
DEF_MAX_COMMITS = None

# Commits to read until printing out current commit
PRINT_INTERVAL = 100000


class CommitCSVWriter:

    def __init__(self):
        self.fields = ['sha1', 'author', 'location', 'lat', 'long',
                       'committed_date', 'authored_date', 'parents_total',
                       'parents_str', 'branches_total', 'branches_str']
        # double-quoted fields
        self.fields_to_quote = ['location', 'committed_date', 'authored_date',
                                'parents_str', 'branches_str']
        self.crlf = '\r\n' # yes, add Windows line ending
        conn = pymongo.Connection()
        self.db = conn.raw
        self.parse_args()
        self.build_csv()

    def parse_args(self):
        opts = OptionParser()
        opts.add_option('--file_name','-f', type = 'string', default = None,
                        help = "output file name; default is gothub... .csv")
        opts.add_option("--max_commits", "-m", type = "int",
                        default = DEF_MAX_COMMITS,
                        help = "max commits to parse; default is all")
        opts.add_option("--no-output", action = "store_false",
                        default = True, dest = "output",
                        help = "print output at end?")
        options, arguments = opts.parse_args()

        if not options.file_name:
            options.file_name = DEF_OUTPUT_FILENAME
            if options.max_commits:
                options.file_name += '-%i' % options.max_commits
            options.file_name += OUTPUT_EXT

        self.options = options

    def get_field(self, commit, input_type, field, key):
        path = os.path.join(self.dirs[input_type][field], key)
        if isfile(path):
            value = open(path, 'r').read().rstrip()
            commit[field] = value
            return value
        else:
            #print "ERROR: missing %s for %s/%s" % (key, input_type, field)
            return None

    def csv_header(self):
        s = ""
        for i, field in enumerate(self.fields):
            s += field
            if i < len(self.fields) - 1:
                s += ', '
        s += self.crlf
        return s

    def format_commit(self, commit):
        s = ''
        for i, field in enumerate(self.fields):
            if field in self.fields_to_quote:
                s += '"' + commit[field] + '"'
                if i < len(self.fields) - 1:
                    s += ', '
            else:
                s += str(commit[field])
                if i < len(self.fields) - 1:
                    s += ', '
        s += self.crlf
        return s

    def build_commit(self, commit):

        #print commit
        c = {}  # key/val pairs of interest            
        for field in self.fields:
            c[field] = 'unknown'
        sha1 = commit['id']
        author = commit['author']['login']
        if author:
            repo = self.db.repos.find_one({'owner' : author})
            if repo:
                if 'branches' in repo:
                    branches = repo['branches'].keys()
                    c['branches_total'] = str(len(branches))
                    c['branches_str'] = ','.join(branches)
                else:
                    #print "could not find branches in repo:", repo
                    pass
            user = self.db.users.find_one({'name' : author})
            if user:
                if 'location' in user:
                    c['location'] = user['location']
                if 'geo' in user:
                    c['lat'] = user['geo']['latitude']
                    c['long'] = user['geo']['longitude']
            else:
                #print "could not find user: %s" % author
                pass

        parents = [parent['id'] for parent in commit['parents']]

        c.update({
             'sha1': sha1,
             'author': author,
             'committed_date': commit['committed_date'], 
             'authored_date': commit['authored_date'],
             'parents_total': str(len(parents)),
             'parents_str': ','.join(parents),
        })
        # TODO: extract time zone from date.
        # example date: 2008-01-20T14:49:00-08:00
        # Not sure if the time is GMT and the shift is at the end?
        return c

    def build_csv(self):
        # Create CSV output
        output = open(DEF_OUTPUT_PATH + self.options.file_name, 'w')
        output.write(self.csv_header())

        print "[time] [commits parsed]"
        start = time.time()

        cursor = self.db.commits.find()
        i = 0
        unicode_errors = 0
        s = ''
        for c in cursor:
            i += 1
            if MODE == 'normal':
                commit = self.build_commit(c)
                formatted = self.format_commit(commit)
                formatted = formatted.encode('ascii', 'xmlcharrefreplace')
                s += formatted
                try:            
                    output.write(formatted)
                except UnicodeEncodeError as inst:
                    print commit
                    unicode_errors += 1
                    print inst
            elif MODE == 'string':
                s = str(c)
            elif MODE == 'null':
                pass
            elif MODE == 'access':
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
        print "skipped %i unicode errors" % unicode_errors
        print "%0.2f commits per second" % (i / elapsed)


if __name__ == "__main__":
    CommitCSVWriter()

# vim: tabstop=4 expandtab shiftwidth=4 softtabstop=4
