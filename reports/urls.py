from django.urls import path

from . import views

app_name = 'reports'

urlpatterns = [
    path('', views.reports_index, name='reports_index'),
    path('bike-locations/', views.bike_locations, name='bike_locations')
]