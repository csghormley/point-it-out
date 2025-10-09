Map Configuration Guide
=======================

This guide explains how to create and configure interactive maps using MapConfigs, FeatureLayers, and MapLayers.

Overview
--------

The map system uses three components that work together:

- **FeatureLayer**: GeoJSON data (points, lines, polygons) - reusable across maps
- **MapConfig**: Map settings (extent, zoom levels, projection, behavior)
- **MapLayer**: Links a FeatureLayer to a MapConfig with styling and rendering order

Each MapConfig can include multiple MapLayers, each referencing a FeatureLayer and defining how it should be styled and stacked.

Step 1: Create a FeatureLayer
------------------------------

FeatureLayers contain your GeoJSON data and can be reused across multiple MapConfigs.

Via Django Admin
~~~~~~~~~~~~~~~~

1. Navigate to **Django Admin** → **PIO** → **Feature Layers** → **Add Feature Layer**
2. Fill in the fields:

   - **Name**: Descriptive name (e.g., "Downtown Landmarks")
   - **Slug**: URL-friendly identifier (e.g., "downtown-landmarks")
   - **Geojson**: Paste your GeoJSON FeatureCollection

GeoJSON Format
~~~~~~~~~~~~~~

Your GeoJSON must be a valid **FeatureCollection**::

    {
      "type": "FeatureCollection",
      "name": "downtown_landmarks",
      "features": [
        {
          "type": "Feature",
          "properties": {
            "name": "City Hall",
            "type": "Government",
            "elevation": 1200
          },
          "geometry": {
            "type": "Point",
            "coordinates": [-121.3, 44.1]
          }
        }
      ]
    }

Coordinate Reference Systems (CRS)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

By default, GeoJSON uses **WGS84 (EPSG:4326)** coordinates. If your data uses a different CRS, you can specify it::

    {
      "type": "FeatureCollection",
      "crs": {
        "type": "name",
        "properties": {
          "name": "EPSG:3857"
        }
      },
      "features": [...]
    }

.. note::
   The system will automatically detect and use the CRS from your GeoJSON, falling back to EPSG:4326 if none is specified.

Step 2: Create a MapConfig
---------------------------

MapConfigs define the overall map settings and behavior.

Via Django Admin
~~~~~~~~~~~~~~~~

1. Navigate to **Django Admin** → **PIO** → **Map Configs** → **Add Map Config**
2. Fill in the fields:

   - **Name**: Descriptive name
   - **Slug**: URL-friendly identifier
   - **Config**: JSON configuration (see below)

MapConfig JSON Options
~~~~~~~~~~~~~~~~~~~~~~

::

    {
      "map_center": [-121.3, 44.1],
      "extent": [-122, 43.4, -120.385, 44.824],
      "boundary": [-123, 41.9, -119.385, 46.324],
      "src_proj": "EPSG:4326",
      "dest_proj": "EPSG:3857",
      "api_url": "/api/surveypoints/",
      "initial_zoom": 4,
      "max_zoom": 16,
      "min_zoom": 4,
      "max_res": 170,
      "edit_worktype": true,
      "verbose": false,
      "show_description": true,
      "show_diameter": false,
      "show_overview": true,
      "show_status": true,
      "show_zoom": false,
      "display_units": "ft",
      "site_description": "region near the map center",
      "site_purpose": "wildfire resilience and vulnerability"
    }

Key Configuration Options
~~~~~~~~~~~~~~~~~~~~~~~~~

.. list-table::
   :header-rows: 1
   :widths: 20 10 70

   * - Option
     - Type
     - Description
   * - ``map_center``
     - Array
     - [longitude, latitude] center point
   * - ``extent``
     - Array
     - [minX, minY, maxX, maxY] initial view extent
   * - ``boundary``
     - Array
     - [minX, minY, maxX, maxY] navigation boundary
   * - ``src_proj``
     - String
     - Source projection (usually ``EPSG:4326``)
   * - ``dest_proj``
     - String
     - Display projection (usually ``EPSG:3857``)
   * - ``initial_zoom``
     - Number
     - Starting zoom level
   * - ``max_zoom`` / ``min_zoom``
     - Number
     - Zoom level limits
   * - ``verbose``
     - Boolean
     - Enable console logging for debugging
   * - ``show_overview``
     - Boolean
     - Show overview map control
   * - ``display_units``
     - String
     - ``"m"`` for metric or ``"ft"`` for US units

Step 3: Create MapLayers
-------------------------

MapLayers connect FeatureLayers to MapConfigs with styling and rendering order.

Via Django Admin
~~~~~~~~~~~~~~~~

1. Navigate to **Django Admin** → **PIO** → **Map Layers** → **Add Map Layer**
2. Fill in the fields:

   - **Mapconfig**: Select the MapConfig
   - **Layer**: Select the FeatureLayer
   - **Z order**: Rendering order (lower values render first/bottom)
   - **Config**: JSON styling configuration (see below)

MapLayer Styling Configuration
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

::

    {
      "min_zoom": 11,
      "max_zoom": 14,
      "point_color": "#555555",
      "point_radius": 4,
      "line_width": 1.5,
      "stroke_color": "#b09592cc",
      "fill_color": "rgba(0, 0, 0, 0.1)",
      "line_dash": [5, 2, 2, 2],
      "font_size": "9px",
      "font_style": "italic",
      "font_face": "Arial, Helvetica, sans-serif",
      "font_color": "#000000",
      "font_stroke_color": "#FFFFFF33",
      "text_offset": [0, -15],
      "text_align": "center",
      "label_format": "{name}"
    }

Visibility Options
~~~~~~~~~~~~~~~~~~

.. list-table::
   :header-rows: 1
   :widths: 20 10 70

   * - Option
     - Type
     - Description
   * - ``min_zoom``
     - Number
     - Minimum zoom level to show layer
   * - ``max_zoom``
     - Number
     - Maximum zoom level to show layer

Point Styling
~~~~~~~~~~~~~

.. list-table::
   :header-rows: 1
   :widths: 20 10 70

   * - Option
     - Type
     - Description
   * - ``point_color``
     - String
     - Fill color (hex or rgba)
   * - ``point_radius``
     - Number
     - Circle radius in pixels

Line Styling
~~~~~~~~~~~~

.. list-table::
   :header-rows: 1
   :widths: 20 10 70

   * - Option
     - Type
     - Description
   * - ``stroke_color``
     - String
     - Line color (hex or rgba)
   * - ``line_width``
     - Number
     - Line width in pixels
   * - ``line_dash``
     - Array
     - Dash pattern ``[dash, gap, dash, gap]``

Polygon Styling
~~~~~~~~~~~~~~~

.. list-table::
   :header-rows: 1
   :widths: 20 10 70

   * - Option
     - Type
     - Description
   * - ``fill_color``
     - String
     - Fill color (hex or rgba)
   * - ``stroke_color``
     - String
     - Border color (hex or rgba)
   * - ``line_width``
     - Number
     - Border width in pixels

Label Styling
~~~~~~~~~~~~~

.. list-table::
   :header-rows: 1
   :widths: 20 10 70

   * - Option
     - Type
     - Description
   * - ``font_size``
     - String
     - Font size with units (e.g., ``"12px"``)
   * - ``font_style``
     - String
     - Font style (``"italic"``, ``"normal"``, ``"bold"``)
   * - ``font_face``
     - String
     - Font family
   * - ``font_color``
     - String
     - Text color
   * - ``font_stroke_color``
     - String
     - Text outline color
   * - ``text_offset``
     - Array
     - ``[x, y]`` pixel offset from feature
   * - ``text_align``
     - String
     - Text alignment (``"center"``, ``"left"``, ``"right"``)

Label Content
~~~~~~~~~~~~~

Labels are configured using the ``label_format`` option with ``{property}`` placeholders.

**Default (if not specified)**::

    {
      "label_format": "{name}"
    }

Uses the ``name`` property from each feature.

**Single Property**::

    {
      "label_format": "{title}"
    }

Uses a different property like ``title``.

**Format String with Multiple Properties**::

    {
      "label_format": "{name} ({type})"
    }

Combines multiple properties: ``"City Hall (Government)"``

**More Examples**::

    {
      "label_format": "{name} - Elev: {elevation}m"
    }

Result: ``"Mt. Bachelor - Elev: 2764m"``

::

    {
      "label_format": "{city}, {state} {zip}"
    }

Result: ``"Bend, OR 97701"``

::

    {
      "label_format": "{name} {type}"
    }

Result: ``"City Hall Government"``

.. note::
   Missing properties are replaced with empty strings and won't break the label.

Z-Order (Layer Stacking)
~~~~~~~~~~~~~~~~~~~~~~~~

The ``z_order`` field controls rendering order:

- **Lower values** render first (bottom of stack)
- **Higher values** render last (top of stack)

Example stacking::

    z_order: 1 → Polygon regions (bottom)
    z_order: 2 → Roads and trails
    z_order: 3 → Point landmarks (top)

Each MapConfig must have unique z-order values across its MapLayers.

Complete Example
----------------

1. Create FeatureLayer "City Landmarks"
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Name**: City Landmarks

**Slug**: ``city-landmarks``

**GeoJSON**::

    {
      "type": "FeatureCollection",
      "name": "city_landmarks",
      "features": [
        {
          "type": "Feature",
          "properties": {
            "name": "City Hall",
            "type": "Government",
            "elevation": 1200
          },
          "geometry": {
            "type": "Point",
            "coordinates": [-121.315, 44.058]
          }
        },
        {
          "type": "Feature",
          "properties": {
            "name": "Public Library",
            "type": "Education",
            "elevation": 1190
          },
          "geometry": {
            "type": "Point",
            "coordinates": [-121.312, 44.062]
          }
        }
      ]
    }

2. Create MapConfig "Downtown Map"
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Name**: Downtown Map

**Slug**: ``downtown-map``

**Config**::

    {
      "map_center": [-121.31, 44.06],
      "extent": [-121.32, 44.05, -121.30, 44.07],
      "boundary": [-121.35, 44.03, -121.27, 44.09],
      "initial_zoom": 13,
      "max_zoom": 18,
      "min_zoom": 11,
      "verbose": true,
      "show_overview": true,
      "display_units": "ft"
    }

3. Create MapLayer
~~~~~~~~~~~~~~~~~~

**Mapconfig**: Downtown Map

**Layer**: City Landmarks

**Z order**: 10

**Config**::

    {
      "min_zoom": 12,
      "max_zoom": 18,
      "point_color": "#FF5733",
      "point_radius": 6,
      "font_size": "12px",
      "font_style": "bold",
      "font_color": "#000000",
      "text_offset": [0, -20],
      "label_format": "{name} ({type})"
    }

This will display landmarks as red circles with labels like "City Hall (Government)".

Best Practices
--------------

Color Formats
~~~~~~~~~~~~~

Use hex with alpha channel for transparency:

- ``#FF5733`` - Opaque red-orange
- ``#FF5733CC`` - Semi-transparent (80% opacity)
- ``#FF573333`` - Very transparent (20% opacity)
- ``rgba(255, 87, 51, 0.8)`` - Alternative RGBA format

Performance
~~~~~~~~~~~

- Use appropriate ``min_zoom``/``max_zoom`` to avoid rendering complex layers when zoomed out
- Keep GeoJSON files reasonably sized (< 1MB recommended)
- Use ``declutter: true`` (automatic) to prevent label overlap

Coordinate Systems
~~~~~~~~~~~~~~~~~~

- Input coordinates in GeoJSON as **[longitude, latitude]** (x, y)
- Use EPSG:4326 (WGS84) for most GPS/geographic data
- The system converts to EPSG:3857 (Web Mercator) for display

Debugging
~~~~~~~~~

Enable verbose logging during development::

    {
      "verbose": true
    }

Check browser console for:

- Feature counts loaded
- CRS detection results
- Layer rendering information
- Style application details

Further Reading
---------------

- See :doc:`development` for code organization and workflow
- See :doc:`api` for API reference
- See :doc:`troubleshooting` for common issues
- `GeoJSON Specification <https://tools.ietf.org/html/rfc7946>`_
- `EPSG Code Reference <https://epsg.io/>`_
