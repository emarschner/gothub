#!/usr/bin/env python
# Brandon Heller
#
# Functions to import graphs.
import time
import json

import networkx as nx


def import_graph(filename, limit = None, graph_type = "dir", threshold = 500, 
                 print_interval = None):
    '''Create graph from file for follower/following lists.

    Assumes a file where each line has this form:
      { "tasukuchan": { "users": [ "daijiro", "tmaesaka" ] }  }

    Error lines look like this:
      { "ngenera": { "error": "Not Found" }  }

    filename: input filename, w/extension
    limit: max lines to parse
    graph_type: one of ["dir", "undir"]
    threshold: above this limit, note names
    print_interval: optional line spacing to print line number

    returns a NetworkX graph object.
    '''
    if graph_type == "dir":
        g = nx.DiGraph()
    else:
        g = nx.Graph()

    seen = {}  # dict of user names to totals.  Mostly to verify no dupe usernames
    unique = set([])  # track unique usernames seen
    empty = set([])  # map of antisocial users: no followers/following
    error = {}  # map of users for which the query returned an error
    lines = 0  # lines read in
    links = 0  # total links seen so far
    bidir = 0  # bidirectional links, counted once
    max_links = -1  # max links for one user
    max_line = -1  # line number for tracking max value after
    
    start = time.time()
    f = open(filename, 'r')
    for l in f:
    
        if l[-1] == '\n':
            l = l.rstrip()
        else:
            raise Exception("line w/no newline?")
        line = json.loads(l)
        lines += 1
        #print("reading line %i: %s" % (lines, line))
        if len(line.keys()) != 1:
            raise Exception("line with other stuff:" % line)
        src = line.keys()[0]
        unique.add(src)
    
        if 'error' in line[src]:
            #print("adding error at line %i: %s" % (lines, line))
            error[src] = 1
        elif 'users' not in line[src]:
            raise Exception("line with src but no users array?")
        else:
            users = len(line[src]['users'])
            if users > max_links:
                max_links = users
                max_line = lines
            if users == 0:
                empty.add(src)
    
            if src not in seen:
                seen[src] = users
            else:
                raise Exception("duplicated line for src: %s" % src)
    
            for dst in line[src]['users']:
                unique.add(dst)
                links += 1
                g.add_edge(src, dst) # dst node added automatically
                if dst in g and src in g[dst]:
                    bidir += 1
    
        if lines == limit:
            break
        if print_interval != None and print_interval != 0:
            if lines % print_interval == 0:
                print lines
    
    duration = time.time() - start
    
    above = [user for user in seen.keys() if seen[user] >= threshold]
    
    print "time to parse: %0.3f sec" % duration
    print "filename: ", filename
    print "lines: ", lines
    print "links: ", links
    print "bidir: ", bidir
    print "errors: ", len(error)
    print "empty: ", len(empty)
    print "unique usernames seen: ", len(unique)
    print "valid lines added: ", len(seen)
    print "max_links: %i, at line %i" % (max_links, max_line)
    print "users w/ at least %i in list: %s" % (threshold, above)

    return g