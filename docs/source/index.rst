MapSurvey Documentation
=======================

MapSurvey is a Django-based web mapping application for collecting and visualizing geographic point data through interactive maps.

.. toctree::
   :maxdepth: 2
   :caption: Contents:

   quickstart
   configuration
   development
   mapcfg
   api
   troubleshooting

Overview
--------

This application provides:

- **Interactive Maps**: OpenLayers-based web maps with configurable layers
- **Survey Integration**: Designed for embedding in survey platforms (e.g., Qualtrics)
- **Flexible Configuration**: Layer styling, CRS support, and dynamic labeling
- **Spatial Database**: PostGIS backend for geographic data storage

Key Components
--------------

- **MapConfig**: Map extent, zoom levels, and behavior settings
- **FeatureLayer**: GeoJSON data (points, lines, polygons)
- **MapLayer**: Styling and rendering order for layers
- **SurveyPoint**: User-submitted geographic points

Getting Started
---------------

For configuration instructions, see :doc:`configuration`.

For development workflow, see :doc:`development`.

Indices and tables
==================

* :ref:`genindex`
* :ref:`search`
