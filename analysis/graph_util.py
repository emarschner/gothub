#!/usr/bin/env python
# Brandon Heller
#
# Import a graph, given a few params.

from graph_lib import import_graph
import json
from optparse import OptionParser
import os

import networkx as nx


# Name of input file
DEF_INPUT_NAME = 'followers'

# Name of output file
DEF_OUTPUT_NAME = None

# Default max number of lines to parse
DEF_MAX_LINES = 1000

# Commits to read until printing out current commit
DEF_PRINT_INTERVAL = None

# Use directed graph or undirected?
DEF_DIRECTED = False

# Compute stats?
DEF_STATS = False

# Write output file?
DEF_WRITE = False

# Create plots?
DEF_PLOT = False


class GraphUtil():
    
    def __init__(self):
        self.parse_args()
        options = self.options
        if '.gpk' in options.input:
            g = nx.read_gpickle(options.input)
        else:
            g, seen, empty = import_graph(options.input,
                limit = options.max_lines,
                print_interval = options.print_interval)
            self.seen = seen
            self.empty = empty

        if options.output:
            output_base = options.output
        else:
            output_base = options.input.split('.')[0]
        if options.max_lines:
            output_base += "_%i" % options.max_lines

        if options.write or options.stats:
            # Create dir
            if output_base not in os.listdir('.'):
                os.mkdir(output_base)
                print "created directory:", output_base

        if options.write:
            gpk_path = os.path.join(output_base, output_base + '.gpk')
            nx.write_gpickle(g, gpk_path)

        if options.stats:
            stats = self.stats(g, options.degree, options.pagerank,
                               options.bc)
            if options.write_stats:
                stats_path = os.path.join(output_base, output_base + '.stats')
                f = open(stats_path, 'w')
                f.write(json.dumps(stats))
                print "wrote output file:", stats_path

    def parse_args(self):
        opts = OptionParser()
        opts.add_option("-m", "--max_lines", type = "int",
                        default = DEF_MAX_LINES,
                        help = "max lines to parse; default is all")
        opts.add_option("-i", "--input", type = 'string', 
                        default = DEF_INPUT_NAME,
                        help = "name of input file")
        opts.add_option("-o", "--output", type = 'string',
                        default = DEF_OUTPUT_NAME,
                        help = "name of output file")
        opts.add_option("-d", "--directed", action = "store_true", 
                        default = DEF_DIRECTED,
                        help = "make directed graph?")
        opts.add_option("-s", "--stats", action = "store_true", 
                        default = DEF_STATS,
                        help = "compute stats?")
        opts.add_option("-w", "--write", action = "store_true", 
                        default = DEF_WRITE,
                        help = "write output file?")
        opts.add_option("--plot", action = "store_true", 
                        default = DEF_PLOT,
                        help = "plot stuff?")
        opts.add_option("-p", "--print_interval", type = "int",
                        default = DEF_PRINT_INTERVAL,
                        help = "lines between printouts")
        opts.add_option("--degree", action = "store_true",
                        default = False, help = "compute degree histogram?")
        opts.add_option("--pagerank",  action = "store_true",
                        default = False, help = "compute PageRank?")
        opts.add_option("--bc",  action = "store_true",
                        default = False,
                        help = "compute betweenness centrality?")
        opts.add_option("--compute_all",  action = "store_true",
                        default = False, help = "compute all?")
        opts.add_option("--write_stats",  action = "store_true",
                        default = False, help = "write stats file?")
        options, arguments = opts.parse_args()
        self.options = options

        if options.write and not options.output:
            print("no write filename provided; assuming input")

        if options.stats:
            options.degree = True
            options.pagerank = True
            options.bc = True

        if (options.degree or options.pagerank or
            options.bc):
            options.stats = True

        if options.write_stats and not options.output:
            print("no write filename (for stats) provided; assuming input")

        if options.write_stats and not options.stats:
            raise Exception("doesn't make sense to write empty stats")

    def stats(self, g, degree, pagerank, bc):
        """Compute the requested stats and return as a dict."""
        stats = {}
        seen = self.seen
        empty = self.empty
        
        # create degree CDF
        if degree:
            degree = [seen[user] for user in seen.keys()]
            stats["degree"] = {
                "type": "array",
                "values": degree
            }

        # compute PageRank.  Note: we have to ignore empties.
        if pagerank:
            start = time.time()
            pagerank_dict = nx.pagerank(g)
            nonempty_seen = [user for user in seen.keys() if user not in empty]
            pagerank = ([pagerank_dict[user] for user in nonempty_seen])
            duration = time.time() - start
            print "time to gen pagerank: %0.3f sec" % duration
            #print pagerank
            stats["pagerank"] = {
                "type": "array",
                "values": pagerank
            }
        
        # compute betweenness centrality  - should empties get added back to CDF?
        if bc:
            start = time.time()
            bc_dict = nx.betweenness_centrality(g)
            bc = ([bc_dict[user] for user in nonempty_seen])
            duration = time.time() - start
            print "time to gen betweenness centrality: %0.3f sec" % duration
            stats["bc"] = {
                "type": "array",
                "values": bc
            }

        return stats
        
if __name__ == "__main__":
    GraphUtil()
