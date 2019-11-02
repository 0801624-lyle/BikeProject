from collections import namedtuple

from django.db.models import F
from django.utils import timezone
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
