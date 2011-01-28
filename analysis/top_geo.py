#!/usr/bin/env python
# Brandon Heller
#
# Given an input geo-graph from geo_reduce.py, cluster nodes.
from operator import itemgetter
from optparse import OptionParser
import os
import time

import networkx as nx

# From http://hoegners.de/Maxi/geo/
import geo
# To test, go to http://www.daftlogic.com/projects-google-maps-distance-calculator.htm
# and run this code - see if the Portland - SanFran distance is ~533 miles.
# portland = geo.xyz(45.5, -122.67)
# sanfran = geo.xyz(37.777, -122.419)
METERS_TO_MILES = 0.000621371192
# print geo.distance(portland, sanfran) * METERS_TO_MILES

from geo_graph import geo_stats

# Default input filename - .gpk extension assumed
DEF_INPUT = "followers"

# Write output file by default?
DEF_WRITE = True

# Default number of clusters
DEF_CLUSTERS = True

# Default number of clusters
DEF_CLUSTERS = True

# Filter out unusable locations, like 106 people who said Earth...
BAD_LOCATIONS = [
]

# Top 12 cities, just a start.
CITIES = [
    ((u'37.777125', u'-122.419644'), 'San Francisco', 100),
    ((u'51.506325', u'-0.127144'), 'London', 100),
    ((u'40.714550', u'-74.007124'), 'New York', 100),
    ((u'35.670479', u'139.740921'), 'Tokyo', 100),
    ((u'41.884150', u'-87.632409'), 'Chicago', 100),
    ((u'47.603560', u'-122.329439'), 'Seattle', 90),
    #((u'51.164175', u'10.454145'), 'Germany', 200)
    ((u'52.516074', u'13.376987'), 'Berlin', 50),
    ((u'48.856930', u'2.341200'), 'Paris', 150),
    #((u'55.008390', u'-5.822485'), 'UK', 270) # would subsume London, but Ireland too.
    #((u'32.991405', u'138.460247'), 'Japan', 50),
    ((u'45.511795', u'-122.675629'), 'Portland', 80),
    ((u'43.648560', u'-79.385324'), 'Toronto', 100),
    ((u'-33.869629', u'151.206955'), 'Sydney', 100),
    ((u'34.053490', u'-118.245319'), 'Los Angeles', 100)
]

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
        input_stats = geo_stats(self.g)
        self.sort(self.g)
        self.reduce()
        output_stats = geo_stats(self.g)

        print "input stats: \n" + input_stats
        print "output stats: \n" + output_stats
        #self.stats(self.g)

        if options.write:
            geo_path = os.path.join(input, input + '.g2')
            nx.write_gpickle(self.r, geo_path)

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
        opts.add_option("-c", "--clusters", type = "int",
                        default = DEF_CLUSTERS,
                        help = "number of clusters to create")
        options, arguments = opts.parse_args()
        self.options = options

    def sort(self, g):
        # Find/print the top N geo locations
        def valid(node, location):
            if node in BAD_LOCATIONS:
                return False
            if node == (None, None):
                return False
            return True

        def in_range(node, city, radius):
            node_geo = geo.xyz(float(node[0]), float(node[1]))
            city_geo = geo.xyz(float(city[0]), float(city[1]))
            dist = geo.distance(node_geo, city_geo) * METERS_TO_MILES
            return dist < radius

        n = 100
        data = []
        filtered_users = 0
        filtered_locations = []
        valid_users = 0
        # For each node, add those users to the total.
        for node in g:
            location = g.node[node]["location"]
            name = g.node[node]["name"]
            if valid(node, location):
                data.append((node, len(name), location))
                valid_users += len(name)
            else:
                filtered_users += len(name)
                filtered_locations.append(location)
        try:
            data = sorted(data, key = itemgetter(1), reverse = True)
        except IndexError:
            print e
        top = []
        # Print out data as a sanity check.
        for i in range(n):
            top.append(data[i])
            locs = list(data[i][2])
            loc_strs = []
            for j in range(min(5, len(locs))):
                loc_strs.append(locs[j])
            print data[i][0], data[i][1], loc_strs

        print "stats for filtered graph:"
        print "\tunique geo-locations: %i" % g.number_of_nodes()
        print "\tvalid users: %i" % valid_users
        print "\tfiltered users: %i" % filtered_users
        print "\tfiltered locations: %s" % len(filtered_locations)
        print "\ttotal users: %i" % (valid_users + filtered_users)

        city_data = {} # map of city (lat, long) pairs to dict of total, 
        # Allocate each city to the nearest 12, or don't allocate.
        # A starting implementation only - doesn't handle edge reassignment.
        edge_map = {} # map original node locations to new ones.
        city_total = 0
        others_total = 0
        for (node, names, location) in data:
            found = False
            for city_loc, city_name, radius in CITIES:
                if in_range(node, city_loc, radius):
                    if city_loc not in city_data:
                        city_data[city_loc] = {'total': 0, 'name': city_name}
                    #print "%s @%s covers %s @ %s\n" % (city_name, city_loc, node, location)
                    city_data[city_loc]['total'] += names
                    edge_map[node] = city_loc
                    found = True
                    break
            if not found:
                others_total += names
                edge_map[node] = (0, 0)
            else:
                city_total += names

        print "stats for geo-clustered graph:"
        print "\tunique geo-locations (eq 13?): %i" % len(set(edge_map.values()))
        print "\tcity_total: %i" % city_total
        print "\tothers_total: %i" % others_total
        print "\tcity_data: %s" % city_data

        # note coverage

    def reduce(self):
        pass

    def stats(self, g):
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