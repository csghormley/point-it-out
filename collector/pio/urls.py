from django.urls import include, path

from rest_framework import routers

from . import views

import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Routers automatically determine the URL conf
router = routers.DefaultRouter()
router.register(r'featurelayers', views.FeatureLayerViewSet, 'FeatureLayer')
router.register(r'map-layers', views.MapLayerViewSet, 'MapLayer')
router.register(r'mapconfigs', views.MapConfigViewSet, 'MapConfig')
router.register(r'surveypoints', views.SurveyPointViewSet, 'SurveyPoint')
router.register(r'visitorlog', views.VisitorBehaviorViewSet, 'VisitorBehavior')

urlpatterns = [

    # front page for demos - no data entry
    path('', views.index, name='index'),

    # standard site url for survey data collection
    path('site/<slug:slug>/', views.index, name='site_index'),

    path('version', views.version, name='version'),

    # Wire up our API using automatic URL routing.
    # Additionally, we include login URLs for the browsable API.
    path('api/', include(router.urls)),
    path('api-auth/', include('rest_framework.urls', namespace='rest_framework')),

]
