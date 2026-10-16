#!/usr/bin/env bash
# Checks a commit message file against the task format in SKILL.md:
# header (title <= 60 chars), blank line, 1-3 description lines (<= 72 chars), optional trailers.
# Usage: bash check-message.sh <message-file>

# Count characters, not bytes: ă, î, ș, ț are two bytes each.
export LC_ALL=C.UTF-8

file="$1"
[[ -f $file ]] || { echo "FAIL: message file not found: $file"; exit 1; }

mapfile -t lines < <(sed 's/\r$//' "$file")
while (( ${#lines[@]} )) && [[ -z ${lines[-1]//[[:space:]]/} ]]; do unset 'lines[-1]'; done

fail=0
err() { echo "FAIL: $1"; fail=1; }

types='feat|fix|docs|style|refactor|perf|test|build|ci|chore|revert'
re="^($types)(\([a-z0-9._/-]+\))?!?: (.+)$"
header="${lines[0]}"
if [[ ! $header =~ $re ]]; then
  echo "FAIL: header must be <type>[(scope)][!]: <titlu>"
  echo "      type: ${types//|/ }; scope lowercase; one space after the colon"
  exit 1
fi
title="${BASH_REMATCH[3]}"
(( ${#title} > 60 )) && err "title is ${#title} chars, max 60"
[[ $title == *. ]] && err "title ends with a period"
[[ $title == " "* ]] && err "more than one space after the colon"
[[ ${title:0:1} == [A-ZĂÂÎȘȚŞŢ] ]] && err "title starts with a capital letter"
[[ $title =~ ^(wip|fixup|misc|update|changes)([^[:alnum:]]|$) ]] && err "title says nothing about the task: '${title%% *}'"

(( ${#lines[@]} > 1 )) && [[ -n ${lines[1]} ]] && err "line 2 must be blank"

# Description: from line 3 up to the next blank line.
i=2; desc=0
while (( i < ${#lines[@]} )) && [[ -n ${lines[i]} ]]; do
  (( desc++ ))
  (( ${#lines[i]} > 72 )) && err "description line $desc is ${#lines[i]} chars, max 72"
  [[ ${lines[i]} =~ ^(Item|BREAKING\ CHANGE|Co-Authored-By): ]] && err "trailer '${lines[i]%%:*}' needs a description before it"
  (( i++ ))
done
(( desc == 0 )) && err "description missing: a blank line, then 1-3 lines"
(( desc > 3 )) && err "description is $desc lines, max 3"

# Trailers: after one blank line, to the end.
trailer_re='^(Item: ([A-Z][A-Z0-9]*-[0-9]+|AB#[0-9]+)|BREAKING CHANGE: .+|Co-Authored-By: .+)$'
items=0
(( i++ ))
while (( i < ${#lines[@]} )); do
  line="${lines[i]}"
  if [[ -z $line ]]; then
    err "blank line inside the trailers"
  elif [[ ! $line =~ $trailer_re ]]; then
    err "not a trailer: '$line' (Item: ABC-12 or AB#12, BREAKING CHANGE:, Co-Authored-By:)"
  elif [[ $line == Item:* ]]; then
    (( items++ ))
  fi
  (( i++ ))
done
(( items > 1 )) && err "$items Item lines, max 1: one commit, one task"

grep -q '[şţŞŢ]' "$file" && err "ş/ţ with cedilla: use ș/ț with comma below"

(( fail )) && exit 1
echo "OK (title ${#title}/60, description $desc/3 lines)"
