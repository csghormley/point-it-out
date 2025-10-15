from django.shortcuts import render
from django.contrib.gis.geoip2 import GeoIP2
from django.core.exceptions import ObjectDoesNotExist

from geoip2.errors import AddressNotFoundError

from rest_framework import serializers, viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.reverse import reverse

from rest_framework_gis.serializers import GeoFeatureModelSerializer
# use local version
##from .serializers import GeoFeatureModelSerializer

from .models import FeatureLayer, MapLayer, MapConfig, BaseMap, MapBasemap, SurveyPoint, VisitorBehavior
from .permissions import FeatureLayerPermission, MapLayerPermission, SurveyPointPermission, VisitorBehaviorPermission
from .throttles import (
    SurveyPointAnonThrottle,
    SurveyPointAuthThrottle,
    MapLayerThrottle,
    MapConfigThrottle,
    FeatureLayerThrottle,
    VisitorBehaviorThrottle,
)

import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# main map view:
# uses index.html as default template
def index(request, slug='default', template_name='pio/index.html'):

    # values from the URL passed in (from the enclosing app, if any)
    if 'id' in request.GET:
        responseid = request.GET['id']
    else:
        responseid = None

    if 'proj_id' in request.GET:
        projectid = request.GET['proj_id']
    else:
        projectid = None

    # look up the specified map configuration, or use the default
    try:
        mapconfig = MapConfig.objects.get(slug=slug)
    except ObjectDoesNotExist:
        logger.error(f"The mapconfig with slug '{slug}' does not exist. Using 'default'.")
        # the 'default' object must exist
        mapconfig = MapConfig.objects.get(slug='default')

    # geolocate the request
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')

    try:
        g = GeoIP2()
        location = g.city(ip)
        location_country = location["country_name"]
        location_city = location["city"]
    except AddressNotFoundError:
        logger.error(f"Unable to geolocate IP {ip}.")
        location_country = 'private'
        location_city = 'private'

    logger.info(f"geolocated {ip} to city <{location_city}> in country <{location_country}>")
    context = {'mapconfig': mapconfig.config,
               'mapconfigid': mapconfig.pk,
               'responseid': responseid,
               'projectid': projectid,
               'ip': ip,
               'country': location_country,
               'city': location_city,
               'maplayers': mapconfig.maplayer_set.all()
               }

    return render(request, template_name, context)

def demo(request):
    context = {}
    return render(request, "pio/demo.html", context)

def version(request):
    context = {}
    return render(request, "pio/version.txt", context)


class MapLayerSerializer(serializers.ModelSerializer):

    # related object details to reduce API calls
    mapconfig_name = serializers.CharField(source='mapconfig.name', read_only=True)
    layer_name = serializers.CharField(source='layer.name', read_only=True)
    layer_slug = serializers.CharField(source='layer.slug', read_only=True)
    layer_features = serializers.JSONField(source='layer.geojson', read_only=True)

    class Meta:
        model = MapLayer
        fields = [
            'id', 'z_order', 'config', 'mapconfig', 'mapconfig_name',
            'layer', 'layer_name', 'layer_slug', 'layer_features'
        ]

class NestedMapLayerSerializer(serializers.ModelSerializer):

    # Simplified version for nesting - excludes mapconfig to avoid redundancy
    # Pull related FeatureLayer properties
    layer_name = serializers.CharField(source='layer.name', read_only=True)
    layer_slug = serializers.CharField(source='layer.slug', read_only=True)
    layer_features = serializers.JSONField(source='layer.geojson', read_only=True)

    class Meta:
        model = MapLayer
        fields = [
            'id', 'z_order', 'config', 'layer', 'layer_name', 'layer_slug', 'layer_features'
        ]

# Serializers define the API representation.
class MapConfigSerializer(serializers.ModelSerializer):

    url = serializers.SerializerMethodField()

    class Meta:
        model = MapConfig
        fields = ['id', 'url', 'name', 'slug', 'config']

    def get_url(self, obj):
        request = self.context.get('request')
        if request:
            return reverse('MapConfig-detail', kwargs={'pk': obj.pk}, request=request)
        return None

class MapConfigDetailSerializer(MapConfigSerializer):
    """Extended serializer with full layer details for detail views"""
    map_layers = NestedMapLayerSerializer(
        source='maplayer_set',
        many=True,
        read_only=True
    )

    class Meta(MapConfigSerializer.Meta):
        fields = MapConfigSerializer.Meta.fields + ['map_layers']

class BaseMapSerializer(serializers.ModelSerializer):
    """Serializer for BaseMap objects"""
    class Meta:
        model = BaseMap
        fields = ['id', 'name', 'slug', 'tile_url', 'attribution']

class MapBasemapSerializer(serializers.ModelSerializer):
    """Serializer for MapBasemap with embedded BaseMap details"""
    basemap_name = serializers.CharField(source='basemap.name', read_only=True)
    basemap_slug = serializers.CharField(source='basemap.slug', read_only=True)
    basemap_tile_url = serializers.CharField(source='basemap.tile_url', read_only=True)
    basemap_attribution = serializers.CharField(source='basemap.attribution', read_only=True)

    class Meta:
        model = MapBasemap
        fields = ['id', 'basemap', 'basemap_name', 'basemap_slug', 'basemap_tile_url',
                  'basemap_attribution', 'min_zoom', 'max_zoom', 'opacity', 'z_index']
        read_only_fields = ['basemap_name', 'basemap_slug', 'basemap_tile_url', 'basemap_attribution']

class FeatureLayerSerializer(serializers.ModelSerializer):
    class Meta:
        fields = '__all__'
        model = FeatureLayer
        #geo_field = "geojson"
        id_field = 'id'

class MapConfigViewSet(viewsets.ModelViewSet):

    queryset = MapConfig.objects.all()
    throttle_classes = [MapConfigThrottle]

    def get_serializer_class(self):
        """Use different serializers for different actions"""
        if self.action == 'retrieve':
            # For detail view, include full layer information
            return MapConfigDetailSerializer
        elif self.action == 'list':
            # For list view, you can choose lighter or full depending on needs
            # Option 1: Light version for faster list loading
            return MapConfigSerializer
            # Option 2: Full version if you always need layer info
            # return MapConfigWithLayersSerializer
        else:
            # For create/update operations, use basic serializer
            return MapConfigSerializer

    @action(detail=True, methods=['get'])
    def layers(self, request, pk=None):
        """Get layers in z-order for this map config"""
        map_config = self.get_object()

        logger.info(map_config)

        ordered_layers = MapLayer.objects.filter(
            mapconfig=map_config.pk
        ).order_by('z_order').select_related('layer')

        logger.info(ordered_layers)

        serializer = MapLayerSerializer(ordered_layers, many=True)
        return Response(serializer.data)

# Define a viewset for the SurveyPoint model
# this API is only valid for a specific response ID
class FeatureLayerViewSet(viewsets.ModelViewSet):

    serializer_class = FeatureLayerSerializer
    throttle_classes = [FeatureLayerThrottle]
    #permission_classes = (FeatureLayerPermission,)

    def get_queryset(self):
            """
            Filters selection based on requested MapConfig.
            """

            mapconfigid = self.request.query_params.get('mapconfigid')

            if mapconfigid is not None:
                self.request.session['mapconfigid'] = mapconfigid
                queryset = FeatureLayer.objects.filter(
                    featurelayerorder__mapconfig_id=mapconfigid
                    ).distinct()
            else:
                queryset = FeatureLayer.objects.all()

            logger.info(f"mapconfigid: {mapconfigid}, queryset count: {queryset.count()}")
            return queryset

class MapLayerViewSet(viewsets.ModelViewSet):
    serializer_class = MapLayerSerializer
    permission_classes = (MapLayerPermission,)
    throttle_classes = [MapLayerThrottle]

    def get_queryset(self):
        """
        Optionally filter by mapconfig or layer
        """
        queryset = MapLayer.objects.all().select_related('mapconfig', 'layer')

        # Filter by mapconfig if provided
        mapconfig_id = self.request.query_params.get('mapconfig')
        if mapconfig_id is not None:
            queryset = queryset.filter(mapconfig_id=mapconfig_id)

        # Filter by layer if provided
        layer_id = self.request.query_params.get('layer')
        if layer_id is not None:
            queryset = queryset.filter(layer_id=layer_id)

        return queryset.order_by('mapconfig', 'z_order')

class MapBasemapViewSet(viewsets.ModelViewSet):
    """
    ViewSet for MapBasemap - provides basemaps for a given MapConfig
    """
    serializer_class = MapBasemapSerializer
    throttle_classes = [MapLayerThrottle]  # Reuse MapLayerThrottle for similar resource

    def get_queryset(self):
        """
        Optionally filter by mapconfig
        """
        queryset = MapBasemap.objects.all().select_related('mapconfig', 'basemap')

        # Filter by mapconfig if provided
        mapconfig_id = self.request.query_params.get('mapconfig')
        if mapconfig_id is not None:
            queryset = queryset.filter(mapconfig_id=mapconfig_id)

        return queryset.order_by('z_index')

# Serializers define the API representation.
class SurveyPointSerializer(GeoFeatureModelSerializer):
    class Meta:
        model = SurveyPoint
        geo_field = "geom"
        exclude = ["timestamp_add", "timestamp_edit"]
        id_field = 'id'

# Define a viewset for the SurveyPoint model
# this API is only valid for a specific response ID
class SurveyPointViewSet(viewsets.ModelViewSet):

    serializer_class = SurveyPointSerializer
    permission_classes = (SurveyPointPermission,)
    throttle_classes = [SurveyPointAnonThrottle, SurveyPointAuthThrottle]

    def get_queryset(self):
            """
            Filters selection based on requested survey responseid.
            if user is staff and no responseid, return all the records, otherwise empty set
            """

            responseid = self.request.query_params.get('responseid')
            projectid = self.request.query_params.get('projectid')

            queryset = SurveyPoint.objects.none()
            if responseid is not None:

                self.request.session['responseid'] = responseid
                queryset = SurveyPoint.objects.filter(responseid=responseid, deleted=False)

                if projectid is not None:
                    try:
                        queryset = queryset.filter(projectid=projectid)
                    except ValueError:
                        logger.error(f"Client requested invald projectid '{projectid}' - ignoring.")
                        pass
            else:
                if self.request.user.is_staff:
                    queryset = SurveyPoint.objects.filter(deleted=False)

            logger.info(f"responseid: {responseid}, user={self.request.user}")
            return queryset

    # override the destroy method to mark deleted
    # use responseid from the session (set in the get_queryset method) to cross-check the pk
    def destroy(self, request, pk=None):

        if (pk is None):
            return Response("FAILED: pk missing",
                            status=status.HTTP_400_BAD_REQUEST)

        try:
            # get the corresponding response ID, either from cookies or built into the session
            if ('responseid' in request.session):
                responseid = request.session['responseid']
                logger.info(f'got respid {responseid} from session')
            elif ('responseid' in request.GET):
                responseid = request.GET['responseid']
                logger.info(f'got respid {responseid} from GET')
            else:
                return Response(f"FAILED {pk}: no responseid in session", status=status.HTTP_400_BAD_REQUEST)

            # make sure this record is associated with the provided responseid
            sp = SurveyPoint.objects.get(pk=pk, responseid=responseid)
            sp.deleted=True
            sp.save()

            return Response({'deleted': pk})

        except Exception as e:
            logger.exception(f'exception in view logic: {e}')
            return Response(f"FAILED {pk}:", status=status.HTTP_400_BAD_REQUEST)

# Serializers define the API representation.
class VisitorBehaviorSerializer(serializers.ModelSerializer):

    # explicitly declare the JSON field properties
    logdata = serializers.JSONField(binary=True)

    class Meta:
        model = VisitorBehavior
        id_field = 'id'
        exclude = []

# Define a viewset for the VisitorBehavior model
# this should be create only from the front end
class VisitorBehaviorViewSet(viewsets.ModelViewSet):

    serializer_class = VisitorBehaviorSerializer
    permission_classes = (VisitorBehaviorPermission,)
    throttle_classes = [VisitorBehaviorThrottle]

    queryset = VisitorBehavior.objects.none()

    """
    def get_queryset(self):
    """
    # Filters selection based on requested survey responseid.
    # if user is staff and no responseid, return all the records, otherwise empty set
    """

            responseid = self.request.query_params.get('responseid')
            projectid = self.request.query_params.get('projectid')

            queryset = SurveyPoint.objects.none()
            if responseid is not None:

                self.request.session['responseid'] = responseid
                queryset = SurveyPoint.objects.filter(responseid=responseid, deleted=False)

                if projectid is not None:
                    queryset = queryset.filter(projectid=projectid)
            else:
                if self.request.user.is_staff:
                    queryset = SurveyPoint.objects.filter(deleted=False)

            logger.info(f"responseid: {responseid}, user={self.request.user}")
            return queryset
    """
