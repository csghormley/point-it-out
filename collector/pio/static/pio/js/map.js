/* see the template for map config
const config = {
	map_center: [-121.3, 44.1],
	extent: [-122, 43.4, -120.385, 44.824],
	boundary: [-123, 41.9, -119.385, 46.324],
	src_proj: 'EPSG:4326', // wgs84
	dest_proj: 'EPSG:3857', // web mercator
	api_url: '/api/surveypoints/',
	zoom: 4,
	max_zoom: 16,
	min_zoom: 4,
	max_res: 170,
	edit_worktype: false,
	verbose: true
};
*/
const config = JSON.parse(document.getElementById('mapconfig-data').textContent);

// check for missing default config values
// the only required values are map_center, boundary, and extent
if (config.api_url == undefined) config.api_url="/api/surveypoints/";
if (config.dest_proj == undefined) config.dest_proj="EPSG:3857"; // web mercator
if (config.edit_worktype == undefined) config.edit_worktype=false;
if (config.max_res == undefined) config.max_res=800; // absolute limit of map scale for data entry
if (config.initial_zoom == undefined) config.initial_zoom=4;
if (config.max_zoom == undefined) config.max_zoom=16;
if (config.src_proj == undefined) config.src_proj="EPSG:4326"; // wgs84
if (config.show_overview == undefined) config.show_overview=true;
if (config.verbose == undefined) config.verbose=false;
if (config.max_diameter == undefined) config.max_diameter=16093.4; // meters; 10mi
if (config.min_diameter == undefined) config.min_diameter=804.67; // meters; 0.5mi

if (config.site_description == undefined) config.site_description="region near the map center";
if (config.site_purpose == undefined) config.site_purpose="wildfire resilience and vulnerability";

// multiplier makes displayed vectors appear the right size on basemap
// adjusts for the size of the cursor image in use
const scl_const = 1.234567;
const meters_per_mile = 1609.34;

// update the display with config info
$('#site_purpose').text(config.site_purpose);
$('#site_description').text(config.site_description);
$('#map_title').text(config.site_description);

let csrftoken = null;
//let cursor_txt = 'Work location';
const img_url = $('#static_img_base').text();
const json_url = $('#static_json_base').text();

// ---------------------------------------------------------------------
// DEFINE MAP TILE LAYERS -----------------------
// ---------------------------------------------------------------------

const tile_xyz = 'MapServer/tile/{z}/{y}/{x}';

// AGOL layers
const agol_url = 'https://server.arcgisonline.com/ArcGIS/rest/services/';
const layer_base_topo = makexyzlayer(agol_url, 'World_Topo_Map');
const layer_base_natgeo = makexyzlayer(agol_url, 'NatGeo_World_Map');
const layer_base_natgeo_ov = makexyzlayer(agol_url, 'NatGeo_World_Map');
const layer_base_terrain = makexyzlayer(agol_url, 'World_Terrain_Base');
const layer_base_reference = makexyzlayer(agol_url, 'Reference/World_Reference_Overlay');

// national map layers
const natlmap_url = 'https://basemap.nationalmap.gov/arcgis/rest/services/';
const layer_base_usgstopo = makexyzlayer(natlmap_url, 'USGSTopo');
const layer_base_usgstopo_ov = makexyzlayer(natlmap_url, 'USGSTopo');
const layer_base_usgsimagerytopo = makexyzlayer(natlmap_url, 'USGSImageryTopo');

const layer_wms_fireshed = new ol.layer.Tile({
	source: new ol.source.TileWMS({url: 
		'https://apps.fs.usda.gov/arcx/services/EDW/EDW_FireshedRegistry_01/MapServer/WMSServer'
	})});

const layer_osm = new ol.layer.Tile({
    source: new ol.source.OSM(),
});

// trying to display firesheds
const fsVectorLayer = new ol.layer.Vector({
    background: '#1a2b39',
    source: new ol.source.Vector({
//        url: 'https://services1.arcgis.com/gGHDlz6USftL5Pau/arcgis/rest/services/Fireshed_Registry_Data_(v3)/FeatureServer/3',
        //url: 'https://services1.arcgis.com/gGHDlz6USftL5Pau/ArcGIS/rest/services/Fireshed_Registry_Data_(v3)/FeatureServer/1/query?where=1%3D1&f=pgeojson',
		url: 'https://services1.arcgis.com/gGHDlz6USftL5Pau/ArcGIS/rest/services/Fireshed_Registry_Data_(v3)/FeatureServer/0/query?where=1%3D1&f=pgeojson',
        format: new ol.format.EsriJSON(),
    }),
    style: {
        'fill-color': ['string', ['get', 'COLOR'], '#eee'],
    },
});

// polygons:	https://services1.arcgis.com/gGHDlz6USftL5Pau/arcgis/rest/services/Fireshed_Registry_Data_(v3)/FeatureServer
// https://apps.fs.usda.gov/arcx/services/EDW/EDW_FireshedRegistry_01/MapServer/WMSServer?request=GetCapabilities&service=WMS

function makexyzlayer(baseurl, servicename) {
    return new ol.layer.Tile({ source: new ol.source.XYZ({url: `${baseurl}${servicename}/${tile_xyz}`})	});
}

// convenience function to enable or disable all logging
function verbose_log(logmsg, override=false) {
	if(config.verbose || override) console.log(logmsg);
}

/*
// Set base layer
const baseLayer = new ol.layer.Tile({
    source: new ol.source.OSM(),
});

// Setup transportation layer (unused)
const transportation = new ol.layer.Tile({
  source: new ol.source.TileArcGISRest({
    url: 'https://services.nationalmap.gov/arcgis/rest/services/transportation/MapServer',
	params: {
		'LAYERS': 'show:25,26,27'
	}
  }),
  maxResolution: 100,
	opacity: 1,
  visible: true,
});
*/

// GET request sets the context for server interaction
let responseid = $.urlParam('id');
let projectid = StrToInt($.urlParam('proj_id'));

$("#projectid").val(projectid);

verbose_log(`survey id = ${responseid}\nproject id = ${projectid}`);

// filter by ID if it exists, otherwise return all records
// this is governed by internal server logic, depends on login state
function getDataUrl() {

	let url_txt = config.api_url;

	if(responseid != null) {

		url_txt += '?responseid=' + responseid;

		if (isValidProjID(projectid)) {
			url_txt += '&projectid=' + projectid;
		}
	}

	return url_txt;
}

// a valid project ID is a positive integer
// consider: https://validatejs.org/#validators-numericality
function isValidProjID(projid) {

	if (typeof projid === 'string') int_projectid = StrToInt(projid);
	if (typeof projid === 'number') int_projectid = projid;
	return (Number.isInteger(int_projectid) && int_projectid > 0);
}

// enable editing if both response id and project id are specified
function editingEnabled(coordinate) {

	// don't allow editing within 2km of the edge
	// hack to prevent undeleteable points
	let bias = 2000;
	if (coordinate!=null) {
		if ((coordinate[0] < boundary[0]+bias || coordinate[1] < boundary[1]+bias
		    || coordinate[0] > boundary[2]-bias || coordinate[1] > boundary[3]-bias)) {
            
			return false;
		}
	}

	return (responseid!=null && isValidProjID(projectid));
};

// count points from each project type
// may not be useful atm
function countPoints() {

	let p1 = 0;
	let p2 = 0;
	let p3 = 0;
	let p4 = 0;

	points_source.getFeatures().forEach(function(f) {
		if(f.get('projectid') == 1) { p1 += 1; }
		if(f.get('projectid') == 2) { p2 += 1; }
		if(f.get('projectid') == 3) { p3 += 1; }
		if(f.get('projectid') == 4) { p4 += 1; }
	});

	$("#responseid").text(responseid)
	$("#pointcount").text(`p1 = ${p1} p2 = ${p2} p3 = ${p3} p4 = ${p4}`)

	verbose_log(`p1 = ${p1} p2 = ${p2} p3 = ${p3} p4 = ${p4}`);
};

// hide the features not matching current project id
function hideFeatures() {

	points_source.getFeatures().forEach(function(f) {
		if (isValidProjID(projectid) && f.get('projectid') != projectid){
			f.setStyle(new ol.style.Style({}));
		} else {
			f.setStyle(mapMarkerStyleFunction);
		};
	});
}

// animate tour of preset points, for training simulation
// code adapted from OpenLayers examples
function flyTo(location, done) {
	const duration = 2000;
	const zoom = view.getZoom();
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
	view.animate(
	  {
		center: location,
		duration: duration,
	  },
	  callback,
	);
	view.animate(
	  {
		zoom: zoom - 1,
		duration: duration / 2,
	  },
	  {
		zoom: zoom,
		duration: duration / 2,
	  },
	  callback,
	);
  }

function tour() {
	const locations = points_source.getFeatures();
	let index = -1;
	let coords = null;
	function next(more) {
	  if (more) {
		++index;
		if (index < locations.length) {
		  const delay = index === 0 ? 0 : 750;
		  setTimeout(function () {
			coords = locations[index].getGeometry().getExtent();
			verbose_log(`flying to ${coords}`);
			flyTo(coords, next);
		  }, delay);
		}
	  }
	}
	next(true);
  }

// show all features regardless of data type/project id
// TODO this function isn't called from anywhere
function showFeatures() {
	points_source.getFeatures().forEach(function(f) {
		f.setStyle(mapMarkerStyleFunction);
	});
}

// ---------------------------------------------------------------------
// DEFINE SOURCE VECTOR OBJECT -----------------------------------------
// ---------------------------------------------------------------------

// library of points
// define the source separately so we can manipulate it later
let points_source = new ol.source.Vector();
let points_vector = new ol.layer.Vector({
	source: points_source,
	updateWhileAnimating: true,
    updateWhileInteracting: true,
    style: mapMarkerStyleFunction
});

// download data from server
// define the source separately so we can manipulate it later
let stored_vector_source = new ol.source.Vector({
	format: new ol.format.GeoJSON(),
	url: getDataUrl()
});

let stored_vector_layer = new ol.layer.Vector({
	source: stored_vector_source,
	updateWhileAnimating: true,
	updateWhileInteracting: true,
	style: new ol.style.Style({
	})
});

// if config specifies a set of geojson layers, load them in
// [{"name": "<filename>.geojson", "stroke_color": "#0000d080", "stroke_width": 2}]
let layer_colormap = ['#ffffd4','#fed98e','#fe9929','#cc4c02'];

let overlay_geojson = [];
if (config.layers!=undefined) {
	config.layers.forEach(function(lyr, index) {
		let layer = new ol.layer.Vector({
			source: new ol.source.Vector({
				format: new ol.format.GeoJSON(),
				url: json_url + lyr.name
			}),
			style: new ol.style.Style({
				fill: new ol.style.Fill({
					color: 'rgba(0, 0, 0, 0)'  // Default fill color (black with transparency)
				  }),
				  stroke: new ol.style.Stroke({
					color: lyr.stroke_color || layer_colormap[index],
					width: lyr.stroke_width || 2
				  })

				})
		});
		// add to the array
		overlay_geojson.push(layer);
	});
}  

// run this function on any change to stored_vector_source
// transfer features from points_source to points_vector?
function updateCartoStyle() {

	stored_vector_source.addEventListener("change", updateCartoStyle);

	let features = points_source.getFeatures()

	for(let i=0; i < features.length; i++) {
		if(features[i].getProperties()['status'] == 0){
			points_source.removeFeature(features[i]);
		}
	}

	// Load previously uploaded data from server and transfer those features into the points_vector layer.
	stored_vector_source.forEachFeature(function(feature){
		let coordinate = feature.getGeometry().getCoordinates()
		let radius = Number(feature.get('radius'))

		// adjust displayed radius using scale constant
		let feature2 = new ol.Feature(new ol.geom.Circle(coordinate, radius*scl_const));

		feature2.setProperties({
			'id': feature.get('id'),
			'description': feature.get('description'),
			'radius': radius,
			'projectid': feature.get('projectid'),
			'status':1,  // 1==on the server
			'label':'.'
		})

		feature2.set('label','')
		feature2.setStyle(mapMarkerStyleFunction);

		points_source.addFeature(feature2);
	})

	// show only current projectid (do we still need this?)
	hideFeatures();
	countPoints();
}

// ---------------------------------------------------------------------
// CREATE BOX AROUND STUDY AREA -----------------------
// ---------------------------------------------------------------------

// 'extent' is shown as a box on the map; 'boundary' bounds the area shown by the map
const extent = ol.proj.transformExtent(config.extent, config.src_proj, config.dest_proj);
const boundary = ol.proj.transformExtent(config.boundary, config.src_proj, config.dest_proj);

const box_coords = [
	[extent[0], extent[1]], [extent[0], extent[3]],
	[extent[2], extent[3]], [extent[2], extent[1]],
	[extent[0], extent[1]]
];

// draw a box around the study extent, and embed it in a vector layer
let vectorSource = new ol.source.Vector();
vectorSource.addFeature(new ol.Feature(new ol.geom.LineString(box_coords)));

const study_area_layer = new ol.layer.Vector({
  source: vectorSource,
  style: new ol.style.Style({
    stroke: new ol.style.Stroke({
        color: '#EF535099',
        width: 4
    }),
  })
});

// ------------------------------------------------------
// DEFINE MAP OBJECT -----------------------
// ------------------------------------------------------

const viewport = document.getElementById('map');

// allow for adjusting zoom level when window changes size
function getMinZoom() {
	const width = viewport.clientWidth;
	return Math.ceil(Math.LOG2E * Math.log(width / 256));
}
  
const initialZoom = Math.max(getMinZoom(), config.initial_zoom);
  
window.addEventListener('resize', function () {
	const minZoom = getMinZoom();
	if (minZoom !== view.getMinZoom()) {
		verbose_log('resizing: min zoom = ' + minZoom);
        view.setMinZoom(minZoom);
	}
});

// scale line
// units in [degrees, imperial, us, nautical, metric]
// type in [line, bar]
function scaleControl() {
	const bar = false;
	const units = 'us';
	const steps = 4;
	const show_text = false;
	const min_width = 140;

	if (bar === false) {
	  control = new ol.control.ScaleLine({
		units: units,
	  });
	} else {
	  control = new ol.control.ScaleLine({
		units: units,
		bar: true,
		steps: steps,
		text: show_text,
		minWidth: min_width,
	  });
	}
	return control;
}

// attribution
const attribution = new ol.control.Attribution({
	collapsible: false,
});

const defaultControls = ol.control.defaults.defaults;

// overview map
const overviewMapControl = new ol.control.OverviewMap({
    layers: [
		layer_base_natgeo_ov
    ],
	className: 'ol-overviewmap ol-custom-overviewmap',
	label:'«',
	collapseLabel:'»',
	view: new ol.View({
		maxZoom: getMinZoom(),
		minZoom: getMinZoom(),
		extent: boundary,
		projection: config.dest_proj
	}),
	collapsed: !config.show_overview,
	collapsible: true
});

// map object TODO attribution fix
const view = new ol.View({
	center: ol.proj.transform(config.map_center, config.src_proj, config.dest_proj),
	minZoom: getMinZoom(),
	zoom: initialZoom,
	maxZoom: config.max_zoom,
	extent: boundary
});

const map = new ol.Map({
	target: document.getElementById('map'),
	interactions: ol.interaction.defaults.defaults({altShiftDragRotate:false, pinchRotate:false}),
	layers: [
		layer_base_natgeo,
		stored_vector_layer,
		points_vector,
		study_area_layer
		],
	controls: defaultControls({attribution: true}).extend([attribution, overviewMapControl, scaleControl()]),
	view: view
});

// for any additional layers specified in the config, show them on top
overlay_geojson.forEach(function(layer) {
	map.addLayer(layer);
})

// initialize some screen elements
updateCartoStyle();
$('#map_info').text(`${getCursorText()}`);

// scale the size of the cursor when the map zooms past the min_res or max_res threshold
/*
How should this work?
In the middle range, the mouse cursor is "full size" or native size.
At the small end of resolution (largest map scale), the icon gets bigger as we continue to zoom in.
At the large end of resolution (smallest map scale), the icon gets smaller as we continue to zoom out.
*/
function getMapScaleFactor() {

	const res = map.getView().getResolution();
	const scl_minres = config.min_diameter / 100; // m/px == meters / 100px
	const scl_maxres = config.max_diameter / 100; // m/px == meters / 100px

	if (res <= scl_maxres && res >= scl_minres) {
		return scl_const;
	} else if (res > scl_maxres) { // zooming out past the limit
		return (scl_maxres / res) * scl_const; // e.g., 190/200 < 1
	} else if (res < scl_minres) { // zooming in past the limit
		return (scl_minres / res) * scl_const; // e.g., 10/8 > 1
	}
};

// calculate an estimated project radius for point based on zoom level, in METERS
// mouse cursor is ~100px across, radius is 50px. what is that in map units?
function getRadius() {

	const res = map.getView().getResolution();

	// basic radius calculation for the cursor circle based on map resolution
	// (and fixed scale correction factor for the size of the image used)
	// circle has a 50px radius
	let rad = 50 * res;

	// miles * meters/mi / pixels = m/px
	const max_rad = config.max_diameter/2;
	const min_rad = config.min_diameter/2;

	if (rad > max_rad) { // zooming out past the limit
        rad = max_rad;
	} else if (rad < min_rad) { // zooming in past the limit
		rad = min_rad;
	}

	verbose_log(`getRadius: res=${res} rad=${rad}`)

	return rad;
};

// ---------------------------------------------------------------------
// CREATE STYLES FOR DISPLAYING POINTS AND CURSOR ----------------------
// ---------------------------------------------------------------------

// visual style for placed points
function mapMarkerStyleFunction(feature) {

	let txt = feature.get('label');
	if (txt.length === 0) txt = "";
	if (txt.length > 25) txt = txt.substring(0, 25) + "...";

	// projectid should only be a positive integer
	const projectid = Number(feature.get('projectid'));

	// colorbrewer 8-class qualitative scheme
	// NOTE: if you change this, also change 'icon_url' generator code
	let colormap = ['#e41a1c','#377eb8','#4daf4a','#984ea3','#ff7f00','#ffff33','#a65628','#f781bf'];
	// 'accent' scheme might also work: ['#7fc97f','#beaed4','#fdc086','#ffff99','#386cb0','#f0027f','#bf5b17','#666666']
	// 'set1' scheme: ['#e41a1c','#377eb8','#4daf4a','#984ea3','#ff7f00','#ffff33','#a65628','#f781bf']
	// 'paired' scheme: ['#a6cee3','#1f78b4','#b2df8a','#33a02c','#fb9a99','#e31a1c','#fdbf6f','#ff7f00'];

	// we only have 8 unique colors. normally this should be plenty, but we want to fail gracefully
	// projectid = 1 gets color 0; projectid = 9 also gets color 0
	// IMPORTANT: use the same colors when generating PNGs for mouse cursor in drawStyleFunction
	let colorid = (projectid-1) % 8;

	// set transparency for stroke (edge) and fill
	let stroke_color = colormap[colorid] + 'cc';
	let fill_color = colormap[colorid] + '4d';

	return [
		new ol.style.Style({
				fill: new  ol.style.Fill({
					color: fill_color
				}),
				stroke: new ol.style.Stroke({
					color: stroke_color,
					width: 3
				}),
				text: new ol.style.Text({
					font: '12px Calibri,sans-serif',
					fill: new ol.style.Fill({color: stroke_color}),
					stroke: new ol.style.Stroke({color: '#ffffff', width: 3}),
					text: txt
				})
		})
	];
}

// helper function to retrieve context-sensitive cursor text
function getCursorText() {

	// distance in map units = meters
	let diameter = 2 * getRadius();
	let cursor_txt = 'circle dia: ~';

	// details: round to 10ths of a mile, then divide by 10 to get miles; or 100s of feet
	// round the diameter, not the radius, so we get odd and even results
	if(diameter > 8000){
		cursor_txt += String(round_x(diameter/meters_per_mile)) + " mi";
	} else if (diameter > 800) { // round to tenths
		cursor_txt += String(round_x(diameter/meters_per_mile, 1)) + " mi";
	} else { // round to hundreds of feet
		cursor_txt += String(round_x(diameter/meters_per_mile*5280,-2)) + " ft"
	};

	// enable for debugging
	// if (config.verbose) {
    //     cursor_txt += ` | ${round_x(diameter)}m`
	// 	cursor_txt += ` | ${round_x(map.getView().getResolution(),1)}m/px`
	// 	cursor_txt += ` | ${round_x(map.getView().getZoom(),1)}x`
	// }

	return cursor_txt;
}

// safely convert string to integer
// return NaN if null or empty string
function StrToInt(val) {
    if (val==null || val=='') return NaN;
	if (!Number.isInteger(Number(val))) return NaN;

	return Number(val);
}

// visual style for drawing highlight halo around mouse cursor
let drawStyleFunction = function (feature, resolution) {

	// resolution is in units per pixel
	let cursor_txt = getCursorText();

	// update the map info text on the fly
	// exploits a side effect of this function being called when the mouse moves
	if (editingEnabled(feature.coordinate)) {
        $('#map_info').text(`| ${cursor_txt}`);
    } else {
		$('#map_info').text('');
	}

	let point_style = new ol.style.Style();

	// default text style: black with white outline for contrast
	let style_text = new ol.style.Text({
		font: '12px Calibri,sans-serif',
		fill: new ol.style.Fill({color: '#000'}),
		stroke: new ol.style.Stroke({color: '#ffffff', width: 3}),
		text: cursor_txt,
		offsetY: 65
	});

	// only allow entry for a valid projectid and not zoomed out too far
	if (!isValidProjID(projectid)) { // i.e., project ID is either missing or non-integer

		// hide the text
		style_text.setText('');

	} else if (resolution >= config.max_res) { // i.e., too many meters per pixel

		// show an error message in red, just offset from the pointer
		style_text.setText('Zoom-in closer to mark locations');
		style_text.setFill(new ol.style.Fill({color: 'red'}),);
		style_text.setOffsetY(-10);

	} else { // everything is OK

		// show a context-sensitive mouse pointer
		let colorid = (projectid-1) % 8;
        let icon_url = `${img_url}circle_st1_${colorid}.png`;

		point_style.setImage(new ol.style.Icon({
			anchor: [0.5, 0.5],
			size: [107, 107],
			offset: [0, 0],
			opacity: 1,
			scale: getMapScaleFactor(),
			src: icon_url
		}));
	}

	// update point style to use style_text determined above
	point_style.setText(style_text);

	return point_style;
}

// -------------------------------------------
// ADD DRAW INTERACTION ----------------------
// -------------------------------------------

// detect map movement including pan or zoom to update status information
function onMoveEnd(evt) {

	if (editingEnabled()) {
        $('#map_info').text(`| ${getCursorText()}`);
    } else {
		$('#map_info').text('');
	}
}
  
map.on('moveend', onMoveEnd);

let selectedFeature = null;

// interaction object to hold drawn points
let draw_point = new ol.interaction.Draw({
	type: 'Point',
	style: drawStyleFunction
});

// on click: save attributes to feature object after being placed on the map
draw_point.on('drawend', function(event) {

	const coordinate = event.feature.getGeometry().getCoordinates();

	if (!isValidProjID(projectid)) { return; }

	// check to see if editing is enabled, including for this coordinate
	if (editingEnabled(coordinate)==false) { return; }

	features = points_source.getFeaturesAtCoordinate(coordinate);
	if (features.length > 0) {
		verbose_log('point detected, exiting draw function');

		// since this point already exists, edit
		pointEdit(features[0]);
		return;
	}

	// don't allow point creation if zoomed out too far
	// i.e. resolution in units per pixel has to be *lower* than max
	if (map.getView().getResolution() > config.max_res) {
		verbose_log('zoomed out too far to accurately draw points');
		return;
	}

  	// change icon size based on zoom level
	let radius = getRadius();

	// create new circle feature and update properties
	let feature = new ol.Feature(new ol.geom.Circle(coordinate, radius*scl_const));

	// prototype feature waiting for form to be filled out
	feature.setProperties({
		'id': -1,
		'description': '', // must be an empty string, not undefined
		'radius': radius,
		'projectid': projectid,
		'status': 0, // < upload status (0=not uploaded)
		'label': 'Saving...',
		'resolution': ol.proj.getPointResolution(config.dest_proj, map.getView().getResolution(), coordinate, 'm')
	})

	feature.setStyle(mapMarkerStyleFunction);

	// add the drawn feature to the collection
	// this does not post it to the server
	points_source.addFeature(feature);

	// close an existing popup, if any
	popup.setPosition(undefined);

	// assign this feature to the global object
	selectedFeature = feature;

	// only show edit popup if enabled
	if (config.edit_worktype===true) {
        pointEditPopup(coordinate);
	}

	// post this point to the server
	createPoint(feature);

	countPoints();

});

// ----------------------------------------------------------------
// HOVER INTERACTION PREVENTS DRAWING OVERLAPPING POINTS ----------
// ----------------------------------------------------------------

let hover = new ol.interaction.Select({
	condition: ol.events.condition.pointerMove,
	layers:[points_vector]  // layers to be hovered
});

// Turn off drawing when hovering over an existing feature;
hover.on('select', function(event) {
	  if(event.selected.length > 0){
	  	verbose_log('point detected');
	  	draw_point.setActive(false);
	  } else {
	  	draw_point.setActive(true);
	  }
});

// ------------------------------------
// ADD SELECT INTERACTION -------------
// ------------------------------------

let clickSelect = new ol.interaction.Select({
	condition: ol.events.condition.click,
	layers: [points_vector]
});

// add select interaction for selecting points
map.addInteraction(clickSelect);
map.addInteraction(draw_point);

clickSelect.on('select', function(evt) {

	verbose_log(evt.target.getFeatures().getLength() +
        ' selected features (last operation selected ' +
        evt.selected.length +
        ' and deselected ' +
        evt.deselected.length +
        ' features)');

	// pass the selected feature into edit logic
    pointEdit(evt.selected[0]);
});

function pointEdit(f) {

	// check for object existence
	if (f != undefined) {
		let extent = f.getGeometry().getExtent();
		function getCenterOfExtent(Extent){
			let X = Extent[0] + (Extent[2]-Extent[0])/2;
			let Y = Extent[1] + (Extent[3]-Extent[1])/2;
			return [X, Y];
		}
		let pt_coords = getCenterOfExtent(extent);
		let id = f.getProperties()['id'];

		f.setStyle(mapMarkerStyleFunction);
		verbose_log('point selected');

		// set the global so the form callbacks get a reference
		selectedFeature = f;

		// only show edit popup if enabled
		if (config.edit_worktype===true) {
            pointEditPopup(pt_coords);
        }
		else {
			pointDeletePopup(pt_coords);
		}

        verbose_log('feature selected', pt_coords, "extent:", extent, "id:", id, f.getProperties());
	}

}

// -------------------------------------------------------------
// CREATE POPUP BOX FOR RECORDING POINT DATA -------------------
// -------------------------------------------------------------

const container = document.getElementById('popup');
const content = document.getElementById('popup-content');
const closer = document.getElementById('popup-closer');

const popup = new ol.Overlay({
	element: container,
	autoPan: true
});
map.addOverlay(popup);

// Add a keydown handler to the document
// close the overlay on ESC
document.addEventListener('keydown', function(event) {
	// Check if ESC key was pressed
	if (event.key === 'Escape') {
        closePopup();
		return false;
	}
},
{ passive: true });

// show a tour on T
document.addEventListener('keydown', function(event) {
	// Check if "T" key was pressed
	if (event.key === 'T') {
        tour();
		return false;
	}
},
{ passive: true });

// popup form to delete a point
function pointDeletePopup(coords){

	content.innerHTML = `<div class="arrow_box button_box">
	<button id="cancel" title="Cancel" class="btn btn-xs btn-secondary" style="position:absolute; left:20px;">Cancel</button>
	<button id="delete" title="Delete work location" class="btn btn-xs btn-danger" style="position:absolute; right:20px;">Delete</button>
	</div>`

	// adding the button actions here means they don't run afoul of the content security policy for inline scripts!
	$("#cancel").on('click', function () { closePopup(); });
	$("#delete").on('click', function () { deleteSelected(); });
	popup.setPosition(coords);
};

// popup form to edit a point
function pointEditPopup(coords){

	// don't allow point EDIT or DELETION if zoomed out too far
	// i.e. resolution in units per pixel has to be *lower* than max
	if (map.getView().getResolution() > config.max_res * 4) {
		verbose_log('zoomed out too far to accurately edit points');
		return;
	}

	content.innerHTML = `<div class="arrow_box work_completed">
	<p style="margin-bottom:10px; padding-bottom:5px; font-size:14px; text-align:center; border-bottom:dashed 1px; line-height:1.25em"><b>WORK COMPLETED</b><br>Mark all that apply</p> 
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
	</div>`

	// adding the button actions here means they don't run afoul of the content security policy for inline scripts!
	$("#edit-save").on('click', function () { updateFeature(); });
	$("#edit-delete").on('click', function () { deleteSelected(); });

	popup.setPosition(coords);

	attachCheckboxHandlers();
};

// ------------------------------------------------------------------
// UPDATE WORK FIELD WHEN CHECK BOXES CLICKED ON/OFF ----------------
// ------------------------------------------------------------------

// call onload or in script segment below form
function attachCheckboxHandlers() {

    let el = document.getElementById('worktypes');
    let works = el.getElementsByTagName('input');
    let worktypes = selectedFeature.getProperties()['description'].split(',');

    verbose_log("work types:", worktypes);

    // setup onclick interaction for each checkbox.
    for (let i=0, len=works.length; i<len; i++) {
        if (works[i].type === 'checkbox' ) {
            works[i].onclick = updateWorkList;
            // check if saved worktypes includes checkbox
            if(worktypes.includes(works[i].name)) {
            	works[i].checked = true;
            }
        }
    }
}

// rebuild csv list of work types when clicking any checkbox
function updateWorkList(e) {

	let el = document.getElementById('worktypes');
    let works = el.getElementsByTagName('input');
    let out = '';

    // setup onclick interaction for each checkbox.
    for (let i=0, len=works.length; i<len; i++) {
        if (works[i].type === 'checkbox' && works[i].checked === true) {
            out = out + works[i].name + ","
        }
    }
    verbose_log(out);
    selectedFeature.setProperties({'description':out})
}


// change mouse cursor when cursor passes over marker
$(map.getViewport()).on('mousemove', function(e) {
  let pixel = map.getEventPixel(e.originalEvent);
  let hit = map.forEachFeatureAtPixel(pixel, function(feature, layer) {
    return true;
  });
  if (hit) {
    map.getTarget().style.cursor = 'context-menu';
  } else {
    map.getTarget().style.cursor = '';
  }
});

// ---------------------------------------------------------------
// SERVER FUNCTIONS FOR ADDING AND DELETING  ---------------------
// ---------------------------------------------------------------

// close the popup AND uninitialize associated variables
let closePopup = function(evt){

	popup.setPosition(undefined);
	
	clickSelect.getFeatures().clear();
	selectedFeature = null;
	closer.blur();
	countPoints();
	return false;

};

// save changes to the server and clean up the form
let updateFeature = function(evt){
	if(selectedFeature != null){
		updateData(selectedFeature);
	}
	closePopup();
	return false;
};

function deleteSelected() {
	deleteData(selectedFeature);

	// unique cleanup tasks not in closepopup
	// what do they do?
	hover.getFeatures().clear();
	draw_point.setActive(true);

	verbose_log('Point deleted');
	closePopup();
	return false;
}

function serializeFeature(f) {

	// in the browser we represent features as circles
	// in the database they are points with a radius
	// create a point and copy properties from the circle 
	// due to a limitation in openlayers/geojson
	let pt = circleToPoint(f);
	let coords = ol.proj.transform(pt.flatCoordinates, config.dest_proj, config.src_proj)

	let data = {};

	if (f.id!=-1) data.id = f.get('id');
	data.label = f.get('label');
	data.description = f.get('description');
	data.radius = f.get('radius');
	data.responseid = responseid;
	data.projectid = f.get('projectid');
	data.ipaddress = context.ip_address;
	data.status = f.get('status');
	data.resolution = f.get('resolution');
	data.geom = {"type": "Point", "coordinates": coords};

	if (data.description==='') data.description = 'new point';
	data.timestamp = encodeURIComponent(Date.now().toString());

    return(JSON.stringify(data));
}

function circleToPoint(f) {

	// convert circle to point
	const extent = f.getGeometry().getExtent();
	function getCenterOfExtent(Extent){
		let X = Extent[0] + (Extent[2]-Extent[0])/2;
		let Y = Extent[1] + (Extent[3]-Extent[1])/2;
		return [X, Y];
	}
	const centroid = getCenterOfExtent(extent);
	const pt = new ol.geom.Point(centroid);

	return pt;
};

// output WKT for a point
function pointToWKT(f) {

    f.set('geometry', f.getGeometry());
    let format = new ol.format.WKT()
    wkt = format.writeFeature(f);
    return(wkt);
};

// create single data points
function createPoint(f) {

	csrftoken = Cookies.get('csrftoken');
	let json = serializeFeature(f);

	// post data using JQuery
	$.ajax({
		type: 'POST',
		url: config.api_url,
		headers: {"X-Csrftoken": csrftoken},
		data: json,
		contentType: "application/json",
		dataType: 'json', // type of data expected from the server
		success: function (responseData, textStatus, jqXHR) {
			verbose_log(JSON.stringify(responseData));
			f.setProperties({'status': 1});
			f.set('label','')
			f.setProperties({'id': parseInt(responseData.id)});
			selectedFeature = f;
			verbose_log(`New point added with ID ${responseData.id}`);
			countPoints();
		},
		error: function (responseData, textStatus, errorThrown) {
			verbose_log("Problem saving the data: " + json);
		}
		});
}

// update single data points
function updateData(f) {

	csrftoken = Cookies.get('csrftoken');

	let json = serializeFeature(f);

	$.ajax({
		type: 'PATCH',
		url: config.api_url + f.get('id') + '/',
		headers: {"X-Csrftoken": csrftoken},
		data: json,
		contentType: 'application/json',
		success: function (responseData, textStatus, jqXHR) {
			verbose_log(JSON.stringify(responseData));
			selectedFeature = f;
			verbose_log('Point ID ' + responseData.id + ' updated.');
		},
		error: function (responseData, textStatus, errorThrown) {
			verbose_log("Problem saving the data: " + json);
		}
	  });
}

// delete single data points
function deleteData(f) {

	csrftoken = Cookies.get('csrftoken');
	const id = f.getProperties()['id']

    $.ajax({
      type: 'DELETE',
      url: `${config.api_url}${id}/?responseid=${responseid}`,
      crossDomain: false,
	  headers: {"X-Csrftoken": csrftoken},
      dataType: 'json', // type of data expected from the server
      success: function (responseData, textStatus, jqXHR) {
			        verbose_log(`Point ${id} deleted from response ${responseid}`);
			        points_source.removeFeature(f);
					countPoints();
      },
      error: function (responseData, textStatus, errorThrown) {
        verbose_log(`Problem deleting the point ${id}`);
      }
    });

}

