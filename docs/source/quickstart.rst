Quick Start
===========

This guide will help you get started with MapSurvey quickly.

Prerequisites
-------------

- Python 3.10+
- PostgreSQL with PostGIS extension
- Docker and Docker Compose (for deployment)

Basic Setup
-----------

1. **Clone the repository**::

    git clone <repository-url>
    cd mapsurvey

2. **Set up Python environment**::

    python -m venv env
    source env/bin/activate  # or `. env/bin/activate`
    pip install -r requirements.txt

3. **Configure database**

   Create a PostgreSQL database with PostGIS extension enabled.

4. **Run migrations**::

    cd collector
    python manage.py migrate

5. **Create superuser**::

    python manage.py createsuperuser

6. **Start development server**::

    python manage.py runserver

7. **Access the application**

   - Application: http://localhost:8000
   - Admin interface: http://localhost:8000/admin

Docker Deployment
-----------------

For production deployment using Docker::

    ./build-docker.sh
    cd docker-stack
    docker compose -f docker-compose.yml up -d

Building Documentation
----------------------

To build this documentation locally::

    cd docs

    # Using uv (recommended)
    uv venv
    source .venv/bin/activate
    uv pip install -r requirements.txt
    make html

    # Or using pip
    python -m venv .venv
    source .venv/bin/activate
    pip install -r requirements.txt
    make html

Open ``build/html/index.html`` in your browser.

Next Steps
----------

- See :doc:`configuration` to set up your first map
- See :doc:`development` for development workflow
- See :doc:`api` for API documentation
