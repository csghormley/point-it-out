Script Call Chain Documentation
================================

This document maps the call chains between scripts in the project's ``scripts/`` directory and related root-level scripts.

Overview
--------

The project uses a hierarchical script structure for development, deployment, and maintenance tasks. Scripts are organized into logical workflows with clear dependencies.

Primary Entry Points
--------------------

1. ``scripts/bootstrap.sh`` - Initial Setup
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Purpose:** First-time environment setup for development

**Call Chain:**

.. code-block:: text

   scripts/bootstrap.sh
   └── (No script dependencies - installs system packages and creates venv)

**Actions:**

- Installs Python 3 and venv via apt-get
- Creates virtual environment in ``env/``
- Installs Python dependencies from ``requirements.txt``

**Usage:** Run once during initial project setup

----

2. ``scripts/migrate.sh`` - Database Migration Workflow
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Purpose:** Complete migration workflow including validation, building, and deployment

**Call Chain:**

.. code-block:: text

   scripts/migrate.sh
   ├── env/bin/activate (sources venv)
   ├── ./collector/manage.py check
   ├── ./collector/manage.py makemigrations
   ├── ./checkbuildrun.sh
   │   ├── ./scripts/build.sh
   │   │   ├── env/bin/activate (sources venv)
   │   │   ├── ./scripts/check.sh
   │   │   │   ├── env/bin/activate (sources venv)
   │   │   │   ├── ./collector/manage.py check
   │   │   │   ├── ./collector/manage.py validate_templates
   │   │   │   └── ruff check collector/
   │   │   ├── ./collector/manage.py collectstatic
   │   │   ├── ./scripts/version.sh
   │   │   │   └── git log (generates version.txt)
   │   │   ├── ./docker-stack/build-deps.sh
   │   │   │   └── docker build (img-django-deps)
   │   │   ├── ./docker-stack/build-django-env.sh
   │   │   │   └── docker build (img-django-env)
   │   │   ├── ./docker-stack/build-django.sh
   │   │   │   └── docker build (img-django-app)
   │   │   └── ./docker-stack/build-nginx.sh
   │   │       └── docker build (nginx)
   │   ├── systemctl restart docker.mapsurvey.service
   │   ├── ./scripts/backup-db.sh (optional, if 'backup' arg provided)
   │   │   ├── docker ps (find container)
   │   │   ├── docker exec (wait for database)
   │   │   ├── docker exec (run pg_dumpall)
   │   │   └── rsync (optional remote backup)
   │   ├── ./scripts/maintenance.sh
   │   │   └── docker system prune --force
   │   └── ./scripts/status.sh
   │       └── docker ps (status checks)
   └── docker compose exec django ./manage.py migrate

**Actions:**

1. Validates Django configuration
2. Creates migration files
3. Builds Docker images (via checkbuildrun.sh)
4. Restarts services
5. Applies migrations to running database

**Usage:** Run after making model changes

----

3. ``./checkbuildrun.sh`` - Build and Deploy
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Purpose:** Build Docker images and restart production services

**Call Chain:** See ``scripts/migrate.sh`` above for complete chain

**Actions:**

1. Builds all Docker images via ``./scripts/build.sh``
2. Restarts systemd service
3. Optionally runs database backup via ``./scripts/backup-db.sh`` (if ``backup`` argument provided)
4. Performs Docker cleanup via ``scripts/maintenance.sh``
5. Shows status via ``scripts/status.sh``

**Usage:**

.. code-block:: bash

   # Normal build and deploy
   ./checkbuildrun.sh

   # Build, deploy, and backup database
   ./checkbuildrun.sh backup

----

4. ``scripts/build.sh`` - Build Docker Images
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Purpose:** Validate code and build all Docker images

**Call Chain:** See ``scripts/migrate.sh`` above for complete chain

**Actions:**

1. Validates Django code via ``./scripts/check.sh``
2. Collects static files
3. Updates version.txt via ``./scripts/version.sh``
4. Builds Docker images in dependency order:

   - deps (Ubuntu + GDAL + Python venv)
   - env (Python libraries from requirements.txt)
   - django (Django application code)
   - nginx (Web server configuration)

**Usage:** Called by ``checkbuildrun.sh``, not typically run standalone

**Note:** All scripts must be run from the project root directory

----

5. ``scripts/check.sh`` - Code Validation
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Purpose:** Run all validation checks before building

**Call Chain:**

.. code-block:: text

   scripts/check.sh
   ├── env/bin/activate (sources venv)
   ├── ./collector/manage.py check
   ├── ./collector/manage.py validate_templates
   └── ruff check collector/

**Actions:**

1. Validates Django configuration
2. Validates Django templates
3. Runs Ruff linter for code quality

**Usage:** Called by ``scripts/build.sh``, or run standalone to validate before commits

----

6. ``scripts/backup-db.sh`` - Database Backup
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Purpose:** Backup PostgreSQL database with optional remote upload

**Call Chain:**

.. code-block:: text

   scripts/backup-db.sh <container> <database> [ssh-server] [ssh-port]
   ├── docker ps (find container)
   ├── docker exec (wait for database)
   ├── docker exec (run pg_dumpall)
   └── rsync (optional remote backup)

**Actions:**

1. Finds running PostgreSQL container
2. Waits for database to be ready
3. Creates compressed SQL dump via pg_dumpall
4. Saves to ``postgis_data/pgdata/``
5. Optionally uploads to remote server via rsync/SSH

**Usage:**

.. code-block:: bash

   ./scripts/backup-db.sh postgis17 mapbe [server.example.com] [22]

----

7. ``scripts/maintenance.sh`` - System Cleanup
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Purpose:** Clean up Docker system resources

**Call Chain:**

.. code-block:: text

   scripts/maintenance.sh
   └── docker system prune --force

**Actions:** Removes unused Docker containers, networks, images, and build cache

**Usage:** Called automatically by ``checkbuildrun.sh``, or run manually when disk space is low

----

8. ``scripts/status.sh`` - System Status Check
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Purpose:** Check Docker container status and disk usage

**Call Chain:**

.. code-block:: text

   scripts/status.sh
   ├── docker ps (check nginx)
   ├── docker ps (check postgis)
   ├── docker ps (check mapsurvey-app)
   └── df -h (disk usage)

**Actions:** Reports running container status and disk space

**Usage:** Run to verify system health after deployment

----

9. ``scripts/version.sh`` - Version File Generation
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Purpose:** Generate version.txt from git commit history

**Call Chain:**

.. code-block:: text

   scripts/version.sh
   └── git log (write to collector/pio/templates/pio/version.txt)

**Actions:** Creates version.txt with latest commit info for display in app

**Usage:** Called automatically by ``build.sh``

----

Script Location Mapping
------------------------

Root Directory Scripts
~~~~~~~~~~~~~~~~~~~~~~

- ``checkbuildrun.sh`` - Build and deploy workflow (top-level entry point)

Scripts Directory (``scripts/``)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

All scripts must be run from the project root directory. Each script validates it is being run from the correct location.

- ``bootstrap.sh`` - Initial setup
- ``migrate.sh`` - Migration workflow
- ``build.sh`` - Main build orchestrator
- ``check.sh`` - Validation checks
- ``backup-db.sh`` - Database backup
- ``maintenance.sh`` - Docker cleanup
- ``status.sh`` - Status checks
- ``version.sh`` - Version generation

Docker Stack Directory (``docker-stack/``)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

- ``build-deps.sh`` - Build base dependencies image
- ``build-django-env.sh`` - Build Python environment image
- ``build-django.sh`` - Build Django application image
- ``build-nginx.sh`` - Build nginx image

----

Common Workflows
----------------

Development Setup (First Time)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: bash

   ./scripts/bootstrap.sh

After Model Changes
~~~~~~~~~~~~~~~~~~~

.. code-block:: bash

   ./scripts/migrate.sh

After Code Changes
~~~~~~~~~~~~~~~~~~

.. code-block:: bash

   # Normal build and deploy
   ./checkbuildrun.sh

   # Build, deploy, and backup database
   ./checkbuildrun.sh backup

Before Committing
~~~~~~~~~~~~~~~~~

.. code-block:: bash

   ./scripts/check.sh

Database Backup
~~~~~~~~~~~~~~~

.. code-block:: bash

   ./scripts/backup-db.sh postgis17 mapbe

Check System Status
~~~~~~~~~~~~~~~~~~~

.. code-block:: bash

   ./scripts/status.sh

----

Dependency Graph
----------------

.. code-block:: text

   scripts/bootstrap.sh (standalone)

   scripts/migrate.sh
       └─→ checkbuildrun.sh
               ├─→ scripts/build.sh
               │       ├─→ scripts/check.sh
               │       ├─→ scripts/version.sh
               │       └─→ docker-stack/build-*.sh (4 scripts)
               ├─→ scripts/backup-db.sh (optional, if 'backup' arg)
               ├─→ scripts/maintenance.sh
               └─→ scripts/status.sh

   scripts/backup-db.sh (standalone or called by checkbuildrun.sh)

----

Notes
-----

1. **Script Organization**: All scripts are now located in the ``scripts/`` directory except for ``checkbuildrun.sh`` which remains at the project root as the primary entry point. All scripts must be run from the project root directory and include validation to ensure correct execution location.

2. **Virtual Environment**: Most scripts activate the Python virtual environment (``env/bin/activate``) before running Django commands.

3. **Error Handling**: Scripts use ``set -e`` or check return codes to abort on errors, preventing cascading failures.

4. **Docker Image Layering**: Images are built in dependency order:

   - ``deps`` → ``env`` → ``django`` (application stack)
   - ``nginx`` (standalone)

5. **Production vs Development**:

   - ``checkbuildrun.sh`` uses systemd for production deployment
   - Development can use ``docker compose up`` directly

6. **Validation First**: The build process validates code before building images to catch errors early and avoid wasting build time.

7. **Database Backups**: The ``checkbuildrun.sh`` script accepts an optional ``backup`` argument to trigger database backup after deployment. Backup parameters (container and database name) are configured at the top of the script.
