// OpenLayers Map Module
// Import the entire ol object and specific components
import ol, {
    Map, View, Feature, Overlay,
    GeoJSON, WKT,
    Point, Circle, LineString,
    TileLayer, VectorLayer,
    OSM, XYZ, TileWMS, VectorSource,
    Style, Fill, Stroke, Text, Icon, CircleStyle,
    Select, Draw,
    Attribution, OverviewMap, ScaleLine,
    fromLonLat, transform, transformExtent, getPointResolution,
    click, pointerMove, defaultInteractions, defaultControls
} from './ol-wrapper.js';

/**
 * MapManager class that handles map initialization and interactions
 * @class
 */
export class MapManager {
    /**
     * Creates a new MapManager instance
     * @param {string} configElementId - The ID of the element containing the map configuration
     */
    constructor(configElementId) {
        // Constants
        this.scl_const = 1.234567;
        this.meters_per_mile = 1609.34;

        // Initialize variables
        this.selectedFeature = null;
        this.responseid = getUrlParam('id');
        this.projectid = this.strToInt(getUrlParam('proj_id'));

        this.attributions =
  '<a href="https://www.usgs.gov/programs/national-geospatial-program/national-map" target="_blank">USGS National Map</a> ' +
  '<a href="https://server.arcgisonline.com/arcgis/rest/services/NatGeo_World_Map/MapServer" target="_blank">&copy; National Geographic, Esri, Garmin, HERE, UNEP-WCMC, USGS, NASA, ESA, METI, NRCAN, GEBCO, NOAA, increment P Corp.</a>';

        // Initialize configuration
        this.initializeConfig(configElementId);

        // Initialize map components asynchronously
        this.initialize();
    }

    /**
     * Async initialization method
     * @private
     */
    async initialize() {
        // Initialize map components
        this.initializeSources();
        await this.initializeLayers();
        this.createMapBoundary();
        this.initializeMapView();
        this.initializeControls();
        this.createMap();
        this.setupInteractions();
        this.setupEventListeners();

        // Update UI elements
        this.updateUIElements();
        this.updateCartoStyle();

        // Log initialization status
        if (this.config.verbose) console.log(`survey id = ${this.responseid}\nproject id = ${this.projectid}`);
    }

    /**
     * Initialize configuration with defaults and getters/setters
     * @param {string} configElementId - The ID of the element containing configuration JSON
     */
    initializeConfig(configElementId) {
        // Define default configuration
        this.defaultConfig = {
            api_url: "/api/surveypoints/",
            dest_proj: "EPSG:3857", // web mercator
            src_proj: "EPSG:4326", // wgs84

            // Colorbrewer 8-class qualitative scheme
            point_colormap: ['#e41a1c','#377eb8','#4daf4a','#984ea3','#ff7f00','#ffff33','#a65628','#f781bf'],
            edit_worktype: false,
            initial_zoom: 4,
            min_zoom: 4,
            max_zoom: 16,
            min_px_km: 10,
            display_units: 'ft',
            show_description: true,
            show_diameter: false,
            show_overview: true,
            show_status: true,
            show_zoom: false,
            verbose: false,
            max_diameter: 16093.4, // meters; 10mi
            min_diameter: 804.67, // meters; 0.5mi
            site_description: "survey mapping application",
            site_purpose: "survey spatial data collection"
        };

        // Parse user configuration
        const userConfig = JSON.parse(document.getElementById(configElementId).textContent);

        // Merge user config with defaults
        this.config = {...this.defaultConfig, ...userConfig};

        // Get resource URLs
        this.img_url = document.getElementById('static_img_base').textContent;
        this.json_url = document.getElementById('static_json_base').textContent;

        // initialize config cache
        this._configCache = {};
    }

    /**
     * Get a configuration value
     * @param {string} key - The configuration key to retrieve
     * @param {*} [defaultValue=null] - Default value if key doesn't exist
     * @returns {*} The configuration value
     */
    getConfig(key, defaultValue = null) {
        // Check cache first
        if (this._configCache.hasOwnProperty(key)) {
            return this._configCache[key];
        }

        // Handle nested keys with dot notation (e.g., "layer.color")
        if (key.includes('.')) {
            const parts = key.split('.');
            let value = this.config;

            for (const part of parts) {
                if (value === undefined || value === null) {
                    return defaultValue;
                }
                value = value[part];
            }

            // Cache the result
            this._configCache[key] = value !== undefined ? value : defaultValue;
            return this._configCache[key];
        }

        // Simple key lookup
        const value = this.config[key];
        this._configCache[key] = value !== undefined ? value : defaultValue;
        return this._configCache[key];
    }

    /**
     * Set a configuration value
     * @param {string} key - The configuration key to set
     * @param {*} value - The value to set
     * @returns {boolean} True if successful
     */
    setConfig(key, value) {
        // Handle nested keys with dot notation
        if (key.includes('.')) {
            const parts = key.split('.');
            let obj = this.config;

            // Navigate to the nested object
            for (let i = 0; i < parts.length - 1; i++) {
                const part = parts[i];
                if (!obj[part]) {
                    obj[part] = {};
                }
                obj = obj[part];
            }

            // Set the value on the final property
            const lastPart = parts[parts.length - 1];
            obj[lastPart] = value;

            // Update cache
            this._configCache[key] = value;
            return true;
        }

        // Simple key update
        this.config[key] = value;
        this._configCache[key] = value;
        return true;
    }

    /**
     * Clear the configuration cache to force re-reading values
     * @param {string} [key=null] - Specific key to clear, or all if null
     */
    clearConfigCache(key = null) {
        if (key) {
            delete this._configCache[key];
        } else {
            this._configCache = {};
        }
    }

    /**
     * Extract CRS from GeoJSON object, with fallback to EPSG:4326
     * @param {Object} geojson - GeoJSON object (FeatureCollection or Feature)
     * @returns {string} CRS string (e.g., 'EPSG:4326')
     */
    extractCrsFromGeoJSON(geojson) {
        // Default CRS for GeoJSON per RFC 7946 is WGS84 (EPSG:4326)
        const defaultCrs = 'EPSG:4326';

        if (!geojson) {
            return defaultCrs;
        }

        // Check for CRS property (legacy GeoJSON spec, pre-RFC 7946)
        if (geojson.crs && geojson.crs.properties && geojson.crs.properties.name) {
            const crsName = geojson.crs.properties.name;

            // Handle different CRS name formats:
            // "urn:ogc:def:crs:EPSG::4326" -> "EPSG:4326"
            // "EPSG:4326" -> "EPSG:4326"
            if (typeof crsName === 'string') {
                const urnMatch = crsName.match(/EPSG::(\d+)/);
                if (urnMatch) {
                    return `EPSG:${urnMatch[1]}`;
                }

                const epsgMatch = crsName.match(/EPSG:\d+/);
                if (epsgMatch) {
                    return epsgMatch[0];
                }
            }
        }

        // RFC 7946 doesn't allow CRS property, assumes WGS84
        return defaultCrs;
    }

    /**
     * Get label text from a feature based on layer configuration
     * @param {ol.Feature} feature - The feature to get label from
     * @param {Object} layerConfig - Layer configuration object
     * @returns {string|null} Label text or null if no label
     */
    getFeatureLabel(feature, layerConfig) {
        // Use label_format, defaulting to "{name}" if not provided
        const formatString = layerConfig.label_format || '{name}';

        // Replace all {property} placeholders with actual values
        const result = formatString.replace(/\{(\w+)\}/g, (match, propName) => {
            const value = feature.get(propName);
            return (value !== undefined && value !== null) ? String(value) : '';
        });

        // Return null if result is empty or only whitespace
        return result.trim() || null;
    }

    /**
     * Initialize vector and data sources
     */
    initializeSources() {
        // Points source for vector features
        this.points_source = new VectorSource();

        // Source for stored data from server
        this.stored_vector_source = new VectorSource({
            format: new GeoJSON(),
            url: this.getDataUrl()
        });

        this.stored_vector_source.addEventListener("change", () => this.updateCartoStyle());
    }

    /**
     * Initialize map layers
     */
    async initializeLayers() {
        const natlmap_url = 'https://basemap.nationalmap.gov/arcgis/rest/services/';

        // layer for overview map
        this.overview_layer = this.makeXYZLayer(natlmap_url,
                                                'USGSTopo');

        // Load basemap layers from API (async)
        // This will fall back to hardcoded basemaps if API fails or no basemaps configured
        this.baselayers = await this.loadBasemapsFromAPI();

        // WMS and OSM layers
        this.layer_wms_fireshed = new TileLayer({
            source: new TileWMS({
                url: 'https://apps.fs.usda.gov/arcx/services/EDW/EDW_FireshedRegistry_01/MapServer/WMSServer'
            })
        });

        this.layer_osm = new TileLayer({
            source: new OSM()
        });

        // Vector layers
        this.points_vector = new VectorLayer({
            source: this.points_source,
            updateWhileAnimating: true,
            updateWhileInteracting: true,
            style: this.mapMarkerStyleFunction.bind(this),
            zIndex: 1000  // Survey points render on top of feature layers
        });

        this.stored_vector_layer = new VectorLayer({
            source: this.stored_vector_source,
            updateWhileAnimating: true,
            updateWhileInteracting: true,
            style: new Style({}),
            zIndex: 900  // Stored points render below active survey points
        });

        // Add configured GeoJSON layers if specified
        this.loadMapLayers();
    }

    /**
     * Load map layers from REST API based on mapconfig
     */
    loadMapLayers() {
        const mapconfigid = window.context?.mapconfigid;

        if (!mapconfigid) {
            if (this.config.verbose) console.log('No mapconfig ID found, falling back to config layers');
            this.loadGeoJSONLayers();
            return;
        }

        // Fetch map layers from the REST API
        const mapLayersUrl = `/api/map-layers/?mapconfig=${mapconfigid}`;

        fetch(mapLayersUrl, {
            method: 'GET',
            headers: {
                'Accept': 'application/json',
                'Content-Type': 'application/json',
            },
            credentials: 'same-origin'
        })
            .then(response => {
                if (!response.ok) {
                    throw new Error(`HTTP error! status: ${response.status}`);
                }
                return response.json();
            })
            .then(data => {
                if (this.config.verbose) console.log(`Retrieved map layers from API:`, data);
                if (this.config.verbose && data.length > 0) console.log('First layer config:', data[0].config);

                // Sort layers by z_order to ensure proper rendering order
                const sortedLayers = data.sort((a, b) => a.z_order - b.z_order);

                // Create OpenLayers vector layers for each map layer
                if (this.config.verbose) console.log(`Processing ${sortedLayers.length} map layers`);
                sortedLayers.forEach((mapLayer, index) => {
                    if (this.config.verbose) console.log(`Processing layer ${index}:`, mapLayer);
                    this.createVectorLayerFromMapLayer(mapLayer, index);
                });
            })
            .catch(error => {
                console.error(`Error loading map layers from API: ${error.message || error}`);
                if (this.config.verbose) console.log(`API call failed (${error.message}), falling back to config layers`);
                this.loadGeoJSONLayers();
            });
    }

    /**
     * Create OpenLayers vector layer from MapLayer API data
     * @param {Object} mapLayer - MapLayer data from API
     * @param {number} index - Layer index for fallback styling
     */
    createVectorLayerFromMapLayer(mapLayer, index) {
        const layerFeatures = mapLayer.layer_features;

        if (!layerFeatures || layerFeatures.type !== 'FeatureCollection') {
            if (this.config.verbose) console.log(`Invalid FeatureCollection for layer ${mapLayer.layer_name}`);
            return;
        }

        // Create vector source with the FeatureCollection data
        const source = new VectorSource({
            format: new GeoJSON(),
        });

        // Store layer metadata for styling
        source.fcName = layerFeatures.name || mapLayer.layer_name;
        source.layerSlug = mapLayer.layer_slug;
        source.mapLayerConfig = mapLayer.config || {};

        if (this.config.verbose) console.log(`Layer ${mapLayer.layer_name} config:`, mapLayer.config);

        // Parse and add features
        let features;
        try {
            // Extract CRS from GeoJSON, fall back to EPSG:4326
            const dataCrs = this.extractCrsFromGeoJSON(layerFeatures);

            features = new GeoJSON().readFeatures(layerFeatures, {
                dataProjection: dataCrs,
                featureProjection: this.config.dest_proj
            });
            source.addFeatures(features);

            if (this.config.verbose) console.log(`Added ${features.length} features for layer ${mapLayer.layer_name} (CRS: ${dataCrs})`);
        } catch (error) {
            console.error(`Error parsing features for layer ${mapLayer.layer_name}: ${error.message || error}`);
            return;
        }

        // Create vector layer with z-order aware styling
        const layer = new VectorLayer({
            source: source,
            minZoom: source.mapLayerConfig.min_zoom || 11,
            maxZoom: source.mapLayerConfig.max_zoom || 14,
            style: (feature) => {
                if (this.config.verbose) console.log(`Styling feature for layer ${mapLayer.layer_name}:`, feature);
                return this.mapLayerStyleFunction(feature, source, index);
            },
            declutter: true,
            // Store z-order for reference
            zIndex: mapLayer.z_order
        });

        // Set the z-index to control rendering order
        layer.setZIndex(mapLayer.z_order);

        // add the layer to the map object
        this.map.addLayer(layer);

        if (this.config.verbose) console.log(`Created layer ${mapLayer.layer_name} with z-order ${mapLayer.z_order}, features: ${features.length}, zoom: ${source.mapLayerConfig.min_zoom}-${source.mapLayerConfig.max_zoom}`);
    }

    /**
     * Style function for map layers loaded from API
     * @param {ol.Feature} feature - The feature to style
     * @param {ol.source.Vector} source - The vector source with layer config
     * @param {number} index - Layer index for fallback styling
     * @returns {ol.style.Style|Array<ol.style.Style>} Style(s) for the feature
     */
    mapLayerStyleFunction(feature, source, index) {
        if (this.config.verbose) console.log('mapLayerStyleFunction called with:', { feature, source, index });

        const geomType = feature.getGeometry()?.getType();
        const fcName = source.fcName || 'unknown';
        const layerConfig = source.mapLayerConfig || {};
        const layer_colormap = ['#ffffd4','#fed98e','#fe9929','#cc4c02'];

        if (this.config.verbose) console.log('Style config:', { geomType, fcName, layerConfig });

        // Use config or fallback to default colors
        const defaultColor = layerConfig.stroke_color || layer_colormap[index % layer_colormap.length] || '#3399CC';

        // If no geometry, return empty style
        if (!geomType) {
            return new Style({});
        }

        // For Point features
        if (geomType === 'Point') {
            const labelText = this.getFeatureLabel(feature, layerConfig);

            const pointStyle = new Style({
                image: new CircleStyle({
                    radius: layerConfig.point_radius || 4,
                    fill: new Fill({
                        color: layerConfig.point_color || defaultColor
                    }),
                    stroke: new Stroke({
                        color: '#FFFFFF33',
                        width: 2
                    })
                }),
                text: labelText ? new Text({
                    text: labelText,
                    font: `${layerConfig.font_style || ''} ${layerConfig.font_size || '9px'} ${layerConfig.font_face || 'Arial, Helvetica, sans-serif'}`,
                    fill: new Fill({
                        color: layerConfig.font_color || '#000000'
                    }),
                    stroke: new Stroke({
                        color: layerConfig.font_stroke_color || '#FFFFFF33',
                        width: layerConfig.font_stroke_width || 3
                    }),
                    offsetX: layerConfig.text_offset?.[0] || 0,
                    offsetY: layerConfig.text_offset?.[1] || -15,
                    textAlign: layerConfig.text_align || 'center',
                    textBaseline: 'middle'
                }) : null
            });

            if (this.config.verbose) console.log(pointStyle);

            return pointStyle;
        }

        // For LineString features
        else if (geomType === 'LineString' || geomType === 'MultiLineString') {
            return new Style({
                stroke: new Stroke({
                    color: layerConfig.stroke_color || defaultColor,
                    width: layerConfig.line_width || 1.5,
                    lineDash: layerConfig.line_dash || [5, 2, 2, 2]
                })
            });
        }

        // For Polygon features
        else if (geomType === 'Polygon' || geomType === 'MultiPolygon') {
            return new Style({
                fill: new Fill({
                    color: layerConfig.fill_color || 'rgba(0, 0, 0, 0.1)'
                }),
                stroke: new Stroke({
                    color: layerConfig.stroke_color || defaultColor,
                    width: layerConfig.line_width || 1.5,
                    lineDash: layerConfig.line_dash || null
                })
            });
        }

        // Default style for other geometry types
        return new Style({
            fill: new Fill({
                color: 'rgba(0, 0, 0, 0)'
            }),
            stroke: new Stroke({
                color: defaultColor,
                width: 2
            })
        });
    }

    /**
     * Load GeoJSON layers from configuration (fallback method)
     */
    loadGeoJSONLayers() {
        const layer_colormap = ['#ffffd4','#fed98e','#fe9929','#cc4c02'];

        let layers = this.getConfig('layers',[]);

        if (layers.length>0) {
            if (this.config.verbose) console.log(layers);
            layers.forEach((lyr, index) => {
                if (this.config.verbose) console.log(lyr);

                // Create vector source with custom loader to extract FeatureCollection name
                const source = new VectorSource({
                    format: new GeoJSON(),
                    loader: (extent, resolution, projection, success, failure) => {
                        fetch(this.json_url + lyr.name)
                            .then(response => response.json())
                            .then(data => {
                                // Store the FeatureCollection name for styling
                                source.fcName = data.name;

                                // Extract CRS from GeoJSON, fall back to EPSG:4326
                                const dataCrs = this.extractCrsFromGeoJSON(data);

                                // Parse and add features
                                const features = new GeoJSON().readFeatures(data, {
                                    dataProjection: dataCrs,
                                    featureProjection: this.config.dest_proj
                                });
                                source.addFeatures(features);
                                if (this.config.verbose) console.log(`Loaded GeoJSON layer ${lyr.name} with CRS: ${dataCrs}`);
                                success(features);
                            })
                            .catch(error => {
                                failure();
                                console.error("Error loading GeoJSON:", error);
                            });
                    }
                });

                // Create vector layer with custom style function
                const layer = new VectorLayer({
                    source: source,
                    minZoom: lyr?.min_zoom || 0,
                    maxZoom: lyr?.max_zoom || 99,
                    style: (feature) => this.geojsonStyleFunction(feature, source, lyr, index),
                    declutter: true
                });

                // add the layer to the map object
                this.map.addLayer(layer);

            });
        }
    }

    /**
     * Style function for GeoJSON features
     * @param {ol.Feature} feature - The feature to style
     * @param {ol.source.Vector} source - The vector source
     * @param {Object} layerConfig - Layer configuration from config.layers
     * @param {number} index - Layer index for default color selection
     * @returns {ol.style.Style|Array<ol.style.Style>} Style(s) for the feature
     */
    geojsonStyleFunction(feature, source, layerConfig, index) {
        const geomType = feature.getGeometry()?.getType();
        const fcName = source.fcName || 'unknown';
        const layer_colormap = ['#ffffd4','#fed98e','#fe9929','#cc4c02'];
        const defaultColor = layerConfig.stroke_color || layer_colormap[index] || '#3399CC';

        // If no geometry, return empty style
        if (!geomType) {
            return new Style({});
        }

        // Create base style object
        const baseStyle = {
            fill: new Fill({
                color: layerConfig.fill_color || 'rgba(0, 0, 0, 0)'
            }),
            stroke: new Stroke({
                color: defaultColor,
                width: layerConfig.stroke_width || 2
            })
        };

        // For Point features
        if (geomType === 'Point') {
            // Get label text using configured property
            const labelText = this.getFeatureLabel(feature, layerConfig);

            // Customize point style based on FeatureCollection name
            let pointStyle;
            let textAlign = 'center';
            let textOffset = [0, -15]; // Default text offset
            let fontColor = '#000000'
            let fontFace = 'Arial, sans-serif';
            let fontSize = '12px';
            let fontStyle = '';
            let pointColor = defaultColor;
            let pointRadius = 5;

            // Customize based on feature collection name
            if (fcName === 'sw_bend_landmarks') {
                pointColor = '#FF5733';
                pointRadius = 6;
                fontSize = '12px';
                textOffset = [0, -20];
            } else if (fcName.includes('trail')) {
                pointColor = '#33A1FF';
                pointRadius = 4;
                fontSize = '11px';
            } else if (fcName.includes('point')) {
                pointColor = '#33FF57';
                pointRadius = 5;
            }

            // Apply any custom style from layer config if provided
            if (layerConfig.point_color) pointColor = layerConfig.point_color;
            if (layerConfig.point_radius) pointRadius = layerConfig.point_radius;
            if (layerConfig.text_align) textAlign = layerConfig.text_align;
            if (layerConfig.text_offset) textOffset = layerConfig.text_offset;
            if (layerConfig.font_color) fontColor = layerConfig.font_color;
            if (layerConfig.font_face) fontFace = layerConfig.font_face;
            if (layerConfig.font_size) fontSize = layerConfig.font_size;
            if (layerConfig.font_style) fontStyle = layerConfig.font_style;

            // Create the point style
            pointStyle = new Style({
                image: new CircleStyle({
                    radius: pointRadius,
                    fill: new Fill({
                        color: pointColor
                    }),
                    stroke: new Stroke({
                        color: '#FFFFFF',
                        width: 2
                    })
                }),
                // Add text if label exists
                text: labelText ? new Text({
                    text: labelText,
                    font: `${fontStyle} ${fontSize} ${fontFace}`,
                    fill: new Fill({
                        color: fontColor
                    }),
                    stroke: new Stroke({
                        color: '#FFFFFF',
                        width: 3
                    }),
                    offsetX: textOffset[0],
                    offsetY: textOffset[1],
                    textAlign: `${textAlign}`,
                    textBaseline: 'middle'
                }) : null
            });

            return pointStyle;
        }

        // For LineString features
        else if (geomType === 'LineString' || geomType === 'MultiLineString') {
            return new Style({
                stroke: new Stroke({
                    color: defaultColor,
                    width: layerConfig.stroke_width || 2,
                    lineDash: layerConfig.line_dash || null
                })
            });
        }

        // For Polygon features
        else if (geomType === 'Polygon' || geomType === 'MultiPolygon') {
            return new Style({
                fill: new Fill({
                    color: layerConfig.fill_color || 'rgba(0, 0, 0, 0.1)'
                }),
                stroke: new Stroke({
                    color: defaultColor,
                    width: layerConfig.stroke_width || 2
                })
            });
        }

        // Default style for other geometry types
        return new Style(baseStyle);
    }

    /**
     * Create map boundary
     */
    createMapBoundary() {
        this.extent = transformExtent(this.config.extent, this.config.src_proj, this.config.dest_proj);
        this.boundary = transformExtent(this.config.boundary, this.config.src_proj, this.config.dest_proj);

        const box_coords = [
            [this.extent[0], this.extent[1]], [this.extent[0], this.extent[3]],
            [this.extent[2], this.extent[3]], [this.extent[2], this.extent[1]],
            [this.extent[0], this.extent[1]]
        ];

        const vectorSource = new VectorSource();
        vectorSource.addFeature(new Feature(new LineString(box_coords)));

        this.study_area_layer = new VectorLayer({
            source: vectorSource,
            style: new Style({
                stroke: new Stroke({
                    color: '#EF535099',
                    width: 4
                })
            }),
            zIndex: 1100  // Study area boundary renders on top of everything
        });
    }

    /**
     * Initialize map view
     */
    initializeMapView() {
        this.viewport = document.getElementById('map');

        let startZoom = Math.max(this.getMinZoom(),
                                 getUrlParam('zoom') || this.config.initial_zoom);
        if (startZoom > this.config.max_zoom) {
            startZoom = this.config.max_zoom;
            if (this.config.verbose) console.log("warning: initial zoom cannot be greater than max zoom.");
        }

        const startCenter = getUrlParam('lonlat')?.split(',').map(
            item => Number(item.trim()));

        let mapCenter;

        if (startCenter!==undefined &&
            startCenter.length==2 &&
            startCenter[0]>=-180 && startCenter[0]<=180 &&
            startCenter[1]>=-90 && startCenter[1]<=90) {

            mapCenter = transform(startCenter,
                                  this.config.src_proj,
                                  this.config.dest_proj);
        }

        else {
            mapCenter = transform(this.config.map_center,
                                  this.config.src_proj,
                                  this.config.dest_proj);
        }

        this.view = new View({
            center: mapCenter,
            minZoom: this.getMinZoom(),
            zoom: startZoom,
            maxZoom: this.config.max_zoom,
            extent: this.boundary
        });

        window.addEventListener('resize', () => {
            const minZoom = this.getMinZoom();
            if (minZoom !== this.view.getMinZoom()) {
                if (this.config.verbose) console.log(`resizing: min zoom = ${minZoom}`);
                this.view.setMinZoom(minZoom);
            }

            if (this.config.verbose) console.log(`resize: minZoom = ${minZoom}`);
        });
    }

    /**
     * Initialize map controls
     */
    initializeControls() {
        this.overviewMapControl = new OverviewMap({
            layers: [this.overview_layer],
            className: 'ol-overviewmap ol-custom-overviewmap',
            label: '«',
            collapseLabel: '»',
            view: new View({
                maxZoom: this.getMinZoom(),
                minZoom: this.getMinZoom(),
                extent: this.boundary,
                projection: this.config.dest_proj
            }),
            collapsed: !this.config.show_overview,
            collapsible: true
        });
    }

    /**
     * Create the map
     */
    createMap() {

        this.map = new Map({
            target: document.getElementById('map'),
            interactions: defaultInteractions({altShiftDragRotate: false, pinchRotate: false}),
            layers: [
                ...this.baselayers,
                this.stored_vector_layer,
                this.points_vector,
                this.study_area_layer
            ],
            controls: defaultControls({attribution: true}).extend([
                this.overviewMapControl,
                this.createScaleControl()
            ]),
            view: this.view
        });

        // Initialize popup overlay
        this.initializePopup();
    }

    /**
     * Initialize popup components
     */
    initializePopup() {
        this.container = document.getElementById('popup');
        this.content = document.getElementById('popup-content');
        this.closer = document.getElementById('popup-closer');

        this.popup = new Overlay({
            element: this.container,
            autoPan: true
        });

        this.map.addOverlay(this.popup);
    }

    /**
     * Setup map interactions
     */
    setupInteractions() {
        // Draw interaction
        this.draw_point = new Draw({
            type: 'Point',
            style: this.getPointerStyle.bind(this)
        });

        this.draw_point.on('drawend', this.handleDrawEnd.bind(this));

        // Hover interaction
        this.hover = new Select({
            condition: pointerMove,
            layers: [this.points_vector]
        });

        this.hover.on('select', event => {
            if (event.selected.length > 0) {
                if (this.config.verbose) console.log('point detected');
                this.draw_point.setActive(false);
            } else {
                this.draw_point.setActive(true);
            }
        });

        // Click select interaction
        this.clickSelect = new Select({
            condition: click,
            layers: [this.points_vector]
        });

        this.clickSelect.on('select', this.handleClickSelect.bind(this));

        // Add interactions to map
        this.map.addInteraction(this.clickSelect);
        this.map.addInteraction(this.draw_point);
        this.map.addInteraction(this.hover);
    }

    /**
     * Setup event listeners
     */
    setupEventListeners() {
        // Map events
        this.map.on('moveend', this.onMoveEnd.bind(this));

        // Mouse cursor change over features
        const mapViewport = this.map.getViewport();
        mapViewport.addEventListener('mousemove', e => {
            const pixel = this.map.getEventPixel(e);
            const hit = this.map.forEachFeatureAtPixel(pixel, () => true);
            mapViewport.style.cursor = hit ? 'context-menu' : '';
        });

        // ** start ** permalink management
        // keep URL updated with permalink
        let shouldUpdate = true;
        const view = this.map.getView();
        const updatePermalink = function () {
            if (!shouldUpdate) {
                // do not update the URL when the view was changed in the 'popstate' handler
                shouldUpdate = true;
                return;
            }

            const center = view.getCenter();
            const hash =
                  '#map=' +
                  view.getZoom().toFixed(2) +
                  '/' +
                  center[0].toFixed(2) +
                  '/' +
                  center[1].toFixed(2) +
                  '/' +
                  view.getRotation();
            const state = {
                zoom: view.getZoom(),
                center: view.getCenter(),
                rotation: view.getRotation(),
            };
            window.history.pushState(state, 'map', hash);
        };

        this.map.on('moveend', updatePermalink);

        // restore the view state when navigating through the history, see
        // https://developer.mozilla.org/en-US/docs/Web/API/WindowEventHandlers/onpopstate
        window.addEventListener('popstate', function (event) {
            if (event.state === null) {
                return;
            }
            this.map.getView().setCenter(event.state.center);
            this.map.getView().setZoom(event.state.zoom);
            this.map.getView().setRotation(event.state.rotation);
            shouldUpdate = false;
        });
        // ** end ** permalink management
        
        // Global keydown events
        document.addEventListener('keydown', event => {
            if (event.key === 'Escape') {
                this.closePopup();
                return false;
            }
            if (event.key === 'T') {
                this.tour();
                return false;
            }
        }, { passive: true });

        // Set project ID from form if available
        const projectIdInput = document.getElementById("projectid");
        if (projectIdInput) {
            projectIdInput.value = this.projectid;
        }
    }

    /**
     * Update UI elements with configuration
     */
    updateUIElements() {

        // these are/are embedded in the status line
        const mapStatus = document.getElementById('map_status2');
        const mapTitle = document.getElementById('map_title');
        const mapInfo = document.getElementById('map_info');

        // these are embedded in the help popup
        const siteDescription = document.getElementById('site_description');
        const sitePurpose = document.getElementById('site_purpose');

        // hide the whole status line if specified
        if (mapStatus) {
            if (this.config.show_status===false) {
                mapStatus.style.display = 'none';
            } else {
                mapStatus.style.display = 'block';

                // update the status line
                if (mapTitle && this.config.show_description)
                    mapTitle.textContent = this.config.site_description;
                if (mapInfo)
                    mapInfo.textContent = this.getCursorText();
            }
        }

        // add context to the help popup
        if (siteDescription)
            siteDescription.textContent = this.config.site_description;
        if (sitePurpose)
            sitePurpose.textContent = this.config.site_purpose;
    }

    /**
     * Handle draw end event
     * @param {Object} event - The draw end event
     */
    handleDrawEnd(event) {
        const coordinate = event.feature.getGeometry().getCoordinates();

        if (!this.isValidProjID(this.projectid)) return;

        // Check if editing is enabled for this coordinate
        if (this.editingEnabled(coordinate) === false) return;

        // Check for existing features at this location
        const features = this.points_source.getFeaturesAtCoordinate(coordinate);
        if (features.length > 0) {
            if (this.config.verbose) console.log('draw_point.on: point detected, exiting draw function');
            return;
        }

        // Don't allow point creation if zoomed out too far
        if (this.getScale() < this.config.min_px_km) {
            if (this.config.verbose) console.log('draw_point.on: zoomed out too far to accurately draw points');
            return;
        }

        // Change icon size based on zoom level
        const radius = this.getRadius();

        // Create new circle feature and update properties
        const feature = new Feature(new Circle(coordinate, radius * this.scl_const));

        // Set feature properties
        feature.setProperties({
            'id': -1,
            'description': '',
            'radius': radius,
            'projectid': this.projectid,
            'status': 0,
            'label': 'Saving...',
            'resolution': getPointResolution(
                this.config.dest_proj,
                this.map.getView().getResolution(),
                coordinate,
                'm'
            )
        });

        feature.setStyle(this.mapMarkerStyleFunction.bind(this));

        // Add feature to source
        this.points_source.addFeature(feature);

        // Close any existing popup
        this.popup.setPosition(undefined);

        // Update selected feature
        this.selectedFeature = feature;

        // Show edit popup if enabled
        if (this.config.edit_worktype === true) {
            this.pointEditPopup(coordinate);
        }

        // Post point to server
        this.createPoint(feature);

        this.countPoints();
    }

    /**
     * Handle click select event
     * @param {Object} evt - The click select event
     */
    handleClickSelect(evt) {
        if (this.config.verbose) console.log(
            evt.target.getFeatures().getLength() +
            ' selected features (last operation selected ' +
            evt.selected.length +
            ' and deselected ' +
            evt.deselected.length +
            ' features)'
        );

        if (evt.selected.length > 0) {
            if (this.config.verbose) console.log("clickSelect calling pointEdit");
            this.pointEdit(evt.selected[0]);
        }
    }

    /**
     * Handle move end event
     * @param {Object} evt - The move end event
     */
    onMoveEnd(evt) {
        const mapInfo = document.getElementById('map_info');
        if (mapInfo) {

            let cursortext = this.getCursorText();

            if (cursortext.length>0 && this.editingEnabled()) {
                mapInfo.textContent = `| ${cursortext}`;
            } else {
                mapInfo.textContent = '';
            }
        }
    }

    /**
     * Style function for map markers
     * @param {Feature} feature - The feature to style
     * @returns {Array<Style>} The styles to apply to the feature
     */
    mapMarkerStyleFunction(feature) {
        let txt = feature.get('label');
        if (txt.length === 0) txt = "";
        if (txt.length > 25) txt = txt.substring(0, 25) + "...";

        // Project ID should only be a positive integer
        const projectid = Number(feature.get('projectid'));

        const colormap = this.getConfig('point_colormap');

        // default is 8 unique colors; rotate through all available
        let colorid = (projectid-1) % colormap.length;

        // Set transparency for stroke (edge) and fill
        let stroke_color = colormap[colorid] + 'cc';
        let fill_color = colormap[colorid] + '4d';

        return [
            new Style({
                fill: new Fill({
                    color: fill_color
                }),
                stroke: new Stroke({
                    color: stroke_color,
                    width: 3
                }),
                text: new Text({
                    font: '12px Calibri,sans-serif',
                    fill: new Fill({color: stroke_color}),
                    stroke: new Stroke({color: '#ffffff', width: 3}),
                    text: txt
                })
            })
        ];
    }

    /**
     * Style function for drawing cursor
     * @param {Feature} feature - The feature being drawn
     * @returns {Style} The style to apply to the drawing cursor
     */
    getPointerStyle(feature) {

        // used for both status line and pointer annotation
        const cursor_txt = this.getCursorText();
        const scl = this.getScale();

        // Update map info text, like circle diameter and zoom level, if enabled
        const mapInfo = document.getElementById('map_info');
        if (mapInfo) {
            if (this.editingEnabled(feature.coordinate)) {
                mapInfo.textContent = `| ${cursor_txt}`;
            } else {
                mapInfo.textContent = '';
            }
        }

        const pointerStyle = new Style();

        // Default text style: black with white outline for contrast
        const cursorText = new Text({
            font: '12px Calibri,sans-serif',
            fill: new Fill({color: '#000'}),
            stroke: new Stroke({color: '#ffffff', width: 3}),
            text: cursor_txt,
            offsetY: 65
        });

        // Only allow entry for a valid projectid
        if (!this.isValidProjID(this.projectid)) {
            cursorText.setText('');
        }
        // Show a warning if too zoomed out
        else if (scl < this.config.min_px_km) {
            cursorText.setText('⚠️ Zoom-in closer to mark locations');
            cursorText.setFill(new Fill({color: 'red'}));
            cursorText.setOffsetY(-10);
        }
        // Everything is OK
        else {
            // Show a context-sensitive mouse pointer
            const colormap = this.getConfig('point_colormap');
            const colorid = (this.projectid-1) % colormap.length;
            const color = colormap[colorid];

            // Create dynamic cursor icon using the colormap color
            const cursorIcon = this.createCursorIcon(color);

            pointerStyle.setImage(new Icon({
                anchor: [0.5, 0.5],
                size: [107, 107],
                offset: [0, 0],
                opacity: 1,
                scale: this.getMapScaleFactor(),
                img: cursorIcon,
                imgSize: [107, 107]
            }));
        }

        // Update pointer style to use cursorText determined above
        pointerStyle.setText(cursorText);

        return pointerStyle;
    }


    /**
     * Create XYZ tile layer
     * @param {string} baseurl - The base URL for the tile service
     * @param {string} servicename - The service name
     * @param {Object} options - Layer options (minZoom, maxZoom, opacity, zIndex)
     * @returns {TileLayer} The created tile layer
     */
    makeXYZLayer(baseurl, servicename, options={"minZoom": 0,
                                                "maxZoom": 99,
                                                "opacity": 1.0,
                                                "zIndex": 0}) {

        return new TileLayer({
            source: new XYZ({
                url: `${baseurl}${servicename}/MapServer/tile/{z}/{y}/{x}`,
                attributions: this.attributions
            }),
            minZoom: options.minZoom,
            maxZoom: options.maxZoom,
            opacity: options.opacity !== undefined ? options.opacity : 1.0,
            zIndex: options.zIndex !== undefined ? options.zIndex : 0
        });
    }

    /**
     * Load basemaps from API for the current MapConfig
     * @returns {Promise<Array<TileLayer>>} Promise resolving to array of basemap layers
     */
    loadBasemapsFromAPI() {
        const mapconfigid = window.context?.mapconfigid;

        if (!mapconfigid) {
            if (this.config.verbose) console.log('No mapconfig ID found, using default basemaps');
            return Promise.resolve(this.getDefaultBasemaps());
        }

        // Fetch basemaps from the REST API
        const basemapsUrl = `/api/basemaps/?mapconfig=${mapconfigid}`;

        return fetch(basemapsUrl, {
            method: 'GET',
            headers: {
                'Accept': 'application/json',
                'Content-Type': 'application/json',
            },
            credentials: 'same-origin'
        })
            .then(response => {
                if (!response.ok) {
                    throw new Error(`HTTP error! status: ${response.status}`);
                }
                return response.json();
            })
            .then(data => {
                if (this.config.verbose) console.log(`Retrieved ${data.length} basemaps from API:`, data);

                // If no basemaps configured, use defaults
                if (data.length === 0) {
                    if (this.config.verbose) console.log('No basemaps configured for this MapConfig, using defaults');
                    return this.getDefaultBasemaps();
                }

                // Sort basemaps by z_index to ensure proper rendering order
                const sortedBasemaps = data.sort((a, b) => a.z_index - b.z_index);

                // Create OpenLayers tile layers for each basemap
                const basemapLayers = sortedBasemaps.map(basemap => {
                    if (this.config.verbose) console.log(`Creating basemap layer: ${basemap.basemap_name} (z=${basemap.z_index})`);

                    return new TileLayer({
                        source: new XYZ({
                            url: basemap.basemap_tile_url,
                            attributions: basemap.basemap_attribution || this.attributions
                        }),
                        minZoom: basemap.min_zoom || 0,
                        maxZoom: basemap.max_zoom || 23,
                        opacity: basemap.opacity !== undefined ? basemap.opacity : 1.0,
                        zIndex: basemap.z_index
                    });
                });

                return basemapLayers;
            })
            .catch(error => {
                console.error(`Error loading basemaps from API: ${error.message || error}`);
                if (this.config.verbose) console.log(`API call failed (${error.message}), falling back to default basemaps`);
                return this.getDefaultBasemaps();
            });
    }

    /**
     * Get default hardcoded basemaps (fallback)
     * @returns {Array<TileLayer>} Array of default basemap layers
     */
    getDefaultBasemaps() {
        const tile_xyz = 'MapServer/tile/{z}/{y}/{x}';
        const agol_url = 'https://server.arcgisonline.com/ArcGIS/rest/services/';
        const natlmap_url = 'https://basemap.nationalmap.gov/arcgis/rest/services/';

        return [
            this.makeXYZLayer(agol_url, 'NatGeo_World_Map', {
                "minZoom": 0,
                "maxZoom": 14,
                "opacity": 1.0,
                "zIndex": 0
            }),
            this.makeXYZLayer(natlmap_url, 'USGSTopo', {
                "minZoom": 13.9,
                "maxZoom": 99,
                "opacity": 1.0,
                "zIndex": 1
            })
        ];
    }

    /**
     * Get minimum zoom level based on viewport width
     * @returns {number} The minimum zoom level
     */
    getMinZoom() {
        const width = this.viewport.clientWidth;
        return Math.ceil(Math.LOG2E * Math.log(width / 256));
    }

    /**
     * Create scale control with appropriate units
     * @returns {ScaleLine} The scale control
     */
    createScaleControl() {
        const units = this.config.display_units === 'm' ? 'metric' : 'us';

        return new ScaleLine({
            units: units
        });
    }

    /**
     * Get data URL based on response and project IDs
     * @returns {string} The API URL with query parameters
     */
    getDataUrl() {
        let url_txt = this.config.api_url;

        if (this.responseid != null) {
            url_txt += '?responseid=' + this.responseid;

            if (this.isValidProjID(this.projectid)) {
                url_txt += '&projectid=' + this.projectid;
            }
        }

        return url_txt;
    }

    /**
     * Check if a project ID is valid (positive integer)
     * @param {string|number} projid - The project ID to validate
     * @returns {boolean} True if the project ID is valid
     */
    isValidProjID(projid) {
        let int_projectid;

        if (typeof projid === 'string') int_projectid = this.strToInt(projid);
        if (typeof projid === 'number') int_projectid = projid;

        return (Number.isInteger(int_projectid) && int_projectid > 0);
    }

    /**
     * Check if editing is enabled for a coordinate
     * @param {Array<number>} [coordinate] - The coordinate to check
     * @returns {boolean} True if editing is enabled
     */
    editingEnabled(coordinate) {
        // Don't allow editing within 2km of the edge to prevent undeleteable points
        const bias = 2000;
        if (coordinate != null) {
            if (coordinate[0] < this.boundary[0] + bias ||
                coordinate[1] < this.boundary[1] + bias ||
                coordinate[0] > this.boundary[2] - bias ||
                coordinate[1] > this.boundary[3] - bias) {
                return false;
            }
        }

        return (this.responseid != null && this.isValidProjID(this.projectid));
    }

    /**
     * Count points from each project type and update UI
     */
    countPoints() {
        let counts = {p1: 0, p2: 0, p3: 0, p4: 0};

        this.points_source.getFeatures().forEach(feature => {
            const pid = feature.get('projectid');
            if (pid >= 1 && pid <= 4) {
                counts[`p${pid}`]++;
            }
        });

        // Update UI elements
        const responseIdEl = document.getElementById("responseid");
        const pointCountEl = document.getElementById("pointcount");

        if (responseIdEl) responseIdEl.textContent = this.responseid;
        if (pointCountEl) pointCountEl.textContent =
            `p1 = ${counts.p1} p2 = ${counts.p2} p3 = ${counts.p3} p4 = ${counts.p4}`;

        if (this.config.verbose) console.log(`p1 = ${counts.p1} p2 = ${counts.p2} p3 = ${counts.p3} p4 = ${counts.p4}`);
    }

    /**
     * Hide features not matching current project ID
     */
    hideFeatures() {
        this.points_source.getFeatures().forEach(feature => {
            if (this.isValidProjID(this.projectid) && feature.get('projectid') != this.projectid) {
                feature.setStyle(new Style({}));
            } else {
                feature.setStyle(this.mapMarkerStyleFunction.bind(this));
            }
        });
    }

    /**
     * Create a dynamic cursor icon with the specified color
     * @param {string} color - Hex color code (e.g., '#e41a1c')
     * @returns {HTMLCanvasElement} Canvas element with the cursor icon
     */
    createCursorIcon(color) {
        const size = 107;
        const canvas = document.createElement('canvas');
        canvas.width = size;
        canvas.height = size;
        const ctx = canvas.getContext('2d');

        const centerX = size / 2;
        const centerY = size / 2;
        const radius = 42; // Main circle radius

        // Draw inner fill (lighter/more transparent)
        ctx.beginPath();
        ctx.arc(centerX, centerY, radius, 0, 2 * Math.PI);
        ctx.fillStyle = color + '4d'; // Add alpha for fill (30% opacity)
        ctx.fill();

        // Draw outer stroke (darker border)
        ctx.beginPath();
        ctx.arc(centerX, centerY, radius, 0, 2 * Math.PI);
        ctx.strokeStyle = color + 'cc'; // Add alpha for stroke (80% opacity)
        ctx.lineWidth = 2;
        ctx.stroke();

        // Draw center dot for precision
        ctx.beginPath();
        ctx.arc(centerX, centerY, 2, 0, 2 * Math.PI);
        ctx.fillStyle = '#00000099'; // 60% opacity
        ctx.fill();

        return canvas;
    }

    /**
     * Get map scale factor for cursor resizing
     * @returns {number} The scale factor to apply
     */
    getMapScaleFactor() {
        const res = this.map.getView().getResolution();
        const scl_minres = this.config.min_diameter / 100; // m/px
        const scl_maxres = this.config.max_diameter / 100; // m/px

        if (res <= scl_maxres && res >= scl_minres) {
            return this.scl_const;
        } else if (res > scl_maxres) { // Zooming out past the limit
            return (scl_maxres / res) * this.scl_const;
        } else if (res < scl_minres) { // Zooming in past the limit
            return (scl_minres / res) * this.scl_const;
        }
    }

    /**
     * Get radius in meters based on zoom level
     * @returns {number} The radius in meters
     */
    getRadius() {
        const res = this.map.getView().getResolution();

        // Basic radius calculation for the cursor circle based on map resolution
        let rad = 50 * res;

        // Set limits for radius
        const min_rad = this.config.min_diameter / 2;
        const max_rad = this.config.max_diameter / 2;

        if (rad > max_rad) {
            rad = max_rad;
        } else if (rad < min_rad) {
            rad = min_rad;
        }

        if (this.config.verbose) console.log(`getRadius: res=${roundX(res, 2)} rad=${roundX(rad, 2)} scl=${roundX(this.getScale(), 2)}`);

        return rad;
    }

    /**
     * Calculate current map scale in px/km
     * @returns {number} The map scale in pixels per kilometer
     */
    getScale() {
        const res = this.map.getView().getResolution();
        return (1 / res * 1000); // px/km
    }

    /**
     * Get text for cursor display
     * @returns {string} Formatted text describing cursor size
     */
    getCursorText() {
        // Distance in map units = meters
        const diameter = 2 * this.getRadius();
        let cursor_txt='';

        // Display values in meters or feet based on config
        if (this.config.show_diameter) {
            cursor_txt += 'circle ⌀: ';
            if (this.config.display_units === 'm') {
                if (diameter > 10000) {
                    cursor_txt += `${roundX(diameter / 1000)} km`;
                } else if (diameter > 1000) {
                    cursor_txt += `${roundX(diameter / 1000, 1)} km`;
                } else {
                    cursor_txt += `${roundX(diameter, -2)} m`;
                }
            } else {
                if (diameter > 8000) {
                    cursor_txt += `${roundX(diameter / this.meters_per_mile)} mi`;
                } else if (diameter > 800) {
                    cursor_txt += `${roundX(diameter / this.meters_per_mile, 1)} mi`;
                } else {
                    cursor_txt += `${roundX(diameter / this.meters_per_mile * 5280, -2)} ft`;
                }
            }
        }

        if (this.config.show_zoom)
            cursor_txt += ` | z: ${this.view.getZoom().toFixed(1)}`;

        return cursor_txt;
    }

    /**
     * Safely convert string to integer
     * @param {string} val - The string to convert
     * @returns {number} The integer value or NaN if invalid
     */
    strToInt(val) {
        if (val == null || val === '') return NaN;
        if (!Number.isInteger(Number(val))) return NaN;
        return Number(val);
    }

    /**
     * Converts a Circle geometry to a Point (for the feature center)
     * @param {Feature} feature - The feature with Circle geometry
     * @returns {Point} The point at the center of the circle
     */
    circleToPoint(feature) {
        const extent = feature.getGeometry().getExtent();
        const centroid = [
            extent[0] + (extent[2] - extent[0]) / 2,
            extent[1] + (extent[3] - extent[1]) / 2
        ];
        return new Point(centroid);
    }

    /**
     * Convert feature to WKT
     * @param {Feature} feature - The feature to convert
     * @returns {string} WKT representation of the feature
     */
    featureToWKT(feature) {
        feature.set('geometry', feature.getGeometry());
        const format = new WKT();
        return format.writeFeature(feature);
    }

    /**
     * Serializes a feature for sending to the API
     * @param {Feature} feature - The OpenLayers feature to serialize
     * @returns {string} JSON string representation of the feature for the API
     */
    serializeFeature(feature) {
        // Convert circle to point
        const pt = this.circleToPoint(feature);
        const coords = transform(pt.getCoordinates(), this.config.dest_proj, this.config.src_proj);

        /** @type {Object} */
        const data = {};

        if (feature.get('id') !== -1) data.id = feature.get('id');
        data.mapconfig = window.context?.mapconfigid || '';
        data.label = feature.get('label');
        data.description = feature.get('description');
        data.radius = feature.get('radius');
        data.responseid = this.responseid;
        data.projectid = feature.get('projectid');
        data.ipaddress = window.context?.ip_address || '';
        data.status = feature.get('status');
        data.resolution = feature.get('resolution');
        data.geom = {"type": "Point", "coordinates": coords};

        if (data.description === '') data.description = 'new point';
        data.timestamp = encodeURIComponent(Date.now().toString());

        return JSON.stringify(data);
    }

    /**
     * Creates a new point on the server
     * @param {Feature} feature - The feature to send to the server
     * @returns {Promise<void>} Promise that resolves when the point is created
     */
    createPoint(feature) {
        const csrftoken = this.getCookie('csrftoken');
        const json = this.serializeFeature(feature);

        return fetch(this.config.api_url, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-Csrftoken': csrftoken
            },
            body: json
        })
        .then(response => response.json())
        .then(responseData => {
            if (this.config.verbose) console.log('createPoint: ' + JSON.stringify(responseData));
            feature.setProperties({'status': 1});
            feature.set('label', '');
            feature.setProperties({'id': parseInt(responseData.id)});
            this.selectedFeature = feature;
            if (this.config.verbose) console.log(`createPoint: New point added with ID ${responseData.id}`);
            this.countPoints();
        })
        .catch(error => {
            if (this.config.verbose) console.log("Problem saving the data: " + json);
        });
    }

    /**
     * Update a point on the server
     * @param {Feature} feature - The feature to update
     * @returns {Promise<void>} Promise that resolves when the point is updated
     */
    updateData(feature) {
        const csrftoken = this.getCookie('csrftoken');

        // Copy new description value back to finalize
        feature.setProperties({'description': feature.get('description_new')});

        const json = this.serializeFeature(feature);

        return fetch(`${this.config.api_url}${feature.get('id')}/`, {
            method: 'PATCH',
            headers: {
                'Content-Type': 'application/json',
                'X-Csrftoken': csrftoken
            },
            body: json
        })
        .then(response => response.json())
        .then(responseData => {
            if (this.config.verbose) console.log(JSON.stringify(responseData));
            this.selectedFeature = feature;
            if (this.config.verbose) console.log(`updateData: Point ID ${responseData.id} updated.`);
        })
        .catch(error => {
            if (this.config.verbose) console.log("updateData: Problem saving the data: " + json);
        });
    }

    /**
     * Delete a point from the server
     * @param {Feature} feature - The feature to delete
     * @returns {Promise<void>} Promise that resolves when the point is deleted
     */
    deleteData(feature) {
        const csrftoken = this.getCookie('csrftoken');
        const id = feature.get('id');

        return fetch(`${this.config.api_url}${id}/?responseid=${this.responseid}`, {
            method: 'DELETE',
            headers: {
                'X-Csrftoken': csrftoken
            }
        })
        .then(response => {
            if (response.ok) {
                if (this.config.verbose)
                    console.log(`deleteData: Point ${id} deleted from response ${this.responseid}`);
                this.points_source.removeFeature(feature);
                this.countPoints();
            } else {
                if (this.config.verbose)
                    console.log(`deleteData: HTTP error ${response.status}`);
            }
        })
        .catch(error => {
            if (this.config.verbose) console.log(`deleteData: Problem deleting the point ${id}`);
        });
    }

    /**
     * Get CSRF cookie
     * @param {string} name - The name of the cookie
     * @returns {string|null} The cookie value or null if not found
     */
    getCookie(name) {
        const value = `; ${document.cookie}`;
        const parts = value.split(`; ${name}=`);
        if (parts.length === 2) return parts.pop().split(';').shift();
        return null;
    }

    /**
     * Point edit handler
     * @param {Feature} feature - The feature to edit
     */
    pointEdit(feature) {
        // Check for object existence
        if (feature !== undefined) {
            const extent = feature.getGeometry().getExtent();
            const pt_coords = [
                extent[0] + (extent[2] - extent[0]) / 2,
                extent[1] + (extent[3] - extent[1]) / 2
            ];
            const id = feature.get('id');

            feature.setStyle(this.mapMarkerStyleFunction.bind(this));
            if (this.config.verbose) console.log('pointEdit: point selected');

            // Set the global so form callbacks get a reference
            this.selectedFeature = feature;

            // Only show edit popup if enabled
            if (this.config.edit_worktype === true) {
                this.pointEditPopup(pt_coords);
            } else {
                this.pointDeletePopup(pt_coords);
            }

            if (this.config.verbose) console.log(`pointEdit: feature selected at ${pt_coords}, \nextent: ${extent} \nid: ${id}`);
        }
    }

    /**
     * Show delete popup
     * @param {Array<number>} coords - The coordinates to position the popup
     */
    pointDeletePopup(coords) {
        this.content.innerHTML = `
        <div class="arrow_box button_box">
            <button id="cancel" title="Cancel" class="btn btn-xs btn-secondary" style="position:absolute; left:20px;">Cancel</button>
            <button id="delete" title="Delete work location" class="btn btn-xs btn-danger" style="position:absolute; right:20px;">Delete</button>
        </div>`;

        // Add event listeners
        document.getElementById("cancel").addEventListener('click', () => this.closePopup());
        document.getElementById("delete").addEventListener('click', () => this.deleteSelected());

        this.popup.setPosition(coords);
    }

    /**
     * Show edit popup
     * @param {Array<number>} coords - The coordinates to position the popup
     */
    pointEditPopup(coords) {
        // Don't allow point EDIT or DELETION if zoomed out too far
        if (this.getScale() < this.config.min_px_km / 4) {
            if (this.config.verbose) console.log('zoomed out too far to accurately edit points');
            return;
        }

        this.content.innerHTML = `
        <div class="arrow_box work_completed">
            <p style="margin-bottom:10px; padding-bottom:5px; font-size:14px; text-align:center; border-bottom:dashed 1px; line-height:1.25em">
                <b>WORK COMPLETED</b><br>Mark all that apply
            </p>
            <a href="#" id="popup-closer"></a>
            <div id="worktypes">
                <label><input type="checkbox" name="response" value="1"> Fire response</label>
                <label><input type="checkbox" name="rxfire" value="1"> Prescribed fire</label>
                <label><input type="checkbox" name="mech" value="1"> Mechanical fuel reduction</label>
                <label><input type="checkbox" name="defense" value="1"> Defensible space</label>
                <label><input type="checkbox" name="harden" value="1"> Structure hardening</label>
                <label><input type="checkbox" name="natres" value="1"> Natural resource planning</label>
                <label><input type="checkbox" name="dev" value="1"> Development planning</label>
                <label><input type="checkbox" name="outreach" value="1"> Resident/landowner outreach</label>
                <label><input type="checkbox" name="relationships" value="1"> Building relationships</label>
                <label><input type="checkbox" name="other" value="1"> Other</label>
            </div>
            <button id="edit-save" title="Save work location information" class="btn btn-xs btn-success" style="position:absolute; left:20px;">Save</button>
            <button id="edit-delete" title="Delete work location" class="btn btn-xs btn-danger" style="position:absolute; right:20px;">Delete</button>
        </div>`;

        // Add event listeners
        document.getElementById("edit-save").addEventListener('click', () => this.updateFeature());
        document.getElementById("edit-delete").addEventListener('click', () => this.deleteSelected());

        this.popup.setPosition(coords);

        this.attachCheckboxHandlers();
    }

    /**
     * Close popup
     * @returns {boolean} False to prevent default behavior
     */
    closePopup() {
        this.popup.setPosition(undefined);

        this.clickSelect.getFeatures().clear();
        this.selectedFeature = null;
        if (this.closer) this.closer.blur();
        this.countPoints();
        return false;
    }

    /**
     * Update feature from form
     * @returns {boolean} False to prevent default behavior
     */
    updateFeature() {
        if (this.selectedFeature != null) {
            this.updateData(this.selectedFeature);
        }
        this.closePopup();
        return false;
    }

    /**
     * Delete selected feature
     * @returns {boolean} False to prevent default behavior
     */
    deleteSelected() {
        this.deleteData(this.selectedFeature);

        // Cleanup tasks
        this.hover.getFeatures().clear();
        this.draw_point.setActive(true);

        if (this.config.verbose) console.log('deleteSelected: Point deleted');
        this.closePopup();
        return false;
    }

    /**
     * Attach checkbox handlers for work types
     */
    attachCheckboxHandlers() {
        const el = document.getElementById('worktypes');
        const works = el.getElementsByTagName('input');
        const worktypes = this.selectedFeature.get('description').split(',');

        if (this.config.verbose) console.log(`attachCheckboxHandlers: work types = ${JSON.stringify(worktypes)}`);

        // Setup onclick interaction for each checkbox
        for (let i = 0; i < works.length; i++) {
            if (works[i].type === 'checkbox') {
                works[i].addEventListener('click', this.updateWorkList.bind(this));
                // Check if saved worktypes includes checkbox
                if (worktypes.includes(works[i].name)) {
                    works[i].checked = true;
                }
            }
        }
    }

    /**
     * Update work list from checkboxes
     * @param {Event} e - The click event
     */
    updateWorkList(e) {
        const el = document.getElementById('worktypes');
        const works = el.getElementsByTagName('input');
        let out = '';

        // Build comma-separated list of checked work types
        for (let i = 0; i < works.length; i++) {
            if (works[i].type === 'checkbox' && works[i].checked === true) {
                out = out + works[i].name + ",";
            }
        }
        this.selectedFeature.setProperties({'description_new': out});
    }

    /**
     * Animate fly to location
     * @param {Array<number>} location - The location to fly to
     * @param {Function} done - Callback when animation is done
     */
    flyTo(location, done) {
        const duration = 2000;
        const zoom = this.view.getZoom();
        let parts = 2;
        let called = false;

        function callback(complete) {
            --parts;
            if (called) {
                return;
            }
            if (parts === 0 || !complete) {
                called = true;
                done(complete);
            }
        }

        this.view.animate(
            {
                center: location,
                duration: duration,
            },
            callback
        );

        this.view.animate(
            {
                zoom: zoom - 1,
                duration: duration / 2,
            },
            {
                zoom: zoom,
                duration: duration / 2,
            },
            callback
        );
    }

    /**
     * Start tour of preset points
     */
    tour() {
        const locations = this.points_source.getFeatures();
        let index = -1;
        let coords = null;

        const next = (more) => {
            if (more) {
                ++index;
                if (index < locations.length) {
                    const delay = index === 0 ? 0 : 750;
                    setTimeout(() => {
                        coords = locations[index].getGeometry().getExtent();
                        if (this.config.verbose) console.log(`flying to ${coords}`);
                        this.flyTo(coords, next);
                    }, delay);
                }
            }
        };

        next(true);
    }

    /**
     * Update style of all features
     */
    updateCartoStyle() {
        let features = this.points_source.getFeatures();

        // Remove features with status 0
        for (let i = 0; i < features.length; i++) {
            if (features[i].get('status') === 0) {
                this.points_source.removeFeature(features[i]);
            }
        }

        // Load previously uploaded data from server
        this.stored_vector_source.forEachFeature(feature => {
            const coordinate = feature.getGeometry().getCoordinates();
            const radius = Number(feature.get('radius'));

            // Adjust displayed radius using scale constant
            const feature2 = new Feature(new Circle(coordinate, radius * this.scl_const));

            feature2.setProperties({
                'id': feature.get('id'),
                'description': feature.get('description'),
                'radius': radius,
                'projectid': feature.get('projectid'),
                'status': 1,  // 1==on the server
                'label': '.'
            });

            feature2.set('label', '');
            feature2.setStyle(this.mapMarkerStyleFunction.bind(this));

            this.points_source.addFeature(feature2);
        });

        // Show only current projectid
        this.hideFeatures();
        this.countPoints();
    }
}

/**
 * Get URL parameters
 * @param {string} name - The name of the parameter to get
 * @returns {string|null} The parameter value or null if not found
 */
export function getUrlParam(name) {
    const urlParams = new URLSearchParams(window.location.search);
    return urlParams.get(name);
}

/**
 * Rounds a number to the specified number of digits
 * @param {number} num - The number to round
 * @param {number} [digits=0] - The number of decimal places
 * @returns {number} The rounded number
 */
export function roundX(num, digits = 0) {
	const factor = Math.pow(10, digits);
	return Math.round(num * factor) / factor;
}

/**
 * Initializes a new map instance
 * @param {string} configElementId - The ID of the element containing the map configuration
 * @returns {MapManager} A new MapManager instance
 */
export function initializeMap(configElementId) {
    return new MapManager(configElementId);
}
