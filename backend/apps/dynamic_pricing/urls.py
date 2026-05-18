"""
URL Configuration for Dynamic Pricing API
"""
from django.urls import path
from rest_framework.routers import SimpleRouter
from . import views

router = SimpleRouter()
router.register(r'quotes', views.QuoteViewSet, basename='quote')
router.register(r'price-history', views.PriceHistoryViewSet, basename='price-history')

app_name = 'dynamic_pricing'

pricing_patterns = [
    path('calculate-premium/', views.calculate_premium, name='calculate-premium'),
    path('generate-quote/', views.generate_quote, name='generate-quote'),
    path('compare-prices/', views.compare_prices, name='compare-prices'),
    path('statistics/', views.pricing_statistics, name='statistics'),
]

urlpatterns = router.urls + pricing_patterns