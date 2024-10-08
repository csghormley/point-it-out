from django.shortcuts import render
from django.http import HttpResponse
from django.contrib.gis.geoip2 import GeoIP2, GeoIP2Exception
from django.core.exceptions import ObjectDoesNotExist

from geoip2.errors import AddressNotFoundError

from rest_framework import routers, serializers, viewsets, status
from rest_framework.response import Response

#from rest_framework_gis.serializers import GeoFeatureModelSerializer
# use local version
from .serializers import GeoFeatureModelSerializer

from .models import MapConfig, SurveyPoint, VisitorBehavior
from .permissions import SurveyPointPermission, VisitorBehaviorPermission

import json

import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# placeholder
def index(request, slug='default'):

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
        # this object must exist, otherwise all is lost!
        logger.error(f"The mapconfig with slug '{slug}' does not exist. Using 'default'.")
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
               'responseid': responseid,
               'projectid': projectid,
               'ip': ip,
               'country': location_country,
               'city': location_city,}

    return render(request, "pio/index.html", context)

def demo(request):
    context = {}
    return render(request, "pio/demo.html", context)

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

        if (pk==None):
            return Response("FAILED: pk missing", status=status.HTTP_400_BAD_REQUEST)

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
