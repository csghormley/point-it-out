#!/bin/sh

# do not run unless running from project root
[ -e scripts/bootstrap.sh ] || { echo "This script must be run from the project root directory."; exit 1; }

# make sure the venv is active
. env/bin/activate

# run django's built-in error checker
if (./collector/manage.py check); then
    echo "manage.py check: passed"
else
    echo "manage.py check: validation error - aborting migration"
    exit 1
fi

# run django's makemigration logic
if (./collector/manage.py makemigrations); then
    echo "manage.py migrations created"
else
    echo "manage.py check: migration error - aborting"
    exit 1
fi

# apply the changes on the running instance
# required since we need an updated image to apply
./checkbuildrun.sh

docker compose -f docker-stack/docker-compose.yml \
       exec -i django ./manage.py migrate

