# -*- coding: utf-8 -*-
# Generated by Django 1.11.13 on 2018-08-29 12:38
from __future__ import unicode_literals

from django.db import migrations, models
import waldur_core.core.validators


class Migration(migrations.Migration):

    dependencies = [
        ('marketplace', '0026_offering_options'),
    ]

    operations = [
        migrations.AlterField(
            model_name='offering',
            name='thumbnail',
            field=models.FileField(blank=True, null=True, upload_to='marketplace_service_offering_thumbnails', validators=[waldur_core.core.validators.FileTypeValidator(allowed_types=['image/png', 'image/jpeg', 'image/svg', 'image/svg+xml'])]),
        ),
    ]
