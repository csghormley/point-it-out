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

- Installs Python 3 and venv (if not present)
- Creates virtual environment in ``env/``
- Installs Python dependencies from ``requirements.txt``

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

**Note:** Equivalent to the legacy ``checkbuildrun.sh`` script

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

**Note:** Equivalent to the legacy ``scripts/migrate.sh`` script

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

The script uses these configuration values (set at the top of the script):

.. code-block:: bash

   DB_CONTAINER="postgis17"
   DB_NAME="mapbe"
   WORKDIR="$(cd "$(dirname "$0")" && pwd)"

Modify these if your database container name or database name differs.

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

Migration from Legacy Scripts
------------------------------

The ``mapcfg`` script consolidates functionality from multiple legacy scripts:

.. list-table::
   :header-rows: 1
   :widths: 30 30 40

   * - Legacy Script
     - mapcfg Command
     - Notes
   * - ``scripts/bootstrap.sh``
     - ``./mapcfg bootstrap``
     - Identical functionality
   * - ``checkbuildrun.sh``
     - ``./mapcfg run``
     - Same workflow, cleaner interface
   * - ``scripts/migrate.sh``
     - ``./mapcfg migrate``
     - Same workflow, cleaner interface
   * - ``scripts/build.sh``
     - ``./mapcfg build``
     - Called internally by ``run``
   * - ``scripts/check.sh``
     - ``./mapcfg check``
     - Called internally by ``build``
   * - ``scripts/backup-db.sh``
     - ``./mapcfg backup``
     - Simplified argument handling
   * - ``scripts/status.sh``
     - ``./mapcfg status``
     - Same functionality
   * - ``scripts/maintenance.sh``
     - ``./mapcfg maintenance``
     - Called internally by ``run``
   * - ``scripts/version.sh``
     - ``./mapcfg version``
     - Called internally by ``build``

**Legacy scripts remain available** and continue to work. The ``mapcfg`` script provides a unified interface but does not replace the underlying scripts.

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

- For script call chains and dependencies, see :doc:`../script-call-chain` (Markdown format in ``docs/``)
- For development workflow, see :doc:`development`
- For troubleshooting, see :doc:`troubleshooting`

See Also
--------

- :doc:`development` - Development workflow guide
- :doc:`quickstart` - Getting started guide
- :doc:`troubleshooting` - Common issues and solutions
