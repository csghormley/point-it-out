# MapSurvey - Spatial Data Entry Application

The MapSurvey application is a Django-based spatial data entry platform for collecting and visualizing geographic point data through interactive maps. It runs as a containerized service stack using Docker Compose.

## Documentation

**Full documentation is available in `docs/`** - build with:

```bash
cd docs
uv venv && source .venv/bin/activate && uv pip install -r requirements.txt
make html
```

Documentation includes:
- **Quickstart Guide** - Initial setup and deployment
- **Configuration Guide** - Map configuration, styling, and layer management
- **Development Guide** - Model changes, testing, and debugging
- **mapcfg Reference** - Unified management script for all operations
- **API Reference** - REST API endpoints and integration
- **Troubleshooting** - Common issues and solutions

## Quick Start

For day-to-day operations, use the unified `mapcfg` script:

```bash
# First-time setup
cp .mapcfgrc.example .mapcfgrc
./mapcfg bootstrap

# Build and deploy
./mapcfg run

# After model changes
./mapcfg migrate

# Get help
./mapcfg help
```

See **CLAUDE.md** for development workflow and **HOWTO.md** for map configuration instructions.

## Overview

MapSurvey is designed for embedding in survey platforms (e.g., Qualtrics) but can also run standalone. It should be deployed behind a reverse proxy (nginx) and is not intended to face the internet directly.

**Prerequisites:** Docker, Linux server administration, Django, Python, and PostgreSQL knowledge will be helpful.

## Architecture

The application consists of:

- **Docker Compose Stack**
  - **Nginx** - Application proxy and static file server
  - **Django Application** (collector/pio/) - GeoDjango with PostGIS backend
  - **PostgreSQL 17/PostGIS 3.5** - Spatial database
- **Nginx** - Reverse proxy for Docker stack

### Project Structure

* `collector/` - Django project directory
* `docker-stack/` - Docker Compose configuration and build scripts
* `docs/` - Sphinx documentation
* `nginx/` - Nginx configuration examples
* `postgis_data/pgdata/` - PostgreSQL data directory
* `etc/` - Example system configuration files
* `mapcfg` - Unified management script
* `.mapcfgrc.example` - Configuration template

---

**For detailed setup instructions, see the full documentation in `docs/`**

The sections below contain legacy setup notes that may be useful for reference.

## Additional Setup Notes

Clone the project into a folder, such as /opt/mapsurvey. Make that
folder the working directory.

Most operations can be performed with the map configuration script,
`mapcfg`, located in the project root directory. For example, to
build the Docker images,

`./mapcfg build`

Provided docker is installed, this will perform syntax checks, download the base docker images, and
install the required software.

If setting up a webserver facing the internet, the following practices
are strongly recommended but out of the scope of this document.

 * install a firewall and secure the Docker installation against outside access (e.g., ufw-docker)
 * install Nginx with config files in ./nginx as an example
 * set up encryption certificates (LetsEncrypt makes it easy)
 * make sure unattended updates are enabled
 * install a systemd service to manage the Mapsurvey processes
   see: ./systemd/docker.mapsurvey.service
   edit the UID and GID values in the systemd to a normal user.

Before running the service for the first time, initialize the secrets files in ./docker-stack/secrets. These contain
 * the encryption key for Django - can be generated with
   ./collector/manage.py generate_secret_key
 * email password (if setting up email notifications for things like new user accounts)
 * root database password for postgres (for the db server itself)
 * app database password (for django)

The first time the docker stack runs, Django will have to set up
its database tables. There are lots of ways for this to fail. Key
things that need to happen:

 * Django connects to the (hopefully running) postgres instance and
   initializes the tables
 * Django creates a superuser account
 * Collect static files (./manage.py collectstatic)

Manually running the docker stack:

cd docker-stack && docker compose -f docker-compose.yml up

## Potential problems

Database bootstrapping
Django dependency issues
 * libgdal on the Docker container has to match the Python gdal library version in pyproject.toml

## Resources

Look at the aliases in ./docker-stack/alias - lots of shortcuts here that will help build situational awareness of the stack. 
Stackoverflow usually has the answer
See Docker.com for docker-compose.yml file directives and options.
Djangoproject.com

Set up the environment:

    % ./mapcfg bootstrap

Run the test server:

% cd collector; python manage.py runserver

Additional libraries for a new environment:

libgdal-dev
libnginx-mod-stream

## Making changes

### Model migrations

If making changes to the database models in pio/models.py, this is
the process for making those changes effective in the database. The
following assumes the aliases in docker-stack/alias are loaded
and that the systemd service is installed.

1. Rebuild the docker images and restart the service (as root).
   This makes the change available within the running container.

   % ./mapcfg run

2. Open a shell to the Django container, with
   % docker_shell django

3. Build migrations, with
   % ./manage.py makemigrations

4. Apply migrations, with
   % ./manage.py migrate
