"""
Standalone unit tests for survey point segmentation functionality.

These tests can run without a Django database connection.
Run with: python -m pytest pio/tests/test_segmentation_standalone.py

Tests cover:
- Temporal segmentation
- Spatial clustering (DBSCAN and radius-based)
- Polygon vs linestring classification
- Convex hull polygon creation
- Linearity calculation
"""

import json
import math
import tempfile
import unittest
from datetime import datetime
from pathlib import Path

# Import the segmentation module
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from pio.segmentation import GeometrySegmenter, SurveyPointData


class TemporalSegmentationTest(unittest.TestCase):
    """Tests for temporal segmentation based on time gaps"""

    def test_single_temporal_segment(self):
        """Points within max_time_gap should form one temporal segment"""
        segmenter = GeometrySegmenter(max_time_gap=180.0)

        points = [
            SurveyPointData(
                id=1, x=-121.5, y=46.15,
                timestamp="2025-11-01T12:00:00+00:00",
                responseid="test", projectid=1
            ),
            SurveyPointData(
                id=2, x=-121.5, y=46.16,
                timestamp="2025-11-01T12:01:00+00:00",
                responseid="test", projectid=1
            ),
            SurveyPointData(
                id=3, x=-121.5, y=46.17,
                timestamp="2025-11-01T12:02:00+00:00",
                responseid="test", projectid=1
            ),
        ]

        segments = segmenter._temporal_segmentation(points)

        self.assertEqual(len(segments), 1)
        self.assertEqual(len(segments[0]), 3)

    def test_multiple_temporal_segments(self):
        """Points with gaps > max_time_gap should form multiple segments"""
        segmenter = GeometrySegmenter(max_time_gap=180.0)

        points = [
            SurveyPointData(
                id=1, x=-121.5, y=46.15,
                timestamp="2025-11-01T12:00:00+00:00",
                responseid="test", projectid=1
            ),
            SurveyPointData(
                id=2, x=-121.5, y=46.16,
                timestamp="2025-11-01T12:05:00+00:00",  # 5 min gap
                responseid="test", projectid=1
            ),
            SurveyPointData(
                id=3, x=-121.5, y=46.17,
                timestamp="2025-11-01T12:10:00+00:00",  # 5 min gap
                responseid="test", projectid=1
            ),
        ]

        segments = segmenter._temporal_segmentation(points)

        self.assertEqual(len(segments), 3)
        self.assertEqual(len(segments[0]), 1)
        self.assertEqual(len(segments[1]), 1)
        self.assertEqual(len(segments[2]), 1)


class SpatialClusteringTest(unittest.TestCase):
    """Tests for spatial clustering algorithms"""

    def test_dbscan_single_cluster(self):
        """Points within max_distance should form one cluster"""
        segmenter = GeometrySegmenter(max_distance=500.0)

        points = [
            SurveyPointData(
                id=1, x=-121.48, y=46.15,
                timestamp="2025-11-01T12:00:00+00:00",
                responseid="test", projectid=1
            ),
            SurveyPointData(
                id=2, x=-121.48, y=46.151,
                timestamp="2025-11-01T12:00:01+00:00",
                responseid="test", projectid=1
            ),
            SurveyPointData(
                id=3, x=-121.48, y=46.152,
                timestamp="2025-11-01T12:00:02+00:00",
                responseid="test", projectid=1
            ),
        ]

        clusters = segmenter._dbscan_clustering(points)

        # Should have one cluster (not counting noise=-1)
        non_noise_clusters = {k: v for k, v in clusters.items() if k != -1}
        self.assertEqual(len(non_noise_clusters), 1)

    def test_radius_based_clustering_overlap(self):
        """Points with overlapping radii should cluster together"""
        segmenter = GeometrySegmenter(use_radius_adjacency=True, min_cluster_points=3)

        # Three points with overlapping radii of 150m each
        # Distance < radius_A + radius_B (200 < 300), so they should cluster
        points = [
            SurveyPointData(
                id=1, x=-121.48, y=46.15,
                timestamp="2025-11-01T12:00:00+00:00",
                responseid="test", projectid=1,
                radius=150.0
            ),
            SurveyPointData(
                id=2, x=-121.48, y=46.152,  # ~222m north
                timestamp="2025-11-01T12:00:01+00:00",
                responseid="test", projectid=1,
                radius=150.0
            ),
            SurveyPointData(
                id=3, x=-121.48, y=46.154,  # ~222m north from point 2
                timestamp="2025-11-01T12:00:02+00:00",
                responseid="test", projectid=1,
                radius=150.0
            ),
        ]

        clusters = segmenter._radius_based_clustering(points)

        # Should form one cluster
        non_noise_clusters = {k: v for k, v in clusters.items() if k != -1}
        self.assertGreaterEqual(len(non_noise_clusters), 1)

    def test_radius_based_clustering_no_overlap(self):
        """Points without overlapping radii should not cluster"""
        segmenter = GeometrySegmenter(use_radius_adjacency=True, min_cluster_points=2)

        # Two points 500m apart with radii of 50m each
        # Distance > radius_A + radius_B (500 > 100), so they should not cluster
        points = [
            SurveyPointData(
                id=1, x=-121.48, y=46.15,
                timestamp="2025-11-01T12:00:00+00:00",
                responseid="test", projectid=1,
                radius=50.0
            ),
            SurveyPointData(
                id=2, x=-121.48, y=46.155,  # ~555m north
                timestamp="2025-11-01T12:00:01+00:00",
                responseid="test", projectid=1,
                radius=50.0
            ),
        ]

        clusters = segmenter._radius_based_clustering(points)

        # Should be marked as noise (no cluster)
        self.assertIn(-1, clusters)


class LinearityCalculationTest(unittest.TestCase):
    """Tests for linearity calculation"""

    def test_perfectly_linear(self):
        """Straight line should have linearity close to 1.0"""
        segmenter = GeometrySegmenter()

        from shapely.geometry import Point
        points = [
            Point(-121.48, 46.15),
            Point(-121.48, 46.16),
            Point(-121.48, 46.17),
        ]

        linearity = segmenter._calculate_linearity(points)

        self.assertGreater(linearity, 0.99)

    def test_circular_pattern(self):
        """Circular pattern should have low linearity"""
        segmenter = GeometrySegmenter()

        from shapely.geometry import Point

        # Create points in a circle
        points = []
        for i in range(8):
            angle = (i / 8) * 2 * math.pi
            x = -121.48 + 0.01 * math.cos(angle)
            y = 46.15 + 0.01 * math.sin(angle)
            points.append(Point(x, y))

        linearity = segmenter._calculate_linearity(points)

        self.assertLess(linearity, 0.3)


class ConvexHullPolygonTest(unittest.TestCase):
    """Tests for convex hull polygon creation from low-linearity points"""

    def test_convex_hull_from_low_linearity(self):
        """Low linearity points should create polygon via convex hull"""
        segmenter = GeometrySegmenter(
            linearity_threshold=0.6,
            min_polygon_points=4
        )

        # Create points in a rough square (low linearity)
        points = [
            SurveyPointData(
                id=1, x=-121.48, y=46.15,
                timestamp="2025-11-01T12:00:00+00:00",
                responseid="test", projectid=1
            ),
            SurveyPointData(
                id=2, x=-121.47, y=46.15,
                timestamp="2025-11-01T12:00:01+00:00",
                responseid="test", projectid=1
            ),
            SurveyPointData(
                id=3, x=-121.47, y=46.16,
                timestamp="2025-11-01T12:00:02+00:00",
                responseid="test", projectid=1
            ),
            SurveyPointData(
                id=4, x=-121.48, y=46.16,
                timestamp="2025-11-01T12:00:03+00:00",
                responseid="test", projectid=1
            ),
        ]

        geometry = segmenter._classify_and_create_geometry(points)

        self.assertEqual(geometry['type'], 'Polygon')
        self.assertEqual(geometry.get('method'), 'convex_hull')
        self.assertIsNotNone(geometry.get('linearity'))

    def test_linestring_from_high_linearity(self):
        """High linearity points should create linestring"""
        segmenter = GeometrySegmenter(
            linearity_threshold=0.6,
            min_linestring_points=2
        )

        # Create points in a straight line (high linearity)
        points = [
            SurveyPointData(
                id=1, x=-121.48, y=46.15,
                timestamp="2025-11-01T12:00:00+00:00",
                responseid="test", projectid=1
            ),
            SurveyPointData(
                id=2, x=-121.47, y=46.15,
                timestamp="2025-11-01T12:00:01+00:00",
                responseid="test", projectid=1
            ),
            SurveyPointData(
                id=3, x=-121.46, y=46.15,
                timestamp="2025-11-01T12:00:02+00:00",
                responseid="test", projectid=1
            ),
        ]

        geometry = segmenter._classify_and_create_geometry(points)

        self.assertEqual(geometry['type'], 'LineString')
        self.assertGreater(geometry.get('linearity', 0), 0.9)


class IntegrationTest(unittest.TestCase):
    """Integration tests with realistic data patterns"""

    def test_segment_polygon_from_circular_path(self):
        """Should create polygon from circular walking path"""
        segmenter = GeometrySegmenter(
            max_time_gap=180.0,
            max_distance=500.0,
            linearity_threshold=0.6,
            min_polygon_points=4
        )

        # Create 8 points in a circle (simulating someone walking around an area)
        points = []
        base_time = datetime.fromisoformat("2025-11-01T12:00:00+00:00")

        for i in range(8):
            angle = (i / 8) * 2 * math.pi
            x = -121.48 + 0.001 * math.cos(angle)
            y = 46.15 + 0.001 * math.sin(angle)
            timestamp = base_time.replace(second=i * 5)

            points.append(SurveyPointData(
                id=i + 1,
                x=x,
                y=y,
                timestamp=timestamp.isoformat(),
                responseid="test",
                projectid=1,
                radius=100.0
            ))

        results = segmenter.segment_session(points)

        # Should create at least one polygon
        self.assertGreater(len(results['polygons']), 0)

        # First polygon should be created via convex hull
        if results['polygons']:
            polygon = results['polygons'][0]
            self.assertEqual(polygon.get('method'), 'convex_hull')
            self.assertLess(polygon.get('linearity', 1.0), 0.6)

    def test_segment_linestring_from_linear_path(self):
        """Should create linestring from linear walking path"""
        segmenter = GeometrySegmenter(
            max_time_gap=180.0,
            max_distance=500.0,
            linearity_threshold=0.6,
            min_linestring_points=2
        )

        # Create points in a straight line
        points = []
        base_time = datetime.fromisoformat("2025-11-01T12:00:00+00:00")

        for i in range(5):
            x = -121.48 + i * 0.001
            y = 46.15
            timestamp = base_time.replace(second=i * 5)

            points.append(SurveyPointData(
                id=i + 1,
                x=x,
                y=y,
                timestamp=timestamp.isoformat(),
                responseid="test",
                projectid=1,
                radius=100.0
            ))

        results = segmenter.segment_session(points)

        # Should create at least one linestring
        self.assertGreater(len(results['linestrings']), 0)

        # First linestring should have high linearity
        if results['linestrings']:
            linestring = results['linestrings'][0]
            self.assertGreater(linestring.get('linearity', 0), 0.9)

    def test_radius_mode_clusters_overlapping_points(self):
        """Radius mode should cluster points with overlapping uncertainty circles"""
        segmenter = GeometrySegmenter(
            max_time_gap=180.0,
            use_radius_adjacency=True,
            linearity_threshold=0.6,
            min_cluster_points=3
        )

        # Create points 150m apart with 100m radii
        # They should cluster because distance < sum of radii (150 < 200)
        points = []
        base_time = datetime.fromisoformat("2025-11-01T12:00:00+00:00")

        for i in range(6):
            x = -121.48
            y = 46.15 + i * 0.0013  # ~145m spacing
            timestamp = base_time.replace(second=i * 5)

            points.append(SurveyPointData(
                id=i + 1,
                x=x,
                y=y,
                timestamp=timestamp.isoformat(),
                responseid="test",
                projectid=1,
                radius=100.0
            ))

        results = segmenter.segment_session(points)

        # Should create geometries (not individual points)
        total_geometries = (
            len(results['polygons']) +
            len(results['linestrings'])
        )
        self.assertGreater(total_geometries, 0)

        # Should have fewer individual points than input
        self.assertLess(len(results['points']), len(points))


if __name__ == '__main__':
    unittest.main()
