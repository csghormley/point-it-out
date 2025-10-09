#!/bin/sh

# do not run unless running from project root
[ -e scripts/bootstrap.sh ] || echo "This script must be run from the project root directory."; exit 1

sudo apt-get install -y python3-venv python-is-python3

# create a fresh virtual environment in 'env',
# and activate it
python3 -m venv env
source env/bin/activate

# install the required packages
pip install -r requirements.txt
