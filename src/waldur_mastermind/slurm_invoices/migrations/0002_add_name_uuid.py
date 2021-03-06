# -*- coding: utf-8 -*-
# Generated by Django 1.11.1 on 2017-09-22 08:49
from django.db import migrations, models
import waldur_core.core.fields
import waldur_core.core.validators


class Migration(migrations.Migration):

    dependencies = [
        ('slurm_invoices', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='slurmpackage',
            name='name',
            field=models.CharField(default='default', max_length=150, validators=[waldur_core.core.validators.validate_name], verbose_name='name'),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='slurmpackage',
            name='uuid',
            field=waldur_core.core.fields.UUIDField(),
        ),
    ]
