"""
Rate limiting throttles for API endpoints.

Each throttle class defines a specific rate limit scope.
Apply these to viewsets to control request rates independently.
"""

from rest_framework.throttling import AnonRateThrottle, UserRateThrottle


class SurveyPointAnonThrottle(AnonRateThrottle):
    """
    Throttle for anonymous survey point submissions.
    More restrictive since these are write operations.
    """
    scope = 'survey_points_anon'


class SurveyPointAuthThrottle(UserRateThrottle):
    """
    Throttle for authenticated survey point submissions.
    More generous for authenticated users.
    """
    scope = 'survey_points_auth'


class MapLayerThrottle(AnonRateThrottle):
    """
    Throttle for map layer data retrieval.
    Read-only, can be more generous.
    """
    scope = 'map_layers'


class MapConfigThrottle(AnonRateThrottle):
    """
    Throttle for map configuration retrieval.
    Read-only, moderate limits.
    """
    scope = 'mapconfigs'


class FeatureLayerThrottle(AnonRateThrottle):
    """
    Throttle for feature layer (GeoJSON) retrieval.
    Read-only, can be generous since layers are cached.
    """
    scope = 'feature_layers'


class VisitorBehaviorThrottle(AnonRateThrottle):
    """
    Throttle for visitor behavior logging.
    Write-only, moderate limits.
    """
    scope = 'visitor_behavior'
