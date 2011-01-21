#!/usr/bin/env python
# Brandon Heller
#
# Tests of jaccard functions.
import unittest

import networkx as nx

from graph_lib import jaccard_edges, jaccard_nodes


def compare_both(test, fcn, left, right, value):
    test.assertEqual(fcn(left, right), value)
    if left != right:
        test.assertEqual(fcn(left, right), value)


class testJaccardEdges(unittest.TestCase):

    def testDirected(self):
        empty = nx.DiGraph()
        half = nx.DiGraph([(0, 1)])
        full = nx.DiGraph(nx.complete_graph(2))
        cases = [(empty, full, 0.0),
                 (full, full, 1.0),
                 (half, full, 0.5)]
        for case in cases:
            compare_both(self, jaccard_edges, *case)

class testJaccardNodes(unittest.TestCase):

    def testDirected(self):
        empty = nx.DiGraph()
        one_edge = nx.DiGraph([(0, 1)])
        one_node = nx.DiGraph()
        one_node.add_node(0)
        full = nx.DiGraph(nx.complete_graph(2))

        cases = [(empty, full, 0.0),
                 (full, full, 1.0),
                 (one_edge, full, 1.0),
                 (one_node, full, 0.5)]
        for case in cases:
            compare_both(self, jaccard_nodes, *case)


if __name__ == '__main__':
    unittest.main()
