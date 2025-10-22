# Survey Point Segmentation Tool

A standalone Python tool for segmenting survey points into polygons, linestrings, and individual points based on temporal and spatial clustering.

## Overview

This tool processes survey points collected through the map interface and automatically identifies geometric patterns:

- **Polygons**: Closed loops where users clicked around an area
- **LineStrings**: Linear paths where users clicked along a route
- **Individual Points**: Isolated clicks or noise points

## Installation

### Prerequisites

Python 3.8 or higher

### Install Dependencies

```bash
pip install -r requirements-segmentation.txt
```

Or manually install:

```bash
pip install numpy scikit-learn shapely requests
```

## Usage

### Basic Examples

Process a single response ID:

```bash
python segment_points.py --responseid ABC123XYZ
```

Process a response ID and export to GeoJSON:

```bash
python segment_points.py --responseid ABC123XYZ --output results.geojson
```

Process all sessions (requires staff authentication):

```bash
python segment_points.py --all --output all_sessions.geojson
```

### Advanced Configuration

Customize segmentation parameters:

```bash
python segment_points.py \
    --responseid ABC123XYZ \
    --max-time-gap 300 \
    --max-distance 100 \
    --polygon-threshold 30 \
    --output results.geojson
```

### Command-Line Options

#### Input Options

- `--responseid <id>`: Response ID to process
- `--projectid <id>`: Project ID to filter by (optional)
- `--all`: Process all response IDs (requires staff authentication)

#### API Configuration

- `--api-url <url>`: Base URL for the API (default: `http://localhost:8000`)

#### Segmentation Parameters

- `--max-time-gap <seconds>`: Maximum time gap for temporal segmentation (default: 180)
  - Points separated by more than this many seconds are treated as separate segments

- `--max-distance <meters>`: Maximum distance for spatial clustering (default: 50)
  - Points within this distance are grouped together using DBSCAN

- `--min-cluster-points <n>`: Minimum points to form a cluster (default: 3)
  - Smaller clusters are treated as individual points

- `--polygon-threshold <meters>`: Max distance between first/last point for polygon (default: 20)
  - If first and last points are within this distance, attempt to create a polygon

#### Output Options

- `--output <file>`: Export results to GeoJSON file
- `--verbose`: Enable detailed logging

## Algorithm Details

### Temporal Segmentation

The algorithm first segments points by time:

1. Sort all points by timestamp
2. Identify gaps larger than `max-time-gap`
3. Split into temporal segments at these gaps

This handles cases where users take breaks or work on different areas at different times.

### Spatial Clustering

Within each temporal segment, DBSCAN clustering groups spatially close points:

- Uses `max-distance` as the epsilon parameter
- Requires at least 2 points for a cluster
- Noise points (not in any cluster) become individual points

### Geometry Classification

For each spatial cluster, the algorithm determines the geometry type:

#### Polygon Detection

A cluster becomes a polygon if:
- It has ≥ 4 points (minimum for a closed shape)
- First and last points are within `polygon-threshold` distance
- The resulting polygon is valid and has non-zero area

#### LineString Detection

A cluster becomes a linestring if:
- It has ≥ 2 points
- It doesn't qualify as a polygon
- The resulting linestring is valid and has non-zero length

Linestrings include a "linearity" metric (0-1) indicating how straight the path is.

#### Individual Points

Points become individual points if:
- They're noise from DBSCAN clustering
- They're in clusters too small to form meaningful geometries
- Geometry creation fails

## Output Format

### Console Output

The tool displays a summary:

```
======================================================================
SEGMENTATION RESULTS
======================================================================

Polygons: 2
  #1: 12 points, area=0.00004231 deg²
       Time: 2024-01-15T14:23:10 to 2024-01-15T14:25:33
  #2: 8 points, area=0.00001842 deg²
       Time: 2024-01-15T14:28:45 to 2024-01-15T14:30:12

LineStrings: 3
  #1: 5 points, length=0.00123456 deg
       Linearity: 0.892
       Time: 2024-01-15T14:26:00 to 2024-01-15T14:27:30

Individual Points: 4

======================================================================
```

### GeoJSON Output

When using `--output`, the tool creates a GeoJSON FeatureCollection with:

**Polygon features:**
```json
{
  "type": "Feature",
  "geometry": {
    "type": "Polygon",
    "coordinates": [[[-121.5, 44.1], ...]]
  },
  "properties": {
    "geometry_type": "polygon",
    "point_count": 12,
    "point_ids": [1, 2, 3, ...],
    "area": 0.00004231,
    "timestamp_start": "2024-01-15T14:23:10",
    "timestamp_end": "2024-01-15T14:25:33"
  }
}
```

**LineString features:**
```json
{
  "type": "Feature",
  "geometry": {
    "type": "LineString",
    "coordinates": [[-121.5, 44.1], ...]
  },
  "properties": {
    "geometry_type": "linestring",
    "point_count": 5,
    "point_ids": [10, 11, 12, 13, 14],
    "length": 0.00123456,
    "linearity": 0.892,
    "timestamp_start": "2024-01-15T14:26:00",
    "timestamp_end": "2024-01-15T14:27:30"
  }
}
```

**Point features:**
```json
{
  "type": "Feature",
  "geometry": {
    "type": "Point",
    "coordinates": [-121.5, 44.1]
  },
  "properties": {
    "geometry_type": "point",
    "point_count": 1,
    "point_ids": [20],
    "timestamp": "2024-01-15T14:31:00"
  }
}
```

## Parameter Tuning Guide

### `max-time-gap`

- **Increase** (e.g., 300-600s) if users take longer breaks but work on the same feature
- **Decrease** (e.g., 60-120s) if users rapidly switch between different tasks
- Default 180s works well for typical survey sessions

### `max-distance`

- **Increase** (e.g., 100-200m) for larger geographic features or lower precision
- **Decrease** (e.g., 20-30m) for detailed urban features or high precision
- Default 50m balances detail and aggregation
- Note: This is approximate; actual distance depends on latitude

### `polygon-threshold`

- **Increase** (e.g., 30-50m) if users are imprecise when closing polygons
- **Decrease** (e.g., 10-15m) if you want strict polygon closure
- Default 20m allows for typical user imprecision

### `min-cluster-points`

- **Increase** (e.g., 4-5) to require more evidence before creating features
- **Decrease** (e.g., 2) to capture smaller features
- Default 3 is a good balance for DBSCAN

## Integration with Django Application

### Using from Django Management Command

Create a Django management command to integrate with the application:

```python
# collector/pio/management/commands/segment_points.py
from django.core.management.base import BaseCommand
from pio.models import SurveyPoint
import sys
sys.path.append('scripts')
from segment_points import GeometrySegmenter, SurveyPointData

class Command(BaseCommand):
    help = 'Segment survey points into geometries'

    def add_arguments(self, parser):
        parser.add_argument('--responseid', type=str, required=True)

    def handle(self, *args, **options):
        responseid = options['responseid']

        # Fetch from database directly
        db_points = SurveyPoint.objects.filter(
            responseid=responseid,
            deleted=False
        ).order_by('timestamp_add')

        # Convert to SurveyPointData objects
        points = [
            SurveyPointData(
                id=p.id,
                x=p.geom.x,
                y=p.geom.y,
                timestamp=p.timestamp,
                responseid=p.responseid,
                projectid=p.projectid,
                description=p.description,
                radius=float(p.radius) if p.radius else None,
                resolution=p.resolution
            )
            for p in db_points
        ]

        # Segment
        segmenter = GeometrySegmenter()
        results = segmenter.segment_session(points)

        self.stdout.write(f"Found {len(results['polygons'])} polygons")
        self.stdout.write(f"Found {len(results['linestrings'])} linestrings")
        self.stdout.write(f"Found {len(results['points'])} points")
```

### API Endpoint for Segmented Geometries

Add an API endpoint to serve segmented geometries:

```python
# In views.py
@action(detail=False, methods=['get'])
def segment(self, request):
    """Segment points for a response ID into geometries"""
    responseid = request.query_params.get('responseid')
    if not responseid:
        return Response({'error': 'responseid required'},
                       status=status.HTTP_400_BAD_REQUEST)

    # Import and use segmenter...
    # Return GeoJSON results
```

## Troubleshooting

### No points found

- Verify the response ID exists in the database
- Check API authentication if using `--all`
- Confirm the API is running at the specified URL

### All points classified as individual points

- Decrease `max-distance` if points are too far apart
- Decrease `max-time-gap` if there are long pauses
- Check that points have valid timestamps

### Too many small features

- Increase `min-cluster-points` to require larger groups
- Increase `max-distance` to cluster more aggressively
- Increase `polygon-threshold` to allow looser polygon closure

### Installation errors

- Ensure Python 3.8+ is installed
- Try upgrading pip: `pip install --upgrade pip`
- Install packages individually to identify the problematic one

## Performance Notes

- Processing time scales linearly with the number of points
- DBSCAN clustering is O(n log n) with efficient implementations
- Memory usage is proportional to the number of points in the largest session
- For very large datasets (>10,000 points per session), consider batching

## Future Enhancements

Potential improvements for future versions:

1. **Multi-geometry support**: Detect mixed polygon/linestring features
2. **Confidence scoring**: Add confidence metrics to classifications
3. **Interactive tuning**: GUI for parameter adjustment with live preview
4. **Database storage**: Store segmented geometries in Django models
5. **Real-time processing**: WebSocket API for live segmentation
6. **ML-based classification**: Train models on labeled data for better accuracy

## License

This tool is part of the mapsurvey project. See the main project LICENSE file.
