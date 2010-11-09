#!/bin/bash

function var_test() {
  echo $RUN_DIR
}

function github_fetch() {
  URL="http://github.com/api/v2/json/${1}"
  echo Fetching: "$URL" 1>&2
  curl -s "$URL" | jsonpretty
  sleep 2
}

function yahoo_geocode() {
  URL="http://where.yahooapis.com/geocode?flags=J&appid=`grep id: ${RUN_DIR}/placefinder/config.yml | sed -e 's/^ *id: "//' | sed -e 's/"$//'`&location=`perl -MURI::Escape -e 'print uri_escape($ARGV[0]);' "$1"`"
  echo Fetching: "$URL" 1>&2
  curl -s "$URL" | jsonpretty
  sleep 0.5
}

function usernames2geocodes() {
  mkdir -p "${RUN_DIR}/raw/user/geocode" &> /dev/null
  mkdir -p "${RUN_DIR}/log/user/geocode" &> /dev/null
  mkdir -p "${RUN_DIR}/log/user/ambiguous_location" &> /dev/null
  ls "${RUN_DIR}"/log/user/location | while read username
  do
    RAW_FILE="${RUN_DIR}/raw/user/geocode/${username}"
    location=`cat "${RUN_DIR}/log/user/location/${username}"`
    if [ ! -e "$RAW_FILE" ]
    then
      yahoo_geocode "$location" > "$RAW_FILE"
      if [ `grep '^  *"latitude":  *' "$RAW_FILE" | wc -l` -gt 0 ]
      then
        if [ `grep '^  *"latitude":  *' "$RAW_FILE" | wc -l` -gt 1 ]
        then
          echo Ambiguous results for: "$username" @ "$location" \(ignoring\)
          rm "${RUN_DIR}/log/user/geocode/${username}" &> /dev/null
          echo "$location" > "${RUN_DIR}/log/user/ambiguous_location/${username}"
        else
          echo Geocoding: "$username" @ "$location"
          lat=`grep '^  *"latitude":  *' "$RAW_FILE" | sed -e 's/^  *"latitude":  *"*//' | sed -e 's/"*,*$//'`
          lng=`grep '^  *"longitude":  *' "$RAW_FILE" | sed -e 's/^  *"longitude":  *"*//' | sed -e 's/"*,*$//'`
          echo ${lat},${lng} > "${RUN_DIR}/log/user/geocode/${username}"
        fi
      fi
    else
      echo "Already geocoded: ${username} (skipping)"
    fi
  done
}

function seed_usernames() {
  mkdir -p "${RUN_DIR}/raw/user/search" &> /dev/null
  mkdir -p "${RUN_DIR}/log/user" &> /dev/null
  touch "${RUN_DIR}/log/user/seen"
  touch "${RUN_DIR}/log/user/done"
  for letter in a b c d e f g h i j k l m n o p q r s t u v w x y z
  do
    if [ `grep "^${letter}$" "${RUN_DIR}/log/user/done" | wc -l` -eq 0 ]
    then
      RAW_FILE="${RUN_DIR}/raw/user/search/${letter}"
      if [ ! -e "$RAW_FILE" ]
      then
        github_fetch "user/search/$letter" > "$RAW_FILE"
      fi

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
      cat "${RAW_FILE}" | ruby user_email.rb | while read useremail
      do
        username=`echo $useremail | sed -e 's/:.*$//'`
        email=`echo $useremail | sed -e 's/^[^:]*: *//'`
        mkdir -p "${RUN_DIR}/log/user/email" &> /dev/null
        if [ `echo $email | wc -m` -gt 1 ]
        then
          echo $email > "${RUN_DIR}/log/user/email/${username}"
          echo $username > "${RUN_DIR}/log/user/email/${email}"
        fi
      done
      echo $letter >> "${RUN_DIR}/log/user/done"
    else
      echo "Already user-searched: $letter (skipping)"
    fi
  done
}

function usernames2repos() {
  mkdir -p "${RUN_DIR}/raw/repos/watched" &> /dev/null
  mkdir -p "${RUN_DIR}/log/repos" &> /dev/null
  touch "${RUN_DIR}/log/repos/seen"
  touch "${RUN_DIR}/log/repos/done"
  cat "${RUN_DIR}/log/user/seen" | while read username
  do
    if [ `grep "^${username}$" "${RUN_DIR}/log/repos/done" | wc -l` -eq 0 ]
    then
      RAW_FILE="${RUN_DIR}/raw/repos/watched/${username}"
      if [ ! -e "$RAW_FILE" ]
      then
        github_fetch "repos/watched/$username" > "$RAW_FILE"
      fi

      echo "Extracting watched repos from: " $username
      cat "$RAW_FILE" | ruby format_repos.rb | while read reponame
      do
        if [ `grep "^${reponame}$" "${RUN_DIR}/log/repos/seen" | wc -l` -eq 0 ]
        then
          echo "$reponame" >> "${RUN_DIR}/log/repos/seen"
        fi
      done
      echo $username >> "${RUN_DIR}/log/repos/done"
    else
      echo "Already got watched: $username (skipping)"
    fi
  done
}

function repos2collaborators() {
  mkdir -p "${RUN_DIR}/log/repos/collaborators" &> /dev/null
  touch "${RUN_DIR}/log/repos/collaborators/done"
  cat "${RUN_DIR}/log/repos/seen" | while read reponame
  do
    if [ `grep "^${reponame}$" "${RUN_DIR}/log/repos/collaborators/done" | wc -l` -eq 0 ]
    then
      RAW_FILE="${RUN_DIR}/raw/repos/show/${reponame}/collaborators"
      mkdir -p "`dirname "${RAW_FILE}"`" &> /dev/null
      if [ ! -e "$RAW_FILE" ]
      then
        github_fetch "repos/show/${reponame}/collaborators" > "$RAW_FILE"
      fi

      mkdir -p "${RUN_DIR}/log/repos/collaborators/`dirname ${reponame}`" &> /dev/null
      touch "${RUN_DIR}/log/repos/collaborators/${reponame}"
      echo "Extracting collaborators for: " $reponame
      cat "$RAW_FILE" | ruby repo_collaborators.rb | while read username
      do
        if [ `grep "^${username}$" "${RUN_DIR}/log/user/seen" | wc -l` -eq 0 ]
        then
          echo "$username" >> "${RUN_DIR}/log/user/seen"
        fi
        if [ `grep "$username" "${RUN_DIR}/log/repos/collaborators/${reponame}" | wc -l` -eq 0 ]
        then
          echo "$username" >> "${RUN_DIR}/log/repos/collaborators/${reponame}"
        fi
        mkdir -p "${RUN_DIR}/log/user/collaborates" &> /dev/null
        touch "${RUN_DIR}/log/user/collaborates/${username}"
        if [ `grep "^${reponame}$" "${RUN_DIR}/log/user/collaborates/${username}" | wc -l` -eq 0 ]
        then
          echo $reponame >> "${RUN_DIR}/log/user/collaborates/${username}"
        fi
      done
      echo $reponame >> "${RUN_DIR}/log/repos/collaborators/done"
    else
      echo "Already got collaborators: $reponame (skipping)"
    fi
  done
}

function repos2contributors() {
  mkdir -p "${RUN_DIR}/log/repos/contributors" &> /dev/null
  touch "${RUN_DIR}/log/repos/contributors/done"
  cat "${RUN_DIR}/log/repos/seen" | while read reponame
  do
    if [ `grep "^${reponame}$" "${RUN_DIR}/log/repos/contributors/done" | wc -l` -eq 0 ]
    then
      RAW_FILE="${RUN_DIR}/raw/repos/show/${reponame}/contributors"
      mkdir -p "`dirname "${RAW_FILE}"`" &> /dev/null
      if [ ! -e "$RAW_FILE" ]
      then
        github_fetch "repos/show/${reponame}/contributors" > "$RAW_FILE"
      fi

      mkdir -p "${RUN_DIR}/log/repos/contributors/`dirname ${reponame}`" &> /dev/null
      mkdir -p "${RUN_DIR}/log/user/location/" &> /dev/null
      mkdir -p "${RUN_DIR}/log/user/email" &> /dev/null
      touch "${RUN_DIR}/log/repos/contributors/${reponame}"
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
        if [ `grep "$username" "${RUN_DIR}/log/repos/contributors/${reponame}" | wc -l` -eq 0 ]
        then
          echo "$username" >> "${RUN_DIR}/log/repos/contributors/${reponame}"
        fi
        mkdir -p "${RUN_DIR}/log/user/contributes" &> /dev/null
        touch "${RUN_DIR}/log/user/contributes/${username}"
        if [ `grep "^${reponame}$" "${RUN_DIR}/log/user/contributes/${username}" | wc -l` -eq 0 ]
        then
          echo $reponame >> "${RUN_DIR}/log/user/contributes/${username}"
        fi
      done
      cat "$RAW_FILE" | ruby user_email.rb contributors | while read useremail
      do
        username=`echo $useremail | sed -e 's/:.*$//'`
        email=`echo $useremail | sed -e 's/^[^:]*: *//'`
        if [ `echo $email | wc -m` -gt 1 ]
        then
          echo $email > "${RUN_DIR}/log/user/email/${username}"
          echo $username > "${RUN_DIR}/log/user/email/${email}"
        fi
      done
      echo $reponame >> "${RUN_DIR}/log/repos/contributors/done"
    else
      echo "Already got contributors: $reponame (skipping)"
    fi
  done
}

function repos2usernames() {
  mkdir -p "${RUN_DIR}/raw/user/search" &> /dev/null
  mkdir -p "${RUN_DIR}/log/user/location" &> /dev/null
  mkdir -p "${RUN_DIR}/log/user/email" &> /dev/null
  touch "${RUN_DIR}/log/user/seen"
  ls "$RUN_DIR/raw/repos/show/" | sed -e 's/\/$//' | while read username
  do
    if [ `grep "^${username}$" "${RUN_DIR}/log/user/done" | wc -l` -eq 0 ]
    then
      RAW_FILE="${RUN_DIR}/raw/user/search/${username}"
      if [ ! -e "$RAW_FILE" ]
      then
        github_fetch "user/search/$username" > "$RAW_FILE"
      fi

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
      cat "${RAW_FILE}" | ruby user_email.rb | while read useremail
      do
        username=`echo $useremail | sed -e 's/:.*$//'`
        email=`echo $useremail | sed -e 's/^[^:]*: *//'`
        if [ `echo $email | wc -m` -gt 1 ]
        then
          echo $email > "${RUN_DIR}/log/user/email/${username}"
          echo $username > "${RUN_DIR}/log/user/email/${email}"
        fi
      done
      echo $username >> "${RUN_DIR}/log/user/done"
    else
      echo "Already user-searched: $username (skipping)"
    fi
  done
}


function repos2branches() {
  mkdir -p "${RUN_DIR}/log/repos/branches" &> /dev/null
  touch "${RUN_DIR}/log/repos/branches/done"
  cat "${RUN_DIR}/log/repos/seen" | while read reponame
  do
    if [ `grep "^${reponame}$" "${RUN_DIR}/log/repos/branches/done" | wc -l` -eq 0 ]
    then
      RAW_FILE="${RUN_DIR}/raw/repos/show/${reponame}/branches"
      mkdir -p "`dirname "${RAW_FILE}"`" &> /dev/null
      if [ ! -e "$RAW_FILE" ]
      then
        github_fetch "repos/show/${reponame}/branches" > "$RAW_FILE"
      fi

      mkdir -p "${RUN_DIR}/log/repos/branches/`dirname ${reponame}`" &> /dev/null
      touch "${RUN_DIR}/log/repos/branches/${reponame}"
      echo "Extracting branches for: " $reponame
      grep -v "[{}]" branches | sed -e 's/^ *"//' | sed -e 's/": *.*//' > "${RUN_DIR}/log/repos/branches/${reponame}"
      echo $reponame >> "${RUN_DIR}/log/repos/branches/done"
    else
      echo "Already got branches: $reponame (skipping)"
    fi
  done
}

function branches2commits() {
  mkdir -p "${RUN_DIR}/log/commits" &> /dev/null
  touch "${RUN_DIR}/log/commits/seen"
  touch "${RUN_DIR}/log/commits/done"
  cat "${RUN_DIR}/log/repos/seen" | while read reponame
  do
    if [ `grep "^${reponame}$" "${RUN_DIR}/log/commits/done" | wc -l` -eq 0 ]
    then
      mkdir -p "${RUN_DIR}/raw/commits/list/${reponame}" &> /dev/null
      cat "${RUN_DIR}/log/repos/branches/${reponame}" | while read branchname
      do
        if [`grep "^${reponame}/${branchname}$" "${RUN_DIR}/log/commits/done" | wc -l` -eq 0 ]
        then
          RAW_FILE="${RUN_DIR}/raw/commits/list/${reponame}/${branchname}"
          mkdir -p "`dirname "${RAW_FILE}"`" &> /dev/null
          if [ ! -e "$RAW_FILE" ]
          then
            github_fetch "commits/list/${reponame}/${branchname}" > "$RAW_FILE"
          fi

          if [ `cat "$RAW_FILE" | wc -l` -gt 0 ]
          then
            mkdir -p "${RUN_DIR}/log/commits/parents" &> /dev/null
            echo "Extracting commits for: " ${reponame}/${branchname}
            cat "$RAW_FILE" | ruby commit_parents.rb | while read commitparents
            do
              commit=`echo $commitparents | sed -e 's/:.*$//'`
              mkdir -p "${RUN_DIR}/log/repos/commits/${reponame}/`dirname "${branchname}"`" &> /dev/null
              touch "${RUN_DIR}/log/repos/commits/${reponame}/${branchname}"
              if [ `grep "^${commit}$" "${RUN_DIR}/log/repos/commits/${reponame}/${branchname}" | wc -l` -eq 0 ]
              then
                echo "$commit" >> "${RUN_DIR}/log/repos/commits/${reponame}/${branchname}"
              fi
              mkdir -p "${RUN_DIR}/log/commits/branches"
              touch "${RUN_DIR}/log/commits/branches/${commit}"
              if [ `grep "^${reponame}/${branchname}$" "${RUN_DIR}/log/commits/branches/${commit}" | wc -l` -eq 0 ]
              then
                echo "${reponame}/${branchname}" >> "${RUN_DIR}/log/commits/branches/${commit}"
              fi
              if [ `grep "^${commit}$" "${RUN_DIR}/log/commits/done" | wc -l` -eq 0 ]
              then
                parents=`echo $commitparents | sed -e 's/[^:]*: *//'`
                touch "${RUN_DIR}/log/commits/parents/${commit}"
                for parent in $parents
                do
                  if [ `grep $parent "${RUN_DIR}/log/commits/parents/${commit}" | wc -l` -eq 0 ]
                  then
                    echo $parent >> "${RUN_DIR}/log/commits/parents/${commit}"
                  fi
                done
                if [ `grep "^${commit}$" "${RUN_DIR}/log/commits/seen" | wc -l` -eq 0 ]
                then
                  echo "$commit" >> "${RUN_DIR}/log/commits/seen"
                fi
                echo "$commit" >> "${RUN_DIR}/log/commits/done"
              else
                echo "Already processed commit: $commit (skipping)"
              fi
            done

            mkdir -p "${RUN_DIR}/log/commits/committed_date" &> /dev/null
            mkdir -p "${RUN_DIR}/log/commits/authored_date" &> /dev/null
            cat "$RAW_FILE" | ruby commit_dates.rb | while read commitdates
            do
              commit=`echo $commitdates | sed -e 's/:.*$//'`
              committed=`echo $commitdates | sed -e 's/[^:]*: *//' | sed -e 's/  *.*$//'`
              authored=`echo $commitdates | sed -e 's/[^:]*: *[^ ]*  *//'`
              echo $committed > "${RUN_DIR}/log/commits/committed_date/${commit}"
              echo $authored > "${RUN_DIR}/log/commits/authored_date/${commit}"
            done

            mkdir -p "${RUN_DIR}/log/commits/author" &> /dev/null
            mkdir -p "${RUN_DIR}/log/commits/email" &> /dev/null
            cat "$RAW_FILE" | ruby commit_author.rb | while read commitauthor
            do
              commit=`echo $commitauthor | sed -e 's/:.*$//'`
              email=`echo $commitauthor | sed -e 's/[^:]*: *//' | sed -e 's/  *.*$//'`
              author=`echo $commitauthor | sed -e 's/[^:]*: *[^ ][^ ]* *//'`
              echo $email > "${RUN_DIR}/log/commits/email/${commit}"
              touch "${RUN_DIR}/log/commits/email/${email}"
              if [ `grep "^${commit}$" "${RUN_DIR}/log/commits/email/${email}" | wc -l` -eq 0 ]
              then
                echo "$commit" >> "${RUN_DIR}/log/commits/email/${email}"
              fi
              if [ `echo $author | wc -m` -gt 1 ]
              then
                echo $author > "${RUN_DIR}/log/commits/author/${commit}"
                touch "${RUN_DIR}/log/commits/author/${author}"
                if [ `grep "^${commit}$" "${RUN_DIR}/log/commits/author/${author}" | wc -l` -eq 0 ]
                then
                  echo "$commit" >> "${RUN_DIR}/log/commits/author/${author}"
                fi
              fi
            done
          fi
          echo "${reponame}/${branchname}" >> "${RUN_DIR}/log/commits/done"
        else
          echo "Already got commits: ${reponame}/${branchname} (skipping)"
        fi
      done
      echo "$reponame" >> "${RUN_DIR}/log/commits/done"
    else
      echo "Already got all commits: ${reponame} (skipping)"
    fi
  done
}
