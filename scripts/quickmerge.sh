#!/bin/sh
git co dev && git pull && git co ubuntu && git merge dev; git push
