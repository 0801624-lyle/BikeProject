from django.contrib.auth import views as auth_views
from django.urls import path

from . import views

app_name = 'bikes'

urlpatterns = [
    path('', views.index, name = 'index'),
    path('view-map/', views.view_map, name='view-map'),
    path('locations/<int:pk>/', views.location_detail, name='location_detail'),

    # login and registration views
    path('profile/', views.profile, name='profile'),
    path('addfunds/', views.addfunds, name='addfunds'),
    path('login/', auth_views.LoginView.as_view(template_name="bikes/login.html"), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name="logout"),
    path('register/', views.RegistrationView.as_view(), name='register'),
    path('profile/<int:pk>/add-photo/', views.profile_pic_add, name='profile_pic_add'),

    # ajax views
    path('register/ajax/check_username/', views.validate_username, name='ajax_check_username'),
    path('register/ajax/check_email/', views.validate_email, name='ajax_check_email'),
    
    path('api/list/locations', views.LocationList.as_view(), name='location_list')
]