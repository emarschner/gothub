#!/usr/bin/env python
# Brandon Heller
#
# Import a graph, given a few params.

from graph_lib import import_graph
from optparse import OptionParser

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

# Analyze by default?
DEF_ANALYZE = False


class GraphUtil():
    
    def __init__(self):
        self.parse_args()
        options = self.options
        if '.gpk' in options.input:
            g = nx.read_gpickle(options.input)
        else:
            g = import_graph(options.input, limit = options.max_lines,
                         print_interval = options.print_interval)
        if options.write:
            nx.write_gpickle(g, options.output + '.gpk')

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
        opts.add_option("--analyze", action = "store_true", 
                        default = DEF_ANALYZE,
                        help = "analyze?")
        opts.add_option("--plot", action = "store_true", 
                        default = DEF_PLOT,
                        help = "plot stuff?")
        opts.add_option("-p", "--print_interval", type = "int",
                        default = DEF_PRINT_INTERVAL,
                        help = "lines between printouts")
        options, arguments = opts.parse_args()
        self.options = options

        if options.write and not options.output:
            raise Exception("no write filename provided")

        
if __name__ == "__main__":
    GraphUtil()
