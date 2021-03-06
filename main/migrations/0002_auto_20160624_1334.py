# -*- coding: utf-8 -*-
# Generated by Django 1.9.7 on 2016-06-24 10:34
from __future__ import unicode_literals

import datetime
from django.db import migrations, models
import django.db.models.deletion
from django.utils.timezone import utc


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='PostHistory',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('commented', models.DateTimeField(blank=True, null=True)),
                ('up_voted', models.DateTimeField(blank=True, null=True)),
                ('down_voted', models.DateTimeField(blank=True, null=True)),
                ('un_voted', models.DateTimeField(blank=True, null=True)),
                ('last_action', models.DateTimeField(blank=True, null=True)),
                ('post', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='history', to='main.Post')),
            ],
        ),
        migrations.AddField(
            model_name='postmark',
            name='created',
            field=models.DateTimeField(auto_created=True, default=datetime.datetime(2016, 6, 24, 10, 34, 12, 75881, tzinfo=utc)),
            preserve_default=False,
        ),
    ]
