#!/bin/sh

# do not run unless running from project root
[ -e scripts/bootstrap.sh ] || { echo "This script must be run from the project root directory."; exit 1; }

# make sure the venv is active
. env/bin/activate

# run django's built-in error checker
if (./collector/manage.py check); then
    echo "manage.py check: passed"
else
    echo "manage.py check: validation error - aborting build"
    exit 1
fi

# run django's built-in template validator
if (./collector/manage.py validate_templates); then
    echo "manage.py validate_templates: passed"
else
    echo "manage.py validate_templates: validation error - aborting build"
    exit 1
fi

# use ruff to check for non-trivial errors
error_lines=$(ruff check collector/ | grep "= help" | grep -v "Remove unused" | wc -l)

if [ $error_lines -gt 0 ]; then
    echo "Ruff found $error_lines errors."
    exit 1
else
    echo "Ruff found no errors."
fi
