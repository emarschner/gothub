#!/usr/bin/env python
'''Basic metrics and construction for GitHub mutual-contributions graph

Assumes a file where each line has this form:
  { "username/reponame": { "contributors": [ { "login": "username", ... } ] } }
'''

import json
import time
import logging
import os
import networkx as nx

filename = 'repos_contributors'
print_intervals = True
print_interval = 10000
limit = 1000 # max lines to read
threshold = 20 # above this, note names
level = logging.INFO

logging.basicConfig(level=logging.INFO)
lg = logging.getLogger("analysis")
lg.setLevel(level)

g = nx.Graph()  # network graph
seen_repos = {}  # dict of repos to num_contributors
unique_repos = set([])  # track unique repos seen
unique_users = set([]) # track unique contributing users
empty_repos = set([])  # map of abandoned repos: no contributors
error = {}  # map of users for which the query returned an error
lines = 0  # lines read in
links = 0  # total links seen so far
max_links = -1  # max links for one user
max_line = -1  # line number for tracking max value after

start = time.time()
f = open(filename, 'r')
for l in f:
    lines += 1
    if l[-1] == '\n':
        l = l.rstrip()
    else:
        raise Exception("line (#%i) w/ no newline?" % lines)
    line = json.loads(l)
    if len(line.keys()) != 1:
        raise Exception("line (#%i) with other stuff" % lines)
    repo_name = line.keys()[0]
    unique_repos.add(repo_name)

    if 'contributors' not in line[repo_name]:
        raise Exception("line (#%i) with repo name but no contributors array?" % lines)
    else:
        num_contributors = len(line[repo_name]['contributors'])
        if num_contributors > max_links:
            max_links = num_contributors
            max_line = lines
        if num_contributors == 0:
            empty_repos.add(repo_name)

        if repo_name not in seen_repos:
            seen_repos[repo_name] = num_contributors
        else:
            raise Exception("duplicated line (%i) for repo: %s" % (lines, repo_name))

        repo_contributors = set([])
        for contributor in line[repo_name]['contributors']:
            repo_contributors.add(contributor['login'])
            unique_users.add(contributor['login'])

        for contributor1 in repo_contributors:
            for contributor2 in repo_contributors:
              if contributor1 != contributor2:
                g.add_edge(contributor1, contributor2)
                links += 1

    if lines == limit:
        break
    if print_intervals:
        if lines % print_interval == 0:
            print lines

duration = time.time() - start

above = [repo for repo in seen_repos.keys() if seen_repos[repo] >= threshold]

print "time to parse: %0.3f sec" % duration
print "filename: ", filename
print "lines: ", lines
print "links: ", links
print "empty: ", len(empty_repos)
print "unique repos seen: ", len(unique_repos)
print "unique usernames seen: ", len(unique_users)
print "valid lines added: ", len(seen_repos)
print "max_links: %i, at line %i" % (max_links, max_line)
print "repos w/ at least %i in list: %s" % (threshold, above) 
