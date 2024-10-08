from rest_framework import permissions

import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SurveyPointPermission(permissions.BasePermission):

    # manage permissions in the viewset
    def has_permission(self, request, view):

        logger.info('has_permission')

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

        logger.info('has_object_permission')
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

        logger.info('has_permission')

        if view.action == 'list':
            return request.user.is_authenticated and request.user.is_staff
        elif view.action == 'create':
            return True
        elif view.action in ['retrieve', 'update', 'partial_update', 'destroy']:
            return False
        else:
            return False
    
    def has_object_permission(self, request, view, obj):

        logger.info('no_object_permission')
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
