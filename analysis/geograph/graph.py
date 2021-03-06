#!/usr/bin/env python
# Brandon Heller
#
# GeoGraph
#

#
import json
from operator import itemgetter
import os
import pickle
import sys

import networkx as nx
import numpy as np

# From http://hoegners.de/Maxi/geo/
import geo


SEP = "\t"  # default separator

# Add edges only when both nodes have valid locations
VALID_LOCATIONS_ONLY = True

# This ugly hack only left in to generate a matrix diag matching a previously
# generated image.  DO NOT USE!
USE_ORIGINAL_WRONG_NAMES = False


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

    def __init__(self, filename = None):
        super(GeoGraph, self).__init__()

    @staticmethod
    def read(filename):
        """Return GeoGraph from pickled file if filename exists."""
        if not os.path.exists(filename):
            raise Exception("no file found: %s" % filename)
        else:
            print " reading input graph from %s" % filename
            file = open(filename, 'r')
            g = pickle.load(file)
            g.remove_nones()
            return g

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

    def copy_node(self, g, key):
        """Add an already existing geo node from another GeoGraph.

        Overwrites any existing data.

        g: other GeoGraph
        key: key to copy
        """
        if not self.has_node(key):
            self.add_node(key)

        self.node[key]["weight"] = g.node[key]["weight"]
        self.node[key]["locations"] = g.node[key]["locations"]

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

    def copy_edge(self, g, src, dst):
        """Add an already existing geo edge from another GeoGraph.

        Overwrites any existing data.

        g: other GeoGraph
        src, dst: keys to copy
        """
        if not self.has_edge(src, dst):
            self.add_edge(src, dst)

        self[src][dst]["weight"] = g[src][dst]["weight"]

    def add_geo_edge(self, src_data, dst_data):
        src_key = self.get_key(src_data)
        dst_key = self.get_key(dst_data)

        if not self.has_edge(src_key, dst_key):
            self.add_edge(src_key, dst_key)
            self[src_key][dst_key]["weight"] = 0

        self[src_key][dst_key]["weight"] += 1

    def aggregate(self, old, new):
        """Aggregate an original location into the new one."""
        if not self.has_node(new):
            self.add_node(new)
            self.node[new]["weight"] = 0
            self.node[new]["locations"] = {}

        # merge node
        self.node[new]["weight"] += self.node[old]["weight"]
        old_locations = self.node[old]["locations"]
        new_locations = self.node[new]["locations"]
        for old_location, old_users in old_locations.iteritems():
            if old_location not in new_locations:
                new_locations[old_location] = set([])
            # take union of new and old sets
            new_locations[old_location] |= old_users

        # update edges.
        for src, dst in self.in_edges(old):
            # merge in new edge, delete old
            if not self.has_edge(src, new):
                self.add_edge(src, new)
                self[src][new]["weight"] = 0
            self[src][new]["weight"] += self[src][dst]["weight"]
            self.remove_edge(src, dst)

        for src, dst in self.out_edges(old):
            # merge in new edge, delete old
            if not self.has_edge(new, dst):
                self.add_edge(new, dst)
                self[new][dst]["weight"] = 0
            self[new][dst]["weight"] += self[src][dst]["weight"]
            self.remove_edge(src, dst)

        # delete old node
        self.remove_node(old)

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

    def write_gexf(self, path, ext = '.gexf', max_edges = None):
        """Write as a GEXF output, suitable for Gephi input."""
        filename = path + ext
        print "writing GeoGraph as GEXF to %s" % filename
        gexf = self.geo_gexf_graph(max_edges)
        #gexf_path = os.path.join(name, name + '_' + '_'.join(append) + ext)
        nx.write_gexf(gexf, filename)

    @staticmethod
    def gexf_viz(node):
        """Return viz param suitable for usage in Gephi."""
        lat, long = node
        return {'position': {'x': long, 'y': lat, 'z': 0}}

    def geo_gexf_graph(self, max_edges = None):
        '''Returns NX graph w/weights between city names plus vis params.'''
        good_names = 0
        good_edges = 0
        c = nx.DiGraph()
        edge_weight_total = 0
        edge_weights = []
        max_edge_weight = 0
        # Iterate over every node: O(E), where E is # edges.
        print "self.number_of_edges: %i" % self.number_of_edges()

        edges_seen = 0
        for src_node, dst_node in self.edges():
            if max_edges and (edges_seen == max_edges):
                break
            else:
                edges_seen += 1

            if self.has_edge(src_node, dst_node):
                edge_weight = self[src_node][dst_node]["weight"]
            else:
                edge_weight = 0

            if USE_ORIGINAL_WRONG_NAMES:
                src_name = self.node[src_node]['locations'].keys()[0]
                dst_name = self.node[dst_node]['locations'].keys()[0]
            else:
                src_name = self._most_popular_location(src_node)
                dst_name = self._most_popular_location(dst_node)

            if src_name:
                good_names += 1

            if dst_name:
                good_names += 1

            if VALID_LOCATIONS_ONLY and src_name and dst_name:
                c.add_edge(src_name, dst_name)
                c[src_name][dst_name]["weight"] = edge_weight
                c.node[src_name] = {'viz': self.gexf_viz(src_node)}
                c.node[dst_name] = {'viz': self.gexf_viz(dst_node)}
                c[src_name][dst_name]["weight"] = edge_weight
                edge_weight_total += edge_weight
                edge_weights.append(edge_weight)
                good_edges += 1
                if edge_weight > max_edge_weight:
                    max_edge_weight = edge_weight

        for node in c.nodes():
            #print "node", c.node[node]
            pass
        print "edge_weight_total: %i" % edge_weight_total
        print "edges_seen: %i" % edges_seen
        print "good_names: %i" % good_names
        print "good_edges: %i" % good_edges
        print "max edge weight: %i" % max_edge_weight
        return c

    def remove_nones(self):
        '''Filter out nodes at (None, None) plus links to there.'''
        if self.has_node((None, None)):
            self.remove_node((None, None))

    def _most_popular_location(self, key):
        """Returns the most popular location string corresponding to a key."""
        # location_strings = array of (location string, count) pairs
        location_strings = []
        for location, users in self.node[key]["locations"].iteritems():
            location_strings.append((location, len(users)))
        location_strings = sorted(location_strings, key = itemgetter(1), reverse = True)
        top_pair = location_strings[0]
        return top_pair[0]

    def remove_none_locations(self):
        """ONLY left in to help generate a matching to an earlier, broken graph."""
        # aggregate to nothing, then remove.
        for key in self.nodes():
            if list(self.node[key]['locations'].keys())[0] == None:
                self.aggregate(key, (None, None))
        self.remove_nones()

    def modify_name(self, key, old, new):
        """Replace instances of a particular location name."""
        users = self.node[key]["locations"][old]
        if new not in self.node[key]["locations"]:
            self.node[key]["locations"][new] = set([])
        self.node[key]["locations"][new] |= users
        del self.node[key]["locations"][old]

    def trim(self, n = 10, verbose = False):
        '''Trim to specified number of edges.

        Attempt to minimize the total edge weight thrown away in the process.

        n: max desired output only the N keys with the highest total degree
        ext: filename extension
        '''
        # Sort by..
        # degree: total degree
        # inweight: total in weight, include selfedges
        # inweight-noself: total in weight, ignore selfedges
        SORT_BY = 'inweight-noself' # degree, inweight, inweight-noself...

        # FIXME:
        # extract the most-popular name from each key's locations dict
        # For now, just use the first name for that key we come across.
        # locations[key] = location string name
        locations = {}
        for key in self.nodes():
            #locations[key] = self.node[key]["locations"].keys()[0]
            locations[key] = self._most_popular_location(key)

        #for now, create map of keys to names
        # location_totals is a list of ((src,dst), some value)
        location_totals = []
        edge_total = 0
        for loc in self.nodes():
            if SORT_BY == 'degree':
                total = self.degree(loc)
            elif SORT_BY in ('inweight', 'inweight-noself'):
                pred = self.predecessors(loc)
                succ = self.successors(loc)

                total = 0
                # For now, only consider incoming edges ("influence") for ranking.
                # This may not be right; alternately, could use total of in and out.
                # To use both, uncomment line below
                #total = sum([self[loc][node]["weight"] for node in succ if node != loc])
                total += sum([self[node][loc]["weight"] for node in pred if node != loc])
                # selfedges are special case; don't want to double-count these
                if (SORT_BY == 'inweight') and self.has_edge(loc, loc):
                    total += self[loc][loc]["weight"]
            edge_total += total
            location_totals.append((loc, total))
        location_totals = sorted(location_totals, key = itemgetter(1))
        print "\tedge_total used for ranking w/sort by %s: %i" % (SORT_BY, edge_total)
        if verbose:
            print "key, in / out / self, location string"
            for i, (loc, total) in enumerate(location_totals):
                locs_to_print = locations[loc]
                #locs_to_print = self.node[loc]["locations"].keys()
                #locs_to_print = self.node[loc]["locations"].keys()[0]
                selfedges = self.edge[loc][loc]["weight"] if self.has_edge(loc, loc) else 0
                succ = self.successors(loc)
                outtotal = sum([self[loc][node]["weight"] for node in succ if node != loc])
                print "%s (%s / %s / %s): %s" % (loc, total, outtotal, selfedges, locs_to_print)
                if i == n - 1: print "------------------------"
                if i == 2 * n: break

        # Chop ordering:
        ordering = [loc for loc, total in location_totals]
        #ordering = ordering[:n]

        # Compute starting # edges
        edges = self.number_of_edges()
        if edges < n:
            raise Exception("edges_start > n!")

        for key in ordering:
            # remove key
            edges_rem = self.degree(key)
            print "removing %s: %s, %s edges" % (key, self._most_popular_location(key), edges_rem)
            self.aggregate(key, (None, None))
            self.remove_nones()

            # see if we've hit the target yet.
            edges -= edges_rem
            if edges < n:
                print "exiting with %i edges" % edges
                break

            print "now at %i edges total" % edges

        print "exited with %i edges" % edges


    def write_matrix_pv_js(self, filename, ordering = None, n = 10, ext = '.js', verbose = False):
        '''Write JSON file suitable for use in Protovis matrix view.

        filename: complete path to write, minus extension
        ordering: optional list of keys
        n: output only the N keys with the highest total degree
        ext: filename extension
        '''
        # Sort by..
        # degree: total degree
        # inweight: total in weight, include selfedges
        # inweight-noself: total in weight, ignore selfedges
        SORT_BY = 'inweight-noself' # degree, inweight, inweight-noself...

        # locations[key] = location string name
        locations = {}
        for key in self.nodes():
            #locations[key] = self.node[key]["locations"].keys()[0]
            locations[key] = self._most_popular_location(key)

        if not ordering:

            #for now, create map of keys to names
            # location_totals is a list of ((src,dst), some value)
            location_totals = []
            edge_total = 0
            for loc in self.nodes():
                if SORT_BY == 'degree':
                    total = self.degree(loc)
                elif SORT_BY in ('inweight', 'inweight-noself'):
                    pred = self.predecessors(loc)
                    succ = self.successors(loc)

                    total = 0
                    # For now, only consider incoming edges ("influence") for ranking.
                    # This may not be right; alternately, could use total of in and out.
                    # To use both, uncomment line below
                    #total = sum([self[loc][node]["weight"] for node in succ if node != loc])
                    total += sum([self[node][loc]["weight"] for node in pred if node != loc])
                    # selfedges are special case; don't want to double-count these
                    if (SORT_BY == 'inweight') and self.has_edge(loc, loc):
                        total += self[loc][loc]["weight"]
                edge_total += total
                location_totals.append((loc, total))
            location_totals = sorted(location_totals, key = itemgetter(1), reverse = True)
            print "\tedge_total used for ranking w/sort by %s: %i" % (SORT_BY, edge_total)
            if verbose:
                print "key, in / out / self, location string"
                for i, (loc, total) in enumerate(location_totals):
                    locs_to_print = locations[loc]
                    #locs_to_print = self.node[loc]["locations"].keys()
                    #locs_to_print = self.node[loc]["locations"].keys()[0]
                    selfedges = self.edge[loc][loc]["weight"] if self.has_edge(loc, loc) else 0
                    succ = self.successors(loc)
                    outtotal = sum([self[loc][node]["weight"] for node in succ if node != loc])
                    print "%s (%s / %s / %s): %s" % (loc, total, outtotal, selfedges, locs_to_print)
                    if i == n - 1: print "------------------------"
                    if i == 2 * n: break

            # Chop ordering:
            ordering = [loc for loc, total in location_totals]
            ordering = ordering[:n]

        text = self.matrix_pv_js(ordering, locations)
        json_out = open(filename + ext, 'w')
        json_out.write(text)

    def matrix_pv_js(self, ordering, locations):
        '''Output JSON string suitable for use in Protovis matrix view.

        ordering: list of keys
        locations: map of key to location names

        The data looks like this:

        var data = {
            nodes:[
                {nodeName:"Myriel", group:1},
                {nodeName:"Napoleon", group:1},
                ...
            ],
            links:[
                {source:1, target:0, value:1},
                {source:2, target:0, value:8},
                ...
            ]
        };
        '''
        nodes = []
        for loc in ordering:
            nodes.append({'nodeName': locations[loc], 'group': 1})

        loc_indices = {}
        for i, loc in enumerate(ordering):
            loc_indices[loc] = i
        links = []
        for src in ordering:
            for dst in ordering:
                src_index = loc_indices[src]
                dst_index = loc_indices[dst]
                if self.has_edge(src, dst):
                    weight = self[src][dst]["weight"]
                else:
                    weight = 0
                links.append({'source': src_index,
                              'target': dst_index,
                              'value': weight
                })
        matrix_data = {'nodes': nodes, 'links': links}
        s = 'var data = ' + json.dumps(matrix_data)

        return s

    @staticmethod
    def in_geo_range(node, box):
        '''Return true if node is in box.

        node: lat/long pair
        box: array of lat/long pairs
        '''
        min_lat = float(box[0][0])
        max_lat = float(box[1][0])
        min_long = float(box[0][1])
        max_long = float(box[1][1])
        lat = float(node[0])
        long = float(node[1])
        lat_in_range = (lat > min_lat) and (lat < max_lat)
        long_in_range = (long > min_long) and (long < max_long)
        if lat_in_range and long_in_range:
            return True
        else:
            return False

    def geo_box_filter(self, box, verbose = False):
        '''Return a new GeoGraph filtered to the specified geo box

        geo_filter_box: array of lat/long pairs.
        '''
        if verbose:
            print "geo box: %s" % box

        r = GeoGraph()

        # Remove edges not fully within bounding box.
        edges_saved = 0
        for src, dst in self.edges_iter():
            if verbose: print "considering edge: %s, %s" % (src, dst)
            if self.in_geo_range(src, box) and self.in_geo_range(dst, box):
                r.copy_node(self, src)
                r.copy_node(self, dst)
                r.copy_edge(self, src, dst)

                edges_saved += 1

        print "Saved %i edges." % edges_saved
        return r
