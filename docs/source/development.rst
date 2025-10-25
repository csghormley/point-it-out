Development Guide
=================

This guide covers the development workflow, architecture, and code organization. It assumes that the files are installed in the folder /opt/mapsurvey, but that is not a requirement.

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

Python Virtual Environment
^^^^^^^^^^^^^^^^^^^^^^^^^^

::

    python -m venv env
    source env/bin/activate  # or `. env/bin/activate`
    pip install -r requirements.txt

Git Hooks
^^^^^^^^^

The repository includes a pre-commit hook that runs ``./mapcfg check`` before allowing commits.

Install the hooks (one-time setup)::

    ./.githooks/install-hooks.sh

This creates symlinks from ``.git/hooks/`` to ``.githooks/`` so the versioned hooks are used automatically.

The pre-commit hook ensures:

- Django system checks pass
- Templates are valid
- Ruff linting passes
- Docker Compose configuration is valid

To bypass the hook temporarily (not recommended)::

    git commit --no-verify -m "message"

See ``.githooks/README.md`` for more information about managing git hooks.

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
- **Secrets directory**: ``docker-stack/secrets/`` (see `Environment Variables (via Docker Secrets)`_ for details)

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

The application uses `docker-environ <https://django-environ.readthedocs.io/>`_ with ``FileAwareEnv`` to automatically read `Docker secrets <https://docs.docker.com/compose/use-secrets/>`_ from files. Environment variables with a ``_FILE`` suffix (e.g., ``SECRET_KEY_FILE``) are automatically resolved by reading the file at the specified path.

Available secret files:

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

    ./mapcfg migrate

This script handles creating migrations, building the Docker image, and applying migrations to the database.

**Important:** Complete all pending Django model migrations BEFORE performing major PostgreSQL version upgrades. This ensures migration files are compatible with both database versions.

Database Backup
^^^^^^^^^^^^^^^

Create a full database backup::

    ./mapcfg backup

For remote backup with SSH::

    ./mapcfg backup <user@server.example.com> [22]

Manual backup using Docker (saves to host filesystem)::

    docker compose exec -i -u root postgis17 \
        runuser -u postgres pg_dumpall > /path/to/host/backup.sql

PostgreSQL Version Migration
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

When migrating between PostgreSQL major versions (e.g., PostgreSQL 16 to 17), follow this procedure carefully. Postgres will not run on a non-matching data directory, so an upgrade requires that any databases be backed up from the old server and restored onto the new server. The OLD database server must be running to back it up, and the NEW database server must be running to restore to it.

The following assumes that the new database container is called ``postgis17`` and its data folder is ``postgis_data/pgdata17``.

**Prerequisites**

- The application uses a PostGIS Docker image with a shared volume mounted at ``/var/lib/postgresql/data`` (in-container path)
- The host path is ``/opt/mapsurvey/postgis_data`` (or ``postgis_data/`` relative to project root)
- The new container requires an empty pgdata directory to initialize
- **Complete all Django model migrations** before starting a PostgreSQL upgrade

**Migration Steps**

1. **Complete Django migrations** (if any pending)::

    ./mapcfg migrate

   This ensures all schema changes are applied before the database upgrade.

2. **Create a full backup** of the CURRENT (old) database using ``pg_dumpall``.

   The old database must be running for this step::

    # Using mapcfg (saves to postgis_data/pgdata/ on host)
    ./mapcfg backup

   Or manually to a specific location on the host::

    docker compose exec -i -u root postgis16 \
        runuser -u postgres pg_dumpall > /opt/mapsurvey/postgis_data/db-backup-pg16.sql

   **Note:** The ``>`` redirection saves the file to the **host filesystem**, not inside the container.

3. **Extract the backup** if compressed (e.g., if using ``mapcfg backup`` which creates gzip files)::

    gunzip /opt/mapsurvey/postgis_data/pgdata/mapbe-backup-YYYY-MM-DD-HHMMSS.sql.gz

4. **Stop the stack** to prepare for the migration::

    cd docker-stack
    docker compose down --remove-orphans

5. **Update docker-compose.yml** to use the new PostGIS image version:

   .. code-block:: yaml

       postgis17:
         image: postgis/postgis:17-3.5
         environment:
           POSTGRES_PASSWORD_FILE: /run/secrets/root_db_password
           PGDATA: /var/lib/postgresql/data/pgdata17  # New data directory (in-container path)
         volumes:
           - /opt/mapsurvey/postgis_data:/var/lib/postgresql/data  # Host:container mount
         # ... rest of configuration

   **Path clarification:**

   - ``PGDATA: /var/lib/postgresql/data/pgdata17`` - in-container path where PostgreSQL stores its data
   - ``/opt/mapsurvey/postgis_data:/var/lib/postgresql/data`` - volume mount (host path : container path)
   - On the host, the new pgdata will be at ``/opt/mapsurvey/postgis_data/pgdata17/``

6. **Ensure the new pgdata directory does not exist** on the host, or is empty::

7. **Copy the backup file** to the shared volume root (``/opt/mapsurvey/postgis_data`` on the host) so it's accessible to the new container::

    cp /opt/mapsurvey/postgis_data/pgdata/mapbe-backup-YYYY-MM-DD-HHMMSS.sql \
       /opt/mapsurvey/postgis_data/db-dump.sql

8. **Copy configuration files** to the new pgdata directory location (if needed):

   From ``/opt/mapsurvey/postgis_data/pgdata/`` (old) to ``/opt/mapsurvey/postgis_data/pgdata17/`` (new):

   - ``postgresql.conf``
   - ``pg_hba.conf``
   - ``fullchain.pem`` (if using SSL)
   - ``privkey.pem`` (if using SSL)

   The new database will initialize with default configs if these aren't copied. You can copy them after initialization if preferred.

9. **Start the new database** to initialize the empty pgdata17 directory::

    cd docker-stack
    docker compose up -d postgis17

   Wait for initialization to complete (check logs)::

    docker compose logs -f postgis17

   Look for "database system is ready to accept connections"

10. **Restore the cluster** from the backup file.

    The backup file must be accessible inside the container. Since we copied it to ``/opt/mapsurvey/postgis_data/db-dump.sql`` on the host, and the volume is mounted at ``/var/lib/postgresql/data`` in the container, the file is at ``/var/lib/postgresql/data/db-dump.sql`` inside the container::

     docker compose exec -i -u root postgis17 \
         psql -U postgres -f /var/lib/postgresql/data/db-dump.sql

    **Path explanation:**

    - Host path: ``/opt/mapsurvey/postgis_data/db-dump.sql``
    - In-container path: ``/var/lib/postgresql/data/db-dump.sql``
    - These refer to the same file via the volume mount

11. **(Optional) Verify the migration** by backing up the new database and comparing::

     # Create new backup (host path)
     docker compose exec -i -u root postgis17 \
         runuser -u postgres pg_dumpall > /opt/mapsurvey/postgis_data/db-dump-pg17.sql

     # Compare (host paths)
     diff /opt/mapsurvey/postgis_data/db-dump.sql \
          /opt/mapsurvey/postgis_data/db-dump-pg17.sql

12. **Update dependencies** in django service to use the new database::

     # In docker-compose.yml, update django service
     depends_on:
       - postgis17  # Changed from postgis16

13. **Restart the full stack** to ensure all services connect properly::

     docker compose down
     docker compose up -d

14. **Verify Django connection** to the new database::

     docker compose exec django ./manage.py check
     docker compose exec django ./manage.py showmigrations

15. **Test systemd units** (if applicable) to ensure everything runs as expected in production::

     systemctl restart docker.mapsurvey.service
     systemctl status docker.mapsurvey.service

16. **Clean up old backup files** after confirming the migration was successful

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
