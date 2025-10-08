// ol-wrapper.js
// A more robust wrapper for OpenLayers when loaded from a CDN

// Make sure OpenLayers is loaded
if (typeof ol === 'undefined') {
    throw new Error('OpenLayers is not loaded. Make sure to include the OpenLayers script before importing this module.');
  }
  
  // Export the entire ol object as the default export
  export default ol;
  
  // Also export individual components for convenience
  export const Map = ol.Map;
  export const View = ol.View;
  export const Feature = ol.Feature;
  export const Overlay = ol.Overlay;
  
  // Formats
  export const GeoJSON = ol.format.GeoJSON;
  export const WKT = ol.format.WKT;
  
  // Geometry
  export const Point = ol.geom.Point;
  export const Circle = ol.geom.Circle;
  export const LineString = ol.geom.LineString;
  
  // Layers
  export const TileLayer = ol.layer.Tile;
  export const VectorLayer = ol.layer.Vector;
  
  // Sources
  export const OSM = ol.source.OSM;
  export const XYZ = ol.source.XYZ;
  export const TileWMS = ol.source.TileWMS;
  export const VectorSource = ol.source.Vector;
  
  // Styles
  export const Style = ol.style.Style;
  export const Fill = ol.style.Fill;
  export const Stroke = ol.style.Stroke;
  export const Text = ol.style.Text;
  export const Icon = ol.style.Icon;
  export const CircleStyle = ol.style.Circle;
  
  // Interactions
  export const defaultInteractions = ol.interaction.defaults.defaults;
  export const Select = ol.interaction.Select;
  export const Draw = ol.interaction.Draw;
  
  // Controls
  export const defaultControls = ol.control.defaults.defaults;
  export const Attribution = ol.control.Attribution;
  export const OverviewMap = ol.control.OverviewMap;
  export const ScaleLine = ol.control.ScaleLine;
  
  // Projections
  export const fromLonLat = ol.proj.fromLonLat;
  export const transform = ol.proj.transform;
  export const transformExtent = ol.proj.transformExtent;
  export const getPointResolution = ol.proj.getPointResolution;
  
  // Events
  export const click = ol.events.condition.click;
  export const pointerMove = ol.events.condition.pointerMove;
