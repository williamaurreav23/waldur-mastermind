# -*- coding: utf-8 -*-
# Generated by Django 1.9 on 2017-03-02 15:24
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


def connect_floating_ips_to_internal_ips(apps, schema_editor):
    Instance = apps.get_model('openstack_tenant', 'Instance')
    InternalIP = apps.get_model('openstack_tenant', 'InternalIP')

    for instance in Instance.objects.iterator():
        floating_ip = instance.external_ip
        internal_ip = InternalIP.objects.filter(instance=instance).first()
        # we assume that instance has only one internal IP.
        if not floating_ip or not internal_ip:
            continue
        floating_ip.internal_ip = internal_ip
        floating_ip.save()


class Migration(migrations.Migration):

    dependencies = [
        ('openstack_tenant', '0021_instance_subnets'),
    ]

    operations = [
        migrations.AddField(
            model_name='floatingip',
            name='internal_ip',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='floating_ips', to='openstack_tenant.InternalIP'),
        ),
        migrations.RunPython(connect_floating_ips_to_internal_ips),
        migrations.AlterField(
            model_name='floatingip',
            name='address',
            field=models.GenericIPAddressField(null=True, protocol='IPv4'),
        ),
        migrations.AlterUniqueTogether(
            name='floatingip',
            unique_together=set([]),
        ),
        migrations.AddField(
            model_name='internalip',
            name='backend_id',
            field=models.CharField(blank=True, max_length=255),
        ),
    ]