from django.contrib.auth import authenticate, login
from django.contrib.messages.views import SuccessMessageMixin
from django.shortcuts import render
from django.views.generic.edit import CreateView

from .forms import RegistrationForm
from .models import BikeHires
from django.utils import timezone
from django.http import Http404
 
# Create your views here.
def index(request):
    return render(request, 'bikes/index.html', {})


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

# return the user's membership type.
def get_membershipType(request,choice):
    stander='stander'
    student='student'
    pensioner='pensioner'
    staff='staff'
    if choice == 1:
        return stander
    elif choice == 2:
        return student
    elif choice == 3:
        return pensioner 
    elif choice == 4:
        return staff 
    else:
        raise Http404('invalid choice')
        
# calculate journey duration. 
def  trip_duration(request):
     now = timezone.now()
     duration= now - BikeHires.date_hired
     return render('bikes/journey_details.html', duration)