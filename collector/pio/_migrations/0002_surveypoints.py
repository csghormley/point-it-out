# Generated by Django 5.0.1 on 2024-01-25 00:22

import django.contrib.gis.db.models.fields
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('pio', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='SurveyPoints',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('cartodb_id', models.IntegerField()),
                ('description', models.CharField()),
                ('datatype', models.PositiveSmallIntegerField()),
                ('ipaddress', models.GenericIPAddressField(null=True)),
                ('timestamp', models.CharField(max_length=60)),
                ('timestamp_add', models.DateTimeField(auto_now_add=True)),
                ('timestamp_edit', models.DateTimeField(auto_now=True)),
                ('radius', models.FloatField()),
                ('responseid', models.CharField(max_length=20)),
                ('geom', django.contrib.gis.db.models.fields.PointField(srid=4326)),
            ],
        ),
    ]