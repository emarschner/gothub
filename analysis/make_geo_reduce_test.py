#!/usr/bin/env python
# Generate input file(s) for verifying geo_reduce
import os
import networkx as nx

filename = "geo_test"
os.mkdir(filename)
filepath = os.path.join(filename, filename + '.gpk')
g = nx.DiGraph()
# Pulled from the processed.users collections:
# db.users.find().sort({number:1}).limit(10)
g.add_edges_from([(1, 2), (2, 3), (3, 6), (6, 7)])
nx.write_gpickle(g, filepath)