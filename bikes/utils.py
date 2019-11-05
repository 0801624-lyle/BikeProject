from collections import namedtuple
from datetime import datetime

from django.db.models import F
from django.utils import timezone
import pytz
import geopy.distance

from .cost_calculator import CostCalculator
from .models import *

def return_bike(hire, end_station, user_discount_code):
    hire.end_station = end_station
    hire.date_returned = timezone.now()
    model = Discounts.objects.filter(code=user_discount_code)
    if model.exists():
        model = model.get()
        hire.discount_applied = model
        discount_model = UserDiscounts(user=hire.user, discounts=model, date_used=timezone.now())
    charges, discount = CostCalculator(hire).calculate_cost()
    if hire.discount_applied is not None:
        discount_model.amount_saved = discount
        discount_model.save()
    hire.charges = charges
    hire.save()

    # nullify user's current hire
    hire.user.current_hire = None
    hire.user.add_charges(charges)
    hire.user.save()

    # set bike location
    bike = hire.bike
    bike.location = hire.end_station
    bike.save()

    return hire

def move_bike(bike, new_station):
    
    # set bike location
    bike.location = new_station
    bike.save()

    return bike

def repair_bike(bike):
    bike.status = 1
    bike.save()

def ride_distance(hire):
    """ Calculates a ride's distance between the start and end stations
        Uses geopy.distance.distance [an implementation of geodesic distance]
        returns namedtuple of distance attributes: kilometres, miles and feet for the distance 
    """
    start, end = hire.start_station, hire.end_station
    Distance = namedtuple('Distance', 'km miles feet')
    if end is not None:
        # extract latitude and longitudes for the start and end stations
        start = start.latitude, start.longitude
        end   = end.latitude, end.longitude
        dist = geopy.distance.distance(start, end) # calculate geodesic distance
        return Distance(km=dist.km, miles=dist.miles, feet=dist.feet)
    return 0 # if end is None

def parse_dates(date_from, date_to):
    """ Creates timezone aware datetime objects from string parameters """
    day_from, month_from, year_from = date_from.split("-")
    day_to, month_to, year_to = date_to.split("-")
    
    _from = datetime(
        year=int(year_from), month=int(month_from), day=int(day_from), tzinfo=pytz.UTC
    )
    _to = datetime(
        year=int(year_to), month=int(month_to), day=int(day_to), tzinfo=pytz.UTC
    )

    return _from, _to