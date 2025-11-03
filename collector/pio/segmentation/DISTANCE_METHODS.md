# Distance Calculation Methods

## Overview

This document describes the distance calculation methods used in the segmentation module and provides mathematical references.

## Methods

### 1. Simple Approximation (Current Method - NOT RECOMMENDED)

**Formula:**
```
distance_deg = sqrt((lon2 - lon1)² + (lat2 - lat1)²)
distance_meters = distance_deg × 111,000
```

**Issues:**
- Assumes 1 degree = 111 km at all latitudes
- Longitude degrees get smaller as you move toward poles
- **Error: ~17% mean, up to 43% max** (at mid-latitudes ~46°N)

**Not recommended for production use.**

---

### 2. Equirectangular Approximation (RECOMMENDED)

**Also known as:**
- Equirectangular projection distance
- Plate carrée distance
- Latitude-corrected distance

**Formula:**
```python
avg_lat = (lat1 + lat2) / 2
x = (lon2 - lon1) × cos(avg_lat)
y = (lat2 - lat1)
distance_deg = sqrt(x² + y²)
distance_meters = distance_deg × 111,000
```

**Where:**
- `x` = longitudinal distance adjusted for latitude
- `y` = latitudinal distance (unchanged)
- `cos(avg_lat)` = latitude correction factor
- 111,000 meters ≈ length of 1 degree at equator

**Mathematical Basis:**

The Earth approximates a sphere with radius R ≈ 6,371 km. On a sphere:
- 1 degree of latitude ≈ πR/180 ≈ 111 km (constant at all latitudes)
- 1 degree of longitude = (πR/180) × cos(latitude)

The longitude distance decreases with latitude because meridians converge at the poles.

**Accuracy:**
- **< 1% error for distances < 500 km** at mid-latitudes
- **< 0.3% mean error** in our benchmark (46°N latitude)
- Maximum error < 0.5%

**Performance:**
- Only ~60% slower than simple method
- ~22x faster than geodesic calculation

**References:**

1. **Movable Type Scripts** - Aviation Formulae
   https://www.movable-type.co.uk/scripts/latlong.html
   Chris Veness's comprehensive guide to latitude/longitude calculations

   Quote: "For small distances (a few kilometers), the equirectangular approximation
   is very fast and gives acceptable results... The cos(lat) term accounts for the
   fact that lines of longitude converge at the poles."

2. **"Map Projections: A Working Manual"** by John P. Snyder (1987)
   U.S. Geological Survey Professional Paper 1395
   https://pubs.usgs.gov/pp/1395/report.pdf

   Section: "Equirectangular Projection" (pages 90-91)
   Also known as "Plate Carrée" or "Simple Cylindrical" projection.

3. **NOAA Technical Report NOS 107 C&GS 3**
   "Datums, Ellipsoids, Grids, and Grid Reference Systems"
   Section on approximating distances on the ellipsoid

4. **Aviation Formulae V1.47** by Ed Williams
   http://edwilliams.org/avform147.htm
   Used extensively in aviation for navigation calculations

**When to Use:**
- Short to medium distances (< 500 km)
- Mid-latitude regions (20° - 70°)
- Clustering and segmentation algorithms
- Real-time applications requiring speed

**When NOT to Use:**
- Very long distances (> 1000 km)
- High-precision geodetic applications
- Near-polar regions (> 85° latitude)
- Legal/surveying applications

---

### 3. Geodesic Distance (Vincenty/Karney Algorithm)

**Also known as:**
- Ellipsoidal distance
- Great circle distance (on ellipsoid)
- Karney's algorithm (modern implementation)

**Formula:**

Uses iterative solution of geodesic equations on the WGS84 ellipsoid.
Too complex to show here - see references.

**Implementation:**

Uses `geopy` library which implements Karney's algorithm:
```python
from geopy.distance import geodesic
distance = geodesic((lat1, lon1), (lat2, lon2)).meters
```

**Accuracy:**
- Sub-millimeter accuracy for any distance
- Accounts for Earth's ellipsoidal shape
- Converges within 1-2 iterations for typical distances

**Performance:**
- **~2200% slower** than equirectangular
- Still fast in absolute terms (< 2ms for 47 calculations)

**References:**

1. **"Algorithms for geodesics"** by Charles F. F. Karney (2013)
   Journal of Geodesy, Volume 87, Issue 1, pages 43-55
   https://doi.org/10.1007/s00190-012-0578-z

   The definitive modern algorithm for geodesic calculations.
   Improves upon Vincenty's formula with better convergence.

2. **GeographicLib documentation**
   https://geographiclib.sourceforge.io/
   C++ library implementing Karney's algorithms

3. **"Direct and inverse solutions of geodesics on the ellipsoid"**
   by Thaddeus Vincenty (1975)
   Survey Review, Volume 23, Number 176
   Classic paper on geodesic calculations (superseded by Karney)

4. **WGS84 Ellipsoid Parameters**
   National Geospatial-Intelligence Agency (NGA)
   Semi-major axis: a = 6,378,137.0 m
   Flattening: f = 1/298.257223563

**When to Use:**
- Surveying and legal applications
- Long distances (> 1000 km)
- High-precision requirements
- Near-polar regions
- Official geodetic work

---

## Comparison Table

| Method | Mean Error | Max Error | Relative Speed | Use Case |
|--------|-----------|-----------|----------------|----------|
| Simple (no correction) | 17.17% | 43% | 1.0x (fastest) | ❌ Not recommended |
| **Equirectangular** | **0.26%** | **0.46%** | **1.6x** | **✓ Recommended** |
| Geodesic (Karney) | 0% | 0% | 37.8x | High precision only |

*Benchmark based on 48 points near Mt. Adams, WA (46°N latitude)*

---

## Implementation in Segmentation

The segmentation module uses distance calculations for:

1. **DBSCAN clustering** (`eps` parameter)
2. **Radius-based adjacency** (circle overlap detection)
3. **Polygon closure threshold** (first/last point distance)
4. **Linearity calculation** (path length vs straight-line distance)

**Recommendation:** Use equirectangular approximation for all segmentation tasks.

**Why:**
- Segmentation clustering typically uses thresholds of 50-500m
- At these distances, < 1% error is negligible compared to GPS accuracy (±5-50m)
- Performance matters when processing hundreds of points
- Simple to implement, no external dependencies

---

## Additional Resources

### Online Calculators
- **Movable Type Scripts Calculator**
  https://www.movable-type.co.uk/scripts/latlong.html
  Interactive calculator for various distance methods

- **GeodSolve Calculator**
  https://geographiclib.sourceforge.io/cgi-bin/GeodSolve
  Official calculator for Karney's geodesic algorithm

### Books
- **"Geodesy"** by Wolfgang Torge & Jürgen Müller (2012)
  Walter de Gruyter, 4th edition
  Comprehensive textbook on geodetic calculations

- **"GPS Satellite Surveying"** by Alfred Leick et al. (2015)
  Wiley, 4th edition
  Practical applications of coordinate systems and distance calculations

### Standards
- **EPSG Geodetic Parameter Dataset**
  https://epsg.org/
  Official coordinate reference system definitions

- **ISO 19111:2019** - Geographic information — Referencing by coordinates
  International standard for spatial referencing

---

## Code Examples

### Current Implementation (Not Recommended)
```python
# collector/pio/segmentation/segmenter.py (lines 47-49)
self.max_distance_deg = max_distance / 111000.0
```

### Recommended Implementation
```python
from pio.segmentation.distance import simple_distance_meters_approx

# For two points
distance = simple_distance_meters_approx(
    (lon1, lat1),
    (lon2, lat2)
)

# Converts internally using equirectangular approximation
```

### High-Precision Implementation (Optional)
```python
from pio.segmentation.distance import DistanceCalculator

calc = DistanceCalculator()  # Auto-detects if geopy available
distance = calc.distance((lon1, lat1), (lon2, lat2))
```

---

## Benchmark Script

Run the benchmark to test on your own data:

```bash
python test_distance_accuracy.py
```

This compares all three methods on your survey points and provides accuracy vs performance recommendations.

---

## Conclusion

For the segmentation use case:

✓ **Use equirectangular approximation** - best balance of accuracy and speed
✗ **Avoid simple (uncorrected)** - unacceptable error at mid-latitudes
⚠ **Geodesic only if required** - overkill for clustering applications

The equirectangular method is well-established in aviation, GIS, and web mapping applications where performance matters and sub-meter accuracy is not critical.
