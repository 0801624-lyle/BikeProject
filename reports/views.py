import math
from datetime import datetime

from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.db.models import Count, Q
from django.http import HttpResponse
from django.shortcuts import render, redirect
from django.urls import reverse

from bokeh.plotting import figure
from bokeh.embed import components
from bokeh.models import HoverTool, LassoSelectTool, WheelZoomTool, PointDrawTool, ColumnDataSource
from bokeh.palettes import *

from bikes.choices import UserType, MembershipType
from bikes.models import Bikes, Location, BikeHires, UserProfile
from reports.models import LocationBikeCount


def is_manager(user):
    """ This function is the 'test' for which a user must pass to view the reports pages.
        The user must be of type UserType.MANAGER in order to view any of these pages. """

    return user.userprofile.user_type == UserType.MANAGER

@login_required
def reports_index(request):
    if not is_manager(request.user):
        return redirect(reverse('bikes:index'))
    return render(request, 'reports/index.html', {})

@login_required
def bike_locations(request):
    if not is_manager(request.user):
        return redirect(reverse('bikes:index'))

    loc = request.GET.get('loc', None)
    if loc is None:
        location_name = Location.objects.first().station_name
    else:
        location_name = Location.objects.get(station_name__iexact=loc).station_name
    loc = Location.objects.get(station_name__iexact=location_name)

    locations = Location.objects.annotate(bike_count=Count('bikes'))
    stations = [location.station_name for location in locations]
    bike_counts = [location.bike_count for location in locations]
    plot = figure(x_range=stations, plot_height=400,  title="Bikes per location", toolbar_location="below")
    source = ColumnDataSource(data=dict(stations=stations, bike_counts=bike_counts, color=Spectral6))
    plot.add_tools(LassoSelectTool())
    plot.add_tools(WheelZoomTool())
    plot.add_tools(HoverTool())

    plot.vbar(x='stations', top='bike_counts', width=.8, color='color', source=source)

    plot.xgrid.grid_line_color = "black"
    plot.xaxis.major_label_orientation = math.pi/6
    plot.min_border_left = 80
    plot.min_border_right = 80
    plot.y_range.start = 0
    plot.y_range.end   = max(bike_counts) + 2

    script, div = components(plot)

    # Time series graph
    hire_history = LocationBikeCount.objects.filter(location=loc).values()
    dates = [hire['datetime'] for hire in hire_history]
    count = [hire['count'] for hire in hire_history]
    time_source = ColumnDataSource(
        data=dict(datetime=dates, count=count)
    )
    time_plot = figure(x_axis_type='datetime', plot_height=400)
    time_plot.step('datetime', 'count', line_width=2, source=time_source)
    hover = HoverTool()
    hover.tooltips = [
        ("Date", "@datetime"), 
        ("Count", "@count")
    ]
    time_plot.add_tools(hover)
    time_script, time_div = components(time_plot)

    context = {
        "script": script, 
        "div": div, "location_name": 
        location_name, 
        "locations": locations,
        "time_series_script": time_script,
        "time_series_div": time_div
    }
    return render(request, 'reports/bike-locations.html', context)


# User Activity report
@login_required
def user_report(request):
    if not is_manager(request.user):
        return redirect(reverse('bikes:index'))
    
    users = UserProfile.objects.all()

    # Count the number of users for each membership type (standard, student, pensioner, staff)
    membershiptype_counts = users.values('membership_type').annotate(membership_count=Count('membership_type'))
    memberships = [MembershipType.get_choice(m['membership_type']) for m in membershiptype_counts]
    member_counts = [m['membership_count'] for m in membershiptype_counts]
    plot = figure(x_range=memberships, plot_height=300, plot_width=300, title="Users by membership type", toolbar_location="below")
    source = ColumnDataSource(data=dict(memberships=memberships, member_counts=member_counts, color=Spectral6))

    plot.vbar(x='memberships', top='member_counts', width=.8, color='color', source=source)

    script, div = components(plot)

    # Count the number of users for each user type (customer, operator, manager)
    usertypes_counts = users.values('user_type').annotate(user_count=Count('user_type'))
    user_types = [UserType.get_choice(u['user_type']) for u in usertypes_counts]
    user_counts = [u['user_count'] for u in usertypes_counts]
    usertype_plot = figure(x_range=user_types, plot_height=300, plot_width=300, title="Users by type", toolbar_location="below")
    source2 = ColumnDataSource(data=dict(user_types=user_types, user_counts=user_counts, color=Spectral6))

    usertype_plot.vbar(x='user_types', top='user_counts', width=.8, color='color', source=source2)

    script2, div2 = components(usertype_plot)
    context = {
        "script": script,
        "div": div,
        "script2": script2,
        "div2": div2
    }

    return render(request, "reports/user-report.html", context)