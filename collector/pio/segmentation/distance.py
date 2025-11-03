"""
Distance calculation utilities for segmentation.

Provides accurate distance calculations using geodesic (great circle) distances.
Falls back to simple approximation if geopy is not available.
"""

import logging
from typing import List, Tuple
import numpy as np

try:
    from geopy.distance import geodesic
    GEOPY_AVAILABLE = True
except ImportError:
    GEOPY_AVAILABLE = False

logger = logging.getLogger(__name__)


class DistanceCalculator:
    """
    Calculator for accurate geodetic distances.

    Uses geodesic (ellipsoidal) distance calculations for accuracy.
    Falls back to simple degree approximation if geopy not available.
    """

    def __init__(self):
        """Initialize distance calculator."""
        self.method = 'geodesic' if GEOPY_AVAILABLE else 'simple'
        if not GEOPY_AVAILABLE:
            logger.warning(
                "geopy not available, using simple approximation. "
                "Install geopy for accurate distances: pip install geopy"
            )

    def distance(self, point1: Tuple[float, float], point2: Tuple[float, float]) -> float:
        """
        Calculate accurate distance between two WGS84 points.

        Args:
            point1: (lon, lat) in degrees
            point2: (lon, lat) in degrees

        Returns:
            Distance in meters
        """
        if GEOPY_AVAILABLE:
            # geopy expects (lat, lon)
            return geodesic((point1[1], point1[0]), (point2[1], point2[0])).meters
        else:
            return simple_distance_meters_approx(point1, point2)

    def distance_matrix(self, points: List[Tuple[float, float]]) -> np.ndarray:
        """
        Calculate pairwise distance matrix for a list of points.

        Args:
            points: List of (lon, lat) tuples

        Returns:
            NxN numpy array of distances in meters
        """
        n = len(points)
        distances = np.zeros((n, n))

        for i in range(n):
            for j in range(i + 1, n):
                dist = self.distance(points[i], points[j])
                distances[i, j] = dist
                distances[j, i] = dist

        return distances


def simple_distance_meters_approx(point1: Tuple[float, float], point2: Tuple[float, float]) -> float:
    """
    Simple approximation of distance using degree-to-meter conversion.

    This is the old method: 1 degree ≈ 111,000 meters.
    Fast but less accurate, especially at higher latitudes and longer distances.

    Args:
        point1: (lon, lat) in degrees
        point2: (lon, lat) in degrees

    Returns:
        Approximate distance in meters
    """
    lon1, lat1 = point1
    lon2, lat2 = point2

    # Account for latitude in longitude distance
    # cos(lat) correction for longitude
    avg_lat = (lat1 + lat2) / 2
    lat_correction = np.cos(np.radians(avg_lat))

    # Calculate distance components
    lon_dist = (lon2 - lon1) * lat_correction
    lat_dist = (lat2 - lat1)

    # Calculate distance in degrees
    distance_deg = np.sqrt(lon_dist**2 + lat_dist**2)

    # Convert to meters (rough approximation: 1 degree ≈ 111,000 meters)
    distance_meters = distance_deg * 111000.0

    return distance_meters


def geodesic_distance(point1: Tuple[float, float], point2: Tuple[float, float]) -> float:
    """
    Calculate geodesic (ellipsoidal) distance between two WGS84 points.

    Uses geopy's geodesic distance (Karney's algorithm) if available,
    otherwise falls back to simple approximation.

    Args:
        point1: (lon, lat) in degrees
        point2: (lon, lat) in degrees

    Returns:
        Distance in meters
    """
    if GEOPY_AVAILABLE:
        # geopy expects (lat, lon)
        return geodesic((point1[1], point1[0]), (point2[1], point2[0])).meters
    else:
        return simple_distance_meters_approx(point1, point2)


def compare_distance_methods(points: List[Tuple[float, float]]) -> dict:
    """
    Compare accuracy and performance of different distance calculation methods.

    Args:
        points: List of (lon, lat) tuples

    Returns:
        Dictionary with comparison results
    """
    import time

    results = {
        'point_count': len(points),
        'methods': {},
        'geopy_available': GEOPY_AVAILABLE
    }

    # Method 1: Simple approximation (old method - no latitude correction)
    start = time.time()
    simple_old_distances = []
    for i in range(len(points) - 1):
        lon1, lat1 = points[i]
        lon2, lat2 = points[i + 1]
        distance_deg = np.sqrt((lon2 - lon1)**2 + (lat2 - lat1)**2)
        dist = distance_deg * 111000.0
        simple_old_distances.append(dist)
    simple_old_time = time.time() - start

    results['methods']['simple_old'] = {
        'name': 'Simple (no lat correction)',
        'time_seconds': simple_old_time,
        'distances': simple_old_distances,
        'mean_distance': np.mean(simple_old_distances) if simple_old_distances else 0,
    }

    # Method 2: Simple approximation with latitude correction
    start = time.time()
    simple_distances = []
    for i in range(len(points) - 1):
        dist = simple_distance_meters_approx(points[i], points[i + 1])
        simple_distances.append(dist)
    simple_time = time.time() - start

    results['methods']['simple_corrected'] = {
        'name': 'Simple (with lat correction)',
        'time_seconds': simple_time,
        'distances': simple_distances,
        'mean_distance': np.mean(simple_distances) if simple_distances else 0,
    }

    # Method 3: Geodesic (if available)
    if GEOPY_AVAILABLE:
        start = time.time()
        calc = DistanceCalculator()
        geodesic_distances = []
        for i in range(len(points) - 1):
            dist = calc.distance(points[i], points[i + 1])
            geodesic_distances.append(dist)
        geodesic_time = time.time() - start

        results['methods']['geodesic'] = {
            'name': 'Geodesic (Karney)',
            'time_seconds': geodesic_time,
            'distances': geodesic_distances,
            'mean_distance': np.mean(geodesic_distances) if geodesic_distances else 0,
        }

        # Calculate differences from geodesic (ground truth)
        diffs_old = [abs(s - g) for s, g in zip(simple_old_distances, geodesic_distances)]
        diffs_corrected = [abs(s - g) for s, g in zip(simple_distances, geodesic_distances)]

        percent_diffs_old = [(s - g) / g * 100 for s, g in zip(simple_old_distances, geodesic_distances) if g > 0]
        percent_diffs_corrected = [(s - g) / g * 100 for s, g in zip(simple_distances, geodesic_distances) if g > 0]

        results['comparison'] = {
            'simple_old_vs_geodesic': {
                'mean_difference_meters': np.mean(diffs_old),
                'max_difference_meters': np.max(diffs_old),
                'mean_percent_error': np.mean(percent_diffs_old),
                'max_percent_error': np.max(np.abs(percent_diffs_old)),
            },
            'simple_corrected_vs_geodesic': {
                'mean_difference_meters': np.mean(diffs_corrected),
                'max_difference_meters': np.max(diffs_corrected),
                'mean_percent_error': np.mean(percent_diffs_corrected),
                'max_percent_error': np.max(np.abs(percent_diffs_corrected)),
            }
        }

        # Performance comparison
        results['performance'] = {
            'geodesic_overhead_vs_simple': (geodesic_time / simple_time - 1) * 100 if simple_time > 0 else 0,
        }

    return results
