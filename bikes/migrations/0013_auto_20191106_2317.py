# Generated by Django 2.2.4 on 2019-11-06 23:17

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('bikes', '0012_merge_20191106_1230'),
    ]

    operations = [
        migrations.AlterField(
            model_name='userprofile',
            name='charges',
            field=models.FloatField(default=0),
        ),
    ]