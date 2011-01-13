#!/usr/bin/env python
'''Basic metrics for GitHub social graph

Assumes a file where each line has this form:
  { "tasukuchan": { "users": [ "daijiro", "tmaesaka" ] }  }

Error lines look like this:
  { "ngenera": { "error": "Not Found" }  }
'''

import json
import time
import logging

filename = 'followers'

print_intervals = True

print_interval = 10000

limit = 10000 # max lines to read

level = logging.INFO

logging.basicConfig(level=logging.INFO)
lg = logging.getLogger("analysis")
lg.setLevel(level)


graph = {}  # graph[src][dst] = 1 --> src follows dst
seen = {}  # dict of user names to totals.  Mostly to verify no dupe usernames
unique = set([])  # track unique usernames seen
empty = set([])  # map of antisocial users: no followers/following
error = {}  # map of users for which the query returned an error
lines = 0  # lines read in
links = 0  # total links seen so far
bidir = 0  # bidirectional links, counted once
max = -1  # max links for one user
max_line = -1  # line number for tracking max value after

start = time.time()
f = open(filename, 'r')
for l in f:

    if l[-1] == '\n':
        l = l.rstrip()
    else:
        raise Exception("line w/no newline?")
    line = json.loads(l)
    lines += 1
    #print("reading line %i: %s" % (lines, line))
    if len(line.keys()) != 1:
        raise Exception("line with other stuff:" % line)
    src = line.keys()[0]
    unique.add(src)

    if 'error' in line[src]:
        #print("adding error at line %i: %s" % (lines, line))
        error[src] = 1
    elif 'users' not in line[src]:
        raise Exception("line with src but no users array?")
    else:
        users = len(line[src]['users'])
        seen[src] = users
        if users > max:
            max = users
            max_line = lines
        for dst in line[src]['users']:
            unique.add(dst)
            links += 1
            if src not in graph:
                graph[src] = {}
            graph[src][dst] = 1
            if dst in graph and (src in graph[dst]):
                bidir += 1

    if lines == limit:
        break
    if print_intervals:
        if lines % print_interval == 0:
            print lines


duration = time.time() - start

print "time: %0.3f sec" % duration
print "filename: ", filename
print "lines: ", lines
print "links: ", links
print "bidir: ", bidir
print "errors: ", len(error)
print "unique usernames seen: ", len(unique)
print "max: %i, at line %i" % (max, max_line)

