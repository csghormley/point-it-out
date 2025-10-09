Development Guide
=================

This guide covers the development workflow, architecture, and code organization.

Development Commands
--------------------

Django Development
~~~~~~~~~~~~~~~~~~

- **Development server**::

    cd collector && python manage.py runserver

- **Django shell**::

    cd collector && python manage.py shell

- **Create migrations**::

    cd collector && python manage.py makemigrations

- **Apply migrations**::

    ./scripts/migrate.sh

  (preferred - handles build and deployment)

- **Collect static files**::

    cd collector && python manage.py collectstatic

- **Django checks**::

    cd collector && python manage.py check

Docker Operations
~~~~~~~~~~~~~~~~~

- **Build and restart services**::

    ./checkbuildrun.sh

- **Build, restart services, and backup database**::

    ./checkbuildrun.sh backup

- **Manual Docker Compose**::

    cd docker-stack && docker compose -f docker-compose.yml up

- **Database backup**::

    ./scripts/backup-db.sh postgis17 mapbe

  Optional remote backup with SSH::

    ./scripts/backup-db.sh postgis17 mapbe server.example.com 22

Environment Setup
~~~~~~~~~~~~~~~~~

::

    python -m venv env
    source env/bin/activate  # or `. env/bin/activate`
    pip install -r requirements.txt

Architecture Overview
---------------------

Core Application Structure
~~~~~~~~~~~~~~~~~~~~~~~~~~

This is a **Django-based web mapping application** with the following key components:

**Primary Django App**: ``collector/pio/`` (Point It Out)

- **Models**: MapConfig, FeatureLayer, MapLayer, SurveyPoint, VisitorBehavior
- **API**: Django REST Framework with GeoDjango for spatial data
- **Frontend**: OpenLayers-based interactive web maps

Data Models Hierarchy
~~~~~~~~~~~~~~~~~~~~~

::

    MapConfig (map configurations)
    ├── MapLayer (through table with z-order)
    │   └── FeatureLayer (GeoJSON feature collections)
    └── SurveyPoint (user-submitted points with geolocation)

Key Technologies
~~~~~~~~~~~~~~~~

- **Backend**: Django 5.2.5, GeoDjango, PostgreSQL/PostGIS
- **Frontend**: OpenLayers, jQuery, Bootstrap
- **Authentication**: django-allauth with MFA support
- **API**: Django REST Framework with GIS extensions
- **Security**: Content Security Policy (CSP), GDAL/GEOS for spatial operations

Deployment Architecture
~~~~~~~~~~~~~~~~~~~~~~~

- **Containerized**: Docker Compose stack with separate containers for:

  - Django app (gunicorn)
  - PostgreSQL/PostGIS database
  - Nginx reverse proxy

- **Production**: Systemd services for container management
- **Secrets**: Docker secrets for sensitive configuration

Key Configuration Files
-----------------------

Django Settings
~~~~~~~~~~~~~~~

- **Main settings**: ``collector/collector/settings.py``
- **Local settings**: ``collector/collector/localsettings.py`` (git-ignored)
- **Dependencies**: ``requirements.txt``

Docker Configuration
~~~~~~~~~~~~~~~~~~~~

- **Compose file**: ``docker-stack/docker-compose.yml``
- **Secrets directory**: ``docker-stack/secrets/``

Map Configuration
~~~~~~~~~~~~~~~~~

- **Default map configs**: Fixtures in ``collector/pio/fixtures/mapconfig.json``
- **Static assets**: ``collector/pio/static/pio/``
- **Templates**: ``collector/pio/templates/pio/``
- **Configuration guide**: See :doc:`configuration` for detailed map configuration instructions

Development Workflow
--------------------

Making Model Changes
~~~~~~~~~~~~~~~~~~~~

1. Modify models in ``collector/pio/models.py``
2. Run ``./scripts/migrate.sh`` (handles makemigrations, build, deploy, and migrate)
3. Alternatively, manual process:

   - ``cd collector && python manage.py makemigrations``
   - ``./checkbuildrun.sh`` (rebuild and restart services)
   - ``docker compose -f docker-stack/docker-compose.yml exec django ./manage.py migrate``

Frontend Development
~~~~~~~~~~~~~~~~~~~~

- **Main map JavaScript**: ``collector/pio/static/pio/js/map.js``

  - Automatic CRS detection via ``extractCrsFromGeoJSON()`` method
  - Supports legacy GeoJSON CRS property and URN formats
  - Label rendering via ``getFeatureLabel()`` with format string support

- **CSS**: ``collector/pio/static/pio/css/map.css``
- **Static files collection**: Run ``python manage.py collectstatic`` after changes

Map Configuration
~~~~~~~~~~~~~~~~~

- Map configurations are managed through Django admin or fixtures
- Default configuration function: ``maplayer_default()`` in ``collector/pio/models.py``
- Configuration stored as JSON in MapLayer.config field
- See :doc:`configuration` for complete configuration reference and styling options

API Endpoints
~~~~~~~~~~~~~

- **Survey Points**: ``/api/surveypoints/`` (filtered by responseid/projectid)
- **Map Configurations**: ``/api/mapconfigs/``
- **Feature Layers**: ``/api/featurelayers/``
- **Map Layers**: ``/api/map-layers/`` (returns layers with GeoJSON and styling, filtered by mapconfig)

Security Considerations
-----------------------

Authentication & Authorization
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

- Uses django-allauth with MFA (TOTP, WebAuthn, recovery codes)
- Custom permission classes for API access
- Session-based authentication for web interface

Content Security Policy
~~~~~~~~~~~~~~~~~~~~~~~

- Strict CSP implemented for XSS protection
- Configured for map tile sources and CDN resources
- Allows inline styles/scripts where necessary for mapping libraries

Database Security
~~~~~~~~~~~~~~~~~

- PostGIS database with separate user accounts
- Password management via Docker secrets
- IP-based access restrictions configured

Environment Variables (via Docker Secrets)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

- ``SECRET_KEY_FILE``: Django secret key
- ``APP_DB_PASSWORD_FILE``: Application database password
- ``ROOT_DB_PASSWORD_FILE``: Database admin password
- ``EMAIL_HOST_PASSWORD_FILE``: SMTP password (optional)

Common Development Tasks
------------------------

Database Management
~~~~~~~~~~~~~~~~~~~

Django Model Migrations
^^^^^^^^^^^^^^^^^^^^^^^

For ordinary Django model migrations in this environment:

1. Make model changes in ``collector/pio/models.py``
2. Run the migration script::

    ./scripts/migrate.sh

This script handles creating migrations, building the Docker image, and applying migrations to the database.

Database Backup
^^^^^^^^^^^^^^^

Create a full database backup::

    ./scripts/backup-db.sh postgis17 mapbe

For remote backup with SSH::

    ./scripts/backup-db.sh postgis17 mapbe server.example.com 22

Manual backup using Docker::

    docker compose exec -i -u root postgis17 \
        runuser -u postgres pg_dumpall > /path/to/backup.sql

PostgreSQL Version Migration
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

When migrating between PostgreSQL major versions (e.g., PostgreSQL 16 to 17), follow this procedure:

**Prerequisites**

The application uses a PostGIS Docker image with a shared volume for the ``pgdata`` directory. The new container requires an empty ``pgdata`` directory to start up.

**Migration Steps**

1. **Create a full backup** using ``pg_dumpall``::

    ./scripts/backup-db.sh postgis17 mapbe

   Or manually::

    docker compose exec -i -u root <old-service-name> \
        runuser -u postgres pg_dumpall > /var/lib/postgresql/data/db-dump.sql

2. **Extract the backup** to the root of the shared volume if compressed

3. **Update docker-compose.yml** to use the new PostGIS image version:

   .. code-block:: yaml

       postgis17:
         image: postgis/postgis:17-3.5  # Updated from 16-3.4
         environment:
           POSTGRES_PASSWORD_FILE: /run/secrets/root_db_password
           PGDATA: /var/lib/postgresql/data/pgdata17  # New data directory
         # ... rest of configuration

4. **Stop the stack**::

    docker compose down --remove-orphans

5. **Restore configuration files** to the new pgdata directory:

   - ``postgresql.conf``
   - ``pg_hba.conf``
   - ``fullchain.pem``
   - ``privkey.pem``

6. **Start the stack** with the new configuration::

    cd docker-stack
    docker compose -f docker-compose.yml up

7. **Restore the cluster**::

    docker compose exec -i -u root postgis17 \
        psql -U postgres -f /var/lib/postgresql/data/db-dump.sql

8. **(Optional) Verify the migration** by backing up the new database and comparing::

    docker compose exec -i -u root postgis17 \
        runuser -u postgres pg_dumpall > /var/lib/postgresql/data/db-dump-new.sql

    diff /var/lib/postgresql/data/db-dump.sql \
         /var/lib/postgresql/data/db-dump-new.sql

9. **Test systemd units** to ensure everything runs as expected in production

.. note::
   For detailed reference on PostgreSQL upgrades in Docker Compose, see:
   https://hahouari.medium.com/upgrade-from-postgresql-16-x-to-17-0-in-docker-compose-00d7417fd555

Common Database Tasks
^^^^^^^^^^^^^^^^^^^^^

- **Reset database**: Stop services, remove pgdata volume, restart
- **View logs**: ``docker compose logs django`` or ``docker compose logs postgis17``
- **Database shell**: ``docker compose exec postgis17 psql -U postgres mapbe``

Debugging
~~~~~~~~~

- **Django debug**: Enable in ``localsettings.py``, uncomment debug_toolbar in settings
- **API testing**: Use Django REST Framework browseable API at ``/api/``
- **Map debugging**: Set ``verbose: true`` in MapConfig.config JSON field

Integration Notes
-----------------

External Integration
~~~~~~~~~~~~~~~~~~~~

- Designed for embedding in survey platforms (e.g., Qualtrics)
- Accepts URL parameters: ``id`` (responseid), ``proj_id`` (projectid)
- GeoIP integration for visitor geolocation
- Content Security Policy configured for iframe embedding

Map Configuration System
~~~~~~~~~~~~~~~~~~~~~~~~

The application uses a three-tier configuration model:

- **MapConfig**: Defines map extent, zoom levels, projection, and behavior
- **FeatureLayer**: Contains GeoJSON data (reusable across maps)
- **MapLayer**: Links FeatureLayers to MapConfigs with styling and z-order

Key capabilities include automatic CRS detection, configurable label formatting with placeholders, comprehensive layer styling, and z-order control for layer stacking.

**For configuration instructions**, see :doc:`configuration`.
