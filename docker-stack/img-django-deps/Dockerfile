# build an image providing all dependencies for the Django project
# (but not the project files)
#
# to build this Dockerfile, run the following command from the directory
# ABOVE the Django project
# docker build . -f<folder-containing-this-Dockerfile>

# pull official base image
# NOTE: keep the GDAL version in sync with the linux GDAL pin in pyproject.toml
# (3.13.x images are based on Ubuntu 26.04, which ships Python 3.14)
FROM ghcr.io/osgeo/gdal:ubuntu-full-3.13.3

# set work directory
WORKDIR /app

# set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# install dependencies
RUN apt-get update \
    && apt-get upgrade -y \
    && apt-get install -y \
      build-essential \
      git \
      libffi-dev \
      postgresql-client \
      python3-venv \
      python3-dev \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# create directory for the app user
RUN mkdir -p /home/app

# create the app user
# (Ubuntu 26.04 base images no longer include adduser/addgroup)
RUN groupadd --system app \
    && useradd --system --gid app --home-dir /home/app --shell /usr/sbin/nologin app

# create the appropriate directories
ENV HOME=/home/app
ENV APP_HOME=/home/app/web
RUN mkdir -p $APP_HOME/staticfiles
WORKDIR $APP_HOME
