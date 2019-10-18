from django.contrib.auth import authenticate, login
from django.contrib.auth.models import User
from django.contrib.messages.views import SuccessMessageMixin
from django.core.paginator import Paginator
from django.http import JsonResponse, HttpResponse
from django.shortcuts import render, redirect
from django.urls import reverse
from django.views.generic.edit import CreateView
from rest_framework.generics import ListAPIView

from .forms import RegistrationForm
from .models import Location
from .serializers import LocationSerializer

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

    paginator = Paginator(locations, 5)

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

    context = {
        "location": location,
        "bikes": bikes,
        "num_bikes": num_bikes
    }

    return render(request, 'bikes/location.html', context)

def profile(request):
    return render(request, 'bikes/profile.html') 

def addfunds(request):
    return render(request, 'bikes/addfunds.html')



class RegistrationView(SuccessMessageMixin, CreateView):
    template_name = "bikes/register.html"
    form_class = RegistrationForm
    success_url = '/'
    success_message = "Registration successful. Welcome, %(username)s"

    # Override to auto-login user when they register
    def form_valid(self, form):
        valid = super().form_valid(form)
        username = self.request.POST['username']
        pw = self.request.POST['password']
        user = authenticate(username=username, password=pw)
        login(self.request, user)
        return valid


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


class LocationList(ListAPIView):
    queryset = Location.objects.all()
    serializer_class = LocationSerializer
