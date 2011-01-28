#!/usr/bin/env python
# Brandon Heller
#
# Given an input geo-graph from geo_reduce.py, cluster nodes.
from optparse import OptionParser
import os
import time

import networkx as nx

from geo_graph import geo_stats, geo_cluster

# Default input filename - .gpk extension assumed
DEF_INPUT = "followers"

# Write output file by default?
DEF_WRITE = True


class TopGeo:

    def __init__(self, post_fcn = None):
        self.parse_args()
        options = self.options

        input = options.input
        # Input graph
        input_path = os.path.join(input, input + '.grg')
        # Nodes: (lat, long) tuples w/ list of associated users & location strings
        # Edges: weight: number of links in this direction
        g = nx.read_gpickle(input_path)
        if not g:
            raise Exception("null input file for input path %s" % input_path)

        print "now processing"
        input_stats = geo_stats(g)
        r = geo_cluster(g)
        output_stats = geo_stats(r)

        print "input stats: \n" + input_stats
        print "output stats: \n" + output_stats
        #self.stats(g)

        if options.write:
            geo_path = os.path.join(input, input + '.g2')
            nx.write_gpickle(r, geo_path)

    def parse_args(self):
        opts = OptionParser()
        opts.add_option("--no-write", action = "store_false",
                        dest = "write", default = DEF_WRITE,
                        help = "don't write output file?")
        opts.add_option("--input", type = 'string', 
                        default = DEF_INPUT,
                        help = "name of input file (no ext)")
        opts.add_option("-v", "--verbose", action = "store_true",
                        dest = "verbose", default = False,
                        help = "verbose output?")
        options, arguments = opts.parse_args()
        self.options = options


if __name__ == "__main__":
    TopGeo()