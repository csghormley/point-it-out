import csv
import json
from django.contrib import admin
from django.http import HttpResponse
from django.contrib.gis.db.models import JSONField
from django.urls import reverse
from django.utils.safestring import mark_safe
from django.contrib.gis.geos import GEOSGeometry

from leaflet.admin import LeafletGeoAdmin

# Register your models here.
from .models import SurveyPoint, MapConfig, FeatureLayer, MapLayer, \
BaseMap, MapBasemap, VisitorBehavior, ResponseSummary

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

class DownloadAsGeoJsonMixin:
    """Mixin to export model instances as GeoJSON FeatureCollection"""

    def download_as_geojson(self, request, queryset):
        """Export selected objects as GeoJSON FeatureCollection"""
        features = []

        for obj in queryset:
            # Get the geometry field - assume it's called 'geom'
            geom_field = getattr(obj, 'geom', None)

            if geom_field is None:
                continue

            # Convert geometry to GeoJSON dict
            if isinstance(geom_field, GEOSGeometry):
                geometry = json.loads(geom_field.geojson)
            else:
                continue

            # Build properties from all non-geometry fields
            properties = {}
            meta = self.model._meta

            for field in meta.fields:
                field_name = field.name

                # Skip the geometry field
                if field_name == 'geom':
                    continue

                field_value = getattr(obj, field_name)

                # Handle special field types
                if hasattr(field_value, 'isoformat'):  # DateTime fields
                    properties[field_name] = field_value.isoformat()
                elif hasattr(field_value, 'pk'):  # ForeignKey fields
                    properties[field_name] = str(field_value)
                    properties[f'{field_name}_id'] = field_value.pk
                elif field_value is None:
                    properties[field_name] = None
                else:
                    properties[field_name] = str(field_value)

            # Create GeoJSON feature
            feature = {
                "type": "Feature",
                "geometry": geometry,
                "properties": properties
            }

            features.append(feature)

        # Create FeatureCollection
        feature_collection = {
            "type": "FeatureCollection",
            "features": features
        }

        # Create response
        response = HttpResponse(
            json.dumps(feature_collection, indent=2),
            content_type='application/geo+json'
        )
        response['Content-Disposition'] = f'attachment; filename="{self.model._meta.model_name}_export.geojson"'

        return response

    download_as_geojson.short_description = "Download Selected as GeoJSON"

@admin.register(SurveyPoint)
class SurveyPointAdmin(LeafletGeoAdmin, ExportCsvMixin, DownloadAsGeoJsonMixin):
    fields = ['surveyid', 'mapconfig', 'description', 'responseid', 'projectid', 'ipaddress', 'timestamp', 'timestamp_add', 'timestamp_edit', 'radius', 'resolution', 'geom', 'deleted']
    readonly_fields = ['surveyid', 'projectid', 'ipaddress', 'timestamp', 'timestamp_add', 'timestamp_edit', 'radius', 'resolution', 'responseid', 'mapconfig',]
    list_filter = ['surveyid', 'mapconfig__name', 'deleted', 'responseid', 'ipaddress', 'radius', ]
    search_fields = ['surveyid', 'mapconfig__name', 'ipaddress', 'radius', 'responseid', 'geom']
    actions = ["export_as_csv", "download_as_geojson"]
    change_list_template = 'admin/pio/surveypoint/change_list.html'

    show_facets = admin.ShowFacets.ALWAYS

    def has_add_permission(self, request, obj=None):
        return False
    
    def changelist_view(self, request, extra_context=None):
        """Add shareable GeoJSON export URL to the context"""
        extra_context = extra_context or {}

        # Build the export URL with current filters
        from django.urls import reverse
        from urllib.parse import urlencode

        # Get query parameters from the changelist
        query_params = {}

        # Extract filter parameters
        responseid = request.GET.get('responseid')
        if responseid:
            query_params['responseid'] = responseid

        projectid = request.GET.get('projectid')
        if projectid:
            query_params['projectid'] = projectid

        surveyid = request.GET.get('surveyid')
        if surveyid:
            query_params['surveyid'] = surveyid

        mapconfig = request.GET.get('mapconfig__name')
        if mapconfig:
            # For related field filters, we need to lookup the ID
            from pio.models import MapConfig
            try:
                mc = MapConfig.objects.get(name=mapconfig)
                query_params['mapconfig'] = mc.id
            except MapConfig.DoesNotExist:
                pass

        deleted = request.GET.get('deleted')
        if deleted:
            query_params['deleted'] = deleted

        # Build the export URL
        base_url = reverse('export_surveypoints_geojson')
        if query_params:
            export_url = f"{base_url}?{urlencode(query_params)}"
        else:
            export_url = base_url

        # Make it an absolute URL for easy sharing
        export_url_absolute = request.build_absolute_uri(export_url)

        extra_context['geojson_export_url'] = export_url
        extra_context['geojson_export_url_absolute'] = export_url_absolute
        extra_context['has_filters'] = bool(query_params)

        return super().changelist_view(request, extra_context=extra_context)

class MapLayerInline(admin.TabularInline):
    model = MapLayer
    extra = 1
    fields = ('layer', 'config', 'z_order')
    ordering = ('z_order',)

    formfield_overrides = {
        JSONField: {'widget': JSONEditorWidget(options={'mode': 'text'},
                                               width='100%',
                                               height='300px')}
    }

    class Media:
        css = {
            'all': ('pio/css/admin-inline.css',)
        }

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('layer')

class MapBasemapInline(admin.TabularInline):
    model = MapBasemap
    extra = 1
    fields = ('basemap', 'min_zoom', 'max_zoom', 'opacity', 'z_index')
    ordering = ('z_index',)

    class Media:
        css = {
            'all': ('pio/css/admin-inline.css',)
        }

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('basemap')

@admin.register(MapConfig)
class MapConfigAdmin(admin.ModelAdmin, ExportCsvMixin):
    save_as = True
    fields = ['id', 'name', 'slug', 'config',]
    list_display = ('name', 'map_link',)
    prepopulated_fields = {"slug": ("name",)}
    readonly_fields = ['id', 'map_link',]
    search_fields = ['name', 'slug', 'config',]
    actions = ["export_as_csv"]

    inlines = [MapLayerInline, MapBasemapInline]

    formfield_overrides = {
        JSONField: {'widget': JSONEditorWidget(options={'mode': 'text'},
                                               width='100%',
                                               height='300px')}
    }

    def map_link(self, obj):
        return mark_safe(f'<a target="_" href="{ reverse("site_index", args=[obj.slug,]) }">{ obj.name }')
    map_link.short_description = 'map link'

@admin.register(FeatureLayer)
class FeatureLayerAdmin(admin.ModelAdmin, ExportCsvMixin):
    save_as = True
    fields = ['id', 'name', 'slug', 'geojson',]
    prepopulated_fields = {"slug": ("name",)}
    readonly_fields = ['id',]
    search_fields = ['name', 'slug', 'geojson',]
    actions = ["export_as_csv"]

    formfield_overrides = {
        JSONField: {'widget': JSONEditorWidget(options={'mode': 'text'},
                                               width='100%',
                                               height='300px')}
    }

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
    save_as = True
    fields = ['surveyid', 'responseid', 'ts_start', 'ts_end', 'duration', 'ipaddr', 'recordct',]
    list_display = fields
    readonly_fields = fields # this is a view - read only
    list_filter = ['surveyid', 'responseid', 'ipaddr',]
    search_fields = ['surveyid', 'responseid', 'ipaddr',]

    actions = ["export_as_csv"]

@admin.register(BaseMap)
class BaseMapAdmin(admin.ModelAdmin, ExportCsvMixin):
    save_as = True
    fields = ['id', 'name', 'slug', 'tile_url', 'attribution']
    list_display = ('name', 'slug', 'tile_url')
    prepopulated_fields = {"slug": ("name",)}
    readonly_fields = ['id']
    search_fields = ['name', 'slug', 'tile_url']
    actions = ["export_as_csv"]
