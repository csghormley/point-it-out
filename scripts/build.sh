#!/bin/sh

# do not run unless running from project root
[ -e scripts/bootstrap.sh ] || { echo "This script must be run from the project root directory."; exit 1; }

# make sure the venv is active
. env/bin/activate

if ! ./scripts/check.sh; then
    echo "errors found - aborting build."
    exit 1
fi

# collect static files (this can be run separately for static file changes)
./collector/manage.py collectstatic --noinput

# update the version.txt file (so that it's included in the images below!)
./scripts/version.sh

# build the docker images in order
# A1. deps - Ubuntu with GDAL + apt updates + python venv
# A2. env - python library requirements.txt (on deps)
# A3. django - this django app (on env)
# B1. nginx - add local config files to nginx mainline image
./docker-stack/build-deps.sh
./docker-stack/build-django-env.sh
./docker-stack/build-django.sh
./docker-stack/build-nginx.sh

