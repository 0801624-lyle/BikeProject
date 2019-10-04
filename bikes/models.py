from django.db import models
from django.contrib.auth.models import User

class Bikes(models.Model):
    status = models.CharField(max_length = 200)
    location = models.CharField(max_length = 200)
    condition = models.CharField(max_length = 200)
    user = models.ForeignKey('User_profile', on_delete = models.SET_NULL)

class User_profile(models.Model):
    #user_type = models.CharField(max_length = 200)
    #username = models.CharField(max_length = 200)
    #email = models.CharField(max_length = 200)
    user = models.OneToOneField(User, on_delete = models.CASCADE)
    balance = models.FloatField(default=0)
    charges = models.FloatField(default=0)

class Location(models.Model):
    station_name = models.CharField(max_length = 200)
    num_bikes = models.IntegerField(default=0)
    latitude = models.FloatField()
    longitude = models.FloatField()

class User_history(models.Model):
    user_id = models.ForeignKey(User_profile)
    bike_id = models.ForeignKey(Bikes)
    date_hired = models.DateTimeField()
    date_returned = models.DateTimeField()
    num_hires = models.IntegerField()
    start_station = models.ForeignKey(Location)
    end_station = models.ForeignKey(Location)