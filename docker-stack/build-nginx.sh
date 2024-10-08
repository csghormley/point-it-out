#!/bin/sh

IMAGE_NAME=csghor/nginx

echo Building a docker image for nginx...
docker build . -f docker-stack/nginx/Dockerfile -t \
    $IMAGE_NAME:$(git rev-parse --short HEAD)
docker tag $IMAGE_NAME:$(git rev-parse --short HEAD) $IMAGE_NAME:latest
