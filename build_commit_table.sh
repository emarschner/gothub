#!/bin/bash

RUN_DIR=`echo $(dirname $0)`
COMMIT_DATA="${RUN_DIR}/data/commits"

mkdir -p "${RUN_DIR}/data" &> /dev/null
touch "${COMMIT_DATA}"
find "${RUN_DIR}/log/repos/commits/" -type f | while read commitlist
do
  significand=`echo $commitlist | sed -e "s/^${RUN_DIR}\/log\/repos\/commits\///"`
  username=`echo $significand | sed -e 's/^\([^/]*\)\/.*/\1/'`
  reponame=`echo $significand | sed -e 's/^[^/]*\/\([^/]*\)\/.*/\1/'`
  branchname=`echo $significand | sed -e 's/^[^/]*\/[^/]*\///'`
  cat "${commitlist}" | while read commit
  do
    if [ `grep "^${commit}" "${COMMIT_DATA}" | wc -l` -eq 0 ]
    then
      echo Analyzing commit: $commit
      ruby build_commit_rows.rb "$username" "$reponame" "$branchname" "$commit" >> "$COMMIT_DATA"
    else
      echo Seen commit: $commit \(skipping\)
    fi
  done
done
