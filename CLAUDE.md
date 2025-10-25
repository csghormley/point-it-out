# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

**Full documentation is available in the `docs/` directory.**

To build documentation:

```bash
cd docs
uv venv && source .venv/bin/activate && uv pip install -r requirements.txt
make html
```

Quick reference for common tasks below.

## Development Commands

### Django Development
- **Development server**: `cd collector && python manage.py runserver`
- **Django shell**: `cd collector && python manage.py shell`
- **Create migrations**: `cd collector && python manage.py makemigrations`
- **Apply migrations**: `./scripts/migrate.sh` (preferred - handles build and deployment)
- **Collect static files**: `cd collector && python manage.py collectstatic`
- **Django checks**: `cd collector && python manage.py check`

### Docker Operations
- **Build and restart services**: `./checkbuildrun.sh`
- **Build Docker images**:
  - Django: `cd docker-stack && ./build-django.sh`
  - Nginx: `cd docker-stack && ./build-nginx.sh`
  - Dependencies: `cd docker-stack && ./build-deps.sh`
- **Manual Docker Compose**: `cd docker-stack && docker compose -f docker-compose.yml up`
- **Database backup**: `./scripts/backup-db.sh`

### Environment Setup
```bash
python -m venv env
source env/bin/activate  # or `. env/bin/activate`
pip install -r requirements.txt
```

### Git Hooks
The repository includes a pre-commit hook that runs `./mapcfg check` before allowing commits.

**Install hooks** (one-time setup):
```bash
./.githooks/install-hooks.sh
```

This ensures all code quality checks pass before committing. To bypass (not recommended):
```bash
git commit --no-verify -m "message"
```

## Architecture Overview

### Core Application Structure
This is a **Django-based spatial data entry application** with the following key components:

**Primary Django App**: `collector/pio/` (Point It Out)
- **Models**: MapConfig, FeatureLayer, MapLayer, SurveyPoint, VisitorBehavior
- **API**: Django REST Framework with GeoDjango for spatial data
- **Frontend**: OpenLayers-based interactive web maps

### Data Models Hierarchy
```
MapConfig (map configurations)
├── MapLayer (through table with z-order)
│   └── FeatureLayer (GeoJSON feature collections)
└── SurveyPoint (user-submitted points with geolocation)
```

### Key Technologies
- **Backend**: Django 5.2.7, GeoDjango, PostgreSQL 17/PostGIS 3.5
- **Frontend**: OpenLayers, jQuery, Bootstrap
- **Authentication**: django-allauth with MFA support
- **API**: Django REST Framework with GIS extensions
- **Security**: Content Security Policy (CSP), GDAL/GEOS for spatial operations

### Deployment Architecture
- **Containerized**: Docker Compose stack with separate containers for:
  - Django app (gunicorn)
  - PostgreSQL 17/PostGIS 3.5 database (default service: `postgis17`)
  - Nginx reverse proxy
- **Production**: Systemd services for container management
- **Secrets**: Docker secrets for sensitive configuration
- **Note**: Legacy `postgis16` service (PostgreSQL 16/PostGIS 3.4) available via profile

## Key Configuration Files

### mapcfg Configuration
- **Configuration file**: `.mapcfgrc` (git-ignored)
  - Database container name and database name
  - Backup settings (SSH server, port, key path, backup directory)
  - Systemd service name
  - All settings can be overridden by environment variables

### Django Settings
- **Main settings**: `collector/collector/settings.py`
- **Local settings**: `collector/collector/localsettings.py` (git-ignored)
- **Dependencies**: `requirements.txt`

### Docker Configuration
- **Compose file**: `docker-stack/docker-compose.yml`
- **Secrets directory**: `docker-stack/secrets/`

### Map Configuration
- **Default map configs**: Fixtures in `collector/pio/fixtures/mapconfig.json`
- **Static assets**: `collector/pio/static/pio/`
- **Templates**: `collector/pio/templates/pio/`
- **Configuration guide**: See `HOWTO.md` for detailed map configuration instructions

## Development Workflow

### Making Model Changes
1. Modify models in `collector/pio/models.py`
2. Run `./scripts/migrate.sh` (handles makemigrations, build, deploy, and migrate)
3. Alternatively, manual process:
   - `cd collector && python manage.py makemigrations`
   - `./checkbuildrun.sh` (rebuild and restart services)
   - `docker compose -f docker-stack/docker-compose.yml exec django ./manage.py migrate`

### Frontend Development
- **Main map JavaScript**: `collector/pio/static/pio/js/map.js`
  - Automatic CRS detection via `extractCrsFromGeoJSON()` method
  - Supports legacy GeoJSON CRS property and URN formats
  - Label rendering via `getFeatureLabel()` with format string support
- **CSS**: `collector/pio/static/pio/css/map.css`
- **Static files collection**: Run `python manage.py collectstatic` after changes

### Map Configuration
- Map configurations are managed through Django admin or fixtures
- Default configuration function: `maplayer_default()` in `collector/pio/models.py`
- Configuration stored as JSON in MapLayer.config field
- See `HOWTO.md` for complete configuration reference and styling options

### API Endpoints
- **Survey Points**: `/api/surveypoints/` (filtered by responseid/projectid)
- **Map Configurations**: `/api/mapconfigs/`
- **Feature Layers**: `/api/featurelayers/`
- **Map Layers**: `/api/map-layers/` (returns layers with GeoJSON and styling, filtered by mapconfig)

## Security Considerations

### Authentication & Authorization
- Uses django-allauth with MFA (TOTP, WebAuthn, recovery codes)
- Custom permission classes for API access
- Session-based authentication for web interface

### Content Security Policy
- Strict CSP implemented for XSS protection
- Configured for map tile sources and CDN resources
- Allows inline styles/scripts where necessary for mapping libraries

### Database Security
- PostGIS database with separate user accounts
- Password management via Docker secrets
- IP-based access restrictions configured

## Environment Variables (via Docker Secrets)
- `SECRET_KEY_FILE`: Django secret key
- `APP_DB_PASSWORD_FILE`: Application database password
- `ROOT_DB_PASSWORD_FILE`: Database admin password  
- `EMAIL_HOST_PASSWORD_FILE`: SMTP password (optional)

## Common Development Tasks

### Database Management
- **Reset database**: Stop services, remove pgdata volume, restart
- **View logs**: `docker compose logs django` or `docker compose logs postgis17`
- **Database shell**: `docker compose exec postgis17 psql -U postgres mapbe`

### Debugging
- **Django debug**: Enable in `localsettings.py`, uncomment debug_toolbar in settings
- **API testing**: Use Django REST Framework browseable API at `/api/`
- **Map debugging**: Set `verbose: true` in MapConfig.config JSON field

## Integration Notes

### External Integration
- Designed for embedding in survey platforms (e.g., Qualtrics)
- Accepts URL parameters: `id` (responseid), `proj_id` (projectid)
- GeoIP integration for visitor geolocation
- Content Security Policy configured for iframe embedding

### Map Configuration System
The application uses a three-tier configuration model:

- **MapConfig**: Defines map extent, zoom levels, projection, and behavior
- **FeatureLayer**: Contains GeoJSON data (reusable across maps)
- **MapLayer**: Links FeatureLayers to MapConfigs with styling and z-order

Key capabilities include automatic CRS detection, configurable label formatting with placeholders, comprehensive layer styling, and z-order control for layer stacking.

**For configuration instructions**, see `HOWTO.md`.