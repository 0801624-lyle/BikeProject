from django.contrib.auth import authenticate, login
from django.contrib.messages.views import SuccessMessageMixin
from django.shortcuts import render
from django.views.generic.edit import CreateView

from .forms import RegistrationForm


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