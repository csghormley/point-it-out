#!/bin/sh

ROOT_PASSWD=$(cat $ROOT_DB_PASSWORD_FILE)
APP_PASSWD=$(cat $APP_DB_PASSWORD_FILE)

# create the database
psql "dbname=postgres host=postgis user=postgres password=$ROOT_PASSWD" \
     -c "CREATE DATABASE $APP_DB_NAME;"

# create a user
psql "dbname=$APP_DB_NAME host=postgis user=postgres password=$ROOT_PASSWD" \
     -c "CREATE USER $APP_DB_USER WITH ENCRYPTED PASSWORD '$APP_PASSWD';"
#ALTER ROLE $APP_DB_USER SET client_encoding TO 'utf8';
#ALTER ROLE $APP_DB_USER SET default_transaction_isolation TO 'read committed';
#ALTER ROLE $APP_DB_USER SET timezone TO 'UTC';"

# make our user owner of the database
psql "dbname=$APP_DB_NAME host=postgis user=postgres password=$ROOT_PASSWD" \
     -c "ALTER DATABASE $APP_DB_NAME OWNER TO $APP_DB_USER;"

# create a schema owned by our user
psql "dbname=$APP_DB_NAME host=postgis user=postgres password=$ROOT_PASSWD" \
     -c "CREATE SCHEMA IF NOT EXISTS $APP_DB_NAME AUTHORIZATION $APP_DB_USER;"

# create postgis extension in the new database
psql "dbname=$APP_DB_NAME host=postgis user=postgres password=$ROOT_PASSWD" \
     -c "CREATE EXTENSION IF NOT EXISTS postgis"

#psql "dbname=$APP_DB_NAME host=postgis user=postgres password=$ROOT_PASSWD" \
#     -c "GRANT ALL PRIVILEGES ON DATABASE $APP_DB_NAME TO $APP_DB_USER;"
#psql "dbname=$APP_DB_NAME host=postgis user=postgres password=$ROOT_PASSWD" \
#     -c "GRANT ALL ON ALL TABLES IN SCHEMA $APP_DB_USER to $APP_DB_USER;"
#psql "dbname=$APP_DB_NAME host=postgis user=postgres password=$ROOT_PASSWD" \
#     -c "GRANT ALL ON ALL SEQUENCES IN SCHEMA $APP_DB_USER to $APP_DB_USER;"
#psql "dbname=$APP_DB_NAME host=postgis user=postgres password=$ROOT_PASSWD" \
#     -c "GRANT ALL ON ALL FUNCTIONS IN SCHEMA $APP_DB_USER to $APP_DB_USER;"
