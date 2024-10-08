from django.contrib.auth.models import User
from django.urls import include, path

from rest_framework import routers

from . import views

import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Routers automatically determine the URL conf
# Model
router = routers.DefaultRouter()
router.register(r'surveypoints', views.SurveyPointViewSet, 'SurveyPoint')
router.register(r'visitorlog', views.VisitorBehaviorViewSet, 'VisitorBehavior')

urlpatterns = [
    path('', views.index, name='index'),
    path('site/<slug:slug>/', views.index, name='site_index'),

    path('demo', views.demo, name='demo'),

    # Wire up our API using automatic URL routing.
    # Additionally, we include login URLs for the browsable API.
    path('api/', include(router.urls)),
    path('api-auth/', include('rest_framework.urls', namespace='rest_framework')),

]

