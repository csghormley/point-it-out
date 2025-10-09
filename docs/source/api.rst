API Reference
=============

This document describes the REST API endpoints available in MapSurvey.

Base URL
--------

All API endpoints are relative to ``/api/``

Authentication
--------------

- Session-based authentication for web interface
- Custom permission classes for API access
- See :doc:`development` for security details

Endpoints
---------

Survey Points
~~~~~~~~~~~~~

``GET /api/surveypoints/``

Returns survey points filtered by responseid and/or projectid.

**Query Parameters:**

.. list-table::
   :header-rows: 1
   :widths: 20 10 70

   * - Parameter
     - Type
     - Description
   * - ``responseid``
     - String
     - Filter by response ID
   * - ``projectid``
     - Number
     - Filter by project ID

**Response:** Array of SurveyPoint objects with GeoJSON geometry

**Example:**

::

    GET /api/surveypoints/?responseid=ABC123&projectid=1

Map Configurations
~~~~~~~~~~~~~~~~~~

``GET /api/mapconfigs/``

Returns list of available map configurations.

**Response:** Array of MapConfig objects

``GET /api/mapconfigs/{id}/``

Returns a specific map configuration.

**Response:** Single MapConfig object with configuration JSON

Feature Layers
~~~~~~~~~~~~~~

``GET /api/featurelayers/``

Returns list of available feature layers.

**Response:** Array of FeatureLayer objects with GeoJSON data

``GET /api/featurelayers/{id}/``

Returns a specific feature layer.

**Response:** Single FeatureLayer object with complete GeoJSON FeatureCollection

Map Layers
~~~~~~~~~~

``GET /api/map-layers/``

Returns map layers with associated GeoJSON data and styling configuration.

**Query Parameters:**

.. list-table::
   :header-rows: 1
   :widths: 20 10 70

   * - Parameter
     - Type
     - Description
   * - ``mapconfig``
     - Number
     - Filter by MapConfig ID (required in practice)

**Response:** Array of MapLayer objects sorted by z-order, each containing:

- Layer configuration (styling, zoom levels)
- Associated FeatureLayer GeoJSON data
- Z-order for rendering

**Example:**

::

    GET /api/map-layers/?mapconfig=1

This endpoint is used by the frontend to load all layers for a specific map.

Data Models
-----------

SurveyPoint
~~~~~~~~~~~

.. code-block:: python

    {
        "id": 123,
        "surveyid": "survey_abc",
        "responseid": "RESP123",
        "projectid": 1,
        "description": "work_type_1,work_type_2",
        "mapconfig": 1,
        "radius": 500.0,
        "resolution": 2.5,
        "timestamp": "1234567890",
        "timestamp_add": "2025-01-01T12:00:00Z",
        "timestamp_edit": "2025-01-01T12:00:00Z",
        "ipaddress": "192.168.1.1",
        "geom": {
            "type": "Point",
            "coordinates": [-121.3, 44.1]
        },
        "deleted": false
    }

MapConfig
~~~~~~~~~

.. code-block:: python

    {
        "id": 1,
        "name": "Downtown Map",
        "slug": "downtown-map",
        "config": {
            "map_center": [-121.3, 44.1],
            "extent": [-122, 43.4, -120.385, 44.824],
            "boundary": [-123, 41.9, -119.385, 46.324],
            "initial_zoom": 4,
            "max_zoom": 16,
            "min_zoom": 4,
            "verbose": false
        }
    }

FeatureLayer
~~~~~~~~~~~~

.. code-block:: python

    {
        "id": 1,
        "name": "City Landmarks",
        "slug": "city-landmarks",
        "geojson": {
            "type": "FeatureCollection",
            "name": "city_landmarks",
            "features": [...]
        }
    }

MapLayer
~~~~~~~~

.. code-block:: python

    {
        "id": 1,
        "mapconfig": 1,
        "layer": 1,
        "layer_name": "City Landmarks",
        "layer_slug": "city-landmarks",
        "layer_features": {
            "type": "FeatureCollection",
            "features": [...]
        },
        "z_order": 10,
        "config": {
            "min_zoom": 11,
            "max_zoom": 14,
            "point_color": "#FF5733",
            "point_radius": 6,
            "label_format": "{name}"
        }
    }

Frontend Integration
--------------------

The frontend JavaScript (``collector/pio/static/pio/js/map.js``) uses these endpoints to:

1. Load MapConfig settings
2. Fetch MapLayers for the specified mapconfig
3. Parse GeoJSON with automatic CRS detection
4. Apply styling from MapLayer configuration
5. Render layers in z-order

Example usage in JavaScript::

    // Fetch map layers
    fetch(`/api/map-layers/?mapconfig=${mapconfigid}`)
        .then(response => response.json())
        .then(data => {
            // Sort by z_order and create OpenLayers layers
            const sortedLayers = data.sort((a, b) => a.z_order - b.z_order);
            // ... render layers
        });

Rate Limiting
-------------

Currently no rate limiting is implemented. Consider adding rate limiting for production deployments.

Error Responses
---------------

API errors return appropriate HTTP status codes:

- ``400 Bad Request``: Invalid parameters
- ``401 Unauthorized``: Authentication required
- ``403 Forbidden``: Insufficient permissions
- ``404 Not Found``: Resource not found
- ``500 Internal Server Error``: Server error

CORS
----

CORS is configured for same-origin requests. Adjust settings in ``collector/collector/settings.py`` for cross-origin access if needed.
