mapcfg - Unified Management Script
===================================

The ``mapcfg`` script is a unified command-line tool that consolidates all development, build, and deployment operations for the MapSurvey application. It provides a simplified, verb-based interface for common tasks.

Overview
--------

Located at the project root (``./mapcfg``), this script serves as a single entry point for all major operations, replacing the need to remember multiple script locations and call chains.

**Key Features:**

- Unified interface for all development tasks
- Color-coded output for easy reading
- Error handling with clear messages
- Automatic virtual environment activation
- Built-in help and documentation

Commands
--------

bootstrap
~~~~~~~~~

**Purpose:** Initial environment setup

**Usage:**

.. code-block:: bash

   ./mapcfg bootstrap

**Actions:**

- Installs Python 3 and uv (if not present)
- Creates virtual environment in ``.venv/``
- Installs Python dependencies via ``uv sync`` from ``pyproject.toml``

**When to use:** Run once during initial project setup

check
~~~~~

**Purpose:** Run validation checks

**Usage:**

.. code-block:: bash

   ./mapcfg check

**Actions:**

- Django configuration check (``manage.py check``)
- Template validation (``manage.py validate_templates``)
- Ruff linting (``ruff check collector/``)

**When to use:** Before committing code or as part of CI/CD pipeline

build
~~~~~

**Purpose:** Build Docker images

**Usage:**

.. code-block:: bash

   ./mapcfg build

**Actions:**

1. Runs validation checks (``check`` command)
2. Collects static files
3. Updates ``version.txt`` from git log
4. Builds Docker images in order:

   - ``build-deps.sh`` (base dependencies)
   - ``build-django-env.sh`` (Python environment)
   - ``build-django.sh`` (Django application)
   - ``build-nginx.sh`` (web server)

**When to use:** After code changes, before deployment

run
~~~

**Purpose:** Build and deploy application

**Usage:**

.. code-block:: bash

   # Normal build and deploy
   ./mapcfg run

   # Build, deploy, and backup database
   ./mapcfg run backup

**Actions:**

1. Builds Docker images (via ``build`` command)
2. Restarts systemd service (``docker.mapsurvey.service``)
3. Optionally backs up database (if ``backup`` argument provided)
4. Runs Docker maintenance cleanup
5. Shows system status

**When to use:** After code changes requiring deployment


migrate
~~~~~~~

**Purpose:** Complete migration workflow

**Usage:**

.. code-block:: bash

   ./mapcfg migrate

**Actions:**

1. Validates Django configuration
2. Creates migration files (``makemigrations``)
3. Builds and deploys application (via ``run`` command)
4. Applies migrations to database

**When to use:** After making model changes

backup
~~~~~~

**Purpose:** Backup database

**Usage:**

.. code-block:: bash

   # Local backup only
   ./mapcfg backup

   # Backup and upload to remote server
   ./mapcfg backup server.example.com 22

**Arguments:**

- ``server`` (optional): Remote server hostname or IP
- ``port`` (optional): SSH port (default: 22)

**Actions:**

- Creates compressed PostgreSQL dump via ``pg_dumpall``
- Saves to ``postgis_data/pgdata/``
- Optionally uploads to remote server via rsync/SSH

**When to use:** Before major changes, as part of deployment, or on schedule

status
~~~~~~

**Purpose:** Check system status

**Usage:**

.. code-block:: bash

   ./mapcfg status

**Actions:**

- Checks Docker container status (nginx, postgis, django)
- Reports running container count
- Shows disk usage

**When to use:** After deployment, troubleshooting

maintenance
~~~~~~~~~~~

**Purpose:** Clean up Docker resources

**Usage:**

.. code-block:: bash

   ./mapcfg maintenance

**Actions:**

- Runs ``docker system prune --force``
- Removes unused containers, networks, images, and build cache

**When to use:** When disk space is low, as part of deployment cleanup

version
~~~~~~~

**Purpose:** Update version.txt from git

**Usage:**

.. code-block:: bash

   ./mapcfg version

**Actions:**

- Generates ``collector/pio/templates/pio/version.txt`` from git log
- Includes commit hash, date, message, and author

**When to use:** Automatically called by ``build`` command

help
~~~~

**Purpose:** Show usage information

**Usage:**

.. code-block:: bash

   ./mapcfg help
   ./mapcfg --help
   ./mapcfg -h

**Actions:** Displays command reference and examples

Configuration
-------------

The ``mapcfg`` script uses a configuration file located at the project root: ``.mapcfgrc``

Configuration File (.mapcfgrc)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The ``.mapcfgrc`` file is required and must be created before running ``mapcfg``. Copy from the example template and customize for your environment:

.. code-block:: bash

   cp .mapcfgrc.example .mapcfgrc

**Available Settings:**

.. code-block:: bash

   # Database configuration
   DB_CONTAINER="postgis"                # PostgreSQL container name
   DB_NAME="mapbe"                       # Database name

   # Backup configuration
   SSH_SERVER=""                         # Remote backup server (user@hostname format, e.g., backups@server.com)
   SSH_PORT="22"                         # SSH port for remote backups
   SSH_KEY_PATH="~/.ssh/id_rsa_backup"  # SSH private key path
   BACKUP_DIR="postgis_data/pgdata"      # Local backup directory

   # Systemd service name
   SYSTEMD_SERVICE="docker.mapsurvey.service"

``.mapcfgrc`` is git-ignored by default. A template is provided in ``.mapcfgrc.example``. Environment variables override ``.mapcfgrc`` settings.

Common Workflows
----------------

First-Time Setup
~~~~~~~~~~~~~~~~

.. code-block:: bash

   ./mapcfg bootstrap

After Model Changes
~~~~~~~~~~~~~~~~~~~

.. code-block:: bash

   ./mapcfg migrate

After Code Changes
~~~~~~~~~~~~~~~~~~

.. code-block:: bash

   # Build and deploy
   ./mapcfg run

   # Build, deploy, and backup
   ./mapcfg run backup

Before Committing
~~~~~~~~~~~~~~~~~

.. code-block:: bash

   ./mapcfg check

Regular Database Backup
~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: bash

   # Local backup
   ./mapcfg backup

   # Remote backup
   ./mapcfg backup backup-server.example.com 22

Check System Health
~~~~~~~~~~~~~~~~~~~

.. code-block:: bash

   ./mapcfg status


Error Handling
--------------

The script uses strict error handling:

- ``set -euo pipefail`` ensures errors halt execution
- Color-coded messages (red for errors, green for success, yellow for info)
- Clear error messages with suggested solutions
- Automatic virtual environment validation

Troubleshooting
---------------

Virtual Environment Not Found
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Error:** ``Virtual environment not found. Run './mapcfg bootstrap' first.``

**Solution:**

.. code-block:: bash

   ./mapcfg bootstrap

Unknown Command
~~~~~~~~~~~~~~~

**Error:** ``Unknown command: <command>``

**Solution:**

.. code-block:: bash

   ./mapcfg help

Must Run from Project Root
~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Error:** ``This script must be run from the project root directory``

**Solution:** Change to the project root directory where ``mapcfg`` is located

Related Documentation
---------------------

- For development workflow, see :doc:`development`
- For troubleshooting, see :doc:`troubleshooting`

See Also
--------

- :doc:`development` - Development workflow guide
- :doc:`quickstart` - Getting started guide
- :doc:`troubleshooting` - Common issues and solutions
