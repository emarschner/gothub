#!/usr/bin/env python
# Brandon Heller
#
# Given an input geo-graph from geo_reduce.py, cluster nodes.
from optparse import OptionParser
import os
import time

import networkx as nx

from geo_graph import geo_stats, geo_cluster, geo_reduce, geo_filter_nones

# Default input filename - .gpk extension assumed
DEF_INPUT = "followers"

# Write output file by default?
DEF_WRITE = True


class GeoGraphProcessor:

    def __init__(self, process_fcn, in_name, in_ext, out_name = None,
                 out_ext = None, write = False):

        # Input graph
        input_path = os.path.join(in_name, in_name + '.grg')
        # Nodes: (lat, long) tuples w/ list of associated users & location strings
        # Edges: weight: number of links in this direction
        g = nx.read_gpickle(input_path)
        if not g:
            raise Exception("null input file for input path %s" % input_path)

        r = process_fcn(g)

        if write:
            geo_path = os.path.join(in_name, in_name + '.g2')
            nx.write_gpickle(r, geo_path)


class GeoReduce:

    def __init__(self):
        self.parse_args()
        options = self.options

        def process_fcn(g):
            print "now processing"
            input_stats = geo_stats(g)
            geo_filter_nones(g)
            filtered_stats = geo_stats(g)
            node_map = geo_cluster(g, restrict = False)
            #r = nx.DiGraph()
            r = geo_reduce(g, node_map)
            output_stats = geo_stats(r)
            print "input stats: \n" + input_stats
            print "filtered stats: \n" + filtered_stats
            print "output stats: \n" + output_stats

            return r

        GeoGraphProcessor(process_fcn, self.options.input, '.grg',
                          out_ext = '.g2', write = self.options.write)

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
    GeoReduce()