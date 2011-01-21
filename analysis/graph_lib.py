#!/usr/bin/env python
'''Brandon Heller

Functions to import graphs.

Two input types:

* Original:
Eli's followers/following files, where normal lines look like this:
      { "tasukuchan": { "users": [ "daijiro", "tmaesaka" ] }  }
    Error lines look like this:
      { "ngenera": { "error": "Not Found" }  }

* Links:
Each link on its own line, with numbers for nodes.  First two lines:
    following_id,user_id
    3,2
    ...
'''
import time
import json

import networkx as nx


# Input type: see descriptions above.
INPUT_TYPES = ['original', 'links']


def import_graph(filename, limit = None, graph_type = "dir",
                 print_interval = None, input_type = 'original'):
    '''Create graph from file for follower/following lists.

    filename: input filename, w/extension
    limit: max lines to parse
    graph_type: one of ["dir", "undir"]
    print_interval: optional line spacing to print line number

    returns a NetworkX graph object and other vars used
    '''
    if graph_type == "dir":
        g = nx.DiGraph()
    else:
        g = nx.Graph()

    seen = {}  # dict of user names to totals.  Mostly to verify no dupe usernames
    unique = set([])  # track unique usernames seen
    empty = set([])  # map of antisocial users: no followers/following
    error = {}  # map of users for which the query returned an error
    errors = 0  # total of invalid lines
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

        if input_type == 'original':
            line = json.loads(l)

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

        elif input_type == 'links':
            # skip first line
            if lines > 0:
                src, dst = l.split(',')
                if src == "" or dst == "":
                    print "error: missing src/dst value on line %i (%s)" % (lines, l)
                    errors += 1
                else:
                    #print "%s --> %s" % (src, dst)
                    if src in g and (dst in g[src]):
                        print "warning: duplicated edge: %s %s on line %s" % (src, dst, lines)
                        errors += 1
                    g.add_edge(src, dst)
                    unique.add(src)
                    unique.add(dst)
                    if dst in g and src in g[dst]:
                        bidir += 1
                    links += 1
        else:
            raise Exception("invalid input_type:%s" % input_type)

        lines += 1

        if limit and lines == limit:
            break
        if print_interval and print_interval != 0:
            if lines % print_interval == 0:
                print lines
    
    duration = time.time() - start

    if not lines > 0:
        raise Exception("import yielded no lines")

    degrees = sorted(g.degree().values(), reverse = True)
    top = [degrees[i] for i in range(min(len(g), 10))]

    print "time to parse: %0.3f sec" % duration
    print "filename: ", filename
    print "lines: ", lines
    print "links: ", links
    print "bidir: ", bidir
    print "error queries: ", len(error)
    print "error lines: ", errors
    print "empty: ", len(empty)
    print "unique usernames seen: ", len(unique)
    print "unique from nx: ", len(g)
    print "valid lines added: ", len(seen)
    print "max_links: %i, at line %i" % (max_links, max_line)
    print "top users' degrees: %s" % top

    return g, seen, empty