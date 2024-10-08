#!/bin/sh

IMAGE_NAME=csghor/mapsurvey-app

# make sure we're running from the right working directory
if !([ -f collector/manage.py ]); then
    echo "ERROR: Run from parent directory containing 'docker-stack' and 'collector' folders."
    exit 1
fi

# (Don't collect static files in docker build - unprivileged user does that; only root builds the image.)
echo Building a docker image for the current Django project...
docker build . -f docker-stack/img-django-app/Dockerfile -t \
    $IMAGE_NAME:$(git rev-parse --short HEAD)
docker tag $IMAGE_NAME:$(git rev-parse --short HEAD) $IMAGE_NAME:latest

# collect static files (they don't live inside the image)
echo remember to collect static files!
echo env/bin/python ../collector/manage.py collectstatic
