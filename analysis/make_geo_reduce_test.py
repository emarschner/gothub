#!/usr/bin/env python
# Generate input file(s) for verifying geo_reduce
import os
import networkx as nx

# Low-numbered GitHub users pulled from the processed.users collections:
# db.users.find().sort({number:1}).limit(10)

def complete_graph(array):
    pairs = []
    for i in array:
        for j in array:
            if i != j:
                pairs.append((i, j))
    return pairs

data = [("geo_test",   [(1, 2), (2, 3), (3, 6), (6, 7)]),
        ("geo_test_2", complete_graph([1, 2, 3, 6, 7])),
        ("geo_test_3", [(1, 2), (2, 3), (3, 6), (6, 7), (6, 18)]),
        ("geo_test_4", [(1, 2), (2, 3), (3, 6), (6, 7), (2, 1), (3, 2), (7, 6), (6, 3)])
]

ext = '.gpk'
for filename, pairs in data:
    if filename not in os.listdir('.'):
        os.mkdir(filename)
    filepath = os.path.join(filename, filename + ext)
    g = nx.DiGraph()
    g.add_edges_from(pairs)
    nx.write_gpickle(g, filepath)