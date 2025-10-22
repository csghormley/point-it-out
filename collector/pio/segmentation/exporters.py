"""
Export utilities for segmentation results
"""

import json
from typing import Dict, List, Any


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
