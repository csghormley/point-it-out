"""
Django management command for segmenting survey points.

Usage:
    python manage.py segment_survey_points --responseid ABC123XYZ
    python manage.py segment_survey_points --responseid ABC123XYZ --output results.geojson
    python manage.py segment_survey_points --all
"""

from django.core.management.base import BaseCommand, CommandError
from pio.models import SurveyPoint
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
            default=50.0,
            help='Maximum distance in meters (default: 50)'
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
            help='Polygon closure threshold in meters (default: 20)'
        )

        # Output options
        parser.add_argument(
            '--output',
            type=str,
            help='Output GeoJSON file path'
        )

    def handle(self, *args, **options):
        # Validate input
        if not options['responseid'] and not options['all']:
            raise CommandError("Either --responseid or --all must be specified")

        # Initialize segmenter
        segmenter = GeometrySegmenter(
            max_time_gap=options['max_time_gap'],
            max_distance=options['max_distance'],
            min_cluster_points=options['min_cluster_points'],
            polygon_closure_threshold=options['polygon_threshold']
        )

        if options['all']:
            # Process all response IDs
            responseids = SurveyPoint.objects.filter(
                deleted=False
            ).values_list('responseid', flat=True).distinct()

            self.stdout.write(f"Processing {len(responseids)} response IDs...")

            all_results = []
            for responseid in responseids:
                points = self._fetch_points(responseid, options.get('projectid'))
                if points:
                    results = segmenter.segment_session(points)
                    all_results.append((responseid, results))

                    self.stdout.write(f"\nResponse ID: {responseid}")
                    self.stdout.write(format_results(results))

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
