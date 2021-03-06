# Generated by Django 2.1.7 on 2019-02-27 14:02

import django.contrib.postgres.fields.hstore
from django.db import migrations, models
from django.contrib.postgres.operations import HStoreExtension


class Migration(migrations.Migration):

    dependencies = [

        ('files', '0014_auto_20190216_1205'),
    ]

    operations = [
        HStoreExtension(),
        migrations.AddField(
            model_name='file',
            name='metadata',
            field=django.contrib.postgres.fields.hstore.HStoreField(null=True),
        ),
        migrations.AlterField(
            model_name='file',
            name='handler',
            field=models.CharField(choices=[('none', 'None'), ('avatar', 'Avatar'), ('audio_enc', 'Audio Encoding'), ('video_enc', 'Video Encoding')], default=None, max_length=9, null=True),
        ),
    ]
