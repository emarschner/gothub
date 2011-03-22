#!/usr/bin/env python
# Brandon Heller
#
# Given an input geo-graph from geo_reduce.py, cluster nodes.
from optparse import OptionParser

import networkx as nx

from geo_graph import geo_stats, geo_cluster, geo_reduce, geo_filter_nones
from geo_graph import GeoGraphProcessor, geo_check_for_isolated
from geo_graph import geo_box_reduce, CITIES_WORLD, CITIES_AMERICA
from geo_graph import CITY_ORDERINGS_WORLD
from geo_graph import CITY_ORDERING_AMERICA_DIST

# Default input filename - .gpk extension assumed
DEF_INPUT = "followers"

# Write output file by default?
DEF_WRITE = True

# Write JSON by default?
DEF_WRITE_JSON = True

# Write gexf by default?
DEF_WRITE_GEXF = True

# Filter cities by default?
DEF_FILTER_CITIES = True

# Maximum edges for GEXF output: if False, use all.
DEF_MAX_EDGES = None

# From gothub/queries.py:
# Lat/long pairs.
GEO_FILTERS = {
    'world': [[-89.9, -179.9], [89.9, 179.9]],
    'bayarea': [[37.2, -123.0], [38.0, -121.0]],
    'cali': [[32.81, -125.0], [42.0, -114.0]],
    'america': [[25.0, -125.0], [50.0, -65.0]],
    'europe': [[33.0, 40.0], [71.55, 71.55]],
    'australia': [[-48.0, 113.1], [-10.5, 179.0]]
}

# List of tuples. Each tuple has a (lat,long) pair, name, and radius in miles.
CITY_FILTERS = {
    'world': CITIES_WORLD,
    'america': CITIES_AMERICA
}

CITY_FILTER_DEF = 'world'

CITY_ORDERINGS_AMERICA = {
    'dist': CITY_ORDERING_AMERICA_DIST
}

CITY_ORDERINGS = {
    'world': CITY_ORDERINGS_WORLD,
    'america': CITY_ORDERINGS_AMERICA
}


class GeoReduce:

    def __init__(self):
        self.parse_args()
        options = self.options

        city_list = CITY_FILTERS[self.options.city_filter]
        city_ordering = CITY_ORDERINGS[self.options.city_filter][self.options.ordering_type]

        def process_fcn(g):
            print "now processing"
            input_stats = geo_stats(g)
            geo_check_for_isolated(g)
            geo_filter_nones(g)
            geo_check_for_isolated(g)
            filtered_stats = geo_stats(g)
            node_map = geo_cluster(g, cities = [], restrict = False)
            #r = nx.DiGraph()
            g = geo_reduce(g, node_map)
            node_map = geo_cluster(g, cities = city_list, restrict = False)
            first_pass_stats = geo_stats(g)
            if self.options.filter_cities:
                g = geo_reduce(g, node_map)
                output_stats = geo_stats(g)
            elif self.options.geo_filter:
                print "Geo filtering..."
                g = geo_box_reduce(g, GEO_FILTERS[self.options.geo_filter])
                output_stats = geo_stats(g)

            print "input stats: \n" + input_stats
            print "filtered stats: \n" + filtered_stats
            print "first pass (no city filtering): \n"+ first_pass_stats
            if self.options.filter_cities or self.options.geo_filter:
                print "output stats (after city filter): \n" + output_stats

            return g

        GeoGraphProcessor(process_fcn, self.options.input, '.grg',
                          out_ext = '.g2', write = self.options.write,
                          write_json = self.options.write_json,
                          ordering_type = self.options.ordering_type,
                          write_gexf = self.options.write_gexf,
                          filter_cities = self.options.filter_cities,
                          max_edges = self.options.max_edges,
                          geo_filter = self.options.geo_filter,
                          append = self.options.append,
                          city_filter_name = self.options.city_filter,
                          city_list = city_list,
                          city_ordering = city_ordering)

    def parse_args(self):
        opts = OptionParser()
        opts.add_option("--no-write", action = "store_false",
                        dest = "write", default = DEF_WRITE,
                        help = "don't write output file?")
        opts.add_option("-j", "--no-write-json", action = "store_false",
                        dest = "write_json", default = DEF_WRITE_JSON,
                        help = "don't write output file?")
        opts.add_option("-g", "--no-write-gexf", action = "store_false",
                        dest = "write_gexf", default = DEF_WRITE,
                        help = "don't write gexf output file?")
        opts.add_option("--ordering_type", type = 'string',
                        default = 'dist',
                        help = "ordering type, one of " + str(CITY_ORDERINGS.keys()))
        opts.add_option("--input", type = 'string', 
                        default = DEF_INPUT,
                        help = "name of input file (no ext)")
        opts.add_option("--no-filter-cities", action = "store_false",
                        dest = "filter_cities", default = DEF_FILTER_CITIES,
                        help = "filter cities?")
        opts.add_option("-m", "--max_edges", type = "int",
                        default = DEF_MAX_EDGES,
                        help = "max edges to output in GEXF; default is all")
        opts.add_option( '--geo_filter', type='choice',
                        choices = GEO_FILTERS.keys(), default = None,
                        help = '[' + ' '.join( GEO_FILTERS.keys() ) + ']' )
        opts.add_option( '--city_filter', type='choice',
                        choices = CITY_FILTERS.keys(), default = CITY_FILTER_DEF,
                        help = '[' + ' '.join( CITY_FILTERS.keys() ) + ']' )
        opts.add_option("--append", type = 'string',
                        default = None,
                        help = "string to append to file output")
        opts.add_option("-v", "--verbose", action = "store_true",
                        dest = "verbose", default = False,
                        help = "verbose output?")
        options, arguments = opts.parse_args()
        self.options = options

if __name__ == "__main__":
    GeoReduce()