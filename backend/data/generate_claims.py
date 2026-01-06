"""
Generate synthetic insurance claims data with fraud patterns
"""

import random
from datetime import datetime, timedelta
from decimal import Decimal
from faker import Faker
from .base_generator import DataGenerator, InsuranceDataConfig

fake = Faker()

class ClaimGenerator(DataGenerator):
    """Generate realistic insurance claims with fraud detection features"""
    
    CLAIM_TYPES = ['ACCIDENT', 'THEFT', 'VANDALISM', 'NATURAL_DISASTER', 'FIRE', 'OTHER']
    CLAIM_STATUSES = ['SUBMITTED', 'UNDER_REVIEW', 'APPROVED', 'REJECTED', 'PAID', 'CLOSED']
    SEVERITIES = ['MINOR', 'MODERATE', 'MAJOR', 'TOTAL_LOSS']
    
    # Typical claim amounts by type and severity
    CLAIM_AMOUNTS = {
        'ACCIDENT': {
            'MINOR': (500, 3000),
            'MODERATE': (3000, 10000),
            'MAJOR': (10000, 30000),
            'TOTAL_LOSS': (30000, 80000)
        },
        'THEFT': {
            'MINOR': (200, 1000),
            'MODERATE': (1000, 5000),
            'MAJOR': (5000, 20000),
            'TOTAL_LOSS': (20000, 60000)
        },
        'VANDALISM': {
            'MINOR': (300, 1500),
            'MODERATE': (1500, 5000),
            'MAJOR': (5000, 15000),
            'TOTAL_LOSS': (15000, 40000)
        },
        'NATURAL_DISASTER': {
            'MINOR': (1000, 5000),
            'MODERATE': (5000, 15000),
            'MAJOR': (15000, 40000),
            'TOTAL_LOSS': (40000, 100000)
        },
        'FIRE': {
            'MINOR': (800, 3000),
            'MODERATE': (3000, 10000),
            'MAJOR': (10000, 35000),
            'TOTAL_LOSS': (35000, 80000)
        },
        'OTHER': {
            'MINOR': (400, 2000),
            'MODERATE': (2000, 8000),
            'MAJOR': (8000, 20000),
            'TOTAL_LOSS': (20000, 50000)
        }
    }
    
    # Incident descriptions by claim type
    INCIDENT_DESCRIPTIONS = {
        'ACCIDENT': [
            'Rear-ended at traffic light during rush hour',
            'Side collision at intersection, other driver ran red light',
            'Hit while parked in grocery store parking lot',
            'Multi-vehicle collision on highway due to sudden braking',
            'Backed into another vehicle in parking garage',
            'T-bone collision at four-way stop',
            'Single vehicle accident, lost control on wet road',
            'Collision with pedestrian crossing at crosswalk',
            'Hit and run incident, other driver fled scene',
            'Accident in parking lot while reversing'
        ],
        'THEFT': [
            'Vehicle stolen from residential driveway overnight',
            'Car broken into, personal belongings stolen',
            'Catalytic converter stolen from parked vehicle',
            'Vehicle stolen from shopping mall parking lot',
            'Wheels and tires stolen while parked on street',
            'Vehicle stolen and later recovered damaged',
            'Break-in, stereo system and electronics stolen',
            'Theft of personal items from unlocked vehicle',
            'Vehicle stolen from office parking garage',
            'Attempted theft, significant damage to ignition'
        ],
        'VANDALISM': [
            'Vehicle spray painted with graffiti',
            'Windows smashed, no items stolen',
            'Tires slashed in apartment complex parking',
            'Deep scratches along entire side of vehicle',
            'Mirrors kicked off and damaged',
            'Windshield deliberately cracked',
            'Interior damaged, seats slashed',
            'Paint damaged with acidic substance',
            'Vehicle keyed in multiple locations',
            'Headlights and taillights smashed'
        ],
        'NATURAL_DISASTER': [
            'Hail damage to hood, roof, and trunk',
            'Tree fell on vehicle during storm',
            'Flood damage, vehicle submerged in water',
            'Tornado debris caused significant damage',
            'Hurricane wind damage and water intrusion',
            'Fallen tree branch damaged roof and windshield',
            'Lightning strike caused electrical damage',
            'Flood swept vehicle into obstruction',
            'Wind-blown debris shattered windows',
            'Snow and ice damage from winter storm'
        ],
        'FIRE': [
            'Engine fire while driving on highway',
            'Electrical fire in dashboard',
            'Vehicle caught fire after accident',
            'Fire originated from catalytic converter',
            'Intentional fire set by unknown party',
            'Fire spread from nearby structure',
            'Fuel leak caused fire after impact',
            'Battery malfunction caused engine fire',
            'Fire in parking garage spread to vehicle',
            'Exhaust system malfunction caused fire'
        ],
        'OTHER': [
            'Animal collision on rural road',
            'Struck by falling object from overpass',
            'Damage from pothole on city street',
            'Hit by shopping cart in parking lot',
            'Collision with cyclist',
            'Damaged by debris on highway',
            'Hit by golf ball at golf course',
            'Collision with deer on country road',
            'Damaged by construction equipment',
            'Rock thrown at vehicle from overpass'
        ]
    }
    
    @staticmethod
    def generate_legitimate_claim(policy, policyholder, vehicle, index):
        """Generate a legitimate (non-fraudulent) claim"""
        
        # Select claim type (weighted by frequency)
        claim_type = ClaimGenerator.weighted_choice(
            ClaimGenerator.CLAIM_TYPES,
            [0.6, 0.1, 0.1, 0.1, 0.05, 0.05]
        )
        
        # Determine severity
        severity = ClaimGenerator.weighted_choice(
            ClaimGenerator.SEVERITIES,
            [0.5, 0.3, 0.15, 0.05]
        )
        
        # Generate claim amount based on type and severity
        amount_range = ClaimGenerator.CLAIM_AMOUNTS[claim_type][severity]
        claimed_amount = Decimal(random.uniform(amount_range[0], amount_range[1]))
        
        # Cap at vehicle value for total loss
        if severity == 'TOTAL_LOSS':
            claimed_amount = min(claimed_amount, vehicle['market_value'] * Decimal('1.1'))
        
        # Incident date (within policy period)
        policy_start = policy['start_date']
        policy_end = min(policy['end_date'], datetime.now().date())

        # Calculate start date for incident (at least 1 day after policy start, or 30 days if policy is long enough)
        days_to_add = min(30, max(1, (policy_end - policy_start).days - 1))
        incident_start = datetime.combine(policy_start, datetime.min.time()) + timedelta(days=days_to_add)
        incident_end = datetime.combine(policy_end, datetime.max.time())

        # Make sure start is before end
        if incident_start >= incident_end:
            incident_start = datetime.combine(policy_start, datetime.min.time()) + timedelta(days=1)

        # Legitimate claims happen at random times during policy
        incident_date = ClaimGenerator.random_datetime_between(incident_start, incident_end)

        
        # Incident location
        location_type = random.choice(InsuranceDataConfig.INCIDENT_LOCATIONS)
        incident_location = f"{location_type}, {fake.city()}, {policyholder['state']}"
        
        # Incident description
        incident_description = random.choice(
            ClaimGenerator.INCIDENT_DESCRIPTIONS[claim_type]
        )
        
        # Police report (more likely for severe incidents)
        if severity in ['MAJOR', 'TOTAL_LOSS']:
            police_report_filed = random.random() > 0.2
        elif claim_type in ['THEFT', 'ACCIDENT']:
            police_report_filed = random.random() > 0.4
        else:
            police_report_filed = random.random() > 0.7
        
        police_report_number = (
            f"PR-{random.randint(100000, 999999)}" 
            if police_report_filed else None
        )
        
        # Witnesses (more likely for accidents)
        if claim_type == 'ACCIDENT':
            witnesses_present = random.random() > 0.4
            number_of_witnesses = random.randint(1, 3) if witnesses_present else 0
        else:
            witnesses_present = random.random() > 0.7
            number_of_witnesses = random.randint(0, 2) if witnesses_present else 0
        
        # Vehicles involved (mainly for accidents)
        if claim_type == 'ACCIDENT':
            number_of_vehicles_involved = ClaimGenerator.weighted_choice(
                [1, 2, 3, 4],
                [0.3, 0.5, 0.15, 0.05]
            )
        else:
            number_of_vehicles_involved = 1
        
        # Injuries (more likely in severe accidents)
        if claim_type == 'ACCIDENT' and severity in ['MAJOR', 'TOTAL_LOSS']:
            number_of_injuries = random.randint(0, 3)
        elif claim_type == 'ACCIDENT':
            number_of_injuries = random.randint(0, 1)
        else:
            number_of_injuries = 0
        
        # Third party involvement
        third_party_involved = (
            number_of_vehicles_involved > 1 or 
            (claim_type == 'ACCIDENT' and random.random() > 0.3)
        )
        
        # Claim status based on submission time
        days_since_incident = (datetime.now().date() - incident_date.date()).days
        
        if days_since_incident < 7:
            claim_status = 'SUBMITTED'
            approved_amount = Decimal('0.00')
            paid_amount = Decimal('0.00')
            reviewed_date = None
            closed_date = None
        elif days_since_incident < 30:
            claim_status = ClaimGenerator.weighted_choice(
                ['SUBMITTED', 'UNDER_REVIEW', 'APPROVED'],
                [0.2, 0.5, 0.3]
            )
            if claim_status == 'APPROVED':
                approved_amount = claimed_amount * Decimal(random.uniform(0.85, 1.0))
                paid_amount = Decimal('0.00')
                reviewed_date = incident_date + timedelta(days=random.randint(5, 15))
                closed_date = None
            else:
                approved_amount = Decimal('0.00')
                paid_amount = Decimal('0.00')
                reviewed_date = None
                closed_date = None
        else:
            claim_status = ClaimGenerator.weighted_choice(
                ['APPROVED', 'PAID', 'CLOSED', 'REJECTED'],
                [0.1, 0.5, 0.35, 0.05]
            )
            if claim_status in ['APPROVED', 'PAID', 'CLOSED']:
                approved_amount = claimed_amount * Decimal(random.uniform(0.85, 1.0))
                paid_amount = approved_amount if claim_status in ['PAID', 'CLOSED'] else Decimal('0.00')
                reviewed_date = incident_date + timedelta(days=random.randint(5, 20))
                closed_date = reviewed_date + timedelta(days=random.randint(5, 15)) if claim_status == 'CLOSED' else None
            else:
                approved_amount = Decimal('0.00')
                paid_amount = Decimal('0.00')
                reviewed_date = incident_date + timedelta(days=random.randint(10, 30))
                closed_date = reviewed_date
        
        # Fraud indicators (legitimate claims have low scores)
        fraud_score = random.uniform(0.0, 0.3)
        is_fraudulent = False
        fraud_reason = None
        
        claim = {
            'claim_number': ClaimGenerator.generate_id('CLM', 12),
            'policy_number': policy['policy_number'],
            'policyholder_id': policyholder['policy_holder_id'],
            'vehicle_id': vehicle['vehicle_id'],
            'claim_type': claim_type,
            'claim_status': claim_status,
            'severity': severity,
            'incident_date': incident_date,
            'incident_location': incident_location,
            'incident_description': incident_description,
            'police_report_filed': police_report_filed,
            'police_report_number': police_report_number,
            'witnesses_present': witnesses_present,
            'number_of_witnesses': number_of_witnesses,
            'number_of_vehicles_involved': number_of_vehicles_involved,
            'number_of_injuries': number_of_injuries,
            'third_party_involved': third_party_involved,
            'claimed_amount': claimed_amount,
            'approved_amount': approved_amount,
            'paid_amount': paid_amount,
            'fraud_score': fraud_score,
            'is_fraudulent': is_fraudulent,
            'fraud_reason': fraud_reason,
            'submitted_date': incident_date + timedelta(hours=random.randint(1, 72)),
            'reviewed_date': reviewed_date,
            'closed_date': closed_date,
        }
        
        return claim
    
    @staticmethod
    def generate_fraudulent_claim(policy, policyholder, vehicle, index):
        """Generate a fraudulent claim with suspicious patterns"""
        
        # Start with a base legitimate claim
        claim = ClaimGenerator.generate_legitimate_claim(
            policy, policyholder, vehicle, index
        )
        
        # Apply fraud patterns
        fraud_indicators = []
        
        # Pattern 1: Amount inflation (30% probability)
        if random.random() < 0.3:
            multiplier = random.uniform(1.5, 2.5)
            claim['claimed_amount'] *= Decimal(str(multiplier))
            fraud_indicators.append('Inflated claim amount')
        
        # Pattern 2: Claim shortly after policy inception (20% probability)
        if random.random() < 0.2:
            policy_start = policy['start_date']
            days_after = random.randint(1, 15)
            claim['incident_date'] = datetime.combine(
                policy_start + timedelta(days=days_after),
                datetime.min.time().replace(hour=random.randint(0, 23))
            )
            claim['submitted_date'] = claim['incident_date'] + timedelta(hours=random.randint(1, 24))
            fraud_indicators.append('Claim filed shortly after policy inception')
        
        # Pattern 3: No police report for severe claim (25% probability)
        if claim['severity'] in ['MAJOR', 'TOTAL_LOSS'] and random.random() < 0.25:
            claim['police_report_filed'] = False
            claim['police_report_number'] = None
            fraud_indicators.append('No police report for severe incident')
        
        # Pattern 4: Suspicious witness pattern (15% probability)
        if random.random() < 0.15:
            claim['witnesses_present'] = True
            claim['number_of_witnesses'] = random.randint(2, 4)
            fraud_indicators.append('Suspicious number of witnesses')
        
        # Pattern 5: Vague incident description (20% probability)
        if random.random() < 0.2:
            vague_descriptions = [
                'Incident occurred, significant damage sustained',
                'Vehicle damaged in unclear circumstances',
                'Accident happened, details uncertain',
                'Damage discovered after unspecified incident',
                'Vehicle compromised, exact cause unknown'
            ]
            claim['incident_description'] = random.choice(vague_descriptions)
            fraud_indicators.append('Vague incident description')
        
        # Pattern 6: Claim amount close to policy coverage (15% probability)
        if random.random() < 0.15:
            coverage = policy['coverage_amount']
            claim['claimed_amount'] = coverage * Decimal(random.uniform(0.95, 1.0))
            fraud_indicators.append('Claim amount suspiciously close to coverage limit')
        
        # Pattern 7: Multiple claims history (will be checked in bulk generation)
        
        # Pattern 8: Claim for older vehicle with high amount (10% probability)
        vehicle_age = datetime.now().year - vehicle['year']
        if vehicle_age > 10 and claim['claimed_amount'] > vehicle['market_value'] and random.random() < 0.1:
            fraud_indicators.append('High claim amount for old vehicle')
        
        # Pattern 9: Theft without proper security measures (10% probability)
        if claim['claim_type'] == 'THEFT' and not vehicle['has_anti_theft'] and random.random() < 0.1:
            fraud_indicators.append('Theft claim without anti-theft device')
        
        # Pattern 10: Inconsistent injury claims (10% probability)
        if claim['claim_type'] == 'ACCIDENT' and random.random() < 0.1:
            claim['number_of_injuries'] = random.randint(3, 5)
            fraud_indicators.append('Unusually high number of injuries')
        
        # Calculate fraud score based on number of indicators
        base_fraud_score = 0.4
        indicator_boost = len(fraud_indicators) * 0.15
        claim['fraud_score'] = min(0.99, base_fraud_score + indicator_boost + random.uniform(-0.1, 0.1))
        
        # Mark as fraudulent if score is high
        claim['is_fraudulent'] = claim['fraud_score'] > 0.7
        claim['fraud_reason'] = '; '.join(fraud_indicators) if fraud_indicators else None
        
        # Fraudulent claims are more likely to be rejected or under review
        if claim['is_fraudulent']:
            claim['claim_status'] = ClaimGenerator.weighted_choice(
                ['UNDER_REVIEW', 'REJECTED', 'SUBMITTED'],
                [0.5, 0.3, 0.2]
            )
            if claim['claim_status'] == 'REJECTED':
                claim['approved_amount'] = Decimal('0.00')
                claim['paid_amount'] = Decimal('0.00')
                claim['reviewed_date'] = claim['submitted_date'] + timedelta(days=random.randint(15, 45))
                claim['closed_date'] = claim['reviewed_date']
        
        return claim
    
    @staticmethod
    def generate_batch(policyholders, vehicles, policies, fraud_percentage=0.15):
        """
        Generate claims for policies
        
        Args:
            policyholders: List of policyholder dictionaries
            vehicles: List of vehicle dictionaries
            policies: List of policy dictionaries
            fraud_percentage: Percentage of fraudulent claims (default 15%)
        """
        print(f"Generating claims with {fraud_percentage*100}% fraud rate...")
        
        # Create lookup dictionaries
        policyholder_dict = {ph['policy_holder_id']: ph for ph in policyholders}
        vehicle_dict = {v['vehicle_id']: v for v in vehicles}
        
        claims = []
        policyholder_claim_count = {}  # Track claims per policyholder
        
        # Only generate claims for active or expired policies
        eligible_policies = [
            p for p in policies 
            if p['status'] in ['ACTIVE', 'EXPIRED']
        ]
        
        print(f"  Eligible policies for claims: {len(eligible_policies)}")
        
        for i, policy in enumerate(eligible_policies):
            # Some policies have no claims
            if random.random() < 0.4:
                continue
            
            # Number of claims per policy (weighted)
            num_claims = ClaimGenerator.weighted_choice(
                [1, 2, 3, 4],
                [0.7, 0.2, 0.08, 0.02]
            )
            
            policyholder = policyholder_dict[policy['policyholder_id']]
            vehicle = vehicle_dict[policy['vehicle_id']]
            
            # Track policyholder claim count
            ph_id = policy['policyholder_id']
            if ph_id not in policyholder_claim_count:
                policyholder_claim_count[ph_id] = 0
            
            for c in range(num_claims):
                # Determine if this claim should be fraudulent
                is_fraud = random.random() < fraud_percentage
                
                # Increase fraud probability for policyholders with multiple claims
                if policyholder_claim_count[ph_id] >= 2:
                    is_fraud = is_fraud or (random.random() < 0.3)
                
                if is_fraud:
                    claim = ClaimGenerator.generate_fraudulent_claim(
                        policy, policyholder, vehicle, len(claims)
                    )
                else:
                    claim = ClaimGenerator.generate_legitimate_claim(
                        policy, policyholder, vehicle, len(claims)
                    )
                
                claims.append(claim)
                policyholder_claim_count[ph_id] += 1
            
            if (i + 1) % 100 == 0:
                print(f"  Processed {i + 1}/{len(eligible_policies)} policies, generated {len(claims)} claims")
        
        # Add fraud indicator for policyholders with excessive claims
        for claim in claims:
            ph_id = claim['policyholder_id']
            if policyholder_claim_count[ph_id] >= 3:
                if claim['fraud_reason']:
                    claim['fraud_reason'] += '; Multiple claims history'
                else:
                    claim['fraud_reason'] = 'Multiple claims history'
                claim['fraud_score'] = min(0.99, claim['fraud_score'] + 0.1)
                claim['is_fraudulent'] = claim['fraud_score'] > 0.7
        
        # Calculate statistics
        fraudulent_count = sum(1 for c in claims if c['is_fraudulent'])
        print(f"✓ Generated {len(claims)} total claims")
        print(f"  - Legitimate claims: {len(claims) - fraudulent_count}")
        print(f"  - Fraudulent claims: {fraudulent_count} ({fraudulent_count/len(claims)*100:.1f}%)")
        
        return claims