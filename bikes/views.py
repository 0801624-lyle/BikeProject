from django.contrib import messages
from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib.messages.views import SuccessMessageMixin
from django.core.paginator import Paginator
from django.db.models import F, ExpressionWrapper, fields
from django.http import JsonResponse, HttpResponse
from django.shortcuts import render, redirect
from django.urls import reverse
from django.utils import timezone
from django.views.generic.edit import CreateView
from django.views.decorators.csrf import csrf_exempt
from rest_framework.generics import ListAPIView

from .cost_calculator import CostCalculator
from .choices import MembershipType, BikeStatus, UserType
from .forms import RegistrationForm, UserProfileForm, BikeHireForm, ReturnBikeForm, BikeRepairsForm, MoveBikeForm, DiscountsForm
from .models import Location, UserProfile, BikeHires, Bikes, Discounts, BikeRepairs
from .serializers import LocationSerializer
from . import utils


# Create your views here.
def index(request):
    locations = Location.objects.all()
    context = {
        "locations": locations
    }
    return render(request, 'bikes/index.html', context)

def view_map(request):
    locations = Location.objects.all()
    locations_api = reverse('bikes:location_list')

    paginator = Paginator(locations, 6)

    page = request.GET.get('page', 1)
    locations = paginator.get_page(page)

    context = {
        "locations": locations,
        "locations_api": locations_api
    }
    return render(request, 'bikes/mapview.html', context)

def location_detail(request, pk):
    """ Individual location view """
    try:
        location = Location.objects.get(pk=pk)
    except Location.DoesNotExist:
        return HttpResponse("Location not found")

    bikes = location.bikes_set.all()
    num_bikes = bikes.count()

    paginator = Paginator(bikes, 10)
    page = request.GET.get('page', 1)
    bikes = paginator.get_page(page)

    hire_form = BikeHireForm()
    repair_form = BikeRepairsForm()

    context = {
        "location": location,
        "bikes": bikes,
        "num_bikes": num_bikes,
        "hire_form": hire_form,
        "repair_form": repair_form
    }

    return render(request, 'bikes/location.html', context)

@login_required
def profile(request):
    # get current user and userprofile models from the request
    user = request.user
    current_user = UserProfile.objects.get(user=user)

    # filter out the user's rides from the database
    user_rides = BikeHires.objects.filter(user=current_user)
    # get the total number of rides the user has taken
    num_bike_rides = user_rides.count()

    # calculate the total distance the user has travelled in all their rides
    distance_travelled = sum([utils.ride_distance(hire).km for hire in user_rides])
    photo_form = UserProfileForm({'picture': current_user.profile_pic})
    context = {
        "num_bike_rides": num_bike_rides,
        "profile_form": photo_form,
        "distance_travelled": distance_travelled,
    }
    
    # return the HTML template with the context dictionary attached
    return render(request, 'bikes/profile.html', context) 

@login_required
def addfunds(request):
    """ Adds funds to a user's balance """

    # must be a POST request
    if request.method != "POST":
        return redirect(reverse('bikes:profile'))
    
    added_balance = request.POST.get('balance', 0)
    added_balance = '%.2f' % (float(added_balance))
    userprofile = request.user.userprofile
    userprofile.add_balance(float(added_balance))
    userprofile.save()
    messages.info(request, f"£{added_balance} was added to your balance.")
    return redirect(reverse("bikes:profile"))

@login_required
def paycharges(request):
    """ Pays user's charges with user's balance """

    # does this have to be a post?
    #      
    userprofile = request.user.userprofile
    if userprofile.balance >= userprofile.charges:
        userprofile.balance = userprofile.balance - userprofile.charges
        userprofile.charges = 0
        userprofile.save()
        messages.info(request, "Your charges have been paid")
    else:
        messages.info(request, "Your balance does not cover your charges. \nPlease add more funds.")
    return redirect(reverse("bikes:profile"))

@login_required
def user_hires(request):
    """ This view shows the user's current hires, as well as their historical hires """
    user = request.user.userprofile
    current_hire = user.current_hire

    ordering = request.GET.get('order')
    if ordering is None:
        ordering = '-date_hired'

    if "duration" not in ordering:
        historical_hires = BikeHires.objects.filter(user=user, end_station__isnull=False).order_by(ordering)
    else:
        # because duration is an 'implied' field, we need to annotate each model with their duration before ordering
        # duration = date_returned - date_hired. The below code annotates each model with a 'duration' field
        duration = ExpressionWrapper(F('date_returned') - F('date_hired'), output_field=fields.DurationField())
        historical_hires = BikeHires.objects.filter(user=user, end_station__isnull=False) \
            .annotate(duration=duration)
        historical_hires = historical_hires.order_by(ordering)
    
    # annotate the historical hires models with the distance travelled for each ride
    for h in historical_hires:
        h.distance = utils.ride_distance(h)

    context = {
        "current_hire": current_hire,
        "historical_hires": historical_hires
    }

    if current_hire is not None:
        return_form = ReturnBikeForm(initial={"hire_id": current_hire.pk})
        context["form"] = return_form
    return render(request, 'bikes/user-hires.html', context)

@login_required
def hire_bike(request):
    if request.method != "POST":
        return redirect(reverse('bikes:view-map'))

    form = BikeHireForm(request.POST or None)
    user = request.user.userprofile
    if form.is_valid():
        bike_id = form.cleaned_data['bike_id'] 
        bike = Bikes.objects.get(pk=bike_id)
        
        if user.current_hire is not None:
            messages.error(request, "Please return your bike before attempting to hire a new one")
            return redirect(reverse('bikes:user-hires'))
        elif user.charges != 0:
            messages.error(request, "You can not hire another bike before you pay your charges.")
            return redirect(reverse('bikes:user-hires'))
        station = bike.location.station_name
        
        # call the hire() method to hire the bike [this is on Bikes model]
        bike.hire(user)

        messages.info(request, f"You have hired bike {bike_id} from station {station}")
        return redirect(reverse('bikes:user-hires'))

@login_required
def return_bike(request):
    user = request.user.userprofile
    form = ReturnBikeForm(request.POST or None)
    if form.is_valid():
        hire = BikeHires.objects.get(pk=form.cleaned_data['hire_id'])
        hire = utils.return_bike(hire, form.cleaned_data['location'], form.cleaned_data['discount'])
        print(form.cleaned_data['discount'])
        messages.info(request, f"Bike {hire.bike.pk} returned. Charges: £{hire.charges:.2f}")
    return redirect(reverse('bikes:user-hires'))

@login_required
def move_bike(request):
    form = MoveBikeForm(request.POST or None)
    if form.is_valid():
        old = form.cleaned_data['location']
        new = form.cleaned_data['new_location']
        #bike = Bikes.objects.get(pk=form.cleaned_data['bike_id'])
        bike = Bikes.objects.get(pk=old.bikes_set.first().id)
        bike = utils.move_bike(bike, new)
        print("hello from views")
        messages.info(request, f"Bike {bike.pk} has been moved to {bike.location}.")
    return redirect(reverse('bikes:operator-index'))
    
class RegistrationView(SuccessMessageMixin, CreateView):
    """ This view handles user registration """

    template_name = "bikes/register.html"
    form_class = RegistrationForm
    success_message = "Registration successful. Welcome, %(username)s!"

    # Override to auto-login user when they register
    def form_valid(self, form):
        valid = super().form_valid(form)
        username = self.request.POST['username']
        pw = self.request.POST['password']
        user = authenticate(username=username, password=pw)
        login(self.request, user)
        return valid

    def get_success_url(self, **kwargs):
        """ This method defines the 'success url' - this is where a user is 
            redirected to after they have successfully registered. #
        """
        return reverse('bikes:profile')

# Ajax views
def validate_username(request):
    """ Called when a user is registering and typing their username.
        Every key typed will send a request to this view function, to check whether the username is taken.
        If the username matches a username in the database, the user should be prevented from signing up
    """
    username = request.GET.get('username', None)
    username_exists = User.objects.filter(username__iexact=username).exists()
    return JsonResponse({
        "username_exists": username_exists
    })

def validate_email(request):
    """ Called when a user is registering and typing their email address.
        Every key typed will send a request to this view function, to check whether the email is taken.
        If the email matches an email address in the database, the user should be prevented from signing up
        unless they change the email address
    """
    email = request.GET.get('email', None)
    email_exists = User.objects.filter(email__iexact=email).exists()
    return JsonResponse({
        "email_exists": email_exists
    })

@login_required
def profile_pic_add(request, pk):
    """ This function adds a profile picture to the User's who uploaded it.
        The 'pk' argument is passed in from the URL, and used to fetch the user profile """
    userprofile = UserProfile.objects.get(id=pk)
    profile_form = UserProfileForm(request.POST, request.FILES, instance=userprofile)

    # Check if the provided form is valid.
    if profile_form.is_valid():
        profile_form.save(commit=True)
        messages.info(request, "Profile picture updated!")
        return redirect(reverse("bikes:profile"))
    else:
        messages.error(request, "Profile picture update failed. \nPlease ensure you select a valid image file")
        return redirect(reverse("bikes:profile"))


class LocationList(ListAPIView):
    queryset = Location.objects.all()
    serializer_class = LocationSerializer

def bike_report(request):
    """ view for handling reporting a Bike as needing repair """
    
    form = BikeRepairsForm(request.POST) 
    if form.is_valid():

        # this is the Bike object (i.e. the model)
        bike = form.cleaned_data['bike']

        # now set bikes status to BEING_REPAIRED
        bike.status = BikeStatus.BEING_REPAIRED
        bike.save()

        # and create the BikeRepairs object
        BikeRepairs.objects.create(bike=bike)

        messages.info(request, f"Bike {bike.pk} has been reported for repair, and taken out of circulation")
        return redirect(reverse('bikes:view-map'))
    print(request.POST)
    messages.error(request, f"Warning: a problem occurred reporting bike")
    return redirect(reverse('bikes:view-map'))

################## 
# OPERATOR VIEWS

def is_operator(user):
    """ This function is the 'test' for which a user must pass to view the reports pages.
        The user must be of type UserType.OPERATOR in order to view any of these pages. """

    return user.userprofile.user_type == UserType.OPERATOR or user.userprofile.user_type == UserType.MANAGER

@login_required
def operator_index(request):
    if not is_operator(request.user):
        return redirect(reverse('bikes:index'))

    trackurl = reverse('bikes:track_bike')
    discount_form = DiscountsForm()
    context = {
        "form" : MoveBikeForm(),
        "trackurl": trackurl,
        "discount_form": discount_form,
    }
    return render(request, 'bikes/operator_index.html',context)

@csrf_exempt
def track_bike(request):
    if not is_operator(request.user):
        return redirect(reverse('bikes:index'))
    bike_id = request.POST['bike_id']
    try:
        bike = Bikes.objects.get(pk = bike_id)
        bike_location = bike.location
        return JsonResponse({"bike_location" : bike_location.station_name})
    except Bikes.DoesNotExist:
        return JsonResponse({"bike_location": "None"})

@login_required
def create_discount(request):
    if not is_operator(request.user):
        return redirect(reverse('bikes:index'))

    form = DiscountsForm(request.POST or None)
    if form.is_valid():
        code = form.cleaned_data.get('code')
        data_from = form.cleaned_data.get('date_from', timezone.now())
        date_to = form.cleaned_data.get('date_to', timezone.now() + timezone.timedelta(days=10))
        discount_amount = form.cleaned_data.get('discount_amount')
        
        discount = form.save()
        messages.info(request, f"Discount was created with code {discount.code}")
        
    return redirect(reverse('bikes:operator-index'))