# Generated by Django 2.0.7 on 2018-07-08 21:28

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0002_auto_20180708_2149'),
    ]

    operations = [
        migrations.AlterField(
            model_name='user',
            name='deleted_at',
            field=models.DateTimeField(blank=True, editable=False, null=True),
        ),
    ]
