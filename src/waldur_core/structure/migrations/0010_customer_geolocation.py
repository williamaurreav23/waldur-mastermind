# Generated by Django 2.2.7 on 2020-01-20 10:44

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('structure', '0009_project_is_removed'),
    ]

    operations = [
        migrations.AddField(
            model_name='customer',
            name='latitude',
            field=models.FloatField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='customer',
            name='longitude',
            field=models.FloatField(blank=True, null=True),
        ),
    ]
