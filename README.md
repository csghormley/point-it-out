# GETTING STARTED

The Mapsurvey application is a set of services running in Docker
(under docker-compose) that together present a web map interface, and
a means of monitoring/managing the collected data. It can be used as a
web mapping/data collection demo, but it is primarily intended to be embedded in
another website such as Qualtrics.

This application is not designed to stand on its own facing the
internet, either. It should normally be set up behind a web proxy
such as nginx.

It will be much easier if you have a little background in Docker,
Linux server administration, Django, Python, and Postgres. All the
information you will need is available on the internet, but it will
take extra time to resolve problems that come up without previous
experience.

## Orientation

* `collector` is the Django project directory
* `docker-stack` contains files to manage the docker-compose configuration
* `nginx` contains files most likely to be found in /etc/nginx in production
* `postgis_data/pgdata` is the folder where the postgres container's data folder will be located by default
* `scripts` contains some useful scripts
* `systemd` contains some unit configuration files

## Setting Up

Clone the project into a folder. Here I have been using
/opt/mapsurvey. Make that folder your working directory.

Run the build-docker.sh script.

`./scripts/build-docker.sh`

Provided docker is installed, this will download the docker images and
install the required software.

If setting up a webserver facing the internet, do the following -
these are strongly recommended but out of the scope of this document.

 * install a firewall and secure your Docker installation against outside access (e.g., ufw-docker)
 * install Nginx with config files in ./nginx as an example (your configuration probably will be different!)
 * set up LetsEncrypt to automate security certificate installation
 * make sure unattended updates are enabled
 * install a systemd service to manage the Mapsurvey processes
   see: ./systemd/docker.mapsurvey.service
   edit the UID and GID values in the systemd to a normal user.

Before running the service for the first time, initialize the secrets files in ./docker-stack/secrets. These contain
 * the encryption key for Django - can be generated with
   ./collector/manage.py generate_secret_key
 * email password (if you are setting up email notifications for things like new user accounts)
 * root database password you're using for postgres (for the db server itself)
 * app database password (for django)

The first time you run the docker stack, Django will have to set up
its database tables. There are lots of ways for this to fail. Key
things that need to happen - i.e. things I should probably script/test
a few dozen times before first release:

 * Django connects to the (hopefully running) postgres instance and
   initializes the tables
 * Django creates a superuser account
 * Collect static files (./manage.py collectstatic)

Manually running the docker stack:

cd docker-stack && docker compose -f docker-compose.yml up

## Potential problems

Database bootstrapping
Django dependency issues
 * libgdal on the Docker container has to match the Python gdal library called out in requirements.txt

## Resources

Look at the aliases in ./docker-stack/alias - lots of shortcuts here that will help you build situational awareness.
Stackoverflow usually has the answer
Docker.com has pretty good documentation on the docker-compose.yml file directives and options.
Djangoproject.com


Baby steps: You're going to need a running postgres to do much with
Django. Fortunately that container runs a recent stock version of the
database server so this is a low barrier to entry.

Activate the venv:

    % source mapbe/bin/activate

Install the requirements in the venv:

    % pip install -r requirements.txt

Run the test server:

% cd collector; python manage.py runserver

Additional libraries for a new environment:

libgdal-dev

== Building a docker image ==

From the project root directory, run the following:

     % docker build . -f docker-django/Dockerfile -t \
         csghor/mapsurvey-app:<version-number>

This pulls in the official OSGeo gdal Docker image, installs
dependencies for Django, and copies the current project. The result is
a docker image ready to run the project.

## Making changes

### Model migrations

If you make changes to the database models in pio/models.py, this is
the process for making those changes effective in the database. The
following assumes you have the aliases in docker-stack/alias loaded
and that the systemd service is installed.

1. Rebuild the docker images and restart the service (as root).
   This makes the change available within the running container.

   % ./build_docker.sh && systemctl restart docker.mapsurvey.service

2. Open a shell to the Django container, with
   % docker_shell django

3. Build migrations, with
   % ./manage.py makemigrations

4. Apply migrations, with
   % ./manage.py migrate
