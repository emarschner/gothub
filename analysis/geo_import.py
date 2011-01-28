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


class GeoImport:

    def __init__(self, post_fcn = None):
        self.parse_args()
        options = self.options

        input = options.input
        # Input graph
        input_path = os.path.join(input, input + '.gpk')
        self.g = nx.read_gpickle(input_path)
        if not self.g:
            raise Exception("null input file for input path %s" % input_path)
        # Output (reduced) graph.
        # Nodes: (lat, long) tuples w/ list of associated users & location strings
        # Edges: weight: number of links in this direction
        self.r = nx.DiGraph()

        conn = Connection()
        self.input_db = conn[self.options.input_db]
        self.input_coll = self.input_db[self.options.input_coll]

        print "now processing"
        self.reduce()
        print geo_stats(self.r)

        if options.write:
            geo_path = os.path.join(input, input + '.grg')
            nx.write_gpickle(self.r, geo_path)

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
        opts.add_option("-v", "--verbose", action = "store_true",
                        dest = "verbose", default = False,
                        help = "verbose output?")
        options, arguments = opts.parse_args()
        self.options = options

    def get_user_data(self, num):
        #print "looking up number: %i" % num
        return self.input_coll.find_one({'number': int(num)})

    @staticmethod
    def get_node_key(data):
        # Return node tuple
        lat = data["lat"]
        long = data["long"]
        return (lat, long)

    def add_geo_node(self, data):
        node_key = self.get_node_key(data)
        name = data["name"]
        location = data["location"]

        if not self.r.has_node(node_key):
            self.r.add_node(node_key)
            self.r.node[node_key]["name"] = set([])
            self.r.node[node_key]["location"] = set([])
            self.r.node[node_key]["selfedges"] = 0

        # Note this username
        self.r.node[node_key]["name"].add(name)
        self.r.node[node_key]["location"].add(location)

    def add_geo_edge(self, src_data, dst_data):
        src_key = self.get_node_key(src_data)
        dst_key = self.get_node_key(dst_data)

        if src_key == dst_key:
            #print "not incrementing selfedges for src/dst pair"
            pass
            #assume that the weight field can handle this
            #self.r.node[src_key]["selfedges"] += 1

        if not self.r.has_edge(src_key, dst_key):
            self.r.add_edge(src_key, dst_key)
            self.r[src_key][dst_key]["weight"] = 0

        self.r[src_key][dst_key]["weight"] += 1

    def reduce(self):

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

            # Get DB data for both edges
            src_data = self.get_user_data(src)
            dst_data = self.get_user_data(dst)

            # Do we have geo data for both edges?
            have_src_geo = src_data and "lat" in src_data
            have_dst_geo = dst_data and "lat" in dst_data

            if have_src_geo and have_dst_geo:
                #print src_data, dst_data
                edges_geo[2] += 1
                self.add_geo_node(src_data)
                self.add_geo_node(dst_data)
                self.add_geo_edge(src_data, dst_data)
            elif have_src_geo or have_dst_geo:
                edges_geo[1] += 1
            else:
                #print "unable to locate data for %s and %s" % (src, dst)
                edges_geo[0] += 1

            edges += 1
            if edges % self.options.print_interval == 0:
                elapsed = float(time.time() - start)
                print '%0.3f %i' % (elapsed, edges)


        print "read %i edges" % edges
        for i in edges_geo:
            print "edges w/ %i geo-locations: %i" % (i, edges_geo[i])


if __name__ == "__main__":
    GeoImport()
