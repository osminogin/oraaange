# Generated by Django 2.0.7 on 2018-07-08 21:28

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('abuses', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='adabuse',
            name='deleted_at',
            field=models.DateTimeField(blank=True, editable=False, null=True),
        ),
        migrations.AlterField(
            model_name='userabuse',
            name='deleted_at',
            field=models.DateTimeField(blank=True, editable=False, null=True),
        ),
    ]
