#! /bin/sh

# create the database if needed
createdb --host=postgis -U postgres

python manage.py createdb

# run the application server
gunicorn collector.wsgi:application --bind 0.0.0.0:8000
