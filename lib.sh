#!/bin/bash

# Usage: github_fetch <API path> => <pretty-formatted JSON data>
function github_fetch() {
  URL="http://github.com/api/v2/json/${1}"
  echo Fetches: "$URL" 1>&2
  curl -s "$URL" | jsonpretty
  sleep 2
}

# Usage: yahoo_geocode <location string> => <pretty-formatted JSON data>
function yahoo_geocode() {
  mkdir -p "${RUN_DIR}/raw/user/geocode" &> /dev/null
  URL="http://where.yahooapis.com/geocode?flags=J&appid=`grep id: ${RUN_DIR}/placefinder/config.yml | sed -e 's/^ *id: "//' | sed -e 's/"$//'`&location=`perl -MURI::Escape -e 'print uri_escape($ARGV[0]);' "$1"`"
  echo Fetches: "$URL" 1>&2
  curl -s "$URL" | jsonpretty
  sleep 0.5
}

# Usage: is_user_seen <username> => true or false
function is_user_seen() {
  mkdir -p "${RUN_DIR}/log/user" &> /dev/null
  touch "${RUN_DIR}/log/user/seen"
  if [ `grep "^${1}$" "${RUN_DIR}/log/user/seen" | wc -l` -eq 0 ]
  then
    echo false
  else
    echo true
  fi
}

# Usage: set_user_seen <username> => void
function set_user_seen() {
  mkdir -p "${RUN_DIR}/log/user" &> /dev/null
  echo "$1" >> "${RUN_DIR}/log/user/seen"
}

# Usage: is_repo_seen <reponame> => true or false
function is_repo_seen() {
  mkdir -p "${RUN_DIR}/log/repos" &> /dev/null
  touch "${RUN_DIR}/log/repos/seen"
  if [ `grep "^${1}$" "${RUN_DIR}/log/repos/seen" | wc -l` -eq 0 ]
  then
    echo false
  else
    echo true
  fi
}

# Usage: set_repo_seen <reponame> => void
function set_repo_seen() {
  mkdir -p "${RUN_DIR}/log/repos" &> /dev/null
  echo "$1" >> "${RUN_DIR}/log/repos/seen"
}

# Usage: is_user_search_done <term> => true or false
function is_user_search_done() {
  mkdir -p "${RUN_DIR}/log/user" &> /dev/null
  touch "${RUN_DIR}/log/user/done"
  if [ `grep "^${1}$" "${RUN_DIR}/log/user/done" | wc -l` -eq 0 ]
  then
    echo false
  else
    echo true
  fi
}

# Usage: is_user_geocoded <username> => true or false
function is_user_geocoded() {
  mkdir -p "${RUN_DIR}/log/user" &> /dev/null
  touch "${RUN_DIR}/log/user/geocoded"
  if [ `grep "^${1}$" "${RUN_DIR}/log/user/geocoded" | wc -l` -eq 0]
  then
    echo false
  else
    echo true
  fi
}

# Usage: is_repo_data_done <[repo-owner]/[repo-name]> <data field> => true or false
function is_repo_data_done() {
  mkdir -p "${RUN_DIR}/log/repos" &> /dev/null
  touch "${RUN_DIR}/log/repos/${2}_done"
  if [ `grep "^${1}$" "${RUN_DIR}/log/repos/${2}_done" | wc -l` -eq 0 ]
  then
    echo false
  else
    echo true
  fi
}

# Usage: are_watched_done <username> => true or false
function are_watched_done() {
  mkdir -p "${RUN_DIR}/log/repos" &> /dev/null
  touch "${RUN_DIR}/log/repos/watched"
  if [ `grep "^${1}$" "${RUN_DIR}/log/repos/watched" | wc -l` -eq 0 ]
  then
    echo false
  else
    echo true
  fi
}

# Usage: are_commits_done <[repo-owner]/[repo-name]/[branch-name]> => true or false
function are_commits_done() {
  mkdir -p "${RUN_DIR}/log/commits" &> /dev/null
  touch "${RUN_DIR}/log/commits/done"
  if [ `grep "^${1}$" "${RUN_DIR}/log/commits/done" | wc -l` -eq 0 ]
  then
    echo false
  else
    echo true
  fi
}

# Usage: set_repo_data_done <[repo-owner]/[repo-name]> <data field> => void
function set_repo_data_done() {
  mkdir -p "${RUN_DIR}/log/repos" &> /dev/null
  echo "$1" >> "${RUN_DIR}/log/repos/${2}_done"
}

# Usage: set_commits_done <[repo-owner]/[repo-name]/[branch-name]> => void
function set_commits_done() {
  mkdir -p "${RUN_DIR}/log/commits" &> /dev/null
  echo "$1" >> "${RUN_DIR}/log/commits/done"
}

# Usage: set_watched_done <username> => void
function set_watched_done() {
  mkdir -p "${RUN_DIR}/log/repos" &> /dev/null
  echo "$1" >> "${RUN_DIR}/log/repos/watched"
}

# Usage: set_user_geocoded <username> => void
function set_user_geocoded() {
  mkdir -p "${RUN_DIR}/log/user" &> /dev/null
  echo "$1" >> "${RUN_DIR}/log/user/geocoded"
}

# Usage: set_user_search_done <term> => void
function set_user_search_done() {
  mkdir -p "${RUN_DIR}/log/user" &> /dev/null
  echo "$1" >> "{RUN_DIR}/log/user/done"
}

# Usage: save_user_location <username> <location> => void
function save_user_location() {
  mkdir -p "${RUN_DIR}/log/user/location/" &> /dev/null
  echo $2 > "${RUN_DIR}/log/user/location/${1}"
}

# Usage: is_key_value <string> => true or false
function is_key_value() {
  if [ `grep ":" "$1" | wc -l` -eq 0 ]
  then
    echo false
  else
    echo true
  fi
}

# Usage: get_key <'key: value' string> => 'key'
function get_key() {
  echo $1 | sed -e 's/:.*$//'
}

# Usage: get_value <'key: value' string> => 'value'
function get_value() {
  echo $1 | sed -e 's/^[^:]*: *//'
}

# Usage: grab_github_data <github api path>
function grab_github_data() {
  API_PATH="$1"
  RAW_FILE="${RUN_DIR}/raw/${API_PATH}"
  mkdir -p "`dirname "$RAW_FILE"`" &> /dev/null
  if [ ! -e "$RAW_FILE" ]
  then
    github_fetch "$API_PATH" > "$RAW_FILE"
  else
    echo "Already fetched: $API_PATH (using cached)"
  fi
}

# Usage: grab_geocode_data <username> => void
function grab_geocode_data() {
  RAW_FILE="${RUN_DIR}/raw/user/geocode/${1}"
  mkdir -p "`dirname "$RAW_FILE"`" &> /dev/null
  location=`cat "${RUN_DIR}/log/user/location/${username}"`
  if [ ! -e "$RAW_FILE" ]
  then
    yahoo_geocode "$location" > "$RAW_FILE"
  else
    echo "Already fetched geocode data for: ${1} (using cached)"
  fi
}

# Usage: user_search_api_path <term> => <github user search api path for 'term'>
function user_search_api_path() {
  echo "user/search/${1}"
}

# Usage: repo_data_api_path <[repo-owner]/[repo-name]> <data field, e.g. collaborators, contributors, branches> => <github repo api path for repo's data>
function repo_data_api_path() {
  echo "repos/show/${1}/${2}"
}

# Usage: branch_commits_api_path <[repo-owner]/[repo-name]/[branch-name]> => <github repo api path for branch's commits data>
function branch_commits_api_path() {
  echo "commits/list/${1}"
}

# Usage: watched_repos_path <username> => <github api path for 'username's watched repos>
function watched_repos_path() {
  echo "repos/watched/${1}"
}

# Usage: store_user_search <user search api path> => void
function store_user_search() {
  echo "Writing user search results to mongo for: " $term
  cat "${RUN_DIR}/raw/${1}" | python crawl2mongo.py --user-search
}

# Usage: repo_owner_name <'[repo owner]/[repo name]'> => '[repo owner]'
function repo_owner_name() {
   echo $1 | sed -e 's/\([^/]*\)\/.*/\1/'
}

# Usage: store_user_geocode <username>
function store_user_geocode() {
  echo "Writing geocode data to mongo for: ${1} -> `cat "${RUN_DIR}/log/user/location/${1}"`"
  cat "${RUN_DIR}/raw/user/geocode/${1}" | python crawl2mongo.py --geocode -u "$1"
}

# Usage: store_repo_data <repo data api path> => void
function store_repo_data() {
  repo_path=`dirname "$1"`
  reponame="${repo_path#repos/show/}"
  owner="`repo_owner_name "$reponame"`"
  echo "Writing `basename "$1"` data to mongo for: $reponame"
  cat "${RUN_DIR}/raw/${1}" | python crawl2mongo.py --repos-show -u "$owner" -r "${reponame#${owner}/}"
}

# Usage: store_commits_data <commits data api path> => void
function store_commits_data() {
  echo "Writing commits to mongo for: ${1#commits/list/}"
  cat "${RUN_DIR}/raw/${1}" | python crawl2mongo.py --commits
}

# Usage: parse_user_search <user search api path> => void
function parse_user_search() {
  term=`basename "$1"`
  if ! `is_user_search_done "$term"`
  then
    echo "Extracting user locations from search for: " $term
    cat "${RUN_DIR}/raw/${1}" | ruby user_data.rb | while read userlocation
    do
      username=`get_key "$userlocation"`
      if ! `is_user_seen "$username"`
      then
        location=`get_value "$userlocation"`
        save_user_location "$username" "$location"
        set_user_seen "$username"
      fi
    done
    store_user_search "$1"
    set_user_search_done "$term"
  else
    echo "Already did user search for: $term (skipping)"
  fi
}

# Usage: save_repo_branches <repo branches api path> => void
function save_repo_branches() {
  repo_path=`dirname "$1"`
  reponame=${repo_path#repos/show/}
  mkdir -p "${RUN_DIR}/log/repos/branches/`dirname ${reponame}`" &> /dev/null
  echo "Extracting branches for: " $reponame
  grep -v "[{}]" "${RUN_DIR}/raw/${1}" | sed -e 's/^ *"//' | sed -e 's/": *.*//' > "${RUN_DIR}/log/repos/branches/${reponame}"
}

# Usage: parse_repo_data <repo data api path> => void
function parse_repo_data() {
  field=`basename "$1"`
  repo_path=`dirname "$1"`
  reponame=${repo_path#repos/show/}
  if ! `is_repo_data_done "$reponame" "$field"`
  then
    echo "Extracting $field for: $reponame"
    if [ $field == 'branches' ]; then save_repo_branches "$1"
    else # collaborators or contributors
      cat "${RUN_DIR}/raw/${1}" | ruby user_data.rb | while read userdata
      do
        if `is_key_value "$userdata"`
          username="`get_key "$userdata"`"
          location="`get_value "$location"`"
          save_user_location "$username" "$location"
        then
          username=$userdata
        fi
        if ! `is_user_seen "$username"`; then set_user_seen "$username"; fi
      done
    fi
    store_repo_data "$1"
    set_repo_data_done "$reponame" "$field"
  else
    echo "Already got ${field} for: $reponame (skipping)"
  fi
}

# Usage: parse_watched_repos <watched repos api path> => void
function parse_watched_repos() {
  username=`basename "$1"`
  if ! `are_watched_done "$username"`
  then
    echo "Extracting watched repos from: " $username
    cat "${RUN_DIR}/raw/${1}" | ruby format_repos.rb | while read reponame
    do
      if ! `is_repo_seen "$reponame"`; then set_repo_seen "$reponame"; fi
    done
    set_watched_done "$username"
  else
    echo "Already got repos watched by: $username (skipping)"
  fi
}

# Usage: parse_geocode_data <username> => void
function parse_geocode_data() {
  if ! `is_user_geocoded "$1"`
  then
    store_user_geocode "$1"
    set_user_geocoded "$1"
  else
    echo "Already geocoded: ${1} (skipping)"
  fi
}

# Usage: all_seen_users => <all seen users, one per line>
function all_seen_users() {
  cat "${RUN_DIR}/log/user/seen"
}

# Usage: all_seen_repos => <all seen repos [owner-name/repo-name], one per line>
function all_seen_repos() {
  cat "${RUN_DIR}/log/repos/seen"
}

# Usage: all_repo_branches <[owner-name]/[repo-name]> => <all branches for given repo, one per line>
function all_repo_branches() {
  cat "${RUN_DIR}/log/repos/branches/${1}"
}
