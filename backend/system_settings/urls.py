from django.urls import path
from .views import global_pricing_settings

urlpatterns = [
    path('pricing/', global_pricing_settings, name='global-pricing-settings'),
]