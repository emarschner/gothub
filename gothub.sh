#!/bin/bash

. "${RUN_DIR}/crawler_tasks.sh"

seed_usernames
usernames2repos
repos2usernames
repos2collaborators
repos2contributors
usernames2geocodes
repos2branches
branches2commits
