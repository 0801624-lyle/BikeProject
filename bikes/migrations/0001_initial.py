# Generated by Django 2.2.4 on 2019-10-14 15:43

from django.conf import settings
import django.core.validators
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Discounts',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('code', models.CharField(blank=True, max_length=12, null=True, unique=True)),
                ('date_from', models.DateField()),
                ('date_to', models.DateField()),
                ('discount_amount', models.FloatField(validators=[django.core.validators.MinValueValidator(0), django.core.validators.MaxValueValidator(1.0)])),
            ],
        ),
        migrations.CreateModel(
            name='Location',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('station_name', models.CharField(max_length=200, unique=True)),
                ('latitude', models.FloatField()),
                ('longitude', models.FloatField()),
            ],
            options={
                'ordering': ('station_name',),
            },
        ),
        migrations.CreateModel(
            name='UserDiscounts',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('date_used', models.DateField(auto_now_add=True)),
                ('amount_saved', models.FloatField()),
                ('discounts', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='bikes.Discounts')),
            ],
        ),
        migrations.CreateModel(
            name='UserProfile',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('membership_type', models.IntegerField(choices=[(1, 'Standard'), (2, 'Student'), (3, 'Pensioner'), (4, 'Staff')], default=1)),
                ('user_type', models.IntegerField(choices=[(1, 'Customer'), (2, 'Operator'), (3, 'Manager')], default=1)),
                ('balance', models.FloatField(default=0)),
                ('charges', models.FloatField(default=0)),
                ('discounts', models.ManyToManyField(through='bikes.UserDiscounts', to='bikes.Discounts')),
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.AddField(
            model_name='userdiscounts',
            name='user',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='bikes.UserProfile'),
        ),
        migrations.CreateModel(
            name='Bikes',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('status', models.IntegerField(choices=[(1, 'Available'), (2, 'Out on hire'), (3, 'Needs repaired')])),
                ('location', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='bikes.Location')),
            ],
        ),
        migrations.CreateModel(
            name='BikeRepairs',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('date_malfunctioned', models.DateTimeField()),
                ('date_repaired', models.DateTimeField(null=True)),
                ('repair_cost', models.FloatField(null=True)),
                ('bike', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='bikes.Bikes')),
            ],
        ),
        migrations.CreateModel(
            name='BikeHires',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('date_hired', models.DateTimeField(auto_now_add=True)),
                ('date_returned', models.DateTimeField(blank=True, null=True)),
                ('charges', models.FloatField(blank=True, null=True)),
                ('bike', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='bikes.Bikes')),
                ('discount_applied', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='bikes.Discounts')),
                ('end_station', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='end_station', to='bikes.Location')),
                ('start_station', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='start_station', to='bikes.Location')),
                ('user', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='bikes.UserProfile')),
            ],
        ),
    ]
