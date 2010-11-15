#!/bin/bash

RUN_DIR=`echo $(dirname $0)`

. "${RUN_DIR}/crawler_tasks.sh"

seed_usernames
usernames2repos
repos2owners
repos2collaborators
repos2contributors
usernames2geocodes
repos2branches
branches2commits
