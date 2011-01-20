#!/usr/bin/env python
'''Basic metrics for GitHub social graph

'''

import time
import logging
import os
import pylab
import matplotlib.pyplot as plt
import networkx as nx

# Compute betweenness centrality?  Gets expensive...
COMPUTE_BC = False

ext = 'png'

level = logging.INFO

logging.basicConfig(level=logging.INFO)
lg = logging.getLogger("analysis")
lg.setLevel(level)

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
