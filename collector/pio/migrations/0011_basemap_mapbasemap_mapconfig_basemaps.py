# Generated manually for basemap feature
# Models: BaseMap, MapBasemap, and MapConfig.basemaps relationship

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('pio', '0010_merge_20251011_2151'),
    ]

    operations = [
        migrations.CreateModel(
            name='BaseMap',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100)),
                ('slug', models.SlugField()),
                ('tile_url', models.URLField(help_text='Tile URL template with {z}/{y}/{x} placeholders (e.g., https://server.com/service/MapServer/tile/{z}/{y}/{x})', max_length=500)),
                ('attribution', models.TextField(blank=True, help_text='Attribution text for the basemap')),
            ],
            options={
                'verbose_name_plural': 'Base Maps',
            },
        ),
        migrations.CreateModel(
            name='MapBasemap',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('min_zoom', models.FloatField(default=0, help_text='Minimum zoom level (0-23)')),
                ('max_zoom', models.FloatField(default=23, help_text='Maximum zoom level (0-23)')),
                ('opacity', models.FloatField(default=1.0, help_text='Opacity 0.0-1.0')),
                ('z_index', models.IntegerField(default=0, help_text='Rendering order (lower values render first/bottom)')),
                ('basemap', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='pio.basemap')),
                ('mapconfig', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='pio.mapconfig')),
            ],
            options={
                'ordering': ['z_index'],
                'unique_together': {('mapconfig', 'z_index')},
            },
        ),
        migrations.AddField(
            model_name='mapconfig',
            name='basemaps',
            field=models.ManyToManyField(blank=True, help_text='Basemap tile layers for this map', related_name='mapconfigs', through='pio.MapBasemap', to='pio.basemap'),
        ),
    ]
