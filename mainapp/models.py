# Create your models here.
from django.db import models
from django.contrib.auth.models import User
import random
from datetime import date

class TripLog(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="trips")
    source_address = models.CharField(max_length=255)
    source_lat = models.DecimalField(max_digits=9, decimal_places=6)
    source_lng = models.DecimalField(max_digits=9, decimal_places=6)
    destination_address = models.CharField(max_length=255)
    dest_lat = models.DecimalField(max_digits=9, decimal_places=6)
    dest_lng = models.DecimalField(max_digits=9, decimal_places=6)
    mode_of_transport = models.CharField(max_length=50)
    time_taken = models.FloatField()  # User-entered trip time in minutes
    api_duration = models.FloatField()  # Fetched time from API in minutes
    api_distance = models.FloatField()  # Fetched distance from API in km
    electric_vehicle = models.BooleanField(default=False)
    co2_emission = models.FloatField()  # CO2 emission in grams
    date = models.DateField()
    passengers = models.IntegerField(default=1)
    
    # New Fields
    public_transport = models.BooleanField(default=False)  # Whether it was public transport
    greener_travel = models.BooleanField(default=False)  # Whether it was a greener travel option

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.source_address} to {self.destination_address} ({self.date})"
    


class Chat(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)  # Link to the user
    source_lat = models.FloatField()
    source_lng = models.FloatField()
    dest_lat = models.FloatField()
    dest_lng = models.FloatField()
    source_address = models.CharField(max_length=255)
    destination_address = models.CharField(max_length=255)
    search_date = models.DateField()
    search_time = models.TimeField()
    distance = models.FloatField()
    duration = models.FloatField()
    carbon_footprint = models.JSONField()  # Store carbon footprint data in JSON format
    Nearby_Bus_Stops = models.CharField(max_length=300)
    def __str__(self):
        return f"Trip from {self.source_address} to {self.destination_address} on {self.search_date}"
    

class Challenge(models.Model):
    title = models.CharField(max_length=255, unique=True)
    description = models.TextField()
    points = models.IntegerField(default=10)
    created_at = models.DateTimeField(auto_now_add=True)  # ✅ This will automatically set the timestamp

    def __str__(self):
        return self.title

class UserChallenge(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    challenge = models.ForeignKey(Challenge, on_delete=models.CASCADE)
    assigned_date = models.DateField(default=date.today)
    completed = models.BooleanField(default=False)

    class Meta:
        unique_together = ('user', 'assigned_date')  # Ensure one challenge per day

    def __str__(self):
        return f"{self.user.username} - {self.challenge.title} ({self.assigned_date})"