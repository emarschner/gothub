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


# 1: mojombo, San Fran
# 2: defunkt, San Fran
# 3: pjhyett, San Fran
# 6: ivey, Alabama (not in cities)
# 7: evanphx, Los Angeles
# 18: wayneeseguin, NY
# 65608: bess, Palo Alto
# 25438: roskoff, Paraguay (not in cities)
# 51689: bamboo, Brazil (not in cities)
data = [[(1, 2), (2, 3), (3, 6), (6, 7)],
        complete_graph([1, 2, 3, 6, 7]),
        [(6, 65608), (6, 1)],  # exposed a bug!
        complete_graph([1, 6, 65608]),
        complete_graph([1, 2, 3, 6, 7, 18, 65608]),
        [(1, 2), (2, 3), (3, 6), (6, 7), (6, 18)],
        [(1, 2), (2, 3), (3, 6), (6, 7), (2, 1), (3, 2), (7, 6), (6, 3)],
        [(1, 65608), (65608, 1)],
        [(1, 2), (6, 18)],
        complete_graph([1, 2, 3]), # expect 6 links in same spot
        complete_graph([1, 7, 18]), # expect 2/3-weight links all over
        complete_graph([6, 25438, 51689]) + complete_graph([1, 7, 18]), # expect 1/4 of total in city matrix 
]

ext = '.gpk'
for i, pairs in enumerate(data):
    filename = 'geo_test_' + str(i)
    if filename not in os.listdir('.'):
        os.mkdir(filename)
    filepath = os.path.join(filename, filename + ext)
    g = nx.DiGraph()
    g.add_edges_from(pairs)
    nx.write_gpickle(g, filepath)