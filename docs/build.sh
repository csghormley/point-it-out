#!/bin/sh

if !( [ -d .venv ] ); then
    echo "creating virtual environment"
    uv venv
fi

. .venv/bin/activate

# make sure we're in the virtual environment
if [ -n "$VIRTUAL_ENV" ]; then
    uv pip install -r requirements.txt && make html
else
    echo "unable to activate virtual environment"
fi

deactivate
