from django.apps import AppConfig
import threading

class MainAppConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "mainapp"

    def ready(self):
        from mainapp.tasks import start_scheduler  # Import inside the method to avoid import issues
        thread = threading.Thread(target=start_scheduler, daemon=True)
        thread.start()