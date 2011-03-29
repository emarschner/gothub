#!/usr/bin/env python
# Brandon Heller
#
# GeoGraph
#

#
import json
from operator import itemgetter
import os
import sys

import networkx as nx
import numpy as np

# From http://hoegners.de/Maxi/geo/
import geo


SEP = "\t"  # default separator

class GeoGraph(nx.DiGraph):
    """GeoGraph: a directed, weighted graph with a geographic embedding.
    
    GeoGraphs are constructed as augmented NetworkX graphs where:
      nodes are (lat, long) tuples
      edges have a required 'weight' field

    For later analysis, the following node data fields are also useful:
      locations: dict of corresponding location keys and array of name values
      weight: total number of users corresponding to this location.

    The advantage of using a GeoGraph is that it comes with additional
    functions for modifying and displaying these graphs.  For example, the
    GEXF output function produces output suitable for viewing in Gephi, a
    network analysis program.
    """

    # Extension for pickled GeoGraphs
    EXT = '.geo'

    def __init__(self):
        super(GeoGraph, self).__init__()

    @staticmethod
    def get_key(data):
        # Return node tuple
        lat = data["lat"]
        long = data["long"]
        return (lat, long)

    def add_name_location_data(self, key, name, location):
        """Add name and location data for a key.
        
        Note the use of a set, so that when we encounter popular usernames,
        they're only counted once.
        """
        locations = self.node[key]["locations"]
        if location not in locations:
            locations[location] = set([])
        if name not in locations[location]:
            self.node[key]["weight"] += 1
        locations[location].add(name)

    def add_geo_node(self, data):
        key = self.get_key(data)

        if not self.has_node(key):
            self.add_node(key)
            self.node[key]["weight"] = 0
            self.node[key]["locations"] = {}

        # Append the name/location values
        name = data["name"]
        location = data["location"]
        self.add_name_location_data(key, name, location)

    def add_geo_edge(self, src_data, dst_data):
        src_key = self.get_key(src_data)
        dst_key = self.get_key(dst_data)

        if not self.has_edge(src_key, dst_key):
            self.add_edge(src_key, dst_key)
            self[src_key][dst_key]["weight"] = 0

        self[src_key][dst_key]["weight"] += 1

    def stats(self, sep = SEP, verbose = False):
        """Compute stats for a geo-graph."""
        i = 0
        node_weight = 0
        locations = 0
        for node in self.nodes_iter():
            node_weight += self.node[node]["weight"]
            locations += len(self.node[node]["locations"])
        edge_weight = 0
        for src, dst in self.edges_iter():
            edge_weight += self[src][dst]["weight"]
    
        s = ''
        s += sep + "nodes: %i\n" % self.number_of_nodes()
        s += sep + "edges: %i\n" % self.number_of_edges()
        s += sep + "node weight: %0.2f\n" % node_weight
        s += sep + "edge weight: %0.2f\n" % edge_weight
        s += sep + "locations: %i\n" % locations
        if verbose:
            s += sep + "nodes: %s\n" % self.nodes()
            s += sep + "edges: %s\n" % self.edges()
            s += sep + "node data: %s\n" % [self.node[n] for n in self.nodes()]
            s += sep + "edge data: %s\n" % [self[src][dst] for src, dst in self.edges()]
    
        return s

    def write(self, path, ext = EXT):
        '''Write to file.'''
        filename = path + ext
        print "writing GeoGraph to %s" % filename
        nx.write_gpickle(self, filename)