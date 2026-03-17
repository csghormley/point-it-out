# build a GDAL-enabled Django environment
# to build this Dockerfile, run the following command from the directory
# ABOVE the Django project
# docker build . -f<folder-containing-this-Dockerfile>

# pull base image containing dependencies
FROM csghor/mapsurvey-env:latest

# set work directory
ENV APP_HOME=/home/app/web
WORKDIR $APP_HOME

# copy project and supporting files
# NOTE: the copy instruction runs from the context of the initiating command line's PWD
# i.e. this is run from two levels up
COPY ./collector/ .

# use COPY instruction for config files so they get cached and updated when changed

# TODO: eliminate localsettings dependency with environment file, since we're already passing secrets that way
COPY ./collector/collector/site-config/localsettings-docker.py collector/localsettings.py

# link to the docker version of the env file (WHY does path differ from localsettings????)
COPY ./collector/collector/site-config/.env.docker .env

# chown all the files to the app user
RUN chown -R app:app $APP_HOME

# change to the app user
USER app
