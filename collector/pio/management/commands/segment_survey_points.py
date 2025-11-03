"""
Django management command for segmenting survey points.

Usage:
    python manage.py segment_survey_points --responseid ABC123XYZ
    python manage.py segment_survey_points --responseid ABC123XYZ --output results.geojson
    python manage.py segment_survey_points --responseid ABC123XYZ --save-layers
    python manage.py segment_survey_points --all
"""

import hashlib
import json
from django.core.management.base import BaseCommand, CommandError
from django.utils.text import slugify
from pio.models import SurveyPoint, FeatureLayer
from pio.segmentation import GeometrySegmenter, SurveyPointData, format_results, export_geojson


class Command(BaseCommand):
    help = 'Segment survey points into polygons, linestrings, and individual points'

    def add_arguments(self, parser):
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
            help='Process all response IDs'
        )
        parser.add_argument(
            '--input-file',
            type=str,
            help='Path to GeoJSON file with survey points (alternative to database query)'
        )

        # Segmentation parameters
        parser.add_argument(
            '--max-time-gap',
            type=float,
            default=180.0,
            help='Maximum time gap in seconds (default: 180)'
        )
        parser.add_argument(
            '--max-distance',
            type=float,
            default=150.0,
            help='Maximum distance in meters (default: 150)'
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
            default=100.0,
            help='Polygon closure threshold in meters (default: 100)'
        )
        parser.add_argument(
            '--linearity-threshold',
            type=float,
            default=0.6,
            help='Linearity threshold below which to create polygons via convex hull (0-1, default: 0.6)'
        )
        parser.add_argument(
            '--use-radius',
            action='store_true',
            help='Use point radius for adjacency detection (points are adjacent if their radii overlap)'
        )

        # Output options
        parser.add_argument(
            '--output',
            type=str,
            help='Output GeoJSON file path'
        )
        parser.add_argument(
            '--save-layers',
            action='store_true',
            help='Save detected geometries as FeatureLayers in the database'
        )

    def handle(self, *args, **options):
        # Validate input
        if options['input_file']:
            # File input mode
            if options['responseid'] or options['all']:
                raise CommandError("Cannot use --input-file with --responseid or --all")
        elif not options['responseid'] and not options['all']:
            raise CommandError("Either --responseid, --all, or --input-file must be specified")

        # Initialize segmenter
        segmenter = GeometrySegmenter(
            max_time_gap=options['max_time_gap'],
            max_distance=options['max_distance'],
            min_cluster_points=options['min_cluster_points'],
            polygon_closure_threshold=options['polygon_threshold'],
            linearity_threshold=options['linearity_threshold'],
            use_radius_adjacency=options['use_radius']
        )

        if options['input_file']:
            # Process GeoJSON file
            points = self._load_points_from_file(options['input_file'])
            if not points:
                raise CommandError(f"No points found in file {options['input_file']}")

            responseid = points[0].responseid if points else 'unknown'
            self.stdout.write(f"Processing {len(points)} points from file...")

            # Segment
            results = segmenter.segment_session(points)

            # Display
            self.stdout.write(format_results(results))

            # Export if requested
            if options['output']:
                export_geojson(results, options['output'])
                self.stdout.write(
                    self.style.SUCCESS(f"✓ Exported to {options['output']}")
                )

            # Note: --save-layers not supported for file input
            if options['save_layers']:
                self.stdout.write(
                    self.style.WARNING("Note: --save-layers is only supported for database queries")
                )

        elif options['all']:
            # Process all response IDs
            responseids = SurveyPoint.objects.filter(
                deleted=False
            ).values_list('responseid', flat=True).distinct()

            self.stdout.write(f"Processing {len(responseids)} response IDs...")

            all_results = []
            param_hash = self._generate_params_hash(options) if options['save_layers'] else None

            for responseid in responseids:
                points = self._fetch_points(responseid, options.get('projectid'))
                if points:
                    results = segmenter.segment_session(points)
                    all_results.append((responseid, results))

                    self.stdout.write(f"\nResponse ID: {responseid}")
                    self.stdout.write(format_results(results))

                    # Save to FeatureLayers if requested
                    if options['save_layers']:
                        self._save_to_feature_layers(responseid, results, param_hash)

            # Display summary statistics
            self._display_summary(all_results)

            # Export combined results if requested
            if options['output']:
                combined = {
                    'polygons': [],
                    'linestrings': [],
                    'points': []
                }
                for _, results in all_results:
                    combined['polygons'].extend(results['polygons'])
                    combined['linestrings'].extend(results['linestrings'])
                    combined['points'].extend(results['points'])

                export_geojson(combined, options['output'])
                self.stdout.write(
                    self.style.SUCCESS(f"\n✓ Exported to {options['output']}")
                )
        else:
            # Process single response ID
            responseid = options['responseid']
            points = self._fetch_points(responseid, options.get('projectid'))

            if not points:
                raise CommandError(f"No points found for responseid={responseid}")

            self.stdout.write(f"Processing {len(points)} points for {responseid}...")

            # Segment
            results = segmenter.segment_session(points)

            # Display
            self.stdout.write(format_results(results))

            # Export if requested
            if options['output']:
                export_geojson(results, options['output'])
                self.stdout.write(
                    self.style.SUCCESS(f"✓ Exported to {options['output']}")
                )

            # Save to FeatureLayers if requested
            if options['save_layers']:
                param_hash = self._generate_params_hash(options)
                self._save_to_feature_layers(responseid, results, param_hash)

    def _display_summary(self, all_results):
        """Display summary statistics across all response IDs"""
        import numpy as np

        total_polygons = 0
        total_linestrings = 0
        total_points = 0
        all_min_distances = []
        all_median_distances = []
        all_max_distances = []

        for _, results in all_results:
            total_polygons += len(results['polygons'])
            total_linestrings += len(results['linestrings'])
            total_points += len(results['points'])

            # Collect distance statistics from temporal segments
            for seg in results.get('temporal_segments', []):
                if seg['point_count'] >= 2:
                    all_min_distances.append(seg['min_distance'])
                    all_median_distances.append(seg['median_distance'])
                    all_max_distances.append(seg['max_distance'])

        # Display summary
        self.stdout.write("\n" + "="*70)
        self.stdout.write("SUMMARY ACROSS ALL RESPONSE IDs")
        self.stdout.write("="*70)
        self.stdout.write(f"\nTotal Response IDs processed: {len(all_results)}")
        self.stdout.write(f"Total Polygons found: {total_polygons}")
        self.stdout.write(f"Total LineStrings found: {total_linestrings}")
        self.stdout.write(f"Total Individual Points: {total_points}")

        if all_median_distances:
            self.stdout.write("\nSpatial Distance Statistics (across all temporal clusters):")
            self.stdout.write(f"  Min distance (smallest):     {min(all_min_distances):7.1f} m")
            self.stdout.write(f"  Median distance (overall):   {np.median(all_median_distances):7.1f} m")
            self.stdout.write(f"  Max distance (largest):      {max(all_max_distances):7.1f} m")

        self.stdout.write("\n" + "="*70 + "\n")

    def _fetch_points(self, responseid, projectid=None):
        """Fetch points from database and convert to SurveyPointData objects"""
        queryset = SurveyPoint.objects.filter(
            responseid=responseid,
            deleted=False
        ).order_by('timestamp_add')

        if projectid is not None:
            queryset = queryset.filter(projectid=projectid)

        # Convert to SurveyPointData objects
        points = []
        for p in queryset:
            points.append(SurveyPointData(
                id=p.id,
                x=p.geom.x,
                y=p.geom.y,
                timestamp=p.timestamp,
                responseid=p.responseid,
                projectid=p.projectid,
                description=p.description,
                radius=float(p.radius) if p.radius else None,
                resolution=p.resolution
            ))

        return points

    def _generate_params_hash(self, options):
        """Generate a hash of segmentation parameters to prevent duplicates"""
        params = {
            'max_time_gap': options['max_time_gap'],
            'max_distance': options['max_distance'],
            'min_cluster_points': options['min_cluster_points'],
            'polygon_threshold': options['polygon_threshold'],
            'linearity_threshold': options['linearity_threshold'],
            'use_radius': options['use_radius']
        }
        # Create a stable JSON representation and hash it
        params_str = json.dumps(params, sort_keys=True)
        return hashlib.md5(params_str.encode()).hexdigest()[:8]

    def _save_to_feature_layers(self, responseid, results, param_hash):
        """Save segmentation results to FeatureLayers"""
        created_layers = []

        # Save polygons if any
        if results['polygons']:
            layer_name = f"seg_{responseid}_{param_hash}_polygons"
            layer = self._create_or_update_feature_layer(
                layer_name,
                results['polygons'],
                'polygon',
                responseid,
                param_hash
            )
            if layer:
                created_layers.append(layer)
                self.stdout.write(
                    self.style.SUCCESS(f"✓ Saved {len(results['polygons'])} polygons to layer: {layer_name}")
                )

        # Save linestrings if any
        if results['linestrings']:
            layer_name = f"seg_{responseid}_{param_hash}_linestrings"
            layer = self._create_or_update_feature_layer(
                layer_name,
                results['linestrings'],
                'linestring',
                responseid,
                param_hash
            )
            if layer:
                created_layers.append(layer)
                self.stdout.write(
                    self.style.SUCCESS(f"✓ Saved {len(results['linestrings'])} linestrings to layer: {layer_name}")
                )

        return created_layers

    def _create_or_update_feature_layer(self, name, geometries, geom_type, responseid, param_hash):
        """Create or update a FeatureLayer with the given geometries"""
        features = []

        for idx, geom_data in enumerate(geometries):
            if geom_type == 'polygon':
                geometry = {
                    'type': 'Polygon',
                    'coordinates': [geom_data['coordinates']]
                }
                properties = {
                    'geometry_type': 'polygon',
                    'point_count': geom_data['point_count'],
                    'point_ids': geom_data['point_ids'],
                    'area': geom_data['area'],
                    'method': geom_data.get('method', 'explicit_closure'),
                    'linearity': geom_data.get('linearity'),
                    'timestamp_start': geom_data['timestamp_range'][0],
                    'timestamp_end': geom_data['timestamp_range'][1],
                    'responseid': responseid,
                    'param_hash': param_hash
                }
            elif geom_type == 'linestring':
                geometry = {
                    'type': 'LineString',
                    'coordinates': geom_data['coordinates']
                }
                properties = {
                    'geometry_type': 'linestring',
                    'point_count': geom_data['point_count'],
                    'point_ids': geom_data['point_ids'],
                    'length': geom_data['length'],
                    'linearity': geom_data.get('linearity', 0),
                    'timestamp_start': geom_data['timestamp_range'][0],
                    'timestamp_end': geom_data['timestamp_range'][1],
                    'responseid': responseid,
                    'param_hash': param_hash
                }
            else:
                continue

            features.append({
                'type': 'Feature',
                'geometry': geometry,
                'properties': properties
            })

        geojson = {
            'type': 'FeatureCollection',
            'features': features
        }

        # Create or update the layer
        slug = slugify(name)
        layer, created = FeatureLayer.objects.update_or_create(
            slug=slug,
            defaults={
                'name': name,
                'geojson': geojson
            }
        )

        return layer

    def _load_points_from_file(self, filepath):
        """Load survey points from a GeoJSON file"""
        import os
        from datetime import datetime

        if not os.path.exists(filepath):
            raise CommandError(f"File not found: {filepath}")

        try:
            with open(filepath, 'r') as f:
                geojson_data = json.load(f)
        except json.JSONDecodeError as e:
            raise CommandError(f"Invalid JSON in file: {e}")

        if geojson_data.get('type') != 'FeatureCollection':
            raise CommandError("GeoJSON must be a FeatureCollection")

        features = geojson_data.get('features', [])
        if not features:
            raise CommandError("No features found in GeoJSON")

        # Convert features to SurveyPointData objects
        points = []
        for feature in features:
            if feature.get('geometry', {}).get('type') != 'Point':
                continue  # Skip non-point features

            coords = feature['geometry']['coordinates']
            props = feature.get('properties', {})

            # Parse timestamp - handle both timestamp and timestamp_add fields
            timestamp = props.get('timestamp_add') or props.get('timestamp')
            if not timestamp:
                self.stdout.write(
                    self.style.WARNING(f"Skipping feature {props.get('id')}: missing timestamp")
                )
                continue

            # Create SurveyPointData
            point = SurveyPointData(
                id=props.get('id', len(points)),
                x=coords[0],
                y=coords[1],
                timestamp=timestamp,
                responseid=props.get('responseid', 'unknown'),
                projectid=props.get('projectid', 0),
                description=props.get('description'),
                radius=props.get('radius'),
                resolution=props.get('resolution')
            )
            points.append(point)

        self.stdout.write(f"Loaded {len(points)} points from {filepath}")
        return points
