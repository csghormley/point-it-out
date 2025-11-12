Survey Point Segmentation (Experimental)
========================================

.. warning::
   This is an **experimental feature** under active development. The API and algorithms may change in future versions.

Overview
--------

The segmentation tool processes survey points collected through the map interface and automatically identifies geometric patterns:

- **Polygons**: Closed loops where users clicked around an area
- **LineStrings**: Linear paths where users clicked along a route
- **Individual Points**: Isolated clicks or noise points

This feature uses temporal and spatial clustering algorithms to infer user intent from sequences of clicked points.

Location
--------

The segmentation code is integrated into the Django application at ``collector/pio/segmentation/``::

    collector/pio/segmentation/
    ├── __init__.py          # Package exports
    ├── data.py              # SurveyPointData dataclass
    ├── segmenter.py         # GeometrySegmenter class
    └── exporters.py         # format_results, export_geojson

Installation
------------

Dependencies are included in ``pyproject.toml``:

.. code-block:: bash

    uv sync

Required packages:

- ``numpy>=1.21.0``
- ``scikit-learn>=1.0.0``
- ``shapely>=2.0.0``

Usage
-----

Django Management Command
~~~~~~~~~~~~~~~~~~~~~~~~~

Process survey points using the Django management command:

.. code-block:: bash

    cd collector

    # Process a single response ID
    python manage.py segment_survey_points --responseid ABC123XYZ

    # Export to GeoJSON
    python manage.py segment_survey_points --responseid ABC123XYZ --output results.geojson

    # Process all sessions
    python manage.py segment_survey_points --all --output all_sessions.geojson

    # Custom parameters
    python manage.py segment_survey_points --responseid ABC123XYZ \
        --max-time-gap 300 \
        --max-distance 100 \
        --polygon-threshold 30

Command-Line Options
~~~~~~~~~~~~~~~~~~~~

Input Options
^^^^^^^^^^^^^

- ``--responseid <id>``: Response ID to process
- ``--projectid <id>``: Project ID to filter by (optional)
- ``--all``: Process all response IDs

Segmentation Parameters
^^^^^^^^^^^^^^^^^^^^^^^

- ``--max-time-gap <seconds>``: Maximum time gap for temporal segmentation (default: 180)

  Points separated by more than this many seconds are treated as separate segments

- ``--max-distance <meters>``: Maximum distance for spatial clustering (default: 50)

  Points within this distance are grouped together using DBSCAN

- ``--min-cluster-points <n>``: Minimum points to form a cluster (default: 3)

  Smaller clusters are treated as individual points

- ``--polygon-threshold <meters>``: Max distance between first/last point for polygon (default: 20)

  If first and last points are within this distance, attempt to create a polygon

Output Options
^^^^^^^^^^^^^^

- ``--output <file>``: Export results to GeoJSON file
- ``--verbose``: Enable detailed logging

Algorithm Details
-----------------

Temporal Segmentation
~~~~~~~~~~~~~~~~~~~~~

The algorithm first segments points by time:

1. Sort all points by timestamp
2. Identify gaps larger than ``max-time-gap``
3. Split into temporal segments at these gaps

This handles cases where users take breaks or work on different areas at different times.

Spatial Clustering
~~~~~~~~~~~~~~~~~~

Within each temporal segment, DBSCAN clustering groups spatially close points:

- Uses ``max-distance`` as the epsilon parameter
- Requires at least 2 points for a cluster
- Noise points (not in any cluster) become individual points

Geometry Classification
~~~~~~~~~~~~~~~~~~~~~~~

For each spatial cluster, the algorithm determines the geometry type:

Polygon Detection
^^^^^^^^^^^^^^^^^

A cluster becomes a polygon if:

- It has ≥ 4 points (minimum for a closed shape)
- First and last points are within ``polygon-threshold`` distance
- The resulting polygon is valid and has non-zero area

LineString Detection
^^^^^^^^^^^^^^^^^^^^

A cluster becomes a linestring if:

- It has ≥ 2 points
- It doesn't qualify as a polygon
- The resulting linestring is valid and has non-zero length

Linestrings include a "linearity" metric (0-1) indicating how straight the path is.

Individual Points
^^^^^^^^^^^^^^^^^

Points become individual points if:

- They're noise from DBSCAN clustering
- They're in clusters too small to form meaningful geometries
- Geometry creation fails

Output Format
-------------

Console Output
~~~~~~~~~~~~~~

The tool displays a summary::

    ======================================================================
    SEGMENTATION RESULTS
    ======================================================================

    Polygons: 2
      #1: 12 points, area=0.00004231 deg²
           Time: 2024-01-15T14:23:10 to 2024-01-15T14:25:33
      #2: 8 points, area=0.00001842 deg²
           Time: 2024-01-15T14:28:45 to 2024-01-15T14:30:12

    LineStrings: 3
      #1: 5 points, length=0.00123456 deg
           Linearity: 0.892
           Time: 2024-01-15T14:26:00 to 2024-01-15T14:27:30

    Individual Points: 4

    ======================================================================

GeoJSON Output
~~~~~~~~~~~~~~

When using ``--output``, the tool creates a GeoJSON FeatureCollection with:

**Polygon features**:

.. code-block:: json

    {
      "type": "Feature",
      "geometry": {
        "type": "Polygon",
        "coordinates": [[[-121.5, 44.1], ...]]
      },
      "properties": {
        "geometry_type": "polygon",
        "point_count": 12,
        "point_ids": [1, 2, 3, ...],
        "area": 0.00004231,
        "timestamp_start": "2024-01-15T14:23:10",
        "timestamp_end": "2024-01-15T14:25:33"
      }
    }

**LineString features**:

.. code-block:: json

    {
      "type": "Feature",
      "geometry": {
        "type": "LineString",
        "coordinates": [[-121.5, 44.1], ...]
      },
      "properties": {
        "geometry_type": "linestring",
        "point_count": 5,
        "point_ids": [10, 11, 12, 13, 14],
        "length": 0.00123456,
        "linearity": 0.892,
        "timestamp_start": "2024-01-15T14:26:00",
        "timestamp_end": "2024-01-15T14:27:30"
      }
    }

**Point features**:

.. code-block:: json

    {
      "type": "Feature",
      "geometry": {
        "type": "Point",
        "coordinates": [-121.5, 44.1]
      },
      "properties": {
        "geometry_type": "point",
        "point_count": 1,
        "point_ids": [20],
        "timestamp": "2024-01-15T14:31:00"
      }
    }

Parameter Tuning Guide
----------------------

max-time-gap
~~~~~~~~~~~~

- **Increase** (e.g., 300-600s) if users take longer breaks but work on the same feature
- **Decrease** (e.g., 60-120s) if users rapidly switch between different tasks
- Default 180s works well for typical survey sessions

max-distance
~~~~~~~~~~~~

- **Increase** (e.g., 100-200m) for larger geographic features or lower precision
- **Decrease** (e.g., 20-30m) for detailed urban features or high precision
- Default 50m balances detail and aggregation
- Note: This is approximate; actual distance depends on latitude

polygon-threshold
~~~~~~~~~~~~~~~~~

- **Increase** (e.g., 30-50m) if users are imprecise when closing polygons
- **Decrease** (e.g., 10-15m) if you want strict polygon closure
- Default 20m allows for typical user imprecision

min-cluster-points
~~~~~~~~~~~~~~~~~~

- **Increase** (e.g., 4-5) to require more evidence before creating features
- **Decrease** (e.g., 2) to capture smaller features
- Default 3 is a good balance for DBSCAN

Programmatic Usage
------------------

The segmentation package can be used directly in Python code:

.. code-block:: python

    from pio.segmentation import GeometrySegmenter, SurveyPointData
    from pio.models import SurveyPoint

    # Fetch points from database
    db_points = SurveyPoint.objects.filter(
        responseid='ABC123XYZ',
        deleted=False
    ).order_by('timestamp_add')

    # Convert to SurveyPointData objects
    points = [
        SurveyPointData(
            id=p.id,
            x=p.geom.x,
            y=p.geom.y,
            timestamp=p.timestamp,
            responseid=p.responseid,
            projectid=p.projectid,
            description=p.description,
            radius=float(p.radius) if p.radius else None,
            resolution=p.resolution
        )
        for p in db_points
    ]

    # Initialize segmenter with custom parameters
    segmenter = GeometrySegmenter(
        max_time_gap=180.0,
        max_distance=50.0,
        min_cluster_points=3,
        polygon_closure_threshold=20.0
    )

    # Segment the points
    results = segmenter.segment_session(points)

    # Access results
    print(f"Found {len(results['polygons'])} polygons")
    print(f"Found {len(results['linestrings'])} linestrings")
    print(f"Found {len(results['points'])} individual points")

Troubleshooting
---------------

No points found
~~~~~~~~~~~~~~~

- Verify the response ID exists in the database
- Check that points have ``deleted=False``
- Confirm the database connection is working

All points classified as individual points
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

- Decrease ``max-distance`` if points are too far apart
- Decrease ``max-time-gap`` if there are long pauses
- Check that points have valid timestamps

Too many small features
~~~~~~~~~~~~~~~~~~~~~~~

- Increase ``min-cluster-points`` to require larger groups
- Increase ``max-distance`` to cluster more aggressively
- Increase ``polygon-threshold`` to allow looser polygon closure

Performance Notes
-----------------

- Processing time scales linearly with the number of points
- DBSCAN clustering is O(n log n) with efficient implementations
- Memory usage is proportional to the number of points in the largest session
- For very large datasets (>10,000 points per session), consider batching

Future Enhancements
-------------------

Potential improvements for future versions:

1. **Multi-geometry support**: Detect mixed polygon/linestring features
2. **Confidence scoring**: Add confidence metrics to classifications
3. **Machine learning**: Train models on labeled data for better accuracy
4. **Real-time processing**: WebSocket API for live segmentation
5. **API endpoint**: Serve segmented geometries via REST API
6. **Admin integration**: View segmented features in Django admin
