#!/bin/sh

# do not run unless running from project root
[ -e scripts/bootstrap.sh ] || { echo "This script must be run from the project root directory."; exit 1; }

# Get the project root directory (parent of scripts folder)
WORKDIR=$(cd "$(dirname "$0")/.." && pwd)

git log --pretty=format:"%h %ad | %s [%an]" --date=short -1 > "$WORKDIR/collector/pio/templates/pio/version.txt"
