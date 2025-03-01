from collections import defaultdict
import json
from django.http import JsonResponse
from django.shortcuts import render,redirect
from django.contrib import messages
from authapp.models import Friendship, UserProfile
from mainapp.models import TripLog,Chat
from .ml.scripts.predict_co2 import predict_co2_emission
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.utils.timezone import now
from django.db.models import Sum,F
from datetime import date, datetime,timedelta
import requests
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt


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
    last_chat = Chat.objects.filter(user=user).order_by('-search_date', '-search_time').first()
    return render(request, 'mainapp/homepage.html', {'graph_data': json.dumps(graph_data),'chats':last_chat})




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

    today = timezone.now().date() 
    print(f"[DEBUG] Today's Date: {today}")

    existing_trips = TripLog.objects.filter(user=user, date=today)
    print(f"[DEBUG] Existing trips for today: {[trip.id for trip in existing_trips]}")
    if existing_trips.count() == 1:
        print("[DEBUG] No previous trips found for today, awarding coins.")
        try:
            user_profile = UserProfile.objects.get(user=user)
            print(f"[DEBUG] Current Coins: {user_profile.coins}")
            user_profile.coins += 50 
            user_profile.streak +=1
            user_profile.save()
            print(f"[DEBUG] New Coins after Award: {user_profile.coins}")
            messages.success(request, 'You earned 50 coins for your first trip today!')
            messages.success(request, 'Your streak was increased 1')
        except UserProfile.DoesNotExist:
            messages.error(request, 'User profile not found. Contact support.')
            return redirect('logtrip')
    else:
        print("[DEBUG] Trip already logged for today.")
        messages.success(request, 'Trip logged successfully!')
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


def get_weekly_leaderboard():
    today = datetime.now().date()
    now = datetime.now()

    # Adjust week start and end dates for a week starting on Sunday and ending on Saturday
    start_of_week = today - timedelta(days=today.weekday() + 1) if today.weekday() != 6 else today
    end_of_week = start_of_week + timedelta(days=6)

    # Filter logs from the start of the current week (Sunday) to the end of the week (Saturday)
    weekly_logs = TripLog.objects.filter(date__gte=start_of_week, date__lte=end_of_week)
    # Aggregate total distance and carbon footprint by user
    leaderboard = weekly_logs.values('user__id', 'user__username').annotate(
        total_distance=Sum('api_distance'),
        total_carbon=Sum('co2_emission')
    ).annotate(
        efficiency=F('total_carbon') / F('total_distance')
    ).order_by('efficiency')  # Order by efficiency (ascending for better efficiency)

    # Get all user profiles with avatars
    profiles = UserProfile.objects.values('user__id', 'avatar')

    # Create a dictionary for quick lookup of avatars by user id
    avatar_dict = {profile['user__id']: profile['avatar'] for profile in profiles}

    # Add avatar information and round efficiency to the leaderboard entries
    for entry in leaderboard:
        user_id = entry['user__id']
        entry['avatar'] = avatar_dict.get(user_id, 'default.jpg')  # Use default if no avatar found
        # Round efficiency to 2 decimal places
        entry['total_distance']= round(entry['total_distance'],2)
        entry['total_carbon']= round(entry['total_carbon'],2)
        entry['efficiency'] = round(entry['efficiency'], 2)

    return {
        'leaderboard': leaderboard,
        'current_datetime': now,
        'start_of_week': start_of_week,
        'end_of_week': end_of_week,
    }

def friend_leaderboards(user):
    today = datetime.now().date()

    # Adjust week start and end dates for a week starting on Sunday and ending on Saturday
    start_of_week = today - timedelta(days=today.weekday() + 1) if today.weekday() != 6 else today
    end_of_week = start_of_week + timedelta(days=6)

    # Get friends' IDs
    friends_from_user = Friendship.objects.filter(from_user=user, accepted=True).values_list('to_user', flat=True)
    friends_to_user = Friendship.objects.filter(to_user=user, accepted=True).values_list('from_user', flat=True)
    
    # Combine both lists to get all friends and include the user themselves
    friends_ids = set(friends_from_user) | set(friends_to_user)
    friends_ids.add(user.id)  # Include the logged-in user

    # Filter logs for friends and the logged-in user
    weekly_logs = TripLog.objects.filter(user__id__in=friends_ids, date__gte=start_of_week, date__lte=end_of_week)

    # Aggregate total distance and carbon footprint by friend
    friend_leaderboard = weekly_logs.values('user__id', 'user__username').annotate(
        total_distance=Sum('api_distance'),
        total_carbon=Sum('co2_emission')
    ).annotate(
        efficiency=F('total_carbon') / F('total_distance')
    ).order_by('efficiency')  # Order by efficiency (ascending for better efficiency)

    # Get friend profiles with avatars
    profiles = UserProfile.objects.filter(user__id__in=friends_ids).values('user__id', 'avatar')

    # Create a dictionary for quick lookup of avatars by user id
    avatar_dict = {profile['user__id']: profile['avatar'] for profile in profiles}

    # Add avatar information and round efficiency to the friend leaderboard entries
    for entry in friend_leaderboard:
        user_id = entry['user__id']
        entry['avatar'] = avatar_dict.get(user_id, 'default.jpg')  # Use default if no avatar found
        # Round efficiency to 2 decimal places
        entry['total_distance']= round(entry['total_distance'],2)
        entry['total_carbon']= round(entry['total_carbon'],2)
        entry['efficiency'] = round(entry['efficiency'], 2)

    return friend_leaderboard

@login_required(login_url='/login/')
def leaderboards(request):
    now = datetime.now()
    user = request.user

    # Get the weekly leaderboard data
    leaderboard_data = get_weekly_leaderboard()

    # Get friend leaderboards data
    friends_lboard_data = friend_leaderboards(user)

    context = {
        'leaderboard': leaderboard_data['leaderboard'],
        'current_datetime': leaderboard_data['current_datetime'],
        'start_of_week': leaderboard_data['start_of_week'],
        'end_of_week': leaderboard_data['end_of_week'],
        'friends_leaderboard': friends_lboard_data  # Add friends leaderboard to context
    }
    return render(request, 'mainapp/leaderboards.html', context)



@csrf_exempt
@login_required(login_url='/login/')
def process_form(request):
    if request.method == 'POST':
        user = request.user
        search_date = date.today()
        search_time = datetime.now().strftime('%H:%M:%S')

        source_lat = request.POST.get('source_lat')
        source_lng = request.POST.get('source_lng')
        dest_lat = request.POST.get('dest_lat')
        dest_lng = request.POST.get('dest_lng')
        source_add = request.POST.get('source-add')
        dest_add = request.POST.get('destination-add')

        print(f"[DEBUG] User: {user}, Date: {search_date}, Time: {search_time}")
        print(f"[DEBUG] Source: ({source_lat}, {source_lng}), Destination: ({dest_lat}, {dest_lng})")
        print(f"[DEBUG] Source Address: {source_add}, Destination Address: {dest_add}")

        if source_lat and source_lng and dest_lat and dest_lng:
            try:
                # Prepare parameters for the OLA Maps API request
                params = {
                    'origin': f'{source_lat},{source_lng}',
                    'destination': f'{dest_lat},{dest_lng}',
                    'mode': 'driving',
                    'alternatives': 'false',
                    'steps': 'true',
                    'overview': 'full',
                    'language': 'en',
                    'traffic_metadata': 'true',
                    'api_key': 'upIsbo0X7RjH2SfHjy2eYpm8TWdynT6vFDCpA85y'
                }

                print(f"[DEBUG] OLA Maps API Request Params: {params}")

                # Make the API request
                response = requests.post('https://api.olamaps.io/routing/v1/directions', params=params)
                print(f"[DEBUG] OLA Maps API Response Code: {response.status_code}")

                if response.status_code == 200:
                    data = response.json()
                    print(f"[DEBUG] OLA Maps API Response Data: {json.dumps(data, indent=2)}")

                    if 'routes' in data and data['routes']:
                        legs = data['routes'][0]['legs']
                        total_distance = sum(leg['distance'] for leg in legs) / 1000  # Convert to km
                        total_duration = sum(leg['duration'] for leg in legs) / 60  # Convert to minutes
                        total_distance = round(total_distance, 2)
                        total_duration = round(total_duration, 2)

                        print(f"[DEBUG] Total Distance: {total_distance} km, Total Duration: {total_duration} mins")

                        # Transport types and their CO2 emissions
                        list_of_transport = {
                            "Bus": 50, "Electric Bus": 10, "AC Bus": 80, "Electric AC Bus": 10,
                            "Train": 41, "Electric Train": 10, "AC Train": 50, "Electric AC Train": 10,
                            "Car 1 Passenger": 128, "Electric Car 1 Passenger": 20,
                            "Car 2 Passenger": 64, "Electric Car 2 Passenger": 20,
                            "Car 3 Passenger": 48, "Electric Car 3 Passenger": 20,
                            "Car 4 Passenger": 32, "Electric Car 4 Passenger": 20,
                            "Bike 1 Passenger": 50, "Electric Bike 1 Passenger": 20,
                            "Bike 2 Passenger": 40, "Electric Bike 2 Passenger": 20,
                            "Rickshaw 1 Passenger": 100, "Electric Rickshaw 1 Passenger": 10,
                            "Rickshaw 2 Passenger": 80, "Electric Rickshaw 2 Passenger": 10,
                            "Rickshaw 3 Passenger": 70, "Electric Rickshaw 3 Passenger": 10,
                            "Scooter 1 Passenger": 50, "Electric Scooter 1 Passenger": 20,
                            "Scooter 2 Passenger": 40, "Electric Scooter 2 Passenger": 20,
                            "Walk": 0, "Bicycle": 0
                        }

                        carbon_footprint_perkm = {mode: round(value * total_distance, 2) for mode, value in list_of_transport.items()}
                        print(f"[DEBUG] Carbon Footprint per KM: {carbon_footprint_perkm}")

                        # Nearby places search
                        # ✅ Corrected Nearby Search API Request
                        url = 'https://api.olamaps.io/places/v1/nearbysearch/advanced'
                        nearby_params = {
                            'location': f'{source_lat},{source_lng}',
                            'radius': 1000,  # Increased to 1000m for better results
                            'types': 'bus_station,train_station,subway_station',  # ✅ Fixed types
                            'withCentroid': 'false',
                            'rankBy': 'distance',
                            'limit': 5,
                            'api_key': 'upIsbo0X7RjH2SfHjy2eYpm8TWdynT6vFDCpA85y'
                        }
                        print(f"[DEBUG] Nearby Search API Request Params: {nearby_params}")

                        headers = {'accept': 'application/json'}
                        nearby_response = requests.get(url, headers=headers, params=nearby_params)
                        print(f"[DEBUG] Nearby Places API Response Code: {nearby_response.status_code}")

                        nearby_bus_stops = []
                        if nearby_response.status_code == 200:
                            nearby_data = nearby_response.json()
                            print(f"[DEBUG] Nearby Places API Response Data: {json.dumps(nearby_data, indent=2)}")

                            if 'predictions' in nearby_data:
                                for place in nearby_data['predictions']:
                                    nearby_bus_stops.append(place.get('structured_formatting', {}).get('main_text', 'Unknown Place'))
                            else:
                                print("[DEBUG] No nearby places found.")

                        nearby_bus_stops_str = ', '.join(nearby_bus_stops)
                        print(f"[DEBUG] Nearby Bus Stops: {nearby_bus_stops_str}")

                        # ✅ Saving Data to Database
                        chat_entry = Chat.objects.create(
                            user=user,
                            source_lat=source_lat,
                            source_lng=source_lng,
                            dest_lat=dest_lat,
                            dest_lng=dest_lng,
                            source_address=source_add,
                            destination_address=dest_add,
                            search_date=search_date,
                            search_time=search_time,
                            distance=total_distance,
                            duration=total_duration,
                            carbon_footprint=carbon_footprint_perkm,
                            Nearby_Bus_Stops=nearby_bus_stops_str
                        )

                        print(f"[DEBUG] Chat entry saved successfully: {chat_entry}")
                        return redirect('homepage')

                    else:
                        print("[ERROR] No valid routes found in API response.")
                        return redirect('homepage')

                else:
                    print(f"[ERROR] OLA Maps API Request Failed: {response.status_code}")
                    return redirect('homepage')

            except Exception as e:
                print(f"[ERROR] Exception occurred: {e}")
                return redirect('homepage')

    print("[ERROR] Invalid request method.")
    return redirect('homepage')