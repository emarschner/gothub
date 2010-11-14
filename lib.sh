#!/bin/bash
#
# Eli Marschner
#
# Communicate with data APIs, backup responses to disk,
# and write to MongoDB via crawl2mongo.py

function github_fetch() {
  URL="http://github.com/api/v2/json/${1}"
  echo Fetching: "$URL" 1>&2
  curl -s "$URL" | jsonpretty
  sleep 2
}

# Fetching: [GITHUB API]/user/search/{letter}
# Processing:
#   usernames => log/user/seen
#   locations => log/user/location/{username}
# DB: insert user data objects
# Run before running:
#   usernames2repos
# Run after running: none
function seed_usernames() {
  mkdir -p "${RUN_DIR}/raw/user/search" &> /dev/null
  for letter in a b c d e f g h i j k l m n o p q r s t u v w x y z
  do
    RAW_FILE="${RUN_DIR}/raw/user/search/${letter}"
    if [ ! -e "$RAW_FILE" ]
    then
      github_fetch "user/search/$letter" > "$RAW_FILE"
      echo "Extracting user locations from search for: " $letter
      cat "${RAW_FILE}" | ruby user_locations.rb | while read userlocation
      do
        username=`echo $userlocation | sed -e 's/:.*$//'`
        location=`echo $userlocation | sed -e 's/^[^:]*: *//'`
        if [ `grep "^${username}$" "${RUN_DIR}/log/user/seen" | wc -l` -eq 0 ]
        then
          echo "$username" >> "${RUN_DIR}/log/user/seen"
        fi
        mkdir -p "${RUN_DIR}/log/user/location/" &> /dev/null
        echo $location > "${RUN_DIR}/log/user/location/${username}"
      done
      echo "Writing user search results to mongo for: " $letter
      cat "$RAW_FILE" | python crawl2mongo.py --user-search
    else
      echo "Already user-searched: $letter (skipping)"
    fi
  done
}

# Fetching: [GITHUB API]/user/search/{username}
# Processing:
#   usernames => log/user/seen
#   locations => log/user/location/{username}
# DB: insert user data objects
# Run before running:
#   usernames2geocodes
#   usernames2repos
# Run after running:
#   usernames2repos
function repos2owners() {
  mkdir -p "${RUN_DIR}/raw/user/search" &> /dev/null
  cat "${RUN_DIR}/log/repos/seen" | while read reponame
  do
    username=`echo $reponame | sed -e 's/\([^/]*\)\/.*/\1/'`
    RAW_FILE="${RUN_DIR}/raw/user/search/${username}"
    if [ ! -e "$RAW_FILE" ]
    then
      github_fetch "user/search/$username" > "$RAW_FILE"
      echo "Extracting user locations from search for: " $username
      cat "${RAW_FILE}" | ruby user_locations.rb | while read userlocation
      do
        username=`echo $userlocation | sed -e 's/:.*$//'`
        location=`echo $userlocation | sed -e 's/^[^:]*: *//'`
        if [ `grep "^${username}$" "${RUN_DIR}/log/user/seen" | wc -l` -eq 0 ]
        then
          echo "$username" >> "${RUN_DIR}/log/user/seen"
        fi
        echo $location > "${RUN_DIR}/log/user/location/${username}"
      done
      echo "Writing user search results to mongo for: " $username
      cat "$RAW_FILE" | python crawl2mongo.py --user-search
    else
      echo "Already user-searched: $username (skipping)"
    fi
  done
}

function yahoo_geocode() {
  URL="http://where.yahooapis.com/geocode?flags=J&appid=`grep id: ${RUN_DIR}/placefinder/config.yml | sed -e 's/^ *id: "//' | sed -e 's/"$//'`&location=`perl -MURI::Escape -e 'print uri_escape($ARGV[0]);' "$1"`"
  echo Fetching: "$URL" 1>&2
  curl -s "$URL" | jsonpretty
  sleep 0.5
}

# Fetching: locations in log/user/location/{username} from Yahoo PlaceFinder API
# Processing: none
# DB: modify user data objects with geocodes
# Run before running: none
# Run after running:
#   repos2owners
#   repos2collaborators
#   repos2contributors
function usernames2geocodes() {
  mkdir -p "${RUN_DIR}/raw/user/geocode" &> /dev/null
  ls "${RUN_DIR}"/log/user/location | while read username
  do
    RAW_FILE="${RUN_DIR}/raw/user/geocode/${username}"
    location=`cat "${RUN_DIR}/log/user/location/${username}"`
    if [ ! -e "$RAW_FILE" ]
    then
      yahoo_geocode "$location" > "$RAW_FILE"
      echo "Writing location to mongo for ${username}: " $location
      cat "$RAW_FILE" | python crawl2mongo.py --geocode -u "$username"
    else
      echo "Already geocoded: ${username} (skipping)"
    fi
  done
}

# Fetching: [GITHUB API]/repos/watched/{username}
# Processing: reponames => log/repos/seen
# DB: none (used ony to get reponames for other crawler functions)
# Run before running:
#   repos2owners
#   repos2collaborators
#   repos2contributors
#   repos2branches
# Run after running:
#   repos2owners
#   repos2collaborators
#   repos2contributors
function usernames2repos() {
  mkdir -p "${RUN_DIR}/raw/repos/watched" &> /dev/null
  mkdir -p "${RUN_DIR}/log/repos" &> /dev/null
  touch "${RUN_DIR}/log/repos/seen"
  cat "${RUN_DIR}/log/user/seen" | while read username
  do
    RAW_FILE="${RUN_DIR}/raw/repos/watched/${username}"
    if [ ! -e "$RAW_FILE" ]
    then
      github_fetch "repos/watched/$username" > "$RAW_FILE"
      echo "Extracting watched repos from: " $username
      cat "$RAW_FILE" | ruby format_repos.rb | while read reponame
      do
        if [ `grep "^${reponame}$" "${RUN_DIR}/log/repos/seen" | wc -l` -eq 0 ]
        then
          echo "$reponame" >> "${RUN_DIR}/log/repos/seen"
        fi
      done
    else
      echo "Already got watched: $username (skipping)"
    fi
  done
}

# Fetching: [GITHUB API]/repos/show/{repo owner}/{repo name}/collaborators
# Processing: usernames => log/user/seen
# DB: insert collaborators property into repo object
# Run before running:
#   usernames2geocodes
#   usernames2repos
# Run after running:
#   usernames2repos
function repos2collaborators() {
  cat "${RUN_DIR}/log/repos/seen" | while read reponame
  do
    RAW_FILE="${RUN_DIR}/raw/repos/show/${reponame}/collaborators"
    mkdir -p "`dirname "${RAW_FILE}"`" &> /dev/null
    if [ ! -e "$RAW_FILE" ]
    then
      github_fetch "repos/show/${reponame}/collaborators" > "$RAW_FILE"
      echo "Extracting collaborators for: " $reponame
      cat "$RAW_FILE" | ruby repo_collaborators.rb | while read username
      do
        if [ `grep "^${username}$" "${RUN_DIR}/log/user/seen" | wc -l` -eq 0 ]
        then
          echo "$username" >> "${RUN_DIR}/log/user/seen"
        fi
      done
      echo "Writing collaborators to mongo for: " $reponame
      cat "$RAW_FILE" | python crawl2mongo.py --repos-show -u "`dirname "$reponame"`" -r "`basename "$reponame"`"
    else
      echo "Already got collaborators: $reponame (skipping)"
    fi
  done
}

# Fetching: [GITHUB API]/repos/show/{repo owner}/{repo name}/contributors
# Processing:
#   usernames => log/user/seen
#   locations => log/user/location/{username}
# DB: insert contributors property into repo object
# Run before running:
#   usernames2geocodes
#   usernames2repos
# Run after running:
#   usernames2repos
function repos2contributors() {
  cat "${RUN_DIR}/log/repos/seen" | while read reponame
  do
    RAW_FILE="${RUN_DIR}/raw/repos/show/${reponame}/contributors"
    mkdir -p "`dirname "${RAW_FILE}"`" &> /dev/null
    if [ ! -e "$RAW_FILE" ]
    then
      github_fetch "repos/show/${reponame}/contributors" > "$RAW_FILE"
      echo "Extracting contributors for: " $reponame
      cat "$RAW_FILE" | ruby user_locations.rb contributors | while read userlocation
      do
        username=`echo $userlocation | sed -e 's/:.*$//'`
        location=`echo $userlocation | sed -e 's/^[^:]*: *//'`
        if [ `grep "^${username}$" "${RUN_DIR}/log/user/seen" | wc -l` -eq 0 ]
        then
          echo "$username" >> "${RUN_DIR}/log/user/seen"
        fi
        echo $location > "${RUN_DIR}/log/user/location/${username}"
      done
      echo "Writing contributors to mongo for: " $reponame
      cat "$RAW_FILE" | python crawl2mongo.py --repos-show -u "`dirname "$reponame"`" -r "`basename "$reponame"`"
    else
      echo "Already got contributors: $reponame (skipping)"
    fi
  done
}

# Fetching: [GITHUB API]/repos/show/{repo owner}/{repo name}/branches
# Processing: repo branches => log/repos/branches/{repo owner}/{repo name}
# DB: insert branches property into repo object
# Run before running:
#   branches2commits
# Run after running:
#   usernames2repos
function repos2branches() {
  cat "${RUN_DIR}/log/repos/seen" | while read reponame
  do
    RAW_FILE="${RUN_DIR}/raw/repos/show/${reponame}/branches"
    mkdir -p "`dirname "${RAW_FILE}"`" &> /dev/null
    if [ ! -e "$RAW_FILE" ]
    then
      github_fetch "repos/show/${reponame}/branches" > "$RAW_FILE"
      mkdir -p "${RUN_DIR}/log/repos/branches/`dirname ${reponame}`" &> /dev/null
      touch "${RUN_DIR}/log/repos/branches/${reponame}"
      echo "Extracting branches for: " $reponame
      grep -v "[{}]" "${RAW_FILE}" | sed -e 's/^ *"//' | sed -e 's/": *.*//' > "${RUN_DIR}/log/repos/branches/${reponame}"
      echo "Writing branches to mongo for: " $reponame
      cat "$RAW_FILE" | python crawl2mongo.py --repos-show -u "`dirname "$reponame"`" -r "`basename "$reponame"`"
    else
      echo "Already got branches: $reponame (skipping)"
    fi
  done
}

# Fetching: [GITHUB API]/commits/list/{repo owner}/{repo name}/{branch name}
# Processing: none
# DB: insert commit objects
# Run before running: none
# Run after running:
#   repos2branches
function branches2commits() {
  cat "${RUN_DIR}/log/repos/seen" | while read reponame
  do
    mkdir -p "${RUN_DIR}/raw/commits/list/${reponame}" &> /dev/null
    cat "${RUN_DIR}/log/repos/branches/${reponame}" | while read branchname
    do
      RAW_FILE="${RUN_DIR}/raw/commits/list/${reponame}/${branchname}"
      mkdir -p "`dirname "${RAW_FILE}"`" &> /dev/null
      if [ ! -e "$RAW_FILE" ]
      then
        github_fetch "commits/list/${reponame}/${branchname}" > "$RAW_FILE"
      else
        echo "Already got commits: ${reponame}/${branchname} (skipping)"
      fi
      echo "Writing commits to mongo for: " ${reponame}/${branchname}
      cat "$RAW_FILE" | python crawl2mongo.py --commits
    done
  done
}
