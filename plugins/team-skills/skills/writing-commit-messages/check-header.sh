#!/usr/bin/env bash
# Checks a commit header: <type>[(scope)][!]: <description>, description <= 50 chars.
# Usage: bash check-header.sh "<header or full message>"

header="${1%%$'\n'*}"
types='feat|fix|docs|style|refactor|perf|test|build|ci|chore|revert'
re="^($types)(\([a-z0-9._/-]+\))?!?: (.+)$"

if [[ ! $header =~ $re ]]; then
  echo "FAIL: header must be <type>[(scope)][!]: <description>"
  echo "      type: ${types//|/ }; scope lowercase; one space after the colon"
  exit 1
fi

desc="${BASH_REMATCH[3]}"
len=${#desc}
fail=0

if (( len > 50 )); then
  echo "FAIL: description is $len chars, max 50"
  fail=1
fi
if [[ $desc == *. ]]; then
  echo "FAIL: description ends with a period"
  fail=1
fi
if [[ $desc == " "* ]]; then
  echo "FAIL: more than one space after the colon"
  fail=1
fi

(( fail )) && exit 1
echo "OK ($len/50)"
