# -*- coding: utf-8 -*-
# Generated by Django 1.9 on 2016-02-18 19:35
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0001_initial'),
    ]

    operations = [
        migrations.RenameField(
            model_name='member',
            old_name='expected_grad_date',
            new_name='graduation_date',
        ),
    ]
