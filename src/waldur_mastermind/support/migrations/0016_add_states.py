# -*- coding: utf-8 -*-
# Generated by Django 1.11.7 on 2018-03-13 12:18
from __future__ import unicode_literals

from django.db import migrations, models
import django_fsm


class Migration(migrations.Migration):

    dependencies = [
        ('support', '0015_offering_report'),
    ]

    operations = [
        migrations.AddField(
            model_name='attachment',
            name='error_message',
            field=models.TextField(blank=True),
        ),
        migrations.AddField(
            model_name='attachment',
            name='state',
            field=django_fsm.FSMIntegerField(choices=[(5, 'Creation Scheduled'), (6, 'Creating'), (1, 'Update Scheduled'), (2, 'Updating'), (7, 'Deletion Scheduled'), (8, 'Deleting'), (3, 'OK'), (4, 'Erred')], default=5),
        ),
        migrations.AddField(
            model_name='comment',
            name='error_message',
            field=models.TextField(blank=True),
        ),
        migrations.AddField(
            model_name='comment',
            name='state',
            field=django_fsm.FSMIntegerField(choices=[(5, 'Creation Scheduled'), (6, 'Creating'), (1, 'Update Scheduled'), (2, 'Updating'), (7, 'Deletion Scheduled'), (8, 'Deleting'), (3, 'OK'), (4, 'Erred')], default=5),
        ),
        migrations.AddField(
            model_name='issue',
            name='error_message',
            field=models.TextField(blank=True),
        ),
        migrations.AddField(
            model_name='issue',
            name='state',
            field=django_fsm.FSMIntegerField(choices=[(5, 'Creation Scheduled'), (6, 'Creating'), (1, 'Update Scheduled'), (2, 'Updating'), (7, 'Deletion Scheduled'), (8, 'Deleting'), (3, 'OK'), (4, 'Erred')], default=5),
        ),
    ]
