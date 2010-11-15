#!/bin/bash

SCRIPT=../../crawl2mongo.py

cat data.search | python ${SCRIPT} -t --user-search
cat data.geo | python ${SCRIPT} -t -u EVANTEST --geocode
cat data.branches | python ${SCRIPT} -t -u EVANTEST -r FAKEREPO --repos-show
cat data.commits | python ${SCRIPT} -t --commits

python test.py

