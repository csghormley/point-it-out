# build a GDAL-enabled Django environment
# to build this Dockerfile, run the following command from the directory
# ABOVE the Django project
# docker build . -f<folder-containing-this-Dockerfile>

# pull base image containing dependencies
FROM csghor/mapsurvey-deps:latest

ENV PROJECT=collector
ENV STATICFILES_SRC=./collector/app_staticfiles

# set work directory
ENV APP_HOME=/home/app/web
WORKDIR $APP_HOME

# copy project and supporting files
# NOTE: the copy instruction runs from the context of the initiating command line's PWD
# i.e. this is run from two levels up
COPY ./$PROJECT/ .

# TODO: eliminate this dependency with environment file, since we're already passing secrets that way
RUN ln -sf site-config/localsettings.py $PROJECT/localsettings.py

#COPY $STATICFILES_SRC ./app_staticfiles

# chown all the files to the app user
RUN chown -R app:app $APP_HOME

# change to the app user
USER app

# DON'T run entrypoint.sh living in ./app folder (see docker-compose.yml for initial command)
##ENTRYPOINT ["/usr/src/app/entrypoint.sh"]
