import math
import os
from datetime import datetime
from itertools import groupby

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.db.models import Count, Q, Sum, Avg, Max
from django.http import HttpResponse
from django.shortcuts import render, redirect
from django.urls import reverse

from bokeh.plotting import figure
from bokeh.embed import components
from bokeh.models import HoverTool, LassoSelectTool, WheelZoomTool, PointDrawTool, ColumnDataSource
from bokeh.palettes import *
import matplotlib
matplotlib.use('Agg')
from matplotlib import pyplot as plt
import networkx as nx

from bikes.choices import UserType, MembershipType
from bikes.models import Bikes, Location, BikeHires, UserProfile
from bikes.utils import ride_distance, parse_dates
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
    hires = BikeHires.objects.all().select_related('bike', 'user', 'start_station', 'end_station')

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

    # users in order of number of hires
    user_hirecount = hires.values('user').order_by('user').annotate(num_hires=Count('user_id')) \
        .order_by('num_hires')

    # user charge totals
    user_charge_totals = hires.values('user').order_by('user').annotate(total=Sum('charges')) \
        .order_by('total')

    # hires_by_month 
    hires_by_month = hires.values('date_hired').order_by('date_hired')
    num_hires_per_month = {
        k: len(list(v)) for k,v in groupby(hires_by_month, key=lambda date: date['date_hired'].month)
    }

    # total distance cycles
    total_distance_cycled = sum([ride_distance(hire).km for hire in hires])

    # number of rides per user type
    hires_per_usertype = hires.values('user__membership_type').order_by('user__membership_type') \
        .annotate(num_hires=Count('id'))

    ###

    script2, div2 = components(usertype_plot)
    context = {
        "script": script,
        "div": div,
        "script2": script2,
        "div2": div2
    }

    return render(request, "reports/user-report.html", context)

@login_required
def financial_report(request):
    """ Generates the application's Financial Report """

    if not is_manager(request.user):
        return redirect(reverse('bikes:index'))

    # All hires
    hires = BikeHires.objects.all().select_related('bike', 'user', 'start_station', 'end_station')

    # total income from rides
    total_income = hires.aggregate(income=Sum('charges'))
    
    # average per ride
    avg_per_ride = BikeHires.objects.aggregate(avg=Avg('charges'))

    # 5 maximum charges for individual rides
    maximum_charges = BikeHires.objects.annotate(max_charge=Max('charges')).order_by('-max_charge')[:5]

    # get hire charges ordered from smallest to largest charge
    hires_by_charge = hires.order_by('charges').values('charges')
    
    # group the hires into discrete bins - i.e., all hires between £1 and £2 get grouped together
    # all hires between £x and £x+1 are grouped, and the number of hires for each bin is calculated
    # The below code uses a dictionary comprehension and the itertools.groupby function to do this
    # the key function for the grouping is the math.floor function, applied to an individual bike hire's charge field
    hires_by_charge_quantized = {
        k: len(list(v)) for k, v in groupby(hires_by_charge, key=lambda x: math.floor(x['charges']))
    }
    ### histogram of above

    # percentage of rides that have a discount applied
    discount_pct = hires.aggregate(has_dis=Count('discount_applied'))['has_dis'] / hires.count() * 100

    # charges per month
    charges_by_month = hires.values('date_hired', 'charges').order_by('date_hired')
    hbm = {
        k: sum(v['charges'] for v in list(v)) \
            for k,v in groupby(charges_by_month, key=lambda date: date['date_hired'].month)
    }

    # charges per user type
    charges_per_usertype = hires.values('user__membership_type').order_by('user__membership_type') \
        .annotate(amt=Sum('charges'))

    # users with outstanding charges
    users_in_debt = UserProfile.objects.filter(charges__gt=0)
    # total amount still to be collected in charges
    total_charges_for_collection = users_in_debt.aggregate(charges=Sum('charges'))

    # amount liquid
    liquid_money = total_income['income'] - total_charges_for_collection['charges']

    return HttpResponse("testing")


def path_routes(request):
    SAVE_PATH = os.path.join(settings.STATIC_DIR, 'network.png')
    locations = Location.objects.all()

    # add nodes to graph
    G = nx.DiGraph()
    for loc in locations:
        G.add_node(loc.station_name, pos=(loc.longitude, loc.latitude))

    station_urlparam = request.GET.get('station', None)
    if station_urlparam is None:
        station = locations.first()
    else:
        station = locations.get(pk=station_urlparam)

    # extract date args from request (if given)
    date_from = request.GET.get('date_from', None)
    date_to   = request.GET.get('date_to', None)
    date_from_should_filter = date_from is not None and len(date_from) > 0
    date_to_should_filter = date_to is not None and len(date_to) > 0


    # get all hires from the given station. filter by date if applicable
    station_links = BikeHires.objects.filter(start_station=station, end_station__isnull=False) \
        .select_related('start_station', 'end_station')

    if date_from_should_filter and date_to_should_filter:
        date_from, date_to = parse_dates(date_from, date_to)
        station_links = station_links.filter(date_hired__gt=date_from, date_hired__lt=date_to)
        ride_counts = BikeHires.objects.filter(start_station=station, date_hired__gt=date_from, date_hired__lt=date_to) \
            .values('end_station').order_by('end_station').annotate(cnt=Count('end_station'))
    else:
        # get number of rides from given station to all other stations
        ride_counts = BikeHires.objects.filter(start_station=station).values('end_station') \
            .order_by('end_station').annotate(cnt=Count('end_station'))

    # add edges to the graphs for all rides
    for hire in station_links:
        start = hire.start_station.station_name
        end   = hire.end_station.station_name
        G.add_edge(start, end) # add edge to graph

    # construct journey counts formatted for adding label to each edge in the graph
    edge_counts = {
        (station.station_name, Location.objects.get(pk=e['end_station']).station_name): e['cnt'] for e in ride_counts
    }

    # remove self loops from the graph
    if (station.station_name, station.station_name) in edge_counts.keys():
        del edge_counts[(station.station_name, station.station_name)]

    # graph options
    options = {
        'node_color': 'blue',
        'node_size': 30,
        'line_color': 'grey',
        'linewidths': 1,
        'edge_color': 'green',
        'width': 2
    }
    fig = plt.figure(figsize=(12,8))
    graph_pos=nx.spring_layout(G)

    labels = {k:k for k in list(graph_pos.keys())}

    # draw graph
    nx.draw_networkx_edge_labels(G, graph_pos, edge_labels=edge_counts,font_size=16)
    nx.draw_networkx_nodes(G,graph_pos, **options)
    nx.draw_networkx_edges(G,graph_pos, width=2)

    # get the given station's y coordinate on figure
    station_ycoord = graph_pos[station.station_name][1]

    # draw station labels on graph
    for k,v in graph_pos.items():
        if k == station.station_name:
            continue
        if v[1] >= float(station_ycoord):
            plt.text(v[0], v[1] + .075, k, fontsize=10, bbox=dict(facecolor='red', alpha=0.3), horizontalalignment='center')
        else:
            plt.text(v[0], v[1] - .075, k, fontsize=10, bbox=dict(facecolor='red', alpha=0.3), horizontalalignment='center')

    plt.title(f"Number of journeys from {station.station_name} \n(centred on graph)")      
    plt.axis('off')
    plt.savefig(SAVE_PATH)
    context = {
        "impath": 'network.png',
        "ride_counts": edge_counts,
        "current_station": station,
        "locations": locations,
        "date_from": request.GET.get('date_from', None),
        "date_to": request.GET.get('date_to', None)
    }

    return render(request, 'reports/path-routes.html', context)