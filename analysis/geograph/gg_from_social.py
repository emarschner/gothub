#!/usr/bin/env python
# Brandon Heller
#
# Given an input graph of GitHub user IDs, geo-locate these and create a
# reduced graph with edges connecting lat/long pairs.

from optparse import OptionParser
import os
import time

import networkx as nx
from pymongo import Connection

from geo_graph import geo_stats

from graph import GeoGraph

# Default max number of edges to parse
# Set to None to read all.
DEF_MAX_EDGES = None

# Default input filename - .gpk extension assumed
DEF_INPUT = "followers_1000"

# Write output file by default?
DEF_WRITE = True

# Default DB names
DEF_INPUT_DB_NAME = 'processed'

# Default collection name
DEF_INPUT_COLL = 'users'

# Interval between printing edge total
DEF_PRINT_INTERVAL = 10000

# Print locations strings at end?
DEF_PRINT_LOCS = False


class GeoImport:

    def __init__(self, post_fcn = None):
        self.parse_args()
        options = self.options

        input = options.input
        # Input graph
        input_path = os.path.join(input, input + '.gpk')
        print " reading input graph from %s" % input_path
        self.g = nx.read_gpickle(input_path)
        if not self.g:
            raise Exception("null input file for input path %s" % input_path)

        conn = Connection()
        self.input_db = conn[self.options.input_db]
        self.input_coll = self.input_db[self.options.input_coll]

        print " now processing"
        gg = self.map_users_to_geo()
        print gg.stats()

        if options.write:
            geo_path = os.path.join(input, input)
            gg.write(geo_path)

    def parse_args(self):
        opts = OptionParser()
        opts.add_option("-m", "--max_edges", type = "int",
                        default = DEF_MAX_EDGES,
                        help = "max edges to parse; default is all")
        opts.add_option("--print_interval", type = "int",
                        default = DEF_PRINT_INTERVAL,
                        help = "edges for print interval")
        opts.add_option("-n", "--no-write", action = "store_false",
                        dest = "write", default = DEF_WRITE,
                        help = "don't write output file?")
        opts.add_option("--input_db", type = 'string', 
                        default = DEF_INPUT_DB_NAME,
                        help = "name of input database (processed)")
        opts.add_option("--input_coll", type = 'string',
                        default = DEF_INPUT_COLL,
                        help = "name of input collection")
        opts.add_option("--input", type = 'string', 
                        default = DEF_INPUT,
                        help = "name of input file (no ext)")
        opts.add_option("--print_locs", action = "store_true",
                        default = DEF_PRINT_LOCS,
                        help = "print loc strings at end?")
        opts.add_option("-v", "--verbose", action = "store_true",
                        dest = "verbose", default = False,
                        help = "verbose output?")
        options, arguments = opts.parse_args()
        self.options = options

    def get_user_data(self, num):
        #print "looking up number: %i" % num
        return self.input_coll.find_one({'number': int(num)})

    def map_users_to_geo(self):
        '''From a DiGraph of users, create a GeoGraph of coordinate pairs.'''
        r = GeoGraph()

        edges = 0  # Edges we've read in
        edges_geo = {}
        edges_geo[0] = 0  # Sad edges
        edges_geo[1] = 0  # Singly-geo-located edges
        edges_geo[2] = 0  # Doubly-geo-located edges

        start = time.time()
        for (src, dst) in self.g.edges_iter():

            if self.options.max_edges and (edges >= self.options.max_edges):
                break

            try:
                #print src, dst
                trash = int(src) + int(dst)
            except ValueError:
                raise Exception("attempted to read non-int node names")

            # Get DB data for both nodes
            src_data = self.get_user_data(src)
            dst_data = self.get_user_data(dst)

            # Do we have geo data for both nodes?
            have_src_geo = src_data and "lat" in src_data
            have_dst_geo = dst_data and "lat" in dst_data

            if have_src_geo:
                r.add_geo_node(src_data)
            if have_dst_geo:
                r.add_geo_node(dst_data)

            if have_src_geo and have_dst_geo:
                #print src_data, dst_data
                edges_geo[2] += 1
                r.add_geo_edge(src_data, dst_data)
            elif have_src_geo or have_dst_geo:
                edges_geo[1] += 1
            else:
                #print "unable to locate data for %s and %s" % (src, dst)
                edges_geo[0] += 1

            edges += 1
            if edges % self.options.print_interval == 0:
                elapsed = float(time.time() - start)
                print '%0.3f %i' % (elapsed, edges)


        print " read %i edges" % edges
        for i in edges_geo:
            print "\tedges w/ %i geo-locations: %i" % (i, edges_geo[i])

        if self.options.print_locs:
            for key in r.nodes_iter():
                print key,
                for loc, users in r.node[key]["locations"].iteritems():
                    print "| %s: %s " % (loc, " ".join([str(user) for user in users])),
                print ""

        return r


if __name__ == "__main__":
    GeoImport()
