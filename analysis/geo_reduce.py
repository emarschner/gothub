#!/usr/bin/env python
# Brandon Heller
#
# Given an input geo-graph from geo_reduce.py, cluster nodes.
from optparse import OptionParser

import networkx as nx

from geo_graph import geo_stats, geo_cluster, geo_reduce, geo_filter_nones
from geo_graph import GeoGraphProcessor, geo_check_for_isolated, geo_city_stats

# Default input filename - .gpk extension assumed
DEF_INPUT = "followers"

# Write output file by default?
DEF_WRITE = True


class GeoReduce:

    def __init__(self):
        self.parse_args()
        options = self.options

        def process_fcn(g):
            print "now processing"
            input_stats = geo_stats(g)
            geo_check_for_isolated(g)
            geo_filter_nones(g)
            geo_check_for_isolated(g)
            filtered_stats = geo_stats(g)
            node_map = geo_cluster(g, restrict = False, cities = [])
            #r = nx.DiGraph()
            g = geo_reduce(g, node_map)
            node_map = geo_cluster(g, restrict = False)
            first_pass_stats = geo_stats(g)
            g = geo_reduce(g, node_map)
            output_stats = geo_stats(g)
            city_stats = geo_city_stats(g)

            print "input stats: \n" + input_stats
            print "filtered stats: \n" + filtered_stats
            print "first pass (no city filtering): \n"+ first_pass_stats
            print "output stats: \n" + output_stats
            print "geo city stats: \n" + city_stats

            return g

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