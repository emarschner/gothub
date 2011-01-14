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
import pylab
import matplotlib.pyplot as plt

filename = 'followers'

print_intervals = True

print_interval = 10000

limit = 100000 # max lines to read

threshold = 500 # above this, note names

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
        if users > max:
            max = users
            max_line = lines
        if users == 0:
            empty.add(src)

        if src not in seen:
            seen[src] = users
        else:
            raise Exception("duplicated line for src: %s" % src)

        if src not in graph:
            graph[src] = {}
        else:
            raise Exception("duplicated addition to graph variable")

        for dst in line[src]['users']:
            unique.add(dst)
            links += 1
            graph[src][dst] = 1
            if dst in graph and (src in graph[dst]):
                bidir += 1

    if lines == limit:
        break
    if print_intervals:
        if lines % print_interval == 0:
            print lines

duration = time.time() - start

above = [user for user in seen.keys() if seen[user] >= threshold]

print "time: %0.3f sec" % duration
print "filename: ", filename
print "lines: ", lines
print "links: ", links
print "bidir: ", bidir
print "errors: ", len(error)
print "empty: ", len(empty)
print "unique usernames seen: ", len(unique)
print "valid lines added: ", len(seen)
print "max: %i, at line %i" % (max, max_line)
print "len(graph): ", len(graph)
print "users w/ at least %i in list: %s" % (threshold, above) 

total_users = len(graph)
user_list = [(user, len(graph[user])) for user in graph.keys()]
user_list = sorted(user_list, key=lambda x: x[1])
points = [(user_list[i][1], float(i + 1) / total_users) for i in range(total_users)]
#print points
x = [point[0] for point in points]
y = [point[1] for point in points]


def plot(out_fname = None):

    fig = pylab.figure()
    l1 = pylab.plot(x, y, "b-")
    #l2 = pylab.plot(range(1,BINS), results_one_queue[6], "r--")
    #l3 = pylab.plot(range(1,BINS), results_two_queue[6], "g-.")
    pylab.grid(True)
    pylab.xscale("linear")
    pylab.axis([0, 100, 0, 1.0])
    pylab.xlabel("total")
    pylab.ylabel("CDF")
    pylab.title("Link degree")
    #pylab.legend((l1,l2,l3), ("no congestion","one congestion point","two congestion points"),"lower right")
    if out_fname:
        fig.savefig(out_fname)
    else:
        pylab.show()

plot()
#plot(filename + '.png')
