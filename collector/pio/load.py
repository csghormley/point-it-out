from pathlib import Path
from django.contrib.gis.utils import LayerMapping
from .models import WorldBorder, SurveyPoint

world_mapping = {
    "fips": "FIPS",
    "iso2": "ISO2",
    "iso3": "ISO3",
    "un": "UN",
    "name": "NAME",
    "area": "AREA",
    "pop2005": "POP2005",
    "region": "REGION",
    "subregion": "SUBREGION",
    "lon": "LON",
    "lat": "LAT",
    "mpoly": "MULTIPOLYGON",
}

world_shp = Path(__file__).resolve().parent / "data" / "TM_WORLD_BORDERS-0.3.shp"

def world_mapping_run(verbose=True):
    lm = LayerMapping(WorldBorder, world_shp, world_mapping, transform=False)
    lm.save(strict=True, verbose=verbose)

# Auto-generated `LayerMapping` dictionary for SurveyPoints model
surveypoint_mapping = {
#    'cartodb_id': 'cartodb_id',
    'description': 'description',
    'datatype': 'datatype',
    'ipaddress': 'ipaddress',
    'timestamp': 'timestamp',
    'radius': 'radius',
    'responseid': 'responseid',
    'geom': 'POINT',
}

surveypoint_json = Path(__file__).resolve().parent / "data" / "surveypoints.json"

def surveypoint_mapping_run(verbose=True):
    lm = LayerMapping(SurveyPoint, surveypoints_json, surveypoint_mapping, transform=False)
    lm.save(strict=True, verbose=verbose)
