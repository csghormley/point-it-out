#!/bin/sh

# do not run unless running from project root
[ -e scripts/bootstrap.sh ] || echo "This script must be run from the project root directory."; exit 1

echo "checking docker process status..." &&
    if ! $(docker ps | grep -q "nginx"); then echo "Docker nginx not running"; fi &&
    if ! $(docker ps | grep -q "postgis"); then echo "Docker postgis not running"; fi &&
    if ! $(docker ps | grep -q "mapsurvey-app"); then echo "Docker mapsurvey process not running"; fi &&
    echo "$(docker ps | grep -v "^CONTAINER" | wc -l) docker processes running"

echo "\nStorage status:"
df -h . | tail -1
