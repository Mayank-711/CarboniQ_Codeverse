from apscheduler.schedulers.background import BackgroundScheduler
from django.utils.timezone import now
from mainapp.models import User, Challenge, UserChallenge
import random

def assign_challenges_midnight():
    """Assigns new daily challenges at midnight for all users."""
    today = now().date()

    for user in User.objects.all():
        if not UserChallenge.objects.filter(user=user, assigned_date=today).exists():
            challenge = random.choice(Challenge.objects.all())
            UserChallenge.objects.create(user=user, challenge=challenge, assigned_date=today)
            print(f"✅ New challenge assigned to {user.username}: {challenge.title}")

def start_scheduler():
    scheduler = BackgroundScheduler()
    scheduler.add_job(assign_challenges_midnight, "cron", hour=0, minute=0)  # Runs at 00:00
    scheduler.start()
