from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth import get_user_model
from django.db import IntegrityError
from django.utils import timezone
import random, string, sys

from bikes.choices import BikeStatus, UserType, MembershipType
from bikes.models import *

class Command(BaseCommand):

    # This method is executed when the management command is run.
    def handle(self, *args, **kwargs):
        if Location.objects.count() == 0:
            self.create_locations()
        if User.objects.count() == 0:
            self.create_users()
        if Bikes.objects.count() == 0:
            self.create_bikes()
        if Discounts.objects.count() == 0:
            self.create_discount()


    def create_locations(self):
        locations = [
            {"station_name": "University of Glasgow", "latitude": 55.8715, "longitude": -4.2887},
            {"station_name": "Strathclyde University", "latitude": 55.862785, "longitude": -4.242353},
            {"station_name": "Glasgow Caledonian University", "latitude": 55.866231, "longitude": -4.250228},
            {"station_name": "Glasgow Science Centre", "latitude": 55.858680, "longitude": -4.293803},
            {"station_name": "Trongate", "latitude": 55.855789, "longitude": -4.246063},
            {"station_name": "Partick Station", "latitude": 55.870007, "longitude": -4.308759},
        ]
        for location in locations:
            Location.objects.create(**location)

    def create_users(self):
        users = [
            {"username": "lyle", "password": "password", "email": "lyle@gmail.com"},
            {"username": "CJ", "password": "password", "email": "cj@gmail.com"},
            {"username": "alexander", "password": "password", "email": "alexander@gmail.com"},
            {"username": "ebtihal", "password": "password", "email": "ebtihal@gmail.com"},
            {"username": "binta", "password": "password", "email": "binta@gmail.com"},
            {"username": "ligen", "password": "password", "email": "ligen@gmail.com"}
        ]
        for user in users:
            db_user = get_user_model().objects.create_user(**user)
            # set these users as managers
            UserProfile.objects.filter(user=db_user).update(user_type=UserType.MANAGER)
        
        # create operators and customers user
        for i in range(3):
            customer = User.objects.create_user(
                username=f"customer{i}", password="password", email=f"customer{i}@gmail.com"
            )
            operator = User.objects.create_user(
                username=f"operator{i}", password="password", email=f"operator{i}@gmail.com"
            )
            UserProfile.objects.filter(user=customer).update(user_type=UserType.CUSTOMER)
            UserProfile.objects.filter(user=operator).update(user_type=UserType.OPERATOR)
    
    def create_bikes(self):
        locations = Location.objects.all()
        for _ in range(25):
            location = random.choice(locations)
            Bikes.objects.create(location=location, status=BikeStatus.AVAILABLE)

    def create_discount(self):
        date_from = timezone.now()
        date_to   = timezone.now() + timezone.timedelta(days=10)
        Discounts.objects.create(
            code="ABCDEFG", date_from=date_from, date_to=date_to, discount_amount=0.5 
        )