# Generated by Django 2.2.7 on 2019-12-03 17:25

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('support', '0002_nullable_issue_caller'),
    ]

    operations = [
        migrations.AlterField(
            model_name='supportcustomer',
            name='user',
            field=models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL),
        ),
    ]
