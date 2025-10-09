# Map Configuration HOWTO

**Complete documentation has been moved to the `docs/` directory.**

To view the full documentation:

**Using uv (recommended):**

```bash
cd docs
uv venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
uv pip install -r requirements.txt
make html
```

**Using pip:**

```bash
cd docs
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -r requirements.txt
make html
```

Then open `docs/build/html/index.html` in your browser.

## Quick Links

- **Quick Start**: See `docs/source/quickstart.rst`
- **Map Configuration**: See `docs/source/configuration.rst`
- **Development Guide**: See `docs/source/development.rst`
- **API Reference**: See `docs/source/api.rst`
- **Troubleshooting**: See `docs/source/troubleshooting.rst`

## Overview

The map system uses three components:

- **FeatureLayer**: GeoJSON data (points, lines, polygons) - reusable across maps
- **MapConfig**: Map settings (extent, zoom levels, projection, behavior)
- **MapLayer**: Links a FeatureLayer to a MapConfig with styling and rendering order

For detailed configuration instructions and examples, see the full documentation in the `docs/` directory.
