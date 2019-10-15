from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth import get_user_model
from django.db import IntegrityError
from django.utils import timezone
import random, string, sys
import datetime

from bikes.choices import BikeStatus, UserType, MembershipType
from bikes.models import *
from reports.models import *

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
        if BikeHires.objects.count() == 0:
            self.create_bike_hire_history()

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
        for _ in range(85):
            location = random.choice(locations)
            Bikes.objects.create(location=location, status=BikeStatus.AVAILABLE)
        for location in locations:
            init_count = location.bikes_set.count()
            location.initial_bike_count = init_count
            d = timezone.make_aware(datetime.datetime(year=2019, month=1, day=1))
            LocationBikeCount.objects.create(location=location, count=init_count, datetime=d)
            location.save()

    def create_discount(self):
        date_from = timezone.now()
        date_to   = timezone.now() + timezone.timedelta(days=10)
        Discounts.objects.create(
            code="ABCDEFG", date_from=date_from, date_to=date_to, discount_amount=0.5 
        )

    def create_bike_hire_history(self):
        users = UserProfile.objects.all()
        locations = Location.objects.all()
        bikes = Bikes.objects.all()
        discount = Discounts.objects.first()
        hires = []
        for i in range(250):
            duration = self._get_random_duration()
            start = self._get_random_datetime()
            end = start + timezone.timedelta(minutes=duration)
            user = random.choice(users)
            hire = BikeHires(user=user, date_hired=start, date_returned=end)

            # Add discount to ~30% of the hires
            if random.random() < 0.3:
                hire.discount_applied = discount
            hires.append(hire)
        
        # sort the hires in date order
        hires = sorted(hires, key=lambda obj: obj.date_hired)
        
        for h in hires:
            bike = random.choice(bikes)
            start_station = bike.location
            end_station = random.choice(locations)
            if end_station.pk == start_station.pk:
                locs = Location.objects.exclude(pk=end_station.pk)
                end_station = random.choice(locs)
            h.bike = bike
            h.start_station = start_station
            h.end_station = end_station
            h.save()
            bike.location = h.end_station
            bike.save()

    def _get_random_duration(self):
        time_ranges = [*list(range(1,36)), *list(range(36,50)), *list(range(50,80)), *list(range(80,500))]
        weights = [*[.70 for _ in range(1,36)], 
                    *[.20 for _ in range(36,50)], 
                    *[.07 for _ in range(50,80)], 
                    *[.03 for _ in range(80,500)]]
        duration = random.choices(time_ranges, weights=weights, k=1)[0]
        return duration

    def _get_random_datetime(self):
        """ generates random date between 1st January 2019 and current date """
        start_dt = timezone.now().replace(day=1, month=1).toordinal()
        end_dt = timezone.now().date().toordinal()
        random_day = datetime.date.fromordinal(random.randint(start_dt, end_dt))
        dt = datetime.datetime(year=random_day.year, month=random_day.month, day=random_day.day)
        dt = dt.replace(hour=random.randint(0,23))
        dt = dt.replace(minute=random.randint(0,59))
        dt = dt.replace(second=random.randint(0,59))
        return timezone.make_aware(dt)