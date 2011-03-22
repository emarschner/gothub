#!/usr/bin/env python
# Graph interchange tests - require newer version of NetworkX
# NX 1.4 seems to work
import networkx as nx
c = nx.complete_graph(3)
g = nx.DiGraph(c)
g.node[0] = {'viz': {'position': {'x': 100, 'y':200, 'z':0}}}
g.node[1] = {'viz': {'position': {'x': 200, 'y':300, 'z':0}}}
g.node[2] = {'viz': {'position': {'x': 100, 'y':400, 'z':0}}}
nx.write_gexf(g, "test.gexf")
#nx.write_graphml(g, "test.graphml")
