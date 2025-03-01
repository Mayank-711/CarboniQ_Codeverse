import os
from django.conf import settings

# Define the path to the ML models directory
ML_MODELS_DIR = os.path.join(settings.BASE_DIR, "mainapp", "ml", "models")
