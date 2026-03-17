#!/bin/sh

# do not run unless running from project root
[ -e scripts/bootstrap.sh ] || echo "This script must be run from the project root directory."; exit 1

sudo apt-get install -y python3 python-is-python3

# Check if uv is installed, install if needed
if ! command -v uv &> /dev/null; then
    echo "Installing uv..."
    curl -LsSf https://astral.sh/uv/install.sh | sh
    # Add uv to PATH for current session
    export PATH="$HOME/.local/bin:$PATH"
fi

# create a fresh virtual environment in 'env' using uv,
# and activate it
uv venv env
source env/bin/activate

# install the required packages with uv
uv pip install -r requirements.txt
