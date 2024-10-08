#!/bin/sh

./docker-stack/build-deps.sh
./docker-stack/build-django.sh
./docker-stack/build-nginx.sh
