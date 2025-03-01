import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "CarboniQ_Codeverse.settings")  # Replace with your actual project name
django.setup()

from mainapp.models import Challenge

challenges = [
    {"title": "Carpool today", "description": "Share a ride with colleagues or friends."},
    {"title": "Use public transport today", "description": "Take a bus, metro, or train."},
    {"title": "Walk for 1 km today", "description": "Get some fresh air and reduce carbon footprint!"},
    {"title": "Use an EV today", "description": "Try an electric vehicle or bike."},
    {"title": "Reduce car AC usage by 50%", "description": "Save energy by lowering AC usage."},
    {"title": "Take a train instead of a car", "description": "Reduce emissions by switching to a train."},
    {"title": "Cycle for at least 2 km", "description": "Boost health and reduce pollution."},
    {"title": "Avoid using plastic bags today", "description": "Carry a cloth or jute bag instead."},
    {"title": "Use a reusable water bottle today", "description": "Say no to single-use plastic bottles."},
    {"title": "Take a shorter shower (5 mins max)", "description": "Save water by reducing shower time."},
    {"title": "Use phone less than 4 hours", "description": "Limit screen time to reduce energy consumption."}
]

for challenge in challenges:
    obj, created = Challenge.objects.get_or_create(title=challenge["title"], defaults={"description": challenge["description"], "points": 10})
    if created:
        print(f"✅ Added: {challenge['title']}")
    else:
        print(f"⏩ Skipped (already exists): {challenge['title']}")

print("🎯 Challenges populated successfully!")
