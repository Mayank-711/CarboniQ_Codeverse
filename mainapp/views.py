from collections import defaultdict
import json
from django.http import JsonResponse
from django.shortcuts import render,redirect
from django.contrib import messages
from authapp.models import Friendship, UserProfile
from mainapp.models import TripLog
from .ml.scripts.predict_co2 import predict_co2_emission
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.utils.timezone import now
from django.db.models import Sum,F
from datetime import date, datetime,timedelta

@login_required(login_url='/login/')
def homepage(request):
    user = request.user
    today = now().date()
    
    # Weekly Data
    week_start = today - timedelta(days=6)
    weekly_trips = TripLog.objects.filter(user=user, date__range=[week_start, today])

    # Monthly Data
    month_start = today - timedelta(days=29)
    monthly_trips = TripLog.objects.filter(user=user, date__range=[month_start, today])

    # Transport Modes for Pie Chart
    transport_modes = weekly_trips.values_list('mode_of_transport', flat=True).distinct()
    pie_labels = list(transport_modes)

    # Inner Pie (Distance) & Outer Pie (CO₂ Emissions)
    distance_values = [
        weekly_trips.filter(mode_of_transport=mode).aggregate(
            total_distance=Sum('api_distance')
        )['total_distance'] or 0 for mode in transport_modes
    ]

    emission_values = [
        weekly_trips.filter(mode_of_transport=mode).aggregate(
            total_emission=Sum('co2_emission')
        )['total_emission'] or 0 for mode in transport_modes
    ]

    # Weekly Line Graph (Daily CO₂ Emission)
    daily_labels = [(week_start + timedelta(days=i)).strftime('%a') for i in range(7)]
    daily_values = [
        weekly_trips.filter(date=week_start + timedelta(days=i)).aggregate(
            total_co2=Sum('co2_emission')
        )['total_co2'] or 0 for i in range(7)
    ]

    # Monthly Line Graph (Daily CO₂ Emission)
    monthly_labels = [(month_start + timedelta(days=i)).strftime('%d %b') for i in range(30)]
    monthly_values = [
        monthly_trips.filter(date=month_start + timedelta(days=i)).aggregate(
            total_co2=Sum('co2_emission')
        )['total_co2'] or 0 for i in range(30)
    ]

    # Stats Data
    total_trips = weekly_trips.count()
    greener_trips = weekly_trips.filter(greener_travel=True).count()
    public_trips = weekly_trips.filter(public_transport=True).count()
    total_co2_emission = weekly_trips.aggregate(total=Sum('co2_emission'))['total'] or 0

    graph_data = {
        'pie_labels': pie_labels,
        'distance_values': distance_values,  # Inner pie (Distance)
        'emission_values': emission_values,  # Outer pie (Emissions)
        'daily_labels': daily_labels,
        'daily_values': daily_values,
        'monthly_labels': monthly_labels,
        'monthly_values': monthly_values,
        'total_trips': total_trips,
        'greener_trips': greener_trips,
        'public_trips': public_trips,
        'total_co2_emission': total_co2_emission
    }

    return render(request, 'mainapp/homepage.html', {'graph_data': json.dumps(graph_data)})




@login_required(login_url='/login/')
def logtrip(request):
    user = request.user
    
    if request.method == "POST":
        source_address = request.POST.get("source")
        source_lat = request.POST.get("source_lat")
        source_lng = request.POST.get("source_lng")
        destination_address = request.POST.get("destination")
        dest_lat = request.POST.get("dest_lat")
        dest_lng = request.POST.get("dest_lng")
        mode_of_transport = request.POST.get("mode_of_transport")
        date = request.POST.get("date")
        time_taken = float(request.POST.get("time_taken"))
        electric_vehicle = request.POST.get("electric_vehicle", "No") == "Yes"
        passengers = int(request.POST.get("passengers", 1))
        api_distance = float(request.POST.get("calculated_distance", "0"))  # in kilometers
        api_duration = float(request.POST.get("calculated_duration", "0"))  # in minutes

        # Debugging logs
        # print("==== LOG TRIP DATA ====")
        # print("Source:", source_address, "Coordinates:", f"{source_lat}, {source_lng}")
        # print("Destination:", destination_address, "Coordinates:", f"{dest_lat}, {dest_lng}")
        # print("Mode of Transport:", mode_of_transport)
        # print("Electric Vehicle:", electric_vehicle)
        # print("Passengers (Before Adjustment):", passengers)
        # print("Distance (API):", api_distance, "km, Time Taken (API):", api_duration, "mins")
        # print("Time Taken (User Entered):", time_taken, "User:", user)

        # Adjust passenger count for public transport
        public_transports = ["bus", "train", "metro", "actrain", "acbus"]
        if mode_of_transport in public_transports:
            passengers = 0

        # Convert "metro" and "train" to "etrain"
        if mode_of_transport in ["metro", "train"]:
            mode_of_transport = "etrain"

        # Add electric prefix if applicable
        if electric_vehicle and mode_of_transport not in ["actrain", "acbus", "etrain"]:
            mode_of_transport = "e" + mode_of_transport

        # Call the prediction function
        predicted_co2 = round(get_predictions(mode_of_transport, passengers, api_distance, api_duration, time_taken), 2)
        # Debugging output
        # print("Final Mode of Transport:", mode_of_transport)
        # print("Passengers (Adjusted):", passengers)
        # print(f"Predicted CO2 Emission: {predicted_co2:.2f}g")
        public_transport_option = False
        greener_travel = False
        public_transports = ["bus", "ebus", "acbus", "eacbus", "etrain", "actrain"]
        if mode_of_transport in public_transports:
            public_transport_option = True
            greener_travel = True

        if mode_of_transport[0] == "e":
            greener_travel = True
        if mode_of_transport == "walk" or mode_of_transport == "cycle":
            greener_travel = True
        if passengers > 3:
            greener_travel = True
        
        TripLog.objects.create(
            user=user,
            source_address=source_address,
            source_lat=source_lat,
            source_lng=source_lng,
            destination_address=destination_address,
            dest_lat=dest_lat,
            dest_lng=dest_lng,
            mode_of_transport=mode_of_transport,
            time_taken=time_taken,
            api_duration=api_duration,
            api_distance=api_distance,
            electric_vehicle=electric_vehicle,
            co2_emission=predicted_co2,
            date=date,
            passengers=passengers,
            public_transport=public_transport_option,
            greener_travel=greener_travel
        )
        messages.success(request, "Trip Logged Successfully!")
        return redirect("logtrip")
    
    trip_logs = TripLog.objects.filter(user=user).order_by("-date", "-created_at") 

    # Paginate (5 logs per page)
    paginator = Paginator(trip_logs, 5)
    page_number = request.GET.get("page")  # Get the page number from URL
    trip_logs_page = paginator.get_page(page_number)
    return render(request, "mainapp/logtrip.html", {"trip_logs": trip_logs_page})



def get_predictions(mode_of_transport, passengers, distance, time,time_taken):
    """
    Wrapper function to call the ML model's CO2 emission prediction.
    """

    # Adjust passenger count for electric vehicles
    passengers = float(passengers)
    

    # Call the ML model prediction function
    co2_count = predict_co2_emission(mode_of_transport, passengers, distance, time)
    if mode_of_transport == "ecar":
        new_passengers = passengers/2
        co2_count = co2_count/ new_passengers
    if mode_of_transport == "actrain":
        co2_count = co2_count/2

    if time_taken > time:
        extra_time = float(time_taken) - time
        carbonfootprint_per_min = co2_count / time
        extra_co2 = extra_time * carbonfootprint_per_min
        co2_count += extra_co2
    
    return co2_count


@login_required(login_url='/login/')
def leaderboards(request):
    return render(request,'mainapp/leaderboards.html')