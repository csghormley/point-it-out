#!/bin/sh

sudo apt-get install -y python3-venv python-is-python3

# create a fresh virtual environment in 'env',
# and activate it
python3 -m venv env
source env/bin/activate

# install the required packages
pip install -r requirements.txt
