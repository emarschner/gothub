#!/usr/bin/env python
# Brandon Heller
#
# Plot graphs from pre-computed stats files
import json
from optparse import OptionParser
import os

import matplotlib.pyplot as plt
import networkx as nx
import pylab


# Input filename of metrics
DEF_INPUT = 'followers_3'

# Name of output file
DEF_OUTPUT_DIR = './'

EXT = 'png'


class Plot():
    
    def __init__(self):
        self.parse_args()
        options = self.options
        input_path = os.path.join(options.input, options.input + '.stats')
        input_file = open(input_path, 'r')
        stats = json.load(input_file)
        self.plot_all(stats)

    def parse_args(self):
        opts = OptionParser()
        opts.add_option("-i", "--input", type = 'string', 
                        default = DEF_INPUT,
                        help = "name of input file")
        opts.add_option("-o", "--output_dir", type = 'string',
                        default = DEF_OUTPUT_DIR,
                        help = "name of output file")
        opts.add_option("-w", "--write",  action = "store_true",
                        default = False,
                        help = "write plots, rather than display?")
        options, arguments = opts.parse_args()
        self.options = options

    def plot(self, ptype, data, color, axes, label, xscale, yscale, write = False, num_bins = None):

        def gen_dirname():
            return self.options.input.split('.')[0]

        def gen_fname(name, insert):
            return name + '_' + insert + '.' + EXT

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
        if self.options.write:
            dirname = gen_dirname()
            if dirname not in os.listdir('.'):
                os.mkdir(dirname)
                print "created directory:", dirname
            filepath = os.path.join(dirname, dirname + '_' + gen_fname(label, xscale + '_' + yscale + '_' + ptype))
            fig.savefig(filepath)
        else:
            pylab.show()

    def plot_all(self, stats):
        if "degree" in stats:
            degree = stats["degree"]["values"]
            self.plot('cdf', degree, "b-", [0, 100, 0, 1.0], "Degree", "linear", "linear", True)
            self.plot('cdf', degree, "b-", [0, 10000, 0, 1.0], "Degree", "log", "linear", True)
            self.plot('ccdf', degree, "b-", [0, 100, 0, 1.0], "Degree", "linear", "linear", True)
            self.plot('ccdf', degree, "b-", [0, 10000, 0, 1.0], "Degree", "log", "log", True)
            self.plot('pdf', degree, "b-", [0, 100, 0, 1.0], "Degree", "linear", "linear", True)
            self.plot('pdf', degree, "b-", [0, 10000, 0, 1.0], "Degree", "log", "linear", True)
        
        if "pagerank" in stats:
            pagerank = stats["pagerank"]["values"]
            self.plot('cdf', pagerank, "r-", [0, sorted(pagerank)[-1], 0, 1.0], "PageRank", "linear", "linear", True)
            self.plot('cdf', pagerank, "r-", [10e-7, 10e-4, 0, 1.0], "PageRank", "log", "linear", True)
            self.plot('ccdf', pagerank, "r-", [0, sorted(pagerank)[-1], 0, 1.0], "PageRank", "linear", "linear", True)
            self.plot('ccdf', pagerank, "r-", [10e-7, 10e-3, 0, 1.0], "PageRank", "log", "log", True)
            self.plot('pdf', pagerank, "r-", [10e-7, 10e-4, 0, 1.0], "PageRank", "linear", "linear", True)

        if "bc" in stats:
            bc = stats["bc"]["values"]
            self.plot('cdf', bc, "r-", [0, sorted(bc)[-1], 0, 1.0], "BetweennessCentrality", "linear", "linear", True)
            self.plot('cdf', bc, "r-", [10e-9, 10e-3, 0, 1.0], "BetweennessCentrality", "log", "linear", True)
            self.plot('ccdf', bc, "r-", [0, sorted(bc)[-1], 0, 1.0], "BetweennessCentrality", "linear", "linear", True)
            self.plot('ccdf', bc, "r-", [10e-9, 10e-3, 0, 1.0], "BetweennessCentrality", "log", "log", True)
            self.plot('pdf', bc, "r-", [10e-9, 10e-3, 0, 1.0], "BetweennessCentrality", "linear", "linear", True)

        
if __name__ == "__main__":
    Plot()
