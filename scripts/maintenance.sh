#!/bin/sh

# do not run unless running from project root
[ -e scripts/bootstrap.sh ] || { echo "This script must be run from the project root directory."; exit 1; }

echo performing a docker system prune

# do a system update
#sudo apt-get update && sudo apt-get upgrade

# clean the docker directory
# --force skips confirmation, nothing drastic
sudo docker system prune --force
