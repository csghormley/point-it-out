#!/usr/bin/env python3
"""
Example usage of the segmentation tool programmatically
"""

import sys
from segment_points import (
    GeometrySegmenter,
    SurveyPointData,
    format_results,
    export_geojson
)
from datetime import datetime, timedelta

def create_example_polygon():
    """Create example points forming a polygon (square)"""
    base_time = datetime.now()
    points = []

    # Square polygon: 4 corners + return to start
    coords = [
        (-121.5, 44.1),
        (-121.5, 44.2),
        (-121.4, 44.2),
        (-121.4, 44.1),
        (-121.5, 44.1),  # Close the loop
    ]

    for i, (x, y) in enumerate(coords):
        points.append(SurveyPointData(
            id=i + 1,
            x=x,
            y=y,
            timestamp=(base_time + timedelta(seconds=i * 10)).isoformat(),
            responseid="EXAMPLE_POLY",
            projectid=1,
            description=f"Point {i+1}"
        ))

    return points


def create_example_linestring():
    """Create example points forming a line"""
    base_time = datetime.now() + timedelta(minutes=5)
    points = []

    # Linear path (not closed)
    coords = [
        (-121.3, 44.0),
        (-121.2, 44.05),
        (-121.1, 44.1),
        (-121.0, 44.15),
    ]

    for i, (x, y) in enumerate(coords):
        points.append(SurveyPointData(
            id=i + 100,
            x=x,
            y=y,
            timestamp=(base_time + timedelta(seconds=i * 15)).isoformat(),
            responseid="EXAMPLE_LINE",
            projectid=1,
            description=f"Line point {i+1}"
        ))

    return points


def create_example_individual_points():
    """Create example individual points (scattered)"""
    base_time = datetime.now() + timedelta(minutes=10)
    points = []

    # Scattered points (far apart)
    coords = [
        (-121.8, 44.3),
        (-121.1, 43.9),
    ]

    for i, (x, y) in enumerate(coords):
        points.append(SurveyPointData(
            id=i + 200,
            x=x,
            y=y,
            timestamp=(base_time + timedelta(seconds=i * 30)).isoformat(),
            responseid="EXAMPLE_POINTS",
            projectid=1,
            description=f"Individual point {i+1}"
        ))

    return points


def main():
    """Run example segmentation"""
    print("Survey Point Segmentation - Example Usage\n")

    # Create example data
    all_points = []
    all_points.extend(create_example_polygon())
    all_points.extend(create_example_linestring())
    all_points.extend(create_example_individual_points())

    print(f"Created {len(all_points)} example points")
    print("  - 5 points forming a square polygon")
    print("  - 4 points forming a linestring")
    print("  - 2 scattered individual points\n")

    # Initialize segmenter with default parameters
    segmenter = GeometrySegmenter(
        max_time_gap=180.0,
        max_distance=50.0,
        min_cluster_points=3,
        polygon_closure_threshold=20.0
    )

    # Segment the points
    print("Running segmentation...")
    results = segmenter.segment_session(all_points)

    # Display results
    print(format_results(results))

    # Show detailed geometry info
    print("\nDetailed Results:")
    print("-" * 70)

    if results['polygons']:
        print("\nPolygon Details:")
        for i, poly in enumerate(results['polygons'], 1):
            print(f"\n  Polygon #{i}:")
            print(f"    Point IDs: {poly['point_ids']}")
            print(f"    Coordinates: {len(poly['coordinates'])} vertices")
            print(f"    Area: {poly['area']:.8f} square degrees")
            print(f"    Time range: {poly['timestamp_range'][0]}")
            print(f"                to {poly['timestamp_range'][1]}")

    if results['linestrings']:
        print("\nLineString Details:")
        for i, line in enumerate(results['linestrings'], 1):
            print(f"\n  LineString #{i}:")
            print(f"    Point IDs: {line['point_ids']}")
            print(f"    Coordinates: {len(line['coordinates'])} points")
            print(f"    Length: {line['length']:.8f} degrees")
            print(f"    Linearity: {line.get('linearity', 0):.3f}")
            print(f"    Time range: {line['timestamp_range'][0]}")
            print(f"                to {line['timestamp_range'][1]}")

    if results['points']:
        print("\nIndividual Points:")
        for i, point in enumerate(results['points'], 1):
            print(f"  Point #{i}: ID {point['point_ids'][0]}, "
                  f"coords {point['coordinates']}")

    # Export to GeoJSON
    output_file = "example_segmentation.geojson"
    export_geojson(results, output_file)
    print(f"\n✓ Results exported to {output_file}")
    print("\nYou can view this file in:")
    print("  - QGIS, ArcGIS, or any GIS software")
    print("  - geojson.io (paste the file contents)")
    print("  - OpenLayers/Leaflet web maps")


if __name__ == '__main__':
    main()
