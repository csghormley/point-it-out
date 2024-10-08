# This is an auto-generated Django model module created by ogrinspect.
from django.contrib.gis.db import models

class SurveyPoint(models.Model):

    surveyid = models.CharField(default="none") # no max length as we're using Postgres!
    description = models.CharField(null=True) # no max length as we're using Postgres!
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
        s = f"{self.responseid}[{self.projectid}] - {self.geom} (radius {round(float(self.radius),1)})".replace('SRID=4326;','')
        if self.deleted:
            return s + ' [deleted]'
        else:
            return s

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

# map configurations
class MapConfig(models.Model):
    name = models.CharField(max_length=50)
    slug = models.SlugField()
    config = models.JSONField(default=mapconfig_default)

    # Returns the string representation of the model.
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

        
