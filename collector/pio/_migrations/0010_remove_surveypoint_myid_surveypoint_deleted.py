# Generated by Django 5.0.1 on 2024-02-03 01:22

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('pio', '0009_alter_surveypoint_myid'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='surveypoint',
            name='myid',
        ),
        migrations.AddField(
            model_name='surveypoint',
            name='deleted',
            field=models.BooleanField(default=False),
        ),
    ]
