# MapSurvey Documentation

This directory contains the Sphinx documentation for MapSurvey.

## Building the Documentation

### Prerequisites

**Option 1: Using uv (recommended)**

```bash
# Install uv if not already installed
curl -LsSf https://astral.sh/uv/install.sh | sh

# Create virtual environment and install dependencies
cd docs
uv venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
uv pip install -r requirements.txt
```

**Option 2: Using pip**

```bash
# Create virtual environment
cd docs
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### Build HTML

```bash
make html
```

The generated HTML will be in `build/html/`. Open `build/html/index.html` in your browser.

### Other Formats

```bash
make latexpdf  # PDF output
make epub      # EPUB output
make man       # Man pages
```

### Clean Build Files

```bash
make clean
```

## Documentation Structure

- `source/index.rst` - Main documentation index
- `source/quickstart.rst` - Quick start guide
- `source/configuration.rst` - Map configuration guide
- `source/development.rst` - Development workflow and architecture
- `source/api.rst` - API reference
- `source/troubleshooting.rst` - Common issues and solutions
- `source/conf.py` - Sphinx configuration

## Live Preview

For development with auto-rebuild:

**Using uv:**

```bash
uv pip install sphinx-autobuild
sphinx-autobuild source build/html
```

**Using pip:**

```bash
pip install sphinx-autobuild
sphinx-autobuild source build/html
```

Then open http://localhost:8000 in your browser.

## Contributing

When updating documentation:

1. Edit the `.rst` files in `source/`
2. Build and preview locally
3. Commit both source files and built HTML (if applicable)
