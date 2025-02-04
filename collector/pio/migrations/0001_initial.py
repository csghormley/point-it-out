# Generated by Django 5.0.3 on 2024-04-19 01:50

import django.contrib.gis.db.models.fields
import pio.models
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='MapConfig',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=50)),
                ('slug', models.SlugField()),
                ('config', models.JSONField(default=pio.models.mapconfig_default)),
            ],
        ),
        migrations.CreateModel(
            name='SurveyPoint',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('description', models.CharField(null=True)),
                ('projectid', models.PositiveSmallIntegerField()),
                ('ipaddress', models.CharField(max_length=20, null=True)),
                ('timestamp', models.CharField(max_length=60)),
                ('timestamp_add', models.DateTimeField(auto_now_add=True)),
                ('timestamp_edit', models.DateTimeField(auto_now=True)),
                ('radius', models.CharField(max_length=20)),
                ('resolution', models.FloatField(help_text='Display resolution at point creation time, in meters per pixel.', max_length=10, null=True)),
                ('responseid', models.CharField(max_length=20)),
                ('geom', django.contrib.gis.db.models.fields.PointField(srid=4326)),
                ('deleted', models.BooleanField(default=False)),
            ],
        ),
        migrations.CreateModel(
            name='VisitorBehavior',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('responseid', models.CharField(max_length=20)),
                ('timestamp_add', models.DateTimeField(auto_now_add=True)),
                ('logdata', models.JSONField()),
            ],
        ),
        migrations.CreateModel(
            name='WorldBorder',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=50)),
                ('area', models.IntegerField()),
                ('pop2005', models.IntegerField(verbose_name='Population 2005')),
                ('fips', models.CharField(max_length=2, null=True, verbose_name='FIPS Code')),
                ('iso2', models.CharField(max_length=2, verbose_name='2 Digit ISO')),
                ('iso3', models.CharField(max_length=3, verbose_name='3 Digit ISO')),
                ('un', models.IntegerField(verbose_name='United Nations Code')),
                ('region', models.IntegerField(verbose_name='Region Code')),
                ('subregion', models.IntegerField(verbose_name='Sub-Region Code')),
                ('lon', models.FloatField()),
                ('lat', models.FloatField()),
                ('mpoly', django.contrib.gis.db.models.fields.MultiPolygonField(srid=4326)),
            ],
        ),
    ]
