#!/usr/bin/env python
# Brandon Heller
# Generate CSV output suitable for Tableau exploration, with:
# - links connecting related commits (parent/child relationships), OR
# - one line per location
#
# Example call, for project 'rails', limiting to 100 commits, showing links:
# > ./process_csv.py --project rails -f rails_100.csv -m 100
#
# Example showing location data:
# > ./process_csv.py --project rails -f rails_loc.csv --type loc
#
# Same as above, plus January only (currently broken)
# > ./process_csv.py --project rails -f rails_100.csv -m 100 --date_start 2010-01-01 --date_end 2010-02-01
#
# Alternately, for easier scripting, use Python directly.  Example:
# sample_query()

# Example output:
# sha, location, lat, long, path_id, path_order
# 26..5f, "San Francisco, CA", 37.777125, -122.419644, 0, 1

import json
from optparse import OptionParser
import os
import time
from os.path import isfile
from datetime import datetime
import pymongo
from sets import Set

# Default output filename
DEF_OUTPUT_FILENAME = 'gothub'

# Path for output files
DEF_OUTPUT_PATH = './'

# Output filename extension
OUTPUT_EXT = '.csv'

# Default max number of commits to parse before outputting csv
# Set to None to read all.
DEF_MAX_COMMITS = None

# Type of output to generate
DEF_TYPE = 'link' # 'loc'

# Hard # of max commits: 10M for now
HARD_MAX_COMMITS = 1e7

# Commits to read until printing out current commit
PRINT_INTERVAL = 1000

class CSVWriter:
    def __init__(self):
        self.fields = []
        self.fields_to_quote = []
    
    def csv_header(self):
        s = ""
        for i, field in enumerate(self.fields):
            s += field
            if i < len(self.fields) - 1:
                s += ', '
        s += self.crlf
        return s

    def format_commit(self, commit):
        """Generate CSV output for commit with path_id & path_order."""
        s = ''
        for i, field in enumerate(self.fields):
            if field == 'date': # special case
                s += '"' + str(commit[field]) + '"'
                if i < len(self.fields) - 1:
                    s += ', '
            elif field in self.fields_to_quote:
                s += '"' + commit[field] + '"'
                if i < len(self.fields) - 1:
                    s += ', '
            else:
                s += str(commit[field])
                if i < len(self.fields) - 1:
                    s += ', '
        s += self.crlf
        return s

class LocCSVWriter(CSVWriter):
    """Given a query and output filename, write CSV with geo links."""

    def __init__(self, filename, query, max_commits = None):
        self.filename = filename
        self.query = query
        self.max_commits = max_commits
        print "using query: %s" % self.query
        self.fields = ['lat', 'long', 'loc_count', 'authors', 'locations']
        self.fields_to_quote = ['authors', 'locations']
        self.crlf = '\r\n' # yes, add Windows line ending
        conn = pymongo.Connection()
        self.db = conn['processed']
        self.build_csv()

    def process_commit(self, c):
        """Note location/author in hash."""

        if 'lat' in c and 'long' in c:
            geo = (c['lat'], c['long'])
            author = c['author']
            location = ''
            if 'location' in c:
                location = c['location']
            else:
                location = None
            if geo not in self.locations:
                self.locations[geo] = {}
                self.locations[geo]['_locations'] = []
            if author not in self.locations[geo]:
                if location:
                    self.locations[geo]['_locations'].append(location)
                self.locations[geo][author] = True

    def build_csv(self):
        self.output = open(self.filename, 'w')
        self.output.write(self.csv_header())

        print "[time] [commits parsed]"
        start = time.time()

        # locations[(lat, long)] = {author1: 1, author2: 1...}
        self.locations = {}
        cursor = self.db.commits.find(self.query)
        i = 0
        s = ''
        for c in cursor:
            self.process_commit(c)
            i += 1

            if i == HARD_MAX_COMMITS:
                break
            if self.max_commits and (i == self.max_commits):
                break

            if i % PRINT_INTERVAL == 0:
                elapsed = float(time.time() - start)
                print '%0.3f %i' % (elapsed, i)

        elapsed = float(time.time() - start)
        print "read %i commits in %0.3f seconds" % (i, elapsed)
        print "%0.2f commits per second" % (i / elapsed)

        for key, val in self.locations.iteritems():
            hash = {}
            hash['lat'] = key[0]
            hash['long'] = key[1]
            # subtract by one because of the ugly way locations are stored
            hash['loc_count'] = max(len(val) - 1, 0)
            hash['authors'] = ', '.join([e for e in val.keys() if e != '_locations'])
            hash['locations'] = ' / '.join(Set(([e for e in val['_locations']])))
            formatted = self.format_commit(hash)
            formatted = formatted.encode('ascii', 'xmlcharrefreplace')
            try:
                self.output.write(formatted)
            except UnicodeEncodeError as inst:
                print c
                unicode_errors += 1
                print inst


class LinkCSVWriter(CSVWriter):
    """Given a query and output filename, write CSV with geo links."""

    def __init__(self, filename, query, max_commits = None, links_only = False,
                 diff_authors = False):
        self.filename = filename
        self.query = query
        self.max_commits = max_commits
        self.links_only = links_only
        self.diff_authors = diff_authors
        print "using query: %s" % self.query
        self.fields = ['sha1', 'location', 'lat', 'long', 'path_id',
                       'path_order', 'date', 'author']
        # double-quoted fields
        self.fields_to_quote = ['location', 'date']
        self.crlf = '\r\n' # yes, add Windows line ending
        conn = pymongo.Connection()
        self.db = conn['processed']
        self.build_csv()

    def should_write_pair(self, c, p):
        """Ensure valid geo values, plus check optional filters."""
        retval = True
        retval = retval and ('lat' in c and 'long' in c)
        retval = retval and (p and 'lat' in p and 'long' in p)
        if self.links_only:
            retval = retval and (c['lat'] != p['lat'] and c['long'] != p['long'])
        if self.diff_authors:
            retval = retval and (c['author'] != p['author'])
        return retval

    def process_commit(self, c):
        """Write related commits as CSV to output file."""
        if 'location' not in c:
            c['location'] = 'unknown'
        for p_sha1 in c['parents']:
            p = self.db.commits.find_one({'sha1': p_sha1})
            if self.should_write_pair(c, p):
                formatted = ''
                if 'location' not in p:
                    p['location'] = 'unknown'
                c['path_id'] = self.path_id
                c['path_order'] = 0
                formatted += self.format_commit(c)
                p['path_id'] = self.path_id
                p['path_order'] = 1
                formatted += self.format_commit(p)
                self.path_id += 1

                formatted = formatted.encode('ascii', 'xmlcharrefreplace')
                try:
                    self.output.write(formatted)
                except UnicodeEncodeError as inst:
                    print c
                    unicode_errors += 1
                    print inst

    def build_csv(self):
        self.output = open(self.filename, 'w')
        self.output.write(self.csv_header())

        print "[time] [commits parsed]"
        start = time.time()

        cursor = self.db.commits.find(self.query)
        self.path_id = 0
        unicode_errors = 0
        i = 0
        s = ''
        for c in cursor:
            csv_str = self.process_commit(c)
            i += 1

            if i == HARD_MAX_COMMITS:
                break
            if self.max_commits and (i == self.max_commits):
                break

            if i % PRINT_INTERVAL == 0:
                elapsed = float(time.time() - start)
                print '%0.3f %i' % (elapsed, i)

        elapsed = float(time.time() - start)
        print "read %i commits in %0.3f seconds" % (i, elapsed) 
        print "skipped %i unicode errors" % unicode_errors
        print "%0.2f commits per second" % (i / elapsed)


class CSVFrontend:

    def __init__(self):
        self.date_format = "%Y-%m-%d"
        self.query = {}
        self.parse_args()
        self.build_query()
        if self.options.type == 'link':
            LinkCSVWriter(self.options.file_name, self.query,
                      self.options.max_commits, self.options.links_only,
                      self.options.diff_authors)
        elif self.options.type == 'loc':
            LocCSVWriter(self.options.file_name, self.query,
                      self.options.max_commits)

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
        opts.add_option("--links_only", action = "store_true",
                        default = False,
                        help = "only write out links with different locations?")
        opts.add_option("--diff_authors", action = "store_true",
                        default = False,
                        help = "only write out links with different authors")
        opts.add_option("--type", type = 'string',
                        default = DEF_TYPE, help = "optional longitude max")
        opts.add_option("--date_start", type = 'string',
                        default = None, help = "optional start date as YYYY-MM-DD")
        opts.add_option("--date_end", type = 'string',
                        default = None, help = "optional end date as YYYY-MM-DD")
        opts.add_option("--project", type = 'string',
                        default = None, help = "optional project file")
        opts.add_option("--lat_min", type = 'float',
                        default = None, help = "optional latitude min")
        opts.add_option("--lat_max", type = 'float',
                        default = None, help = "optional latitude max")
        opts.add_option("--long_min", type = 'float',
                        default = None, help = "optional longitude min")
        opts.add_option("--long_max", type = 'float',
                        default = None, help = "optional longitude max")
        options, arguments = opts.parse_args()

        if not options.file_name:
            options.file_name = DEF_OUTPUT_FILENAME
            if options.max_commits:
                options.file_name += '-%i' % options.max_commits
            options.file_name += OUTPUT_EXT

        if options.date_start:
            options.date_start = time.strptime(options.date_start, self.date_format)
            options.date_end = time.strptime(options.date_end, self.date_format)

        self.options = options

    def build_query(self):
        options = self.options
        if options.lat_min and options.lat_max:
            self.query["lat"] = {"$gt": options.lat_min, "$lt": options.lat_max}
        if options.long_min and options.long_max:
            self.query["long"] = {"$gt": options.long_min, "$lt": options.long_max}            
        if options.date_start and options.date_end:
            self.query["date"] = {"$gt": options.date_start, "$lt": options.date_end}
        if options.project:
            self.query["project"] = options.project


# Example usage w/o frontend:
def sample_query():
    date_start = datetime(2010, 1, 1)
    date_end = datetime(2010, 2, 1)
    project = 'rails'
    query = {
        "date": {"$gt": date_start, "$lt": date_end},
        "project": project
    }
    LinkCSVWriter('sample_query.csv', query)


if __name__ == "__main__":
    CSVFrontend()

# vim: tabstop=4 expandtab shiftwidth=4 softtabstop=4