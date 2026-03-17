# Segmentation Tests

Unit tests for the survey point segmentation functionality.

## Test Files

### `test_segmentation_standalone.py`

Standalone unit tests that don't require Django database connection. Can be run with standard Python unittest or pytest.

**Coverage:**
- Temporal segmentation (time-based grouping)
- Spatial clustering (DBSCAN and radius-based)
- Linearity calculation
- Polygon vs linestring classification
- Convex hull polygon creation
- Integration tests with realistic patterns

**Run tests:**
```bash
# Using unittest
python -m unittest pio.tests.test_segmentation_standalone -v

# Using pytest (if installed)
pytest pio/tests/test_segmentation_standalone.py -v
```

### `test_segmentation.py`

Django integration tests that require database connection. Run with Django's test runner.

**Run tests:**
```bash
python manage.py test pio.tests.test_segmentation
```

## Test Cases

### Temporal Segmentation Tests
- **test_single_temporal_segment**: Verifies points within max_time_gap form one segment
- **test_multiple_temporal_segments**: Verifies points with large time gaps split into multiple segments

### Spatial Clustering Tests
- **test_dbscan_single_cluster**: Tests standard DBSCAN clustering with distance threshold
- **test_radius_based_clustering_overlap**: Tests radius-based mode with overlapping circles
- **test_radius_based_clustering_no_overlap**: Tests radius-based mode rejects non-overlapping points

### Linearity Calculation Tests
- **test_perfectly_linear**: Verifies straight line has linearity ~1.0
- **test_circular_pattern**: Verifies circular pattern has low linearity (<0.3)

### Convex Hull Polygon Tests
- **test_convex_hull_from_low_linearity**: Low-linearity points create polygon via convex hull
- **test_linestring_from_high_linearity**: High-linearity points create linestring

### Integration Tests
- **test_segment_polygon_from_circular_path**: Circular walking path creates polygon
- **test_segment_linestring_from_linear_path**: Linear walking path creates linestring
- **test_radius_mode_clusters_overlapping_points**: Radius mode properly clusters overlapping uncertainty circles

## Test Data

Tests use synthetic data with realistic coordinates near Mount Adams, Washington:
- Latitude: ~46.15° N
- Longitude: ~-121.48° W
- Typical radius values: 50-150 meters
- Typical spacing: 100-500 meters

## Expected Results

### Standard Mode (DBSCAN)
- Points within `max_distance` (default: 150m) cluster together
- Temporal gaps > `max_time_gap` (default: 180s) split into segments
- Linearity threshold (default: 0.6) determines polygon vs linestring

### Radius Mode
- Points cluster when: `distance(A, B) < radius(A) + radius(B)`
- Useful for GPS accuracy circles or uncertainty regions
- Same linearity logic applies to resulting clusters

## Example Test Run

```bash
$ python -m unittest pio.tests.test_segmentation_standalone -v

test_convex_hull_from_low_linearity ... ok
test_linestring_from_high_linearity ... ok
test_radius_mode_clusters_overlapping_points ... ok
test_segment_linestring_from_linear_path ... ok
test_segment_polygon_from_circular_path ... ok
test_circular_pattern ... ok
test_perfectly_linear ... ok
test_dbscan_single_cluster ... ok
test_radius_based_clustering_no_overlap ... ok
test_radius_based_clustering_overlap ... ok
test_multiple_temporal_segments ... ok
test_single_temporal_segment ... ok

----------------------------------------------------------------------
Ran 12 tests in 0.022s

OK
```

## Adding New Tests

When adding segmentation features, add corresponding tests:

1. **Unit tests**: Add to `test_segmentation_standalone.py` for algorithm-level tests
2. **Integration tests**: Add realistic scenarios that combine multiple features
3. **Django tests**: Add to `test_segmentation.py` for database-dependent tests

Example test structure:
```python
def test_new_feature(self):
    """Brief description of what this test verifies"""
    segmenter = GeometrySegmenter(
        # configuration parameters
    )

    points = [
        # Create test data
    ]

    results = segmenter.segment_session(points)

    # Assertions
    self.assertEqual(len(results['polygons']), expected_count)
```

## Continuous Integration

These tests should be run:
- Before committing changes to segmentation code
- In CI/CD pipeline
- When modifying segmentation parameters

## Related Documentation

- Main segmentation docs: `docs/source/segmentation.rst`
- Command usage: `python manage.py segment_survey_points --help`
- API documentation: See docstrings in `pio/segmentation/segmenter.py`
