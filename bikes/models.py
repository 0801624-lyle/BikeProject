from django.core.validators import MaxValueValidator, MinValueValidator
from django.contrib.auth.models import User
from django.db import models
from django.utils import timezone

from .choices import UserType, BikeStatus, MembershipType


class Bikes(models.Model):
    status = models.IntegerField(choices=BikeStatus.CHOICES)
    location = models.ForeignKey("Location", on_delete=models.SET_NULL, blank=True, null=True)

class UserProfile(models.Model):
    """ Extends the native Django `User` model via a 1-1 relationship (see the `user` field below)
        The user_type field is given pre-defined choices from the choices.py file (imported at top).
        user_type is either: Customer, Operator, or Manager
        An integer is assigned to each of these in choices.py, and stored in the database.
        The "discounts" field tracks which discounts the user has already used, if any
    """
    
    # 1-1 relationship between a user and their profile
    user = models.OneToOneField(User, on_delete = models.CASCADE)
    membership_type = models.IntegerField(choices=MembershipType.CHOICES, default=MembershipType.STANDARD) 
    user_type = models.IntegerField(choices=UserType.CHOICES, default=UserType.CUSTOMER)
    balance = models.FloatField(default=0)
    charges = models.FloatField(default=0)
    discounts = models.ManyToManyField("Discounts", through='UserDiscounts')

class Location(models.Model):
    """ Table that stores all the locations where bikes are available, along with lat/lon coordinates """

    station_name = models.CharField(max_length = 200, unique=True)
    latitude = models.FloatField()
    longitude = models.FloatField()
    initial_bike_count = models.IntegerField(default=0)

    class Meta:
        ordering = ("station_name",)

class BikeHires(models.Model):
    """ A table that tracks all historical bike hires.
        This model tracks which user hired the bike, the bike id, start/end stations, and the duration of the journey.
        Also has a field for the charges/cost of the hire - this is based on the duration of the journey.
    """
    user = models.ForeignKey(UserProfile, on_delete=models.SET_NULL, null=True)
    bike = models.ForeignKey(Bikes, on_delete=models.CASCADE, null=True)
<<<<<<< HEAD
    date_hired = models.DateTimeField()
=======
    date_hired = models.DateTimeField(auto_now_add=True)
>>>>>>> be42bab9add3e16ae59971bfc5011dfaff3fbf93
    date_returned = models.DateTimeField(null=True, blank=True) # allow null for current hires
    start_station = models.ForeignKey(Location, on_delete=models.SET_NULL, blank=True, null=True, related_name="start_station")
    end_station = models.ForeignKey(Location, on_delete=models.SET_NULL, blank=True, null=True,  related_name="end_station")
    charges = models.FloatField(null=True, blank=True) # Tracks how much the user was charged for the hire
    discount_applied = models.ForeignKey("Discounts", on_delete=models.SET_NULL, blank=True, null=True)

    def get_duration(self):
        """ Gets the length of the hire. If the hire is still ongoing, returns current amount of time hired """
        if self.date_returned is not None:
            return self.date_returned - self.date_hired
        else:
            now = timezone.now()
            return now - self.date_hired

    class Meta:
        ordering = ("date_hired",)

class BikeRepairs(models.Model):
    """ A table to track all historical bike repairs """

    bike = models.ForeignKey(Bikes, on_delete=models.CASCADE)
    date_malfunctioned = models.DateTimeField()
    date_repaired = models.DateTimeField(null=True) # allow this to be null in case the Bike isn't yet fixed
    repair_cost = models.FloatField(null=True) # how much repair cost

class Discounts(models.Model):
    """ Tracks any discounts currently available for bike hires.
        Users can enter a code to receive a discount.
        The discount should be valid only between date_from and date_to dates.
        The discount should also only be applicable once to each user
    """
    code = models.CharField(max_length=12, unique=True, blank=True, null=True)
    date_from = models.DateField()
    date_to   = models.DateField()
    discount_amount = models.FloatField(validators=[MinValueValidator(0), MaxValueValidator(1.0)])

    def save(self, *args, **kwargs):
        # We override save() here to ensure the discount_applied field is a fractional value between 0 and 1.
        if self.discount_amount < 0:
            self.discount_amount = 0
        elif self.discount_amount > 1:
            self.discount_amount = 1
        super().save(*args, **kwargs)

class UserDiscounts(models.Model):
    """ Tracks which user has used which discounts.
        Also stores the date they used it, and the amount they saved via the discount 
    """

    user = models.ForeignKey(UserProfile, on_delete=models.CASCADE)
    discounts = models.ForeignKey(Discounts, on_delete=models.CASCADE)
    date_used = models.DateField(auto_now_add=True)
    amount_saved = models.FloatField()