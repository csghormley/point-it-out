import csv
from django.contrib import admin
from django.http import HttpResponse
from django.contrib.gis.db.models import JSONField
from django.urls import reverse
from django.utils.safestring import mark_safe

from leaflet.admin import LeafletGeoAdmin

# Register your models here.
from .models import SurveyPoint, MapConfig, GeoJSONLayer, VisitorBehavior, ResponseSummary

from django_json_widget.widgets import JSONEditorWidget

class ExportCsvMixin:
    def export_as_csv(self, request, queryset):

        meta = self.model._meta
        field_names = [field.name for field in meta.fields]

        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename={}.csv'.format(meta)
        writer = csv.writer(response)

        writer.writerow(field_names)
        for obj in queryset:
            writer.writerow([getattr(obj, field) for field in field_names])

        return response

    export_as_csv.short_description = "Export Selected to CSV"

@admin.register(SurveyPoint)
class SurveyPointAdmin(LeafletGeoAdmin, ExportCsvMixin):
    fields = ['surveyid', 'mapconfig', 'description', 'responseid', 'projectid', 'ipaddress', 'timestamp', 'timestamp_add', 'timestamp_edit', 'radius', 'resolution', 'geom', 'deleted']
    readonly_fields = ['surveyid', 'projectid', 'ipaddress', 'timestamp', 'timestamp_add', 'timestamp_edit', 'radius', 'resolution', 'responseid', 'mapconfig',]
    list_filter = ['surveyid', 'deleted', 'responseid', 'ipaddress', 'radius', ]
    search_fields = ['surveyid', 'ipaddress', 'radius', 'responseid', 'geom']
    actions = ["export_as_csv"]

@admin.register(MapConfig)
class MapConfigAdmin(admin.ModelAdmin, ExportCsvMixin):
    fields = ['name', 'slug', 'config', 'layers',]
    list_display = ('name', 'map_link',)
    prepopulated_fields = {"slug": ("name",)}
    readonly_fields = ['map_link',]
    search_fields = ['name', 'slug', 'config',]
    actions = ["export_as_csv"]

    formfield_overrides = {
        JSONField: {'widget': JSONEditorWidget(options={'mode': 'text'})},
    }

    def map_link(self, obj):
        return mark_safe(f'<a target="_" href="{ reverse("site_index", args=[obj.slug,]) }">{ obj.name }')
    map_link.short_description = 'map link'

@admin.register(GeoJSONLayer)
class GeoJSONLayerAdmin(admin.ModelAdmin, ExportCsvMixin):
    fields = ['name', 'slug', 'geojson',]
    prepopulated_fields = {"slug": ("name",)}
    search_fields = ['name', 'slug', 'geojson',]
    actions = ["export_as_csv"]

@admin.register(VisitorBehavior)
class VisitorBehaviorAdmin(admin.ModelAdmin, ExportCsvMixin):
    fields = ['responseid', 'timestamp_add', 'logdata',]
    list_display = ('responseid', 'timestamp_add',)
    readonly_fields = fields # treat all as raw - not necessary to edit
    list_filter = ['responseid',]
    search_fields = ['responseid', 'logdata',]
    
    actions = ["export_as_csv"]

@admin.register(ResponseSummary)
class ResponseSummaryAdmin(admin.ModelAdmin, ExportCsvMixin):
    fields = ['surveyid', 'responseid', 'ts_start', 'ts_end', 'duration', 'ipaddr', 'recordct',]
    list_display = fields
    readonly_fields = fields # this is a view - read only
    list_filter = ['surveyid', 'responseid', 'ipaddr',]
    search_fields = ['surveyid', 'responseid', 'ipaddr',]
    
    actions = ["export_as_csv"]

