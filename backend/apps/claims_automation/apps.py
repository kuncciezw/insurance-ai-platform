"""
Django App Configuration for Claims Automation
"""

from django.apps import AppConfig


class ClaimsAutomationConfig(AppConfig):
    """Configuration for Claims Automation application"""
    
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.claims_automation'
    verbose_name = 'Claims Automation'
    
    def ready(self):
        """
        Initialize app on startup
        Pre-load ML models for faster predictions
        """
        try:
            # Import model loader to initialize models
            from ml_models.model_loader import get_model_loader
            
            # Pre-load models on startup
            loader = get_model_loader()
            
            print("✓ Claims Automation: ML models loaded")
        except Exception as e:
            print(f"⚠️ Claims Automation: Could not pre-load models - {e}")