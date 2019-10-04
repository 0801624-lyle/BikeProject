from django.urls import path

from . import views
app_name = 'bikes'
urlpatterns = [
    path('', views.index, name = 'index'),
]