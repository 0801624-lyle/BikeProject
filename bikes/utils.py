from django.db.models import F
from django.utils import timezone

from .cost_calculator import CostCalculator
from .models import *

def return_bike(hire, end_station, user_discount_code):
    hire.end_station = end_station
    hire.date_returned = timezone.now()
    model = Discounts.objects.filter(code=user_discount_code)
    if model.exists():
        model = model.get()
        hire.discount_applied = model
    charges = CostCalculator(hire).calculate_cost()
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