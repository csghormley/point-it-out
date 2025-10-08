from rest_framework import permissions

import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class FeatureLayerPermission(permissions.BasePermission):

    # manage permissions in the viewset
    # view only through the API
    def has_permission(self, request, view):

        logger.debug('FeatureLayerPermission has_permission')

        if view.action == 'list':
            return request.user.is_authenticated and request.user.is_staff
        elif view.action == 'retrieve':
            return True
        else:
            return False

    def has_object_permission(self, request, view, obj):

        logger.debug('FeatureLayerPermission has_object_permission')

        if view.action == 'retrieve':
            return True
        else:
            return False

class MapLayerPermission(permissions.BasePermission):
    """
    Custom permission for MapLayer operations
    """
    def has_permission(self, request, view):
        logger.debug('MapLayerPermission has_permission')

        if view.action in ['list', 'retrieve']:
            return True  # Allow read access to everyone
        elif view.action in ['create', 'update', 'partial_update', 'destroy']:
            return request.user.is_authenticated and request.user.is_staff
        else:
            return False

    def has_object_permission(self, request, view, obj):
        logger.debug('MapLayerPermission has_object_permission')

        if view.action in ['retrieve']:
            return True
        elif view.action in ['update', 'partial_update', 'destroy']:
            return request.user.is_authenticated and request.user.is_staff
        else:
            return False

class SurveyPointPermission(permissions.BasePermission):

    # manage permissions in the viewset
    def has_permission(self, request, view):

        logger.debug('has_permission')

        return True

        """
        if view.action == 'list':
            return request.user.is_authenticated() and request.user.is_admin
        elif view.action == 'create':
            return True
        elif view.action in ['retrieve', 'update', 'partial_update', 'destroy']:
            return True
        else:
            return False
        """

    def has_object_permission(self, request, view, obj):

        logger.debug('has_object_permission')
        return True

        """
        # Deny actions on objects if the user is not authenticated
        if not request.user.is_authenticated():
            return False

        if view.action == 'retrieve':
            return obj == request.user or request.user.is_admin
        elif view.action in ['update', 'partial_update']:
            return obj == request.user or request.user.is_admin
        elif view.action == 'destroy':
            return request.user.is_admin
        else:
            return False
        """

class VisitorBehaviorPermission(permissions.BasePermission):

    # manage permissions in the viewset
    def has_permission(self, request, view):

        logger.debug('has_permission')

        if view.action == 'list':
            return request.user.is_authenticated and request.user.is_staff
        elif view.action == 'create':
            return True
        elif view.action in ['retrieve', 'update', 'partial_update', 'destroy']:
            return False
        else:
            return False

    def has_object_permission(self, request, view, obj):

        logger.debug('no_object_permission')
        return False

        # Deny actions on objects if the user is not authenticated
        if not request.user.is_authenticated:
            return False

        if view.action == 'retrieve':
            return obj == request.user or request.user.is_staff
        elif view.action in ['update', 'partial_update']:
            return obj == request.user or request.user.is_staff
        elif view.action == 'destroy':
            return request.user.is_staff
        else:
            return False
