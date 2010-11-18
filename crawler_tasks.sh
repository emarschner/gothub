#!/bin/bash
#
# Eli Marschner
#
# Communicate with data APIs, backup responses to disk,
# and write to MongoDB via crawl2mongo.py

. "${RUN_DIR}/lib.sh"

# Fetches: [GITHUB API]/user/search/{letter}
# Processing:
#   usernames => log/user/seen
#   locations => log/user/location/{username}
# DB: insert user data objects
# State files:
#   log/user/done
#   log/user/seen
# Run before running:
#   usernames2repos
# Run after running: none
function seed_usernames() {
  for letter in a b c d e f g h i j k l m n o p q r s t u v w x y z
  do
    user_search_api_path="`user_search_api_path ${letter}`"
    grab_github_data "$user_search_api_path"
    parse_user_search "$user_search_api_path"
  done
}

# Fetches: locations in log/user/location/{username} from Yahoo PlaceFinder API
# Processing: none
# DB: modify user data objects with geocodes
# State files:
#   log/user/geocoded
# Run before running: none
# Run after running:
#   repos2owners
#   repos2collaborators
#   repos2contributors
function usernames2geocodes() {
  all_seen_users | while read username
  do
    grab_geocode_data "$username"
    parse_geocode_data "$username"
  done
}

# Fetches: [GITHUB API]/repos/watched/{username}
# Processing: reponames => log/repos/seen
# DB: none (used ony to get reponames for other crawler functions)
# State files:
#   log/repos/watched
#   log/repos/seen
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
  all_seen_users | while read username
  do
    watched_repos_path="`watched_repos_path "$username"`"
    grab_github_data "$watched_repos_path"
    parse_watched_repos "$watched_repos_path"
  done
}

# Fetches: [GITHUB API]/user/search/{username}
# Processing:
#   usernames => log/user/seen
#   locations => log/user/location/{username}
# DB: insert user data objects
# State files:
#   log/user/done
#   log/user/seen
# Run before running:
#   usernames2geocodes
#   usernames2repos
# Run after running:
#   usernames2repos
function repos2owners() {
  all_seen_repos | while read reponame
  do
    user_search_api_path="`user_search_api_path "$(repo_owner_name "$reponame")"`"
    grab_github_data "$user_search_api_path"
    parse_user_search "$user_search_api_path"
  done
}

# Fetches: [GITHUB API]/repos/show/{repo owner}/{repo name}/collaborators
# Processing: usernames => log/user/seen
# DB: insert collaborators property into repo object
# State files:
#   log/repos/collaborators/done
#   log/user/seen
# Run before running:
#   usernames2geocodes
#   usernames2repos
# Run after running:
#   usernames2repos
function repos2collaborators() {
  all_seen_repos | while read reponame
  do
    repo_collaborators_api_path="`repo_data_api_path "$reponame" collaborators`"
    grab_github_data "$repo_collaborators_api_path"
    parse_repo_data "$repo_collaborators_api_path"
  done
}

# Fetches: [GITHUB API]/repos/show/{repo owner}/{repo name}/contributors
# Processing:
#   usernames => log/user/seen
#   locations => log/user/location/{username}
# DB: insert contributors property into repo object
# State files:
#   log/repos/contributors/done
#   log/user/seen
# Run before running:
#   usernames2geocodes
#   usernames2repos
# Run after running:
#   usernames2repos
function repos2contributors() {
  all_seen_repos | while read reponame
  do
    repo_contributors_api_path="`repo_data_api_path "$reponame" contributors`"
    grab_github_data "$repo_contributors_api_path"
    parse_repo_data "$repo_contributors_api_path"
  done
}

# Fetches: [GITHUB API]/repos/show/{repo owner}/{repo name}/branches
# Processing: repo branches => log/repos/branches/{repo owner}/{repo name}
# DB: insert branches property into repo object
# State files:
#   log/repos/branches/done
# Run before running:
#   branches2commits
# Run after running:
#   usernames2repos
function repos2branches() {
  all_seen_repos | while read reponame
  do
    repo_branches_api_path="`repo_data_api_path "$reponame" branches`"
    grab_github_data "$repo_branches_api_path"
    parse_repo_data "$repo_branches_api_path"
  done
}

# Fetches: [GITHUB API]/commits/list/{repo owner}/{repo name}/{branch name}
# Processing: none
# DB: insert commit objects
# State files:
#   log/commits/done
# Run before running: none
# Run after running:
#   repos2branches
function branches2commits() {
  all_seen_repos | while read reponame
  do
    all_repo_branches "$reponame" | while read branchname
    do
      if ! `are_commits_done "${reponame}/${branchname}"`
      then
        branch_commits_api_path="`branch_commits_api_path "${reponame}/${branchname}"`"
        grab_github_data "$branch_commits_api_path"
        store_commits_data "$branch_commits_api_path"
        set_commits_done "${reponame}/${branchname}"
      fi
    done
  done
}
