# Generated by Django 2.2.4 on 2019-10-18 09:50

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('reports', '0001_initial'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='locationbikecount',
            options={'ordering': ('datetime',)},
        ),
    ]
