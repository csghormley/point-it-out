#!/usr/bin/env python3
"""
Survey Point Segmentation Tool

Ingests survey points from the API and segments them into polygons, linestrings,
and individual points based on temporal and spatial clustering.

Usage:
    python segment_points.py --responseid <id> [options]
    python segment_points.py --all [options]

Examples:
    # Process a single session
    python segment_points.py --responseid ABC123XYZ

    # Process all sessions
    python segment_points.py --all

    # Custom parameters
    python segment_points.py --responseid ABC123XYZ --max-time-gap 300 --max-distance 100
"""

import argparse
import sys
import json
import logging
from typing import List, Dict, Tuple, Optional, Any
from datetime import datetime, timedelta
from dataclasses import dataclass
import requests

try:
    import numpy as np
    from sklearn.cluster import DBSCAN
    from shapely.geometry import Point, LineString, Polygon, MultiPoint
    from shapely.ops import nearest_points
except ImportError as e:
    print(f"Error: Required package not found: {e}")
    print("\nInstall required packages:")
    print("  pip install numpy scikit-learn shapely requests")
    sys.exit(1)


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@dataclass
class SurveyPointData:
    """Represents a survey point with spatial and temporal attributes"""
    id: int
    x: float
    y: float
    timestamp: str
    responseid: str
    projectid: int
    description: Optional[str] = None
    radius: Optional[float] = None
    resolution: Optional[float] = None

    @property
    def coords(self) -> Tuple[float, float]:
        return (self.x, self.y)

    @property
    def datetime(self) -> datetime:
        """Parse timestamp to datetime object"""
        # Handle various timestamp formats
        try:
            # Try ISO format first
            return datetime.fromisoformat(self.timestamp.replace('Z', '+00:00'))
        except (ValueError, AttributeError):
            # Try Unix timestamp (milliseconds)
            try:
                return datetime.fromtimestamp(float(self.timestamp) / 1000)
            except (ValueError, TypeError):
                logger.warning(f"Could not parse timestamp: {self.timestamp}")
                return datetime.now()


class GeometrySegmenter:
    """Segments survey points into meaningful geometric features"""

    def __init__(
        self,
        max_time_gap: float = 180.0,  # seconds
        max_distance: float = 50.0,    # meters (approximate for EPSG:4326)
        min_cluster_points: int = 3,
        polygon_closure_threshold: float = 20.0,  # meters
        min_polygon_points: int = 4,
        min_linestring_points: int = 2
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
        """
        self.max_time_gap = timedelta(seconds=max_time_gap)
        # Convert meters to degrees (rough approximation at mid-latitudes)
        # 1 degree ≈ 111,000 meters
        self.max_distance_deg = max_distance / 111000.0
        self.min_cluster_points = min_cluster_points
        self.polygon_closure_threshold_deg = polygon_closure_threshold / 111000.0
        self.min_polygon_points = min_polygon_points
        self.min_linestring_points = min_linestring_points

    def segment_session(
        self,
        points: List[SurveyPointData]
    ) -> Dict[str, List[Dict[str, Any]]]:
        """
        Segment a session's points into polygons, linestrings, and individual points.

        Returns:
            Dictionary with keys 'polygons', 'linestrings', 'points'
        """
        if not points:
            return {'polygons': [], 'linestrings': [], 'points': []}

        # Step 1: Sort by timestamp
        sorted_points = sorted(points, key=lambda p: p.datetime)

        # Step 2: Temporal segmentation
        temporal_segments = self._temporal_segmentation(sorted_points)
        logger.info(f"Created {len(temporal_segments)} temporal segments")

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
            'points': individual_points
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

        return clusters

    def _classify_and_create_geometry(
        self,
        points: List[SurveyPointData]
    ) -> Dict[str, Any]:
        """
        Classify a cluster of points as polygon, linestring, or point.

        Classification logic:
        1. If points form a closed loop (first ≈ last) and >= min_polygon_points → Polygon
        2. If points follow a linear pattern → LineString
        3. Otherwise → Individual points or MultiPoint
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
                            'timestamp_range': (
                                points[0].datetime.isoformat(),
                                points[-1].datetime.isoformat()
                            )
                        }
                except Exception as e:
                    logger.warning(f"Failed to create polygon: {e}")

        # Check for linestring
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


class SurveyPointAPI:
    """Client for interacting with the survey points API"""

    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url.rstrip('/')
        self.api_endpoint = f"{self.base_url}/api/surveypoints/"

    def fetch_points(
        self,
        responseid: Optional[str] = None,
        projectid: Optional[int] = None
    ) -> List[SurveyPointData]:
        """
        Fetch survey points from the API.

        Args:
            responseid: Optional response ID to filter by
            projectid: Optional project ID to filter by

        Returns:
            List of SurveyPointData objects
        """
        params = {}
        if responseid:
            params['responseid'] = responseid
        if projectid:
            params['projectid'] = projectid

        try:
            response = requests.get(self.api_endpoint, params=params)
            response.raise_for_status()
            data = response.json()

            # Parse GeoJSON features
            points = []
            for feature in data.get('features', []):
                props = feature['properties']
                coords = feature['geometry']['coordinates']

                point = SurveyPointData(
                    id=props['id'],
                    x=coords[0],
                    y=coords[1],
                    timestamp=props['timestamp'],
                    responseid=props['responseid'],
                    projectid=props['projectid'],
                    description=props.get('description'),
                    radius=float(props['radius']) if props.get('radius') else None,
                    resolution=props.get('resolution')
                )
                points.append(point)

            logger.info(f"Fetched {len(points)} points from API")
            return points

        except requests.exceptions.RequestException as e:
            logger.error(f"API request failed: {e}")
            return []

    def fetch_all_responseids(self) -> List[str]:
        """
        Fetch all unique response IDs (requires staff authentication).

        Returns:
            List of response IDs
        """
        try:
            # This requires authentication as staff user
            response = requests.get(self.api_endpoint)
            response.raise_for_status()
            data = response.json()

            # Extract unique response IDs
            responseids = set()
            for feature in data.get('features', []):
                responseids.add(feature['properties']['responseid'])

            return sorted(list(responseids))

        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to fetch all response IDs: {e}")
            return []


def format_results(results: Dict[str, List[Dict[str, Any]]]) -> str:
    """Format segmentation results as human-readable text"""
    output = []
    output.append("\n" + "="*70)
    output.append("SEGMENTATION RESULTS")
    output.append("="*70)

    output.append(f"\nPolygons: {len(results['polygons'])}")
    for idx, poly in enumerate(results['polygons'], 1):
        output.append(f"  #{idx}: {poly['point_count']} points, area={poly['area']:.8f} deg²")
        output.append(f"       Time: {poly['timestamp_range'][0]} to {poly['timestamp_range'][1]}")

    output.append(f"\nLineStrings: {len(results['linestrings'])}")
    for idx, line in enumerate(results['linestrings'], 1):
        output.append(f"  #{idx}: {line['point_count']} points, length={line['length']:.8f} deg")
        output.append(f"       Linearity: {line.get('linearity', 0):.3f}")
        output.append(f"       Time: {line['timestamp_range'][0]} to {line['timestamp_range'][1]}")

    output.append(f"\nIndividual Points: {len(results['points'])}")

    output.append("\n" + "="*70 + "\n")
    return "\n".join(output)


def export_geojson(
    results: Dict[str, List[Dict[str, Any]]],
    output_file: str
) -> None:
    """Export results to GeoJSON format"""
    features = []

    # Add polygons
    for poly in results['polygons']:
        features.append({
            'type': 'Feature',
            'geometry': {
                'type': 'Polygon',
                'coordinates': [poly['coordinates']]
            },
            'properties': {
                'geometry_type': 'polygon',
                'point_count': poly['point_count'],
                'point_ids': poly['point_ids'],
                'area': poly['area'],
                'timestamp_start': poly['timestamp_range'][0],
                'timestamp_end': poly['timestamp_range'][1]
            }
        })

    # Add linestrings
    for line in results['linestrings']:
        features.append({
            'type': 'Feature',
            'geometry': {
                'type': 'LineString',
                'coordinates': line['coordinates']
            },
            'properties': {
                'geometry_type': 'linestring',
                'point_count': line['point_count'],
                'point_ids': line['point_ids'],
                'length': line['length'],
                'linearity': line.get('linearity', 0),
                'timestamp_start': line['timestamp_range'][0],
                'timestamp_end': line['timestamp_range'][1]
            }
        })

    # Add individual points
    for point in results['points']:
        features.append({
            'type': 'Feature',
            'geometry': {
                'type': 'Point',
                'coordinates': point['coordinates']
            },
            'properties': {
                'geometry_type': 'point',
                'point_count': 1,
                'point_ids': point['point_ids'],
                'timestamp': point.get('timestamp', '')
            }
        })

    geojson = {
        'type': 'FeatureCollection',
        'features': features
    }

    with open(output_file, 'w') as f:
        json.dump(geojson, f, indent=2)

    logger.info(f"Exported {len(features)} features to {output_file}")


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description='Segment survey points into polygons, linestrings, and individual points',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )

    # Input options
    parser.add_argument(
        '--responseid',
        type=str,
        help='Response ID to process'
    )
    parser.add_argument(
        '--projectid',
        type=int,
        help='Project ID to filter by'
    )
    parser.add_argument(
        '--all',
        action='store_true',
        help='Process all response IDs (requires staff auth)'
    )

    # API configuration
    parser.add_argument(
        '--api-url',
        type=str,
        default='http://localhost:8000',
        help='Base URL for the API (default: http://localhost:8000)'
    )

    # Segmentation parameters
    parser.add_argument(
        '--max-time-gap',
        type=float,
        default=180.0,
        help='Maximum time gap in seconds for temporal segmentation (default: 180)'
    )
    parser.add_argument(
        '--max-distance',
        type=float,
        default=50.0,
        help='Maximum distance in meters for spatial clustering (default: 50)'
    )
    parser.add_argument(
        '--min-cluster-points',
        type=int,
        default=3,
        help='Minimum points to form a cluster (default: 3)'
    )
    parser.add_argument(
        '--polygon-threshold',
        type=float,
        default=20.0,
        help='Max distance in meters between first/last point for polygon (default: 20)'
    )

    # Output options
    parser.add_argument(
        '--output',
        type=str,
        help='Output GeoJSON file path'
    )
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Enable verbose logging'
    )

    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    # Validate input
    if not args.responseid and not args.all:
        parser.error("Either --responseid or --all must be specified")

    # Initialize API client
    api = SurveyPointAPI(base_url=args.api_url)

    # Initialize segmenter
    segmenter = GeometrySegmenter(
        max_time_gap=args.max_time_gap,
        max_distance=args.max_distance,
        min_cluster_points=args.min_cluster_points,
        polygon_closure_threshold=args.polygon_threshold
    )

    # Fetch and process points
    if args.all:
        responseids = api.fetch_all_responseids()
        logger.info(f"Processing {len(responseids)} response IDs")

        all_results = []
        for responseid in responseids:
            points = api.fetch_points(responseid=responseid, projectid=args.projectid)
            if points:
                results = segmenter.segment_session(points)
                all_results.append((responseid, results))
                print(f"\nResponse ID: {responseid}")
                print(format_results(results))

        # Optionally combine and export all results
        if args.output:
            combined_results = {
                'polygons': [],
                'linestrings': [],
                'points': []
            }
            for _, results in all_results:
                combined_results['polygons'].extend(results['polygons'])
                combined_results['linestrings'].extend(results['linestrings'])
                combined_results['points'].extend(results['points'])

            export_geojson(combined_results, args.output)
    else:
        # Single response ID
        points = api.fetch_points(responseid=args.responseid, projectid=args.projectid)

        if not points:
            logger.error(f"No points found for responseid={args.responseid}")
            sys.exit(1)

        # Segment the points
        results = segmenter.segment_session(points)

        # Display results
        print(format_results(results))

        # Export if requested
        if args.output:
            export_geojson(results, args.output)


if __name__ == '__main__':
    main()
