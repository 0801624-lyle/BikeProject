# Generated by Django 2.2.4 on 2019-11-01 15:29

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('bikes', '0010_auto_20191030_2021'),
    ]

    operations = [
        migrations.AlterField(
            model_name='bikes',
            name='status',
            field=models.IntegerField(choices=[(1, 'Available'), (2, 'Out on hire'), (3, 'Being repaired')]),
        ),
        migrations.AlterField(
            model_name='userprofile',
            name='charges',
            field=models.FloatField(default=10),
        ),
    ]
