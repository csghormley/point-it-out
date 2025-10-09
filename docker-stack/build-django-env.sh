#!/bin/sh

IMAGE_NAME=csghor/mapsurvey-env

# make sure we're running from the right working directory
if !([ -f collector/manage.py ]); then
    echo "ERROR: Run from parent directory containing 'docker-stack' and 'collector' folders."
    exit 1
fi

echo Building a docker image with required Python libraries...
docker build . -f docker-stack/img-django-env/Dockerfile -t \
    $IMAGE_NAME:$(git rev-parse --short HEAD)
docker tag $IMAGE_NAME:$(git rev-parse --short HEAD) $IMAGE_NAME:latest
