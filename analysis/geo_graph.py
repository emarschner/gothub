#!/usr/bin/env python
# Brandon Heller
#
# Utility functions for geo-graphs
#
# Geo-graphs are NetworkX graphs where:
# nodes are (lat, long) tuples with these fields:
#   selfedges: float
#   name: array of names
#   location: array of locations
# edges have these fields:
#   weight: float
import json
from operator import itemgetter
import os
import numpy as np

import networkx as nx

# From http://hoegners.de/Maxi/geo/
import geo
# To test, go to http://www.daftlogic.com/projects-google-maps-distance-calculator.htm
# and run this code - see if the Portland - SanFran distance is ~533 miles.
# portland = geo.xyz(45.5, -122.67)
# sanfran = geo.xyz(37.777, -122.419)
METERS_TO_MILES = 0.000621371192
# print geo.distance(portland, sanfran) * METERS_TO_MILES

NODE_FIELDS = ["name", "location", "selfedges"]
EDGE_FIELDS = ["weight"]

SEP = "\t"  # default separator

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

CITY_NAMES_STARTER = [city[1] for city in CITIES]

# City names ordered manually (& roughly) by distance to San Fran
CITY_NAMES_DIST = [
    'San Francisco',
    'Los Angeles',
    'Portland',
    'Seattle',
    'Chicago',
    'Toronto',
    'New York',
    'Tokyo',
    'London',
    'Berlin',
    'Paris',
    'Sydney'
]


def geo_edge_weight(g):
    """Compute total edge weight for a geo-graph."""
    i = 0
    selfedges = 0
    for node in g.nodes_iter():
        selfedges += g.node[node]["selfedges"]
    edge_weight = 0
    for src, dst in g.edges_iter():
        edge_weight += g[src][dst]["weight"]
    return (edge_weight + selfedges)


def geo_stats(g, sep = SEP, verbose = False):
    """Compute stats for a geo-graph."""
    i = 0
    node_weight = 0
    selfedges = 0
    locations = 0
    for node in g.nodes_iter():
        node_weight += len(g.node[node]["name"])
        selfedges += g.node[node]["selfedges"]
        locations += len(g.node[node]["location"])
    edge_weight = 0
    for src, dst in g.edges_iter():
        edge_weight += g[src][dst]["weight"]

    s = ''
    s += sep + "nodes: %i\n" % g.number_of_nodes()
    s += sep + "edges: %i\n" % g.number_of_edges()
    s += sep + "node weight: %0.2f\n" % node_weight
    s += sep + "edge weight: %0.2f\n" % edge_weight
    s += sep + "selfedges: %i\n" % selfedges
    s += sep + "total edge weight: %i\n" % (edge_weight + selfedges)
    s += sep + "locations: %i\n" % locations
    if verbose:
        s += sep + "nodes: %s\n" % g.nodes()
        s += sep + "edges: %s\n" % g.edges()
        s += sep + "node data: %s\n" % [g.node[n] for n in g.nodes()]
        s += sep + "edge data: %s\n" % [g[src][dst] for src, dst in g.edges()]

    return s


def pad(input, width):
    blank_str = ''
    for i in range(width):
        blank_str += ' '
    line = input + blank_str
    return line[0:width]


def text_matrix(g, labels, param, width = 6, format = "%i"):
    s = ''
    s += '|'.join([pad('', width)] + [pad(label, width) for label in labels]) + '\n'
    s += '|'.join(["------" for i in range(len(labels) + 1)]) + '\n'
    values = []
    for src_name in labels:
        line_values = [src_name]
        for dst_name in labels:
            line_values.append(pad(format % g[src_name][dst_name][param], width))
            values.append(g[src_name][dst_name][param])
        s += '|'.join([pad(value, width) for value in line_values]) + '\n'
    s += '>>> median: %0.2f, mean: %0.2f, min: %0.2f, max: %0.2f' % \
        (np.median(values), np.mean(values), min(values), max(values)) +'\n'
    return s

def geo_city_graph(g, cities = CITIES):
    '''Returns graph w/weights between city names plus totals.

    g: geo-graph
    cities: array like CITIES
    '''
    c = nx.DiGraph()
    edge_weight_total = 0
    edge_weights = []
    for src_node, src_name, src_radius in cities:
        for dst_node, dst_name, dst_radius  in cities:
            if src_node == dst_node:
                if src_node in g:
                    edge_weight = g.node[src_node]['selfedges']
                else:
                    edge_weight = 0
            elif g.has_edge(src_node, dst_node):
                edge_weight = g[src_node][dst_node]["weight"]
            else:
                edge_weight = 0
            c.add_edge(src_name, dst_name)
            c[src_name][dst_name]["weight"] = edge_weight
            edge_weight_total += edge_weight
            edge_weights.append(edge_weight)
    return (c, edge_weight_total, edge_weights)


def geo_pv_json(c, ordering = CITY_NAMES_DIST):
    '''Make JSON string suitable for use in Protovis matrix view.

    c: DiGraph w/city names for nodes and weight field for each link

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
    nodes = [{'nodeName': name, 'group': 1} for name in ordering]
    name_indices = {}
    for i, name in enumerate(ordering):
        name_indices[name] = i
    links = []
    for src in ordering:
        for dst in ordering:
            src_index = name_indices[src]
            dst_index = name_indices[dst]
            links.append({'source': src_index,
                          'target': dst_index,
                          'value': c[src][dst]["weight"]
            })
    matrix_data = { 'nodes': nodes, 'links': links}
    s = 'var data = ' + json.dumps(matrix_data)

    return s


# Ratio to use in place of None or divide-by-zero error.
RATIO_MAX = 1000
RATIO_INDETERMINATE = 1.0

def link_asym(g, cities = CITIES):
    '''Returns matrix of link asymmetry ratios.

    For link (a, b), the ratio equals (a / b)

    g: geo-graph
    cities: array like CITIES

    return a DiGraph w/city names for nodes
    '''
    a = nx.DiGraph()
    for src_node, src_name, src_radius in cities:
        for dst_node, dst_name, dst_radius  in cities:
            if g.has_edge(src_node, dst_node):
                forward = g[src_node][dst_node]["weight"]
            else:
                forward = 0

            if g.has_edge(dst_node, src_node):
                expected = g[dst_node][src_node]["weight"]
            else:
                expected = 0

            if expected == 0 and forward == 0:
                ratio = RATIO_INDETERMINATE
            elif expected == 0:
                ratio = RATIO_MAX
            else:
                ratio = float(forward) / float(expected)

            a.add_edge(src_name, dst_name)
            a[src_name][dst_name]["weight"] = ratio

    return a


def geo_expected(g, total_edges = 1.0, cities = CITIES):
    '''Returns expected link distribution of geo-graph.

    g: geo-graph
    locations: list of (lat, long) pairs

    Expected link distribution refers to a uniform link distribution built
    only with knowledge of the number of users at each location.  If we were to
    randomly pick users this is the graph that would result, in the limit.  It
    assumes that geography has no effect.
    '''
    e = nx.DiGraph()
    exp_total = 0.0
    total_edges = geo_edge_weight(g)
    total_users = sum([len(g.node[node]["name"]) for node in g.nodes()])
    for src_node, src_name, src_radius in cities:
        for dst_node, dst_name, dst_radius  in cities:
            src_users = 0
            dst_users = 0
            if src_node in g:
                src_users = len(g.node[src_node]["name"])
            if dst_node in g:
                dst_users = len(g.node[dst_node]["name"])
            src_fraction = float(src_users) / total_users
            dst_fraction = float(dst_users) / total_users
            link_expectation = src_fraction * dst_fraction * total_edges
            e.add_edge(src_name, dst_name)
            e[src_name][dst_name]["weight"] = link_expectation
            exp_total += link_expectation

    print "total users: %i" % total_users
    print "total input edges: %i" % total_edges
    print "aggregate in-city edge total: %0.2f" % exp_total

    return e


def geo_actual_exp_ratio(g, exp, cities = CITIES):
    '''Compute actual-to-expected ratio for each major city pair.'''
    r = nx.DiGraph()
    for src_node, src_name, src_radius in cities:
        for dst_node, dst_name, dst_radius  in cities:
            if src_node == dst_node:
                # Stupide selfedges special case (should remove)
                if src_node in g:
                    actual = g.node[src_node]["selfedges"]
                else:
                    actual = 0
            else:
                if g.has_edge(src_node, dst_node):
                    actual = g[src_node][dst_node]["weight"]
                else:
                    actual = 0

            if exp.has_edge(src_name, dst_name):
                expected = exp[src_name][dst_name]["weight"]
            else:
                expected = 0

            if expected == 0 and actual == 0:
                ratio = RATIO_INDETERMINATE
            elif expected == 0:
                ratio = RATIO_MAX
            else:
                ratio = float(actual) / float(expected)

            r.add_edge(src_name, dst_name)
            r[src_name][dst_name]["weight"] = ratio

    return r


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


def init_geo_node(key, g):
    '''Initialize node w/geo attributes.'''
    g.add_node(key)
    g.node[key]["name"] = set([])
    g.node[key]["location"] = set([])
    g.node[key]["selfedges"] = 0


def merge_geo_node(key, mapped_key, g_in, g_out):
    '''Merge node geo attributes.'''
    g_out.node[mapped_key]["name"] |= g_in.node[key]["name"]
    g_out.node[mapped_key]["location"] |= g_in.node[key]["location"]
    g_out.node[mapped_key]["selfedges"] += g_in.node[key]["selfedges"]


def init_geo_edge(src, dst, g):
    '''Intialize node w/geo attributes.'''
    g.add_edge(src, dst)
    g[src][dst]["weight"] = 0


def merge_geo_edge(src, dst, src_mapped, dst_mapped, g_in, g_out):
    '''Merge edge geo attributes.'''
    g_out[src_mapped][dst_mapped]["weight"] += g_in[src][dst]["weight"]


def geo_reduce(g, node_map, verbose = False):
    '''Reduce a geo-graph, given a node mapping.'''
    r = nx.DiGraph()

    # Initialize r and copy in previously known names, locations, selfedges...
    for key in node_map.values():
        init_geo_node(key, r)

    # Now merge all nodes into the initialized reduced graph
    for key in g.nodes_iter():
        merge_geo_node(key, node_map[key], g, r)

    # Add edges, possibly merging
    for src, dst in g.edges_iter():

        if verbose: print "considering edge: %s, %s" % (src, dst)
        src_mapped = node_map[src]
        dst_mapped = node_map[dst]

        if src_mapped == dst_mapped:
            # if reducing this edge leads to a selfedge, don't add an edge
            # just increment the selfedges field
            r.node[src_mapped]["selfedges"] += g[src][dst]["weight"]
            if verbose: print "\tadding as selfedge"
        else:
            if not r.has_edge(src_mapped, dst_mapped):
                if verbose: print "\tinitializing edge"
                init_geo_edge(src_mapped, dst_mapped, r)
            if verbose: print "\tmerging edge"
            merge_geo_edge(src, dst, src_mapped, dst_mapped, g, r)

    return r


def geo_filter_nones(g):
    '''Filter out nodes at (None, None) plus links to there.'''
    if g.has_node((None, None)):
        g.remove_node((None, None))


def print_top_n(data, n, m):
    '''Print top n locations by user total, with up to m location names.

    data: array of ((lat, long), names, [location]) tuples
    '''
    top = []
    for i in range(min(n, len(data))):
        top.append(data[i])
        locs = list(data[i][2])
        loc_strs = []
        for j in range(min(m, len(locs))):
            loc_strs.append(locs[j])
        print data[i][0], data[i][1], loc_strs


def geo_cluster(g, restrict = True, cities = CITIES):
    '''Cluster nodes via curated city descriptions.

    g: geo DiGraph
    restrict: boolean
        when True, node_map maps to None those not in cities
        when False, node_map includes

    '''
    # Find/print the top N geo locations
    n = 20
    data = []  # Array of ((lat, long), names, [location]) tuples
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

    # Print out data as a sanity check.
    print_top_n(data, n, 5)

    print "stats for filtered graph:"
    print "\tunique geo-locations: %i" % g.number_of_nodes()
    print "\tvalid users: %i" % valid_users
    print "\tfiltered users: %i" % filtered_users
    print "\tfiltered locations: %s" % len(filtered_locations)
    print "\ttotal users: %i" % (valid_users + filtered_users)

    city_data = {} # map of city (lat, long) pairs to dict of total,
    # Allocate each city to the nearest 12, or don't allocate.
    # A starting implementation only - doesn't handle edge reassignment.
    node_map = {} # map original node locations to new ones.
    city_total = 0
    others_total = 0
    for (node, names, location) in data:
        found = False
        mapped_loc = node  # by default, keep the mapping.
        for city_loc, city_name, radius in cities:
            if in_range(node, city_loc, radius):
                if city_loc not in city_data:
                    city_data[city_loc] = {'total': 0, 'name': city_name}
                #print "%s @%s covers %s @ %s\n" % (city_name, city_loc, node, location)
                city_data[city_loc]['total'] += names
                #node_map[node] = city_loc
                mapped_loc = city_loc
                found = True
                break
        if not found:
            others_total += names
        else:
            city_total += names

        if not restrict or found:
            node_map[node] = mapped_loc

    print "stats for geo-clustered graph:"
    print "\tunique geo-locations (12 for restrict): %i" % len(set(node_map.values()))
    print "\tcity_total: %i" % city_total
    print "\tothers_total: %i" % others_total
    print "\tcity_data: %s" % city_data

    # TEMP: verify node_map coverage
    for node in g.nodes():
        if node not in node_map:
            print "WARNING: node %s not in node_map" % node

    return node_map


def geo_check_for_isolated(g):
    '''Print warning if isolated (edge-less) nodes are found'''
    total = 0
    for node in g.nodes():
        if g.degree(node) == 0:
            total += 1
    if total > 0:
        print "WARNING: isolated nodes: %i" % total


def geo_node_stats(g):
    '''Print detailed stats for each node'''
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


CITY_ORDERINGS = {'starter': CITY_NAMES_STARTER,
                  'dist': CITY_NAMES_DIST
}


def write_json_file(text, name, append, ext = '.js'):
    json_path = os.path.join(name, name + '_' + '_'.join(append) + ext)
    json_out = open(json_path, 'w')
    json_out.write(text)


class GeoGraphProcessor:
    '''Helper for import/process/export on geo-graphs.'''

    def __init__(self, process_fcn, in_name, in_ext, out_name = None,
                 out_ext = None, write = False, write_json = False,
                 ordering_type = 'starter'):

        if ordering_type not in CITY_ORDERINGS:
            raise Exception("invalid city ordering type: %s" % ordering_type)

        input_path = os.path.join(in_name, in_name + in_ext)
        g = nx.read_gpickle(input_path)
        if not g:
            raise Exception("null input file for input path %s" % input_path)

        g = process_fcn(g)

        if write:
            geo_path = os.path.join(in_name, in_name + out_ext)
            nx.write_gpickle(g, geo_path)

        if write_json:
            #print "using ordering: %s" % ordering_type
            ordering = CITY_ORDERINGS[ordering_type]
            #print "ordering is: %s" % ordering
            #print "city_names_starter: %s" % CITY_NAMES_STARTER

            c = geo_city_graph(g)[0]
            text = geo_pv_json(c, ordering)
            write_json_file(text, in_name, ["link", ordering_type])
            link_matrix = text_matrix(c, ordering, "weight")

            a = link_asym(g)
            text = geo_pv_json(a, ordering)
            write_json_file(text, in_name, ["asym", ordering_type])
            asym_matrix = text_matrix(a, ordering, "weight", format = "%0.2f")

            e = geo_expected(g)
            text = geo_pv_json(e, ordering)
            write_json_file(text, in_name, ["exp", ordering_type])
            exp_matrix = text_matrix(e, ordering, "weight", format = "%0.2f")

            r = geo_actual_exp_ratio(g, e)
            text = geo_pv_json(r, ordering)
            write_json_file(text, in_name, ["act-exp-ratio", ordering_type])
            ratio_matrix = text_matrix(r, ordering, "weight", format = "%0.2f")

            print '\nLinks: actual link totals\n' + link_matrix
            print '\nAsym: asymmetry ratio\n' +  asym_matrix
            print '\nExp: expected link totals, given uniform distribution\n' + exp_matrix
            print '\nActExpRatio: actual links / expected links\n' + ratio_matrix
