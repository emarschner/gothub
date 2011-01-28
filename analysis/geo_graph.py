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

def geo_stats(g, sep = "\t"):
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
    s += sep + "node weight: %02f\n" % node_weight
    s += sep + "edge weight: %02f\n" % edge_weight
    s += sep + "selfedges: %i\n" % selfedges
    s += sep + "locations: %i\n" % locations

    return s
