Troubleshooting
===============

This guide covers common issues and their solutions.

Map Display Issues
------------------

Labels Not Appearing
~~~~~~~~~~~~~~~~~~~~

**Symptoms:** Point features display but labels are missing

**Check:**

1. Feature has the property specified in ``label_format`` (default is ``{name}``)
2. Zoom level is within ``min_zoom`` and ``max_zoom`` range
3. ``font_color`` contrasts with the map background
4. Label text is not empty after placeholder replacement

**Solution:**

- Verify GeoJSON features have the required property::

    {
      "type": "Feature",
      "properties": {
        "name": "City Hall"  // Required for default label_format: "{name}"
      }
    }

- Check MapLayer config zoom settings match current zoom level
- Try a contrasting color like ``"#000000"`` for light backgrounds or ``"#FFFFFF"`` for dark backgrounds

Layer Not Visible
~~~~~~~~~~~~~~~~~~

**Symptoms:** Layer doesn't appear on the map

**Check:**

1. Current zoom level is within the layer's ``min_zoom``/``max_zoom``
2. Layer extent overlaps with the map extent
3. ``z_order`` doesn't place it behind an opaque layer
4. Colors aren't fully transparent

**Solution:**

- Enable verbose logging in MapConfig::

    {
      "verbose": true
    }

- Check browser console for layer loading messages
- Verify GeoJSON coordinates are within map boundary
- Check ``point_color``, ``stroke_color``, and ``fill_color`` opacity

Features in Wrong Location
~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Symptoms:** Features appear in unexpected geographic locations

**Check:**

1. GeoJSON coordinates are ``[longitude, latitude]``, not ``[latitude, longitude]``
2. CRS is correct in the GeoJSON (or omit for default EPSG:4326)
3. MapConfig ``extent`` and ``boundary`` are correct

**Solution:**

- Swap coordinate order if needed::

    // Correct (longitude, latitude)
    "coordinates": [-121.3, 44.1]

    // Incorrect (latitude, longitude)
    "coordinates": [44.1, -121.3]

- Remove CRS property from GeoJSON to use default EPSG:4326
- Verify extent coordinates are in correct projection

Map Not Loading
~~~~~~~~~~~~~~~

**Symptoms:** Blank map or error messages

**Check:**

1. JavaScript console for error messages
2. Network tab for failed API requests
3. MapConfig exists and is accessible
4. Static files are collected (``python manage.py collectstatic``)

**Solution:**

- Check that the mapconfig ID is correct
- Verify API endpoints return valid JSON
- Ensure OpenLayers library is loaded
- Clear browser cache and reload

Data Issues
-----------

GeoJSON Validation Errors
~~~~~~~~~~~~~~~~~~~~~~~~~~

**Symptoms:** Error when saving FeatureLayer

**Common Errors:**

- "Must be a FeatureCollection" - Root object type is incorrect
- "Must have features array" - Missing ``features`` property
- Invalid JSON syntax

**Solution:**

- Validate GeoJSON at `geojson.io <https://geojson.io>`_ or `geojsonlint.com <https://geojsonlint.com>`_
- Ensure structure matches::

    {
      "type": "FeatureCollection",
      "features": [
        {
          "type": "Feature",
          "properties": {...},
          "geometry": {...}
        }
      ]
    }

Z-Order Conflicts
~~~~~~~~~~~~~~~~~

**Symptoms:** Error when saving MapLayer - "Z-order already exists for this map"

**Solution:**

- Each MapLayer in a MapConfig must have a unique ``z_order`` value
- Check existing MapLayers for the same MapConfig
- Choose an unused z-order value
- Remember: lower values render first (bottom), higher values render last (top)

CRS Detection Issues
~~~~~~~~~~~~~~~~~~~~

**Symptoms:** Features appear distorted or in wrong locations despite correct coordinates

**Solution:**

- Add explicit CRS to GeoJSON if not using EPSG:4326::

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

- Check browser console for CRS detection messages (requires ``verbose: true``)
- Verify source data CRS matches declared CRS

Development Issues
------------------

Migrations Not Applying
~~~~~~~~~~~~~~~~~~~~~~~~

**Symptoms:** Database schema doesn't match models

**Solution:**

1. Check for migration files::

    cd collector
    python manage.py showmigrations

2. Create missing migrations::

    python manage.py makemigrations

3. Apply migrations::

    ./migrate.sh
    # or manually:
    python manage.py migrate

4. For Docker deployment::

    docker compose -f docker-stack/docker-compose.yml exec django ./manage.py migrate

Static Files Not Updated
~~~~~~~~~~~~~~~~~~~~~~~~~

**Symptoms:** JavaScript/CSS changes not reflected in browser

**Solution:**

1. Collect static files::

    cd collector
    python manage.py collectstatic --noinput

2. Clear browser cache or hard reload (Ctrl+F5 / Cmd+Shift+R)

3. For Docker deployment, rebuild::

    ./checkbuildrun.sh

Database Connection Errors
~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Symptoms:** "could not connect to server" or similar database errors

**Solution:**

1. Verify PostgreSQL is running::

    docker compose ps postgis17

2. Check database credentials in secrets or ``localsettings.py``

3. Verify PostGIS extension is installed::

    docker compose exec postgis17 psql -U postgres -d mapbe -c "SELECT postgis_version();"

4. Check logs::

    docker compose logs postgis17

Performance Issues
------------------

Slow Map Loading
~~~~~~~~~~~~~~~~

**Symptoms:** Map takes a long time to load or render

**Solution:**

- Reduce GeoJSON file size (< 1MB recommended)
- Use appropriate ``min_zoom``/``max_zoom`` to avoid rendering complex layers when zoomed out
- Simplify geometries using tools like `mapshaper <https://mapshaper.org>`_
- Consider splitting large FeatureLayers into multiple smaller layers

Debugging Tools
---------------

Browser Console
~~~~~~~~~~~~~~~

Enable verbose logging in MapConfig::

    {
      "verbose": true
    }

Then check browser console (F12) for:

- Feature counts loaded
- CRS detection results
- Layer rendering information
- Style application details

Django Debug Toolbar
~~~~~~~~~~~~~~~~~~~~

1. Uncomment ``debug_toolbar`` in ``collector/collector/settings.py``
2. Set ``DEBUG = True`` in ``localsettings.py``
3. Access application to see debug toolbar
4. View SQL queries, template rendering, and more

**Warning:** Never enable DEBUG mode in production

API Testing
~~~~~~~~~~~

Use Django REST Framework browseable API:

1. Navigate to ``http://localhost:8000/api/``
2. Click on endpoints to view responses
3. Test filters and parameters
4. Verify JSON structure

Database Inspection
~~~~~~~~~~~~~~~~~~~

Access PostgreSQL shell::

    docker compose exec postgis17 psql -U postgres mapbe

Useful queries::

    -- List all MapConfigs
    SELECT id, name, slug FROM pio_mapconfig;

    -- List all FeatureLayers
    SELECT id, name, slug FROM pio_featurelayer;

    -- List MapLayers for a specific MapConfig
    SELECT id, z_order, layer_id FROM pio_maplayer WHERE mapconfig_id = 1 ORDER BY z_order;

    -- View SurveyPoints for a responseid
    SELECT id, projectid, ST_AsText(geom) FROM pio_surveypoint WHERE responseid = 'ABC123';

Getting Help
------------

If you encounter issues not covered here:

1. Check the browser console for JavaScript errors
2. Review server logs: ``docker compose logs django``
3. Verify configuration against examples in :doc:`configuration`
4. Review code organization in :doc:`development`
5. Test API endpoints directly using :doc:`api` reference

Common Error Messages
---------------------

"Invalid FeatureCollection"
~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Cause:** GeoJSON structure is incorrect

**Fix:** Ensure ``type: "FeatureCollection"`` and ``features`` array are present

"Z-order already exists for this map"
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Cause:** Duplicate z-order value in MapLayers for the same MapConfig

**Fix:** Choose a unique z-order value

"CSRF verification failed"
~~~~~~~~~~~~~~~~~~~~~~~~~~

**Cause:** Missing or invalid CSRF token

**Fix:** Ensure CSRF token is included in POST/PATCH/DELETE requests

"PostGIS not available"
~~~~~~~~~~~~~~~~~~~~~~~

**Cause:** PostGIS extension not installed or enabled

**Fix:** Run in PostgreSQL::

    CREATE EXTENSION postgis;
