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
import os
import pylab
import matplotlib.pyplot as plt
import networkx as nx

# Compute betweenness centrality?  Gets expensive...
COMPUTE_BC = False

filename = 'followers'

ext = 'png'

print_intervals = True

print_interval = 10000

limit = 1000 # max lines to read

threshold = 500 # above this, note names

level = logging.INFO

logging.basicConfig(level=logging.INFO)
lg = logging.getLogger("analysis")
lg.setLevel(level)


g = nx.DiGraph()  # network graph
seen = {}  # dict of user names to totals.  Mostly to verify no dupe usernames
unique = set([])  # track unique usernames seen
empty = set([])  # map of antisocial users: no followers/following
error = {}  # map of users for which the query returned an error
lines = 0  # lines read in
links = 0  # total links seen so far
bidir = 0  # bidirectional links, counted once
max_links = -1  # max links for one user
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
        if users > max_links:
            max_links = users
            max_line = lines
        if users == 0:
            empty.add(src)

        if src not in seen:
            seen[src] = users
        else:
            raise Exception("duplicated line for src: %s" % src)

        for dst in line[src]['users']:
            unique.add(dst)
            links += 1
            g.add_edge(src, dst) # dst node added automatically
            if dst in g and src in g[dst]:
                bidir += 1

    if lines == limit:
        break
    if print_intervals:
        if lines % print_interval == 0:
            print lines

duration = time.time() - start

above = [user for user in seen.keys() if seen[user] >= threshold]

print "time to parse: %0.3f sec" % duration
print "filename: ", filename
print "lines: ", lines
print "links: ", links
print "bidir: ", bidir
print "errors: ", len(error)
print "empty: ", len(empty)
print "unique usernames seen: ", len(unique)
print "valid lines added: ", len(seen)
print "max_links: %i, at line %i" % (max_links, max_line)
print "users w/ at least %i in list: %s" % (threshold, above) 

# create degree CDF
degree = [seen[user] for user in seen.keys()]

# compute PageRank.  Note: we have to ignore empties.
start = time.time()
pagerank_dict = nx.pagerank(g)
nonempty_seen = [user for user in seen.keys() if user not in empty]
pagerank = ([pagerank_dict[user] for user in nonempty_seen])
duration = time.time() - start
print "time to gen pagerank: %0.3f sec" % duration
#print pagerank

# compute betweenness centrality  - should empties get added back to CDF?
if COMPUTE_BC:
    start = time.time()
    bc_dict = nx.betweenness_centrality(g)
    bc = ([bc_dict[user] for user in nonempty_seen])
    duration = time.time() - start
    print "time to gen betweenness centrality: %0.3f sec" % duration

def gen_dirname():
    return filename + '_' + str(lines)

def gen_fname(name, insert):
    return name + '_' + insert + '.' + ext

def plot(ptype, data, color, axes, label, xscale, yscale, write = False, num_bins = None):
    fig = pylab.figure()
    if ptype == 'cdf':
        x = sorted(data)
        y = [(float(i + 1) / len(x)) for i in range(len(x))]
    elif ptype == 'ccdf':
        x = sorted(data)
        y = [1.0 - (float(i + 1) / len(x)) for i in range(len(x))]
    elif ptype == 'pdf':
        # bin data by value
        hist = {}
        data_max = max(data)
        # use all bins if our data is integers
        if data_max == int(data_max):
            num_bins = data_max
        else:
            num_bins = 1000
        for d in data:
            bin = int((float(d) * num_bins) / float(data_max))
            if bin not in hist:
                hist[bin] = 1
            else:
                hist[bin] += 1

        x = []
        y = []
        for i in range(num_bins + 1):
            range_lo = float(i) / float(num_bins) * data_max
            range_hi = float(i + 1) / float(num_bins) * data_max
            y_val = (float(hist[i]) / len(data)) if i in hist else 0
            x.append(range_lo)
            y.append(y_val)

            x.append(range_hi)
            y.append(y_val)

        # scale max Y
        axes[3] = float(max(hist.values())) / len(data)
    else:
        raise Exception("invalid plot type")
    l1 = pylab.plot(x, y, color)
    #l2 = pylab.plot(range(1,BINS), results_one_queue[6], "r--")
    #l3 = pylab.plot(range(1,BINS), results_two_queue[6], "g-.")
    pylab.grid(True)
    pylab.xscale(xscale)
    pylab.yscale(yscale)
    pylab.axis(axes)
    pylab.xlabel("value")
    pylab.ylabel(ptype)
    pylab.title(label)
    #pylab.legend((l1,l2,l3), ("no congestion","one congestion point","two congestion points"),"lower right")
    if write:
        dirname = gen_dirname()
        if dirname not in os.listdir('.'):
            os.mkdir(dirname)
        filepath = os.path.join(dirname, dirname + '_' + gen_fname(label, xscale + '_' + yscale + '_' + ptype))
        fig.savefig(filepath)
    else:
        pylab.show()

plot('cdf', degree, "b-", [0, 100, 0, 1.0], "Degree", "linear", "linear", True)
plot('cdf', degree, "b-", [0, 10000, 0, 1.0], "Degree", "log", "linear", True)
plot('ccdf', degree, "b-", [0, 100, 0, 1.0], "Degree", "linear", "linear", True)
plot('ccdf', degree, "b-", [0, 10000, 0, 1.0], "Degree", "log", "log", True)
plot('pdf', degree, "b-", [0, 100, 0, 1.0], "Degree", "linear", "linear", True)
plot('pdf', degree, "b-", [0, 10000, 0, 1.0], "Degree", "log", "linear", True)

plot('cdf', pagerank, "r-", [0, sorted(pagerank)[-1], 0, 1.0], "PageRank", "linear", "linear", True)
plot('cdf', pagerank, "r-", [10e-7, 10e-4, 0, 1.0], "PageRank", "log", "linear", True)
plot('ccdf', pagerank, "r-", [0, sorted(pagerank)[-1], 0, 1.0], "PageRank", "linear", "linear", True)
plot('ccdf', pagerank, "r-", [10e-7, 10e-4, 0, 1.0], "PageRank", "log", "log", True)
plot('pdf', pagerank, "r-", [10e-7, 10e-4, 0, 1.0], "PageRank", "linear", "linear", True)

if COMPUTE_BC:
    plot('cdf', bc, "r-", [0, sorted(bc)[-1], 0, 1.0], "BetweennessCentrality", "linear", "linear", True)
    plot('cdf', bc, "r-", [10e-9, 10e-3, 0, 1.0], "BetweennessCentrality", "log", "linear", True)
    plot('ccdf', bc, "r-", [0, sorted(bc)[-1], 0, 1.0], "BetweennessCentrality", "linear", "linear", True)
    plot('ccdf', bc, "r-", [10e-9, 10e-3, 0, 1.0], "BetweennessCentrality", "log", "log", True)
    plot('pdf', bc, "r-", [10e-9, 10e-3, 0, 1.0], "BetweennessCentrality", "linear", "linear", True)
