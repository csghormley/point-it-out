"""
Core segmentation logic for survey points
"""

from datetime import timedelta
from typing import List, Dict, Any
import logging

import numpy as np
from sklearn.cluster import DBSCAN
from shapely.geometry import Point, LineString, Polygon, MultiPoint
from shapely.ops import unary_union

from .data import SurveyPointData

logger = logging.getLogger(__name__)


class GeometrySegmenter:
    """Segments survey points into meaningful geometric features"""

    def __init__(
        self,
        max_time_gap: float = 180.0,  # seconds
        max_distance: float = 50.0,    # meters (approximate for EPSG:4326)
        min_cluster_points: int = 3,
        polygon_closure_threshold: float = 20.0,  # meters
        min_polygon_points: int = 4,
        min_linestring_points: int = 2,
        linearity_threshold: float = 0.6  # threshold below which to create polygon
    ):
        """
        Initialize the segmenter with configuration parameters.

        Args:
            max_time_gap: Maximum time gap (seconds) to split temporal segments
            max_distance: Maximum distance for DBSCAN clustering (approx meters)
            min_cluster_points: Minimum points to form a cluster
            polygon_closure_threshold: Max distance between first/last point for polygon
            min_polygon_points: Minimum points required for polygon
            min_linestring_points: Minimum points required for linestring
            linearity_threshold: Linearity below which linestrings become polygons (0-1)
        """
        self.max_time_gap = timedelta(seconds=max_time_gap)
        # Convert meters to degrees (rough approximation at mid-latitudes)
        # 1 degree ≈ 111,000 meters
        self.max_distance_deg = max_distance / 111000.0
        self.min_cluster_points = min_cluster_points
        self.polygon_closure_threshold_deg = polygon_closure_threshold / 111000.0
        self.min_polygon_points = min_polygon_points
        self.min_linestring_points = min_linestring_points
        self.linearity_threshold = linearity_threshold

    def segment_session(
        self,
        points: List[SurveyPointData]
    ) -> Dict[str, List[Dict[str, Any]]]:
        """
        Segment a session's points into polygons, linestrings, and individual points.

        Returns:
            Dictionary with keys 'polygons', 'linestrings', 'points', 'temporal_segments'
        """
        if not points:
            return {
                'polygons': [],
                'linestrings': [],
                'points': [],
                'temporal_segments': []
            }

        # Step 1: Sort by timestamp
        sorted_points = sorted(points, key=lambda p: p.datetime)

        # Step 2: Temporal segmentation
        temporal_segments = self._temporal_segmentation(sorted_points)
        logger.info(f"Created {len(temporal_segments)} temporal segments")

        # Calculate statistics for temporal segments
        temporal_segment_stats = []
        for segment_idx, segment in enumerate(temporal_segments):
            stats = self._calculate_segment_statistics(segment, segment_idx)
            temporal_segment_stats.append(stats)

        # Step 3: Process each segment
        polygons = []
        linestrings = []
        individual_points = []

        for segment_idx, segment in enumerate(temporal_segments):
            logger.debug(f"Processing segment {segment_idx + 1} with {len(segment)} points")

            if len(segment) < self.min_cluster_points:
                # Too few points - treat as individual points
                individual_points.extend(self._points_to_features(segment))
                continue

            # Step 4: Spatial clustering within segment
            clusters = self._spatial_clustering(segment)

            # Step 5: Classify each cluster
            for cluster_id, cluster_points in clusters.items():
                if cluster_id == -1:  # DBSCAN noise points
                    individual_points.extend(self._points_to_features(cluster_points))
                    continue

                geometry = self._classify_and_create_geometry(cluster_points)

                if geometry['type'] == 'Polygon':
                    polygons.append(geometry)
                elif geometry['type'] == 'LineString':
                    linestrings.append(geometry)
                elif geometry['type'] == 'Point':
                    individual_points.append(geometry)

        return {
            'polygons': polygons,
            'linestrings': linestrings,
            'points': individual_points,
            'temporal_segments': temporal_segment_stats
        }

    def _temporal_segmentation(
        self,
        points: List[SurveyPointData]
    ) -> List[List[SurveyPointData]]:
        """Split points into temporal segments based on time gaps"""
        if not points:
            return []

        segments = []
        current_segment = [points[0]]

        for i in range(1, len(points)):
            time_gap = points[i].datetime - points[i-1].datetime

            if time_gap > self.max_time_gap:
                segments.append(current_segment)
                current_segment = [points[i]]
            else:
                current_segment.append(points[i])

        segments.append(current_segment)
        return segments

    def _spatial_clustering(
        self,
        points: List[SurveyPointData]
    ) -> Dict[int, List[SurveyPointData]]:
        """Perform DBSCAN spatial clustering on a segment"""
        coords = np.array([p.coords for p in points])

        clustering = DBSCAN(
            eps=self.max_distance_deg,
            min_samples=2,
            metric='euclidean'
        ).fit(coords)

        # Group points by cluster label
        clusters = {}
        for idx, label in enumerate(clustering.labels_):
            if label not in clusters:
                clusters[label] = []
            clusters[label].append(points[idx])

        # Filter out clusters that are spatially disconnected
        # (temporally adjacent but spatially distinct)
        filtered_clusters = {}
        for label, cluster_points in clusters.items():
            if label == -1:  # Keep noise points as-is
                filtered_clusters[label] = cluster_points
                continue

            # Check spatial compactness: ensure cluster diameter is reasonable
            if len(cluster_points) >= 2:
                coords_array = np.array([p.coords for p in cluster_points])
                # Calculate centroid
                centroid = np.mean(coords_array, axis=0)
                # Calculate maximum distance from centroid
                max_dist_from_centroid = max(
                    np.linalg.norm(coord - centroid)
                    for coord in coords_array
                )

                # If the cluster is too spread out (diameter > 3x max_distance),
                # it's likely spatially disconnected points
                if max_dist_from_centroid > (3 * self.max_distance_deg):
                    # Mark as noise instead
                    if -1 not in filtered_clusters:
                        filtered_clusters[-1] = []
                    filtered_clusters[-1].extend(cluster_points)
                    logger.debug(
                        f"Cluster {label} rejected due to spatial spread "
                        f"({max_dist_from_centroid*111000:.1f}m from centroid)"
                    )
                else:
                    filtered_clusters[label] = cluster_points
            else:
                filtered_clusters[label] = cluster_points

        return filtered_clusters

    def _classify_and_create_geometry(
        self,
        points: List[SurveyPointData]
    ) -> Dict[str, Any]:
        """
        Classify a cluster of points as polygon, linestring, or point.

        Classification logic:
        1. If points form a closed loop (first ≈ last) and >= min_polygon_points → Polygon
        2. If linearity is low (< threshold) and enough points → Polygon via convex hull
        3. If points follow a linear pattern → LineString
        4. Otherwise → Individual points or MultiPoint
        """
        n_points = len(points)

        # Not enough points for complex geometry
        if n_points < self.min_linestring_points:
            return self._points_to_features(points)[0]

        coords = [p.coords for p in points]
        shapely_points = [Point(c) for c in coords]

        # Check for polygon (closed loop)
        if n_points >= self.min_polygon_points:
            first_point = Point(coords[0])
            last_point = Point(coords[-1])
            closure_distance = first_point.distance(last_point)

            if closure_distance < self.polygon_closure_threshold_deg:
                # Create polygon
                try:
                    # Ensure closure
                    if coords[0] != coords[-1]:
                        coords.append(coords[0])

                    poly = Polygon(coords)

                    # Validate polygon
                    if poly.is_valid and poly.area > 0:
                        return {
                            'type': 'Polygon',
                            'geometry': poly,
                            'coordinates': list(poly.exterior.coords),
                            'point_count': n_points,
                            'point_ids': [p.id for p in points],
                            'area': poly.area,
                            'method': 'explicit_closure',
                            'timestamp_range': (
                                points[0].datetime.isoformat(),
                                points[-1].datetime.isoformat()
                            )
                        }
                except Exception as e:
                    logger.warning(f"Failed to create polygon: {e}")

        # Check linearity for potential polygon via convex hull
        if n_points >= self.min_polygon_points:
            linearity = self._calculate_linearity(shapely_points)

            # If linearity is low, the points form a non-linear pattern
            # Use convex hull to create a polygon
            if linearity < self.linearity_threshold:
                try:
                    multi_point = MultiPoint(shapely_points)
                    convex_hull = multi_point.convex_hull

                    # Only use convex hull if it creates a valid polygon
                    if isinstance(convex_hull, Polygon) and convex_hull.is_valid and convex_hull.area > 0:
                        logger.info(
                            f"Created polygon via convex hull (linearity={linearity:.3f}, "
                            f"points={n_points})"
                        )
                        return {
                            'type': 'Polygon',
                            'geometry': convex_hull,
                            'coordinates': list(convex_hull.exterior.coords),
                            'point_count': n_points,
                            'point_ids': [p.id for p in points],
                            'area': convex_hull.area,
                            'linearity': linearity,
                            'method': 'convex_hull',
                            'timestamp_range': (
                                points[0].datetime.isoformat(),
                                points[-1].datetime.isoformat()
                            )
                        }
                except Exception as e:
                    logger.warning(f"Failed to create convex hull polygon: {e}")

        # Check for linestring (high linearity or not enough points for polygon)
        if n_points >= self.min_linestring_points:
            try:
                line = LineString(coords)

                if line.is_valid and line.length > 0:
                    # Calculate linearity (how straight the line is)
                    linearity = self._calculate_linearity(shapely_points)

                    return {
                        'type': 'LineString',
                        'geometry': line,
                        'coordinates': list(line.coords),
                        'point_count': n_points,
                        'point_ids': [p.id for p in points],
                        'length': line.length,
                        'linearity': linearity,
                        'timestamp_range': (
                            points[0].datetime.isoformat(),
                            points[-1].datetime.isoformat()
                        )
                    }
            except Exception as e:
                logger.warning(f"Failed to create linestring: {e}")

        # Fallback to individual points
        if n_points == 1:
            return self._points_to_features(points)[0]
        else:
            # Create MultiPoint
            multi_point = MultiPoint(shapely_points)
            return {
                'type': 'MultiPoint',
                'geometry': multi_point,
                'coordinates': coords,
                'point_count': n_points,
                'point_ids': [p.id for p in points]
            }

    def _calculate_linearity(self, points: List[Point]) -> float:
        """
        Calculate how linear a set of points is (0-1, where 1 is perfectly linear).

        Uses the ratio of actual path length to straight-line distance.
        """
        if len(points) < 2:
            return 1.0

        # Total path length
        path_length = sum(
            points[i].distance(points[i+1])
            for i in range(len(points) - 1)
        )

        # Straight-line distance from first to last
        straight_distance = points[0].distance(points[-1])

        if path_length == 0:
            return 0.0

        # Linearity: closer to 1 means more linear
        linearity = straight_distance / path_length
        return linearity

    def _calculate_segment_statistics(
        self,
        segment: List[SurveyPointData],
        segment_idx: int
    ) -> Dict[str, Any]:
        """
        Calculate spatial statistics for a temporal segment.

        Returns statistics including min/max/median distance between consecutive points.
        """
        if len(segment) < 2:
            return {
                'segment_id': segment_idx + 1,
                'point_count': len(segment),
                'min_distance': 0.0,
                'max_distance': 0.0,
                'median_distance': 0.0,
                'mean_distance': 0.0,
                'total_distance': 0.0,
                'duration_seconds': 0.0,
                'timestamp_start': segment[0].datetime.isoformat() if segment else None,
                'timestamp_end': segment[0].datetime.isoformat() if segment else None,
            }

        # Calculate distances between consecutive points
        distances = []
        shapely_points = [Point(p.coords) for p in segment]

        for i in range(len(shapely_points) - 1):
            # Distance in degrees, convert to approximate meters
            dist_deg = shapely_points[i].distance(shapely_points[i+1])
            dist_meters = dist_deg * 111000.0  # Approximate conversion
            distances.append(dist_meters)

        # Calculate statistics
        distances_array = np.array(distances)

        # Calculate duration
        duration = (segment[-1].datetime - segment[0].datetime).total_seconds()

        return {
            'segment_id': segment_idx + 1,
            'point_count': len(segment),
            'min_distance': float(np.min(distances_array)),
            'max_distance': float(np.max(distances_array)),
            'median_distance': float(np.median(distances_array)),
            'mean_distance': float(np.mean(distances_array)),
            'total_distance': float(np.sum(distances_array)),
            'duration_seconds': duration,
            'timestamp_start': segment[0].datetime.isoformat(),
            'timestamp_end': segment[-1].datetime.isoformat(),
        }

    def _points_to_features(
        self,
        points: List[SurveyPointData]
    ) -> List[Dict[str, Any]]:
        """Convert individual points to feature dictionaries"""
        features = []
        for p in points:
            features.append({
                'type': 'Point',
                'geometry': Point(p.coords),
                'coordinates': p.coords,
                'point_count': 1,
                'point_ids': [p.id],
                'timestamp': p.datetime.isoformat()
            })
        return features
