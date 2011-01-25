#!/usr/bin/env python
# Brandon Heller
#
# Given an input geo-graph from geo_reduce.py, cluster nodes.
from operator import itemgetter
from optparse import OptionParser
import os
import time

import networkx as nx


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
        self.g = nx.read_gpickle(input_path)
        if not self.g:
            raise Exception("null input file for input path %s" % input_path)

        self.r = nx.DiGraph()

        print "now processing"
        self.sort(self.g)
        self.reduce()
        self.stats(self.g)

        if options.write:
            geo_path = os.path.join(input, input + '.g2')
            nx.write_gpickle(self.r, geo_path)

    def parse_args(self):
        opts = OptionParser()
        opts.add_option("-n", "--no-write", action = "store_false",
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

    def sort(self, g):
        # Find/print the top N geo locations
        n = 100
        data = []
        for node in g:
            location = g.node[node]["location"]
            data.append((node, len(g.predecessors(node)), location))
        data = sorted(data, key = itemgetter(1), reverse = True)
        top = []
        for i in range(n):
            top.append(data[i])
            print data[i]

    def reduce(self):
        pass

    def stats(self, g):
        i = 0
        print "stats for reduced graph:"
        print "\tnodes: %i" % g.number_of_nodes()
        print "\tedges: %i" % g.number_of_edges()
        total_edge_weight = 0
        for src, dst in g.edges():
            total_edge_weight += g[src][dst]["weight"]
        print "\tedge weight total: %i" % total_edge_weight
        if self.options.verbose:
            for node in g:
                print "node %i: %s" % (i, node)
                #print g.node[node]
                selfedges = g.node[node]["selfedges"]
                location = g.node[node]["location"]
                name = g.node[node]["name"]
                print "\tselfedges: %s" % selfedges
                print "\tlocations (%i): %s" % (len(location), location)
                print "\tnames: %i" % len(name)
                #print "\tnames (%i): %s" % (len(name), name)
                print "\tout_degree: %i" % len(g.neighbors(node))
                print "\tin_degree: %i" % len(g.predecessors(node))
                i += 1



if __name__ == "__main__":
    TopGeo()