"""
ML-Powered Dynamic Pricing API Views
Provides endpoints for premium calculation using trained ML models and Global Settings
"""

from rest_framework import status, viewsets
from rest_framework.decorators import api_view, action, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.db.models import Q, Avg, Count
from django.utils import timezone
from datetime import timedelta, date
from decimal import Decimal
import pandas as pd
import random

from .models import Quote, PriceHistory
from .serializers import (
    QuoteSerializer, QuoteListSerializer, QuoteCalculationInputSerializer,
    PriceHistorySerializer, PriceHistoryListSerializer
)
from apps.fraud_detection.models import Policyholder, Vehicle, Policy
from ml_models.model_loader import get_model_loader
from ml_models.feature_engineering import FeatureEngineer
from system_settings.models import GlobalPricingSettings

# Initialize model loader (singleton pattern)
model_loader = get_model_loader()
feature_engineer = FeatureEngineer()


class QuoteViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Quote management
    List, create, retrieve, update, and delete quotes
    """
    queryset = Quote.objects.all()
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        if self.action == 'list':
            return QuoteListSerializer
        return QuoteSerializer

    def get_queryset(self):
        """Filter quotes with query parameters"""
        queryset = Quote.objects.select_related(
            'policyholder', 'vehicle', 'converted_policy'
        )

        status_param = self.request.query_params.get('status')
        if status_param:
            queryset = queryset.filter(status=status_param)

        valid_only = self.request.query_params.get('valid_only')
        if valid_only == 'true':
            today = date.today()
            queryset = queryset.filter(
                status__in=['CALCULATED', 'SENT'],
                valid_until__gte=today
            )

        policyholder_id = self.request.query_params.get('policyholder_id')
        if policyholder_id:
            queryset = queryset.filter(policyholder_id=policyholder_id)

        return queryset.order_by('-created_at')

    @action(detail=True, methods=['post'])
    def send_to_customer(self, request, pk=None):
        """Mark quote as sent to customer"""
        quote = self.get_object()

        if quote.status != 'CALCULATED':
            return Response(
                {'error': 'Only calculated quotes can be sent'},
                status=status.HTTP_400_BAD_REQUEST
            )

        quote.status = 'SENT'
        quote.sent_at = timezone.now()
        quote.save()

        return Response({
            'message': 'Quote sent to customer',
            'quote_id': str(quote.id),
            'sent_at': quote.sent_at
        })

    @action(detail=True, methods=['post'])
    def accept_quote(self, request, pk=None):
        """Accept quote and convert to policy"""
        quote = self.get_object()

        if quote.status not in ['CALCULATED', 'SENT']:
            return Response(
                {'error': 'Quote cannot be accepted in current status'},
                status=status.HTTP_400_BAD_REQUEST
            )

        if not quote.is_valid:
            return Response(
                {'error': 'Quote has expired'},
                status=status.HTTP_400_BAD_REQUEST
            )

        quote.status = 'ACCEPTED'
        quote.save()

        return Response({
            'message': 'Quote accepted successfully',
            'quote_id': str(quote.id),
            'next_step': 'Create policy from quote'
        })


class PriceHistoryViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for PriceHistory (read-only)
    View historical pricing data for policies
    """
    queryset = PriceHistory.objects.all()
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        if self.action == 'list':
            return PriceHistoryListSerializer
        return PriceHistorySerializer

    def get_queryset(self):
        queryset = PriceHistory.objects.select_related(
            'policy', 'policy__policyholder', 'quote'
        )

        policy_id = self.request.query_params.get('policy_id')
        if policy_id:
            queryset = queryset.filter(policy_id=policy_id)

        reason = self.request.query_params.get('reason')
        if reason:
            queryset = queryset.filter(change_reason=reason)

        start_date = self.request.query_params.get('start_date')
        end_date = self.request.query_params.get('end_date')
        if start_date:
            queryset = queryset.filter(effective_from__gte=start_date)
        if end_date:
            queryset = queryset.filter(effective_from__lte=end_date)

        return queryset.order_by('-created_at')


def prepare_pricing_features(data, policyholder=None, vehicle=None):
    """Prepare features for ML pricing model"""
    current_year = date.today().year

    if policyholder:
        age = policyholder.age
        gender = policyholder.gender
        marital_status = policyholder.marital_status
        occupation = policyholder.occupation
        credit_score = policyholder.credit_score
        years_with_company = policyholder.years_with_company
        state = policyholder.state
    else:
        age = data.get('customer_age')
        credit_score = data.get('customer_credit_score')
        years_with_company = data.get('customer_years_experience', 0)
        gender = 'M'
        marital_status = 'Single'
        occupation = 'Professional'
        state = 'CA'

    if vehicle:
        vehicle_year = vehicle.manufacture_year
        vehicle_value = float(vehicle.market_value)
        vehicle_type = vehicle.vehicle_type
        fuel_type = vehicle.fuel_type
        has_anti_theft = vehicle.has_anti_theft
        has_airbags = vehicle.has_airbags
        has_abs = vehicle.has_abs
        is_modified = vehicle.is_modified
        odometer_reading = vehicle.odometer_reading
    else:
        vehicle_year = data.get('vehicle_manufacture_year')
        vehicle_value = float(data.get('vehicle_value'))
        has_anti_theft = data.get('vehicle_has_anti_theft', False)
        is_modified = data.get('vehicle_is_modified', False)
        vehicle_type = 'Sedan'
        fuel_type = 'Petrol'
        has_airbags = True
        has_abs = True
        odometer_reading = 50000

    vehicle_age = current_year - vehicle_year

    gender_map = {'M': 0, 'F': 1, 'Other': 2}
    marital_map = {'Single': 0, 'Married': 1, 'Divorced': 2, 'Widowed': 3}
    occupation_map = {'Professional': 0, 'Business': 1, 'Employee': 2, 'Self-Employed': 3}
    vehicle_type_map = {'Sedan': 0, 'SUV': 1, 'Truck': 2, 'Coupe': 3, 'Van': 4}
    fuel_type_map = {'Petrol': 0, 'Diesel': 1, 'Electric': 2, 'Hybrid': 3}
    policy_type_map = {'COMPREHENSIVE': 0, 'THIRD_PARTY': 1, 'COLLISION': 2, 'LIABILITY': 3}
    coverage_level_map = {'BASIC': 0, 'STANDARD': 1, 'PREMIUM': 2}
    state_map = {s: i for i, s in enumerate(['CA', 'NY', 'TX', 'FL', 'IL'])}

    features = {
        'age': age,
        'gender_encoded': gender_map.get(gender, 0),
        'marital_status_encoded': marital_map.get(marital_status, 0),
        'occupation_encoded': occupation_map.get(occupation, 0),
        'credit_score': credit_score,
        'years_with_company': years_with_company,
        'vehicle_age': vehicle_age,
        'vehicle_value': vehicle_value,
        'vehicle_type_encoded': vehicle_type_map.get(vehicle_type, 0),
        'fuel_type_encoded': fuel_type_map.get(fuel_type, 0),
        'has_anti_theft': int(has_anti_theft),
        'has_airbags': int(has_airbags),
        'has_abs': int(has_abs),
        'is_modified': int(is_modified),
        'odometer_reading': odometer_reading,
        'policy_type_encoded': policy_type_map.get(data.get('policy_type'), 0),
        'coverage_level_encoded': coverage_level_map.get(data.get('coverage_level'), 1),
        'coverage_amount': float(data.get('coverage_amount')),
        'deductible': float(data.get('deductible')),
        'state_encoded': state_map.get(state, 0)
    }

    return pd.DataFrame([features])


def _apply_global_pricing_rules(ml_premium: Decimal, customer_age: int, 
                                customer_credit_score: int, years_with_company: int, 
                                vehicle_age: int, vehicle_has_anti_theft: bool, 
                                vehicle_is_modified: bool, has_roadside: bool, 
                                has_rental: bool, has_glass: bool):
    """
    Private helper to calculate dynamic risk adjustments, discounts, and optional coverages
    using the singleton GlobalPricingSettings.
    """
    settings = GlobalPricingSettings.get_solo()
    risk_factors = {}
    risk_adjustment = Decimal('0.00')

    # Age factors (Dynamic)
    if customer_age < settings.age_threshold_young_driver:
        surcharge = ml_premium * Decimal(str(settings.surcharge_young_driver))
        risk_adjustment += surcharge
        risk_factors['young_driver'] = {
            'impact': f"+{float(settings.surcharge_young_driver) * 100:.0f}%",
            'reason': f'Driver under {settings.age_threshold_young_driver} years old'
        }
    elif customer_age > settings.age_threshold_senior_driver:
        surcharge = ml_premium * Decimal(str(settings.surcharge_senior_driver))
        risk_adjustment += surcharge
        risk_factors['senior_driver'] = {
            'impact': f"+{float(settings.surcharge_senior_driver) * 100:.0f}%",
            'reason': f'Driver over {settings.age_threshold_senior_driver} years old'
        }

    # Credit score factor (Dynamic)
    if customer_credit_score < settings.credit_threshold_poor:
        surcharge = ml_premium * Decimal(str(settings.surcharge_poor_credit))
        risk_adjustment += surcharge
        risk_factors['low_credit'] = {
            'impact': f"+{float(settings.surcharge_poor_credit) * 100:.0f}%",
            'reason': f'Credit score below {settings.credit_threshold_poor}'
    }


    # Vehicle age factor (Heuristic standard)
    if vehicle_age > settings.vehicle_age_threshold_old:
        risk_adjustment += ml_premium * Decimal(str(settings.surcharge_old_vehicle))
        risk_factors['old_vehicle'] = {
            'impact': f'+{float(settings.surcharge_old_vehicle) * 100:.0f}%',
            'reason': f'Vehicle is {vehicle_age} years old'
    }

    # Modified vehicle (Heuristic standard)
    if vehicle_is_modified:
        risk_adjustment += ml_premium * Decimal(str(settings.surcharge_modified_vehicle))
        risk_factors['modified_vehicle'] = {
            'impact': f'+{float(settings.surcharge_modified_vehicle) * 100:.0f}%',
            'reason': 'Vehicle has modifications'
    }

    # Calculate discounts
    discount_amount = Decimal('0.00')
    discounts = {}

    # Good credit discount (Dynamic)
    if customer_credit_score >= settings.credit_threshold_excellent:
        discount = ml_premium * Decimal(str(settings.discount_excellent_credit))
        discount_amount += discount
        discounts['good_credit'] = {
            'amount': float(discount),
            'reason': f'Credit score {settings.credit_threshold_excellent}+'
    }

    # Anti-theft discount (Dynamic)
    if vehicle_has_anti_theft:
        discount = ml_premium * Decimal(str(settings.discount_anti_theft))
        discount_amount += discount
        discounts['anti_theft'] = {
            'amount': float(discount),
            'reason': 'Anti-theft device installed'
    }


    # Loyalty discount (Heuristic standard)
    if years_with_company >= settings.loyalty_years_threshold:
        discount = ml_premium * Decimal(str(settings.discount_loyalty))
        discount_amount += discount
        discounts['loyalty'] = {
            'amount': float(discount),
            'reason': f'{years_with_company} years with company'
    }

    # Add optional coverages (Dynamic flat fees)
    optional_costs = {}
    optional_fees_total = Decimal('0.00')
    
    if has_roadside:
        optional_costs['roadside_assistance'] = float(settings.addon_roadside_assistance)
        optional_fees_total += Decimal(str(settings.addon_roadside_assistance))
    if has_rental:
        optional_costs['rental_coverage'] = float(settings.addon_rental_coverage)
        optional_fees_total += Decimal(str(settings.addon_rental_coverage))
    if has_glass:
        optional_costs['glass_coverage'] = float(settings.addon_glass_coverage)
        optional_fees_total += Decimal(str(settings.addon_glass_coverage))

    # Calculate final premium and enforce global minimum premium
    final_premium = ml_premium + risk_adjustment - discount_amount + optional_fees_total
    final_premium = max(final_premium, Decimal(str(settings.minimum_premium)))

    return risk_adjustment, risk_factors, discount_amount, discounts, optional_costs, final_premium


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def calculate_premium(request):
    """
    Calculate insurance premium using ML model and Global Rules
    POST /api/dynamic-pricing/calculate-premium/
    """
    try:
        input_serializer = QuoteCalculationInputSerializer(data=request.data)
        if not input_serializer.is_valid():
            return Response(input_serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        data = input_serializer.validated_data

        policyholder = None
        if data.get('policyholder_id'):
            try:
                policyholder = Policyholder.objects.get(id=data['policyholder_id'])
            except Policyholder.DoesNotExist:
                return Response({'error': 'Policyholder not found'}, status=status.HTTP_404_NOT_FOUND)

        vehicle = None
        if data.get('vehicle_id'):
            try:
                vehicle = Vehicle.objects.get(id=data['vehicle_id'])
            except Vehicle.DoesNotExist:
                return Response({'error': 'Vehicle not found'}, status=status.HTTP_404_NOT_FOUND)

        pricing_data = prepare_pricing_features(data, policyholder, vehicle)

        try:
            prediction = model_loader.predict_premium(pricing_data.iloc[0])
            ml_premium = Decimal(str(prediction['predicted_premium']))
            confidence = prediction.get('confidence', 0.85)
        except Exception as e:
            return Response({'error': f'ML prediction failed: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        customer_age = policyholder.age if policyholder else data.get('customer_age')
        customer_credit_score = policyholder.credit_score if policyholder else data.get('customer_credit_score')
        years_with_company = policyholder.years_with_company if policyholder else data.get('customer_years_experience', 0)

        current_year = date.today().year
        vehicle_year = vehicle.manufacture_year if vehicle else data.get('vehicle_manufacture_year')
        vehicle_age = current_year - vehicle_year
        vehicle_has_anti_theft = vehicle.has_anti_theft if vehicle else data.get('vehicle_has_anti_theft', False)
        vehicle_is_modified = vehicle.is_modified if vehicle else data.get('vehicle_is_modified', False)

        # Apply Global Pricing Rules using Helper
        risk_adjustment, risk_factors, discount_amount, discounts, optional_costs, final_premium = _apply_global_pricing_rules(
            ml_premium, customer_age, customer_credit_score, years_with_company,
            vehicle_age, vehicle_has_anti_theft, vehicle_is_modified,
            data.get('has_roadside_assistance', False), 
            data.get('has_rental_coverage', False), 
            data.get('has_glass_coverage', False)
        )

        response_data = {
            'base_premium': float(ml_premium),
            'risk_adjustment': float(risk_adjustment),
            'discount_amount': float(discount_amount),
            'final_premium': float(final_premium),
            'ml_predicted_premium': float(ml_premium),
            'confidence_score': confidence,
            'risk_factors': risk_factors,
            'discounts': discounts,
            'optional_coverages': optional_costs,
            'breakdown': {
                'coverage_amount': float(data['coverage_amount']),
                'deductible': float(data['deductible']),
                'policy_type': data['policy_type'],
                'coverage_level': data['coverage_level'],
                'customer_age': customer_age,
                'vehicle_age': vehicle_age,
            },
            'calculated_at': timezone.now().isoformat(),
        }

        return Response(response_data, status=status.HTTP_200_OK)

    except Exception as e:
        return Response({'error': f'Error calculating premium: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def generate_quote(request):
    """
    Generate a full insurance quote with ML pricing and Global Rules
    POST /api/dynamic-pricing/generate-quote/
    """
    try:
        input_serializer = QuoteCalculationInputSerializer(data=request.data)
        if not input_serializer.is_valid():
            return Response(input_serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        validated_data = input_serializer.validated_data

        policyholder = None
        if validated_data.get('policyholder_id'):
            try:
                policyholder = Policyholder.objects.get(id=validated_data['policyholder_id'])
            except Policyholder.DoesNotExist:
                return Response({'error': 'Policyholder not found'}, status=status.HTTP_404_NOT_FOUND)

        vehicle = None
        if validated_data.get('vehicle_id'):
            try:
                vehicle = Vehicle.objects.get(id=validated_data['vehicle_id'])
            except Vehicle.DoesNotExist:
                return Response({'error': 'Vehicle not found'}, status=status.HTTP_404_NOT_FOUND)

        pricing_data_df = prepare_pricing_features(validated_data, policyholder, vehicle)

        try:
            prediction = model_loader.predict_premium(pricing_data_df.iloc[0])
            ml_premium = Decimal(str(prediction['predicted_premium']))
            confidence = prediction.get('confidence', 0.85)
        except Exception as e:
            return Response({'error': f'ML prediction failed: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        customer_age = policyholder.age if policyholder else validated_data.get('customer_age')
        customer_credit_score = policyholder.credit_score if policyholder else validated_data.get('customer_credit_score')
        years_with_company = policyholder.years_with_company if policyholder else validated_data.get('customer_years_experience', 0)

        current_year = date.today().year
        vehicle_year = vehicle.manufacture_year if vehicle else validated_data.get('vehicle_manufacture_year')
        vehicle_age = current_year - vehicle_year
        vehicle_has_anti_theft = vehicle.has_anti_theft if vehicle else validated_data.get('vehicle_has_anti_theft', False)
        vehicle_is_modified = vehicle.is_modified if vehicle else validated_data.get('vehicle_is_modified', False)

        # Apply Global Pricing Rules using Helper
        risk_adjustment, risk_factors, discount_amount, discounts, optional_costs, final_premium = _apply_global_pricing_rules(
            ml_premium, customer_age, customer_credit_score, years_with_company,
            vehicle_age, vehicle_has_anti_theft, vehicle_is_modified,
            validated_data.get('has_roadside_assistance', False), 
            validated_data.get('has_rental_coverage', False), 
            validated_data.get('has_glass_coverage', False)
        )

        pricing_data = {
            'base_premium': float(ml_premium),
            'risk_adjustment': float(risk_adjustment),
            'discount_amount': float(discount_amount),
            'final_premium': float(final_premium),
            'ml_predicted_premium': float(ml_premium),
            'confidence_score': confidence,
            'risk_factors': risk_factors,
            'discounts': discounts,
            'optional_coverages': optional_costs,
        }

        input_data = request.data
        quote_number = f"QTE-{random.randint(100000000000, 999999999999)}"

        quote_data = {
            'quote_number': quote_number,
            'policy_type': input_data['policy_type'],
            'coverage_level': input_data['coverage_level'],
            'coverage_amount': input_data['coverage_amount'],
            'deductible': input_data['deductible'],
            'base_premium': Decimal(str(pricing_data['base_premium'])),
            'risk_adjustment': Decimal(str(pricing_data['risk_adjustment'])),
            'discount_amount': Decimal(str(pricing_data['discount_amount'])),
            'final_premium': Decimal(str(pricing_data['final_premium'])),
            'ml_predicted_premium': Decimal(str(pricing_data['ml_predicted_premium'])),
            'confidence_score': pricing_data['confidence_score'],
            'risk_factors': pricing_data['risk_factors'],
            'status': 'CALCULATED',
            'valid_until': date.today() + timedelta(days=30),
            'has_roadside_assistance': input_data.get('has_roadside_assistance', False),
            'has_rental_coverage': input_data.get('has_rental_coverage', False),
            'has_glass_coverage': input_data.get('has_glass_coverage', False),
        }

        if input_data.get('policyholder_id'):
            quote_data['policyholder_id'] = input_data['policyholder_id']
        else:
            quote_data.update({
                'customer_age': input_data['customer_age'],
                'customer_credit_score': input_data['customer_credit_score'],
                'customer_years_experience': input_data.get('customer_years_experience', 0),
            })

        if input_data.get('vehicle_id'):
            quote_data['vehicle_id'] = input_data['vehicle_id']
        else:
            quote_data.update({
                'vehicle_manufacture_year': input_data['vehicle_manufacture_year'],
                'vehicle_make': input_data['vehicle_make'],
                'vehicle_model': input_data['vehicle_model'],
                'vehicle_value': input_data['vehicle_value'],
                'vehicle_has_anti_theft': input_data.get('vehicle_has_anti_theft', False),
                'vehicle_is_modified': input_data.get('vehicle_is_modified', False),
            })

        if input_data.get('customer_email'):
            quote_data['customer_email'] = input_data['customer_email']
        if input_data.get('customer_phone'):
            quote_data['customer_phone'] = input_data['customer_phone']

        quote = Quote.objects.create(**quote_data)
        serializer = QuoteSerializer(quote)

        return Response({
            'message': 'Quote generated successfully',
            'quote': serializer.data,
            'pricing_details': pricing_data
        }, status=status.HTTP_201_CREATED)

    except Exception as e:
        return Response({'error': f'Error generating quote: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def compare_prices(request):
    """
    Compare prices across different coverage levels
    POST /api/dynamic-pricing/compare-prices/
    """
    try:
        base_data = request.data.copy()
        coverage_levels = ['BASIC', 'STANDARD', 'PREMIUM']
        comparisons = []

        for level in coverage_levels:
            level_data = base_data.copy()
            level_data['coverage_level'] = level

            base_coverage = float(base_data.get('coverage_amount', 50000))
            if level == 'BASIC':
                level_data['coverage_amount'] = base_coverage * 0.7
            elif level == 'STANDARD':
                level_data['coverage_amount'] = base_coverage
            else:
                level_data['coverage_amount'] = base_coverage * 1.5

            input_serializer = QuoteCalculationInputSerializer(data=level_data)
            if not input_serializer.is_valid():
                continue

            validated_data = input_serializer.validated_data

            policyholder = None
            vehicle = None

            if validated_data.get('policyholder_id'):
                try:
                    policyholder = Policyholder.objects.get(id=validated_data['policyholder_id'])
                except Policyholder.DoesNotExist:
                    pass

            if validated_data.get('vehicle_id'):
                try:
                    vehicle = Vehicle.objects.get(id=validated_data['vehicle_id'])
                except Vehicle.DoesNotExist:
                    pass

            pricing_data = prepare_pricing_features(validated_data, policyholder, vehicle)

            try:
                prediction = model_loader.predict_premium(pricing_data.iloc[0])
                ml_premium = Decimal(str(prediction['predicted_premium']))

                # Fetch variables to run accurate risk checks in comparison
                customer_age = policyholder.age if policyholder else validated_data.get('customer_age')
                customer_credit_score = policyholder.credit_score if policyholder else validated_data.get('customer_credit_score')
                years_with_company = policyholder.years_with_company if policyholder else validated_data.get('customer_years_experience', 0)
                vehicle_year = vehicle.manufacture_year if vehicle else validated_data.get('vehicle_manufacture_year')
                vehicle_age = date.today().year - vehicle_year
                vehicle_has_anti_theft = vehicle.has_anti_theft if vehicle else validated_data.get('vehicle_has_anti_theft', False)
                vehicle_is_modified = vehicle.is_modified if vehicle else validated_data.get('vehicle_is_modified', False)

                # Pass through the helper to get accurate representation for comparison
                risk_adj, r_factors, disc_amt, _, _, final_premium = _apply_global_pricing_rules(
                    ml_premium, customer_age, customer_credit_score, years_with_company,
                    vehicle_age, vehicle_has_anti_theft, vehicle_is_modified,
                    validated_data.get('has_roadside_assistance', False), 
                    validated_data.get('has_rental_coverage', False), 
                    validated_data.get('has_glass_coverage', False)
                )

                comparisons.append({
                    'coverage_level': level,
                    'coverage_amount': float(level_data['coverage_amount']),
                    'final_premium': float(final_premium),
                    'base_premium': float(ml_premium),
                    'risk_adjustment': float(risk_adj),
                    'discount_amount': float(disc_amt),
                    'risk_factors': r_factors
                })
            except Exception as e:
                print(f"Error calculating for {level}: {e}")
                continue

        if len(comparisons) >= 2:
            standard_premium = next((c['final_premium'] for c in comparisons if c['coverage_level'] == 'STANDARD'), None)
            if standard_premium:
                for comparison in comparisons:
                    comparison['savings_vs_standard'] = standard_premium - comparison['final_premium']

        return Response({
            'comparisons': comparisons,
            'policy_type': base_data['policy_type'],
            'generated_at': timezone.now().isoformat()
        }, status=status.HTTP_200_OK)

    except Exception as e:
        return Response({'error': f'Error comparing prices: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def pricing_statistics(request):
    """
    Get pricing statistics and trends
    GET /api/dynamic-pricing/statistics/
    """
    try:
        total_quotes = Quote.objects.count()
        active_quotes = Quote.objects.filter(
            status__in=['CALCULATED', 'SENT'],
            valid_until__gte=date.today()
        ).count()
        accepted_quotes = Quote.objects.filter(status='ACCEPTED').count()
        conversion_rate = (accepted_quotes / total_quotes * 100) if total_quotes > 0 else 0

        avg_premium = Quote.objects.aggregate(Avg('final_premium'))['final_premium__avg'] or 0

        by_policy_type = {}
        for policy_type in ['COMPREHENSIVE', 'THIRD_PARTY', 'COLLISION', 'LIABILITY']:
            quotes = Quote.objects.filter(policy_type=policy_type)
            by_policy_type[policy_type] = {
                'count': quotes.count(),
                'avg_premium': float(quotes.aggregate(Avg('final_premium'))['final_premium__avg'] or 0)
            }

        by_coverage = {}
        for level in ['BASIC', 'STANDARD', 'PREMIUM']:
            quotes = Quote.objects.filter(coverage_level=level)
            by_coverage[level] = {
                'count': quotes.count(),
                'avg_premium': float(quotes.aggregate(Avg('final_premium'))['final_premium__avg'] or 0)
            }

        thirty_days_ago = timezone.now() - timedelta(days=30)
        recent_quotes = Quote.objects.filter(created_at__gte=thirty_days_ago)

        response_data = {
            'total_quotes': total_quotes,
            'active_quotes': active_quotes,
            'accepted_quotes': accepted_quotes,
            'conversion_rate': round(conversion_rate, 2),
            'average_premium': float(avg_premium),
            'by_policy_type': by_policy_type,
            'by_coverage_level': by_coverage,
            'recent_trends': {
                'last_30_days_quotes': recent_quotes.count(),
                'last_30_days_accepted': recent_quotes.filter(status='ACCEPTED').count(),
            },
            'generated_at': timezone.now().isoformat(),
        }

        return Response(response_data, status=status.HTTP_200_OK)

    except Exception as e:
        return Response({'error': f'Error generating statistics: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)