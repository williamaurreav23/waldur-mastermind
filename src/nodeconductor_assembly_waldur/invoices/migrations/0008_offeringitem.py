# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion
from decimal import Decimal
import django.core.validators
import nodeconductor_assembly_waldur.invoices.utils


class Migration(migrations.Migration):

    dependencies = [
        ('support', '0006_offering'),
        ('invoices', '0007_item_remove_price'),
    ]

    operations = [
        migrations.CreateModel(
            name='OfferingItem',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('daily_price', models.DecimalField(default=0, help_text='Price per day.', max_digits=22, decimal_places=7, validators=[django.core.validators.MinValueValidator(Decimal('0'))])),
                ('start', models.DateTimeField(default=nodeconductor_assembly_waldur.invoices.utils.get_current_month_start, help_text='Date and time when package usage has started.')),
                ('end', models.DateTimeField(default=nodeconductor_assembly_waldur.invoices.utils.get_current_month_end, help_text='Date and time when package usage has ended.')),
                ('invoice', models.ForeignKey(related_name='offering_items', to='invoices.Invoice')),
                ('offering', models.ForeignKey(related_name='+', on_delete=django.db.models.deletion.SET_NULL, to='support.Offering', null=True)),
            ],
            options={
                'abstract': False,
            },
        ),
    ]
