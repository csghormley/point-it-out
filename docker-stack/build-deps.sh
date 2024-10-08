#!/bin/sh

IMAGE_NAME=csghor/mapsurvey-deps

echo building a docker image for the current Django project dependencies
docker build . -f docker-stack/img-django-deps/Dockerfile -t \
    $IMAGE_NAME:$(git rev-parse --short HEAD)
docker tag $IMAGE_NAME:$(git rev-parse --short HEAD) $IMAGE_NAME:latest
