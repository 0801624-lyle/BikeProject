from django.contrib.auth import views as auth_views
from django.urls import path

from . import views

app_name = 'bikes'

urlpatterns = [
    path('', views.index, name = 'index'),

    # login and registration views
    path('login/', auth_views.LoginView.as_view(template_name="bikes/login.html"), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name="logout"),
    path('register', views.RegistrationView.as_view(), name='register'),
]