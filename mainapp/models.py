# Create your models here.
from django.db import models
from django.contrib.auth.models import User

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