# Generated by Django 2.0.8 on 2018-08-23 17:25

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('files', '0003_auto_20180827_1023'),
    ]

    operations = [
        migrations.AddField(
            model_name='file',
            name='preview',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='original_file', to='files.File'),
        ),
    ]
