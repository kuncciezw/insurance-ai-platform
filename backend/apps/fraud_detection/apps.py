from django.apps import AppConfig
 
 
class FraudDetectionConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.fraud_detection"
 
    def ready(self):
        import apps.fraud_detection.signals  