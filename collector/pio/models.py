from django.core.exceptions import ValidationError
from django.contrib.gis.db import models
from djgeojson.fields import GeometryCollectionField

# supply a default configuration dict for MapConfig.config
# see also map.js for internal defaults this would override,
# and all configuration settings
def mapconfig_default():
    return dict(
        map_center = [-121.3, 44.1],
        extent = [-122, 43.4, -120.385, 44.824],
        boundary = [-123, 41.9, -119.385, 46.324],
        src_proj = 'EPSG:4326', # wgs84
        dest_proj = 'EPSG:3857', # web mercator
        api_url = '/api/surveypoints/',
        zoom = 4,
        max_zoom = 16,
        min_zoom = 4,
        max_res = 170,
        edit_worktype = True,
        verbose = False
    )

# supply a default configuration dict for MapLayer.config
# see also map.js for internal defaults this would override,
# and all configuration settings
def maplayer_default():
    return dict(
        max_zoom = 14,
        min_zoom = 11,
        point_color = "#555555",
        point_radius = 4,
        line_width = 1.5,
        stroke_color = "#b09592cc",
        line_dash = [
            5,
            2,
            2,
            2
        ],
        font_size = "9px",
        font_style = "italic",
        font_face = "Arial, Helvetica, sans-serif",
        label_format = "{name}"  # Format string with {property} placeholders
    )

# allow shared layers between MapConfigs
class FeatureLayer(models.Model):
    name = models.CharField(max_length=50)
    slug = models.SlugField()
    geojson = models.JSONField()

    def __str__(self):
        return self.name

    def clean(self):
        """Validate that the JSON is a proper FeatureCollection"""
        if not isinstance(self.geojson, dict):
            raise ValidationError("Must be a valid JSON object")

        if self.geojson.get('type') != 'FeatureCollection':
            raise ValidationError("Must be a FeatureCollection")

        if 'features' not in self.geojson:
            raise ValidationError("FeatureCollection must have features array")

    class Meta:
        verbose_name_plural = "Feature Layers"

# specify a FeatureLayer and display parameters
class MapLayer(models.Model):
    mapconfig = models.ForeignKey("MapConfig", on_delete=models.CASCADE)
    layer = models.ForeignKey("FeatureLayer", on_delete=models.CASCADE)
    config = models.JSONField(default=maplayer_default)
    z_order = models.IntegerField(default=1,
                                  help_text="Lower values render first (bottom)")

    class Meta:
        unique_together = [('mapconfig', 'layer'), ('mapconfig', 'z_order')]
        ordering = ['z_order']

    def clean(self):

        # Only validate if both mapconfig and layer are set
        if self.mapconfig_id and self.layer_id:
            # Ensure z_order is unique within the map
            existing = MapLayer.objects.filter(
                mapconfig=self.mapconfig,
                z_order=self.z_order
            )

            # Exclude self if this is an update
            if self.pk:
                existing = existing.exclude(pk=self.pk)

            if existing.exists():
                raise ValidationError(f"Z-order {self.z_order} already exists for this map")

    def __str__(self):
        return f"layer ({self.id}) '{self.layer.name}' z={self.z_order}"

"""
map configurations

The MapConfig object organizes the stack of map layers and display
details for a particular map configuration.

MapLayers define an arbitrary number of FeatureLayers to be displayed
on the canvas, including display parameters and z-order.

So, displaying a MapConfig means
(1) load the config to the javascript config object
(2) retrieve all the FeatureLayers
(3) apply the display parameters from the MapLayers

"""

class MapConfig(models.Model):
    name = models.CharField(max_length=50)
    slug = models.SlugField()
    config = models.JSONField(default=mapconfig_default)
    layers = models.ManyToManyField(
        'FeatureLayer',
        through='MapLayer',
        related_name='mapconfig',
        blank=True)

    def __str__(self):
        return self.name

# log data from web-user-behaviour, when enabled
class VisitorBehavior(models.Model):
    responseid = models.CharField(max_length=20)
    timestamp_add = models.DateTimeField(auto_now_add=True)
    logdata = models.JSONField()

# model representing a view summarizing submissions
class ResponseSummary(models.Model):
    rsid = models.CharField(primary_key=True)
    surveyid = models.CharField()
    responseid = models.CharField(max_length=20)
    ts_start = models.DateField()
    ts_end = models.DateField()
    duration = models.DurationField()
    ipaddr = models.CharField(max_length=20)
    recordct = models.IntegerField()

    class Meta:
        verbose_name_plural = "Response summaries"
        db_table = "response_summary"
        managed = False

class SurveyPoint(models.Model):

    surveyid = models.CharField(default="none")
    description = models.CharField(null=True)
    mapconfig = models.ForeignKey(MapConfig,
                                  on_delete=models.SET_NULL,
                                  null=True)
    projectid = models.PositiveSmallIntegerField()
    ipaddress = models.CharField(null=True, max_length=20)
    timestamp = models.CharField(max_length=60)
    timestamp_add = models.DateTimeField(auto_now_add=True)
    timestamp_edit = models.DateTimeField(auto_now=True)
    radius = models.CharField(max_length=20) # think about making this an integerfield
    resolution = models.FloatField(max_length=10,
                                  null=True,
                                  help_text='Display resolution at point creation time, in meters per pixel.')
    responseid = models.CharField(max_length=20) # existing points have an ID 17 characters long
    geom = models.PointField(srid=4326)
    deleted = models.BooleanField(default=False)

    def __str__(self):
        s = f"{self.responseid}[{self.projectid}] - {self.mapconfig} (radius {round(float(self.radius),1)})".replace('SRID=4326;','')
        if self.deleted:
            return s + ' [deleted]'
        else:
            return s
