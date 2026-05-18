"""
Generate synthetic insurance claims data with fraud patterns
REFACTORED VERSION
- Completely removed: police_report_filed, police_report_number,
  witnesses_present, number_of_witnesses, number_of_injuries,
  third_party_involved (all dropped from Claim model)
- Added: payment_method, incident_evidence
- claimed_amount is severity-based (% of vehicle value), capped at coverage_amount
- Fraudulent patterns are purely financial / timing anomalies
"""

import random
from datetime import datetime, timedelta
from decimal import Decimal
from faker import Faker
from .base_generator import DataGenerator, InsuranceDataConfig

fake = Faker()


class ClaimGenerator(DataGenerator):
    """Generate realistic insurance claims with fraud detection features"""

    CLAIM_TYPES    = ['ACCIDENT', 'THEFT', 'VANDALISM', 'NATURAL_DISASTER', 'FIRE', 'OTHER']
    CLAIM_STATUSES = ['SUBMITTED', 'UNDER_REVIEW', 'APPROVED', 'REJECTED', 'PAID', 'CLOSED']
    SEVERITIES     = ['MINOR', 'MODERATE', 'MAJOR', 'TOTAL_LOSS']
    PAYMENT_METHODS = ['SWIPE', 'ECOCASH', 'CASH', 'BANK_TRANSFER']

    # Severity expressed as a fraction of vehicle market_value
    # claimed_amount = vehicle_value × random(low, high), capped at coverage_amount
    SEVERITY_VALUE_FRACTIONS = {
        'MINOR':      (0.05, 0.15),
        'MODERATE':   (0.15, 0.35),
        'MAJOR':      (0.35, 0.70),
        'TOTAL_LOSS': (0.80, 1.00),
    }

    # Incident descriptions by claim type
    INCIDENT_DESCRIPTIONS = {
        'ACCIDENT': [
            'Rear-ended at traffic light during rush hour on Samora Machel Avenue',
            'Side collision at intersection — other driver ran red light in Harare CBD',
            'Hit while parked at Sam Levy Shopping Centre',
            'Multi-vehicle collision on A1 highway due to sudden braking',
            'Backed into another vehicle at Borrowdale Racecourse parking',
            'T-bone collision at four-way stop near Chitungwiza',
            'Single vehicle accident — lost control on wet road near Mutare',
            'Hit and run incident on Simon Mazorodze Road, other driver fled',
            'Collision in Westgate shopping mall parking area while reversing',
            'Side-swipe on Bulawayo Road near Gweru tollgate',
        ],
        'THEFT': [
            'Vehicle stolen from residential driveway in Borrowdale overnight',
            'Car broken into at Avondale flea market, laptop and handbag stolen',
            'Catalytic converter stolen while parked near First Street Mall',
            'Vehicle stolen from Malls car park, later recovered without engine',
            'Wheels and rims stolen while parked on Jason Moyo Avenue overnight',
            'Vehicle stolen and recovered badly damaged near Highfield',
            'Break-in at office park, sound system and GPS unit stolen',
            'Vehicle stolen from Bulawayo Show Grounds during public event',
            'Theft of tools from bakkie load bed at construction site',
            'Attempted carjacking in Eastlea, significant ignition damage',
        ],
        'VANDALISM': [
            'Vehicle spray-painted with graffiti in Mbare overnight',
            'Windscreen and side windows smashed, nothing stolen',
            'Tyres slashed in Avenues apartment block parking',
            'Deep keymarks along both doors while parked in CBD',
            'Side mirrors broken off in Hatfield residential area',
            'Paint scorched with chemical substance in Southerton industrial',
            'Interior fabric slashed and dashboard cracked',
            'All four tyres deflated and rims scratched',
            'Headlights and taillights smashed in parking garage',
            'Aerial snapped and roof aerial mount vandalised',
        ],
        'NATURAL_DISASTER': [
            'Severe hail damage to bonnet, roof and boot during Harare storms',
            'Msasa tree fell on vehicle during Cyclone-linked winds in Mutare',
            'Flash flood submerged vehicle in Budiriro low-lying area',
            'Flooding swept vehicle into storm drain along Marimba Road',
            'Tornado debris caused significant body damage in Chipinge',
            'Large branch fell through windscreen during overnight storm',
            'Lightning strike triggered electrical fire in dashboard',
            'Erosion collapsed parking bay, vehicle dropped into ditch',
        ],
        'FIRE': [
            'Engine fire while driving on Harare-Beitbridge highway',
            'Electrical fire originated in dashboard near fuse box',
            'Vehicle caught fire after rear-end collision',
            'Catalytic converter overheated and ignited dry grass under vehicle',
            'Fuel line rupture caused fire after pothole impact',
            'Battery malfunction overnight — vehicle gutted by morning',
            'Fire from adjacent structure spread to vehicle in industrial area',
            'Exhaust system fault caused slow-burning fire under chassis',
        ],
        'OTHER': [
            'Collision with cattle on A5 rural road near Gwanda',
            'Struck by falling rock from kopje near Marondera',
            'Front suspension damaged by large pothole on Julius Nyerere Way',
            'Shopping trolley rolled into vehicle at Pick n Pay car park',
            'Collision with cyclist at roundabout near Airport Road',
            'Struck by flying debris from mine truck on Hwange road',
            'Rock thrown at windscreen from overpass near Chitungwiza',
            'Collision with donkey cart on rural road near Chiredzi',
        ],
    }

    # Vague fraudulent descriptions
    VAGUE_DESCRIPTIONS = [
        'Vehicle sustained damage under unclear circumstances',
        'Incident occurred — significant damage discovered afterwards',
        'Accident happened, full details still being established',
        'Damage found on vehicle, cause uncertain at this time',
        'Vehicle compromised — exact sequence of events unknown',
        'Damage noted upon return to vehicle, cause unconfirmed',
    ]

    # -----------------------------------------------------------------------
    # Internal: calculate claimed_amount from severity and vehicle value
    # -----------------------------------------------------------------------
    @staticmethod
    def _calculate_claimed_amount(severity: str,
                                   vehicle_value: float,
                                   coverage_amount: float) -> Decimal:
        """
        Derive a realistic claimed_amount from severity and vehicle market value.
        Always capped at the policy coverage_amount.
        """
        low, high = ClaimGenerator.SEVERITY_VALUE_FRACTIONS[severity]
        raw       = vehicle_value * random.uniform(low, high)
        capped    = min(raw, coverage_amount)
        return Decimal(str(round(capped, 2)))

    # -----------------------------------------------------------------------
    # Legitimate claim
    # -----------------------------------------------------------------------
    @staticmethod
    def generate_legitimate_claim(policy: dict, policyholder: dict,
                                   vehicle: dict, index: int) -> dict:
        """Generate a legitimate (non-fraudulent) claim"""

        claim_type = ClaimGenerator.weighted_choice(
            ClaimGenerator.CLAIM_TYPES,
            [0.60, 0.10, 0.10, 0.10, 0.05, 0.05]
        )

        severity = ClaimGenerator.weighted_choice(
            ClaimGenerator.SEVERITIES,
            [0.50, 0.30, 0.15, 0.05]
        )

        vehicle_value   = float(vehicle['market_value'])
        coverage_amount = float(policy['coverage_amount'])

        claimed_amount = ClaimGenerator._calculate_claimed_amount(
            severity, vehicle_value, coverage_amount
        )

        # Incident date — within policy period, at least 1 day after start
        policy_start = policy['start_date']
        policy_end   = min(policy['end_date'], datetime.now().date())

        days_buffer     = min(30, max(1, (policy_end - policy_start).days - 1))
        incident_start  = datetime.combine(
            policy_start + timedelta(days=days_buffer), datetime.min.time()
        )
        incident_end    = datetime.combine(policy_end, datetime.max.time())

        if incident_start >= incident_end:
            incident_start = datetime.combine(
                policy_start + timedelta(days=1), datetime.min.time()
            )

        incident_date = ClaimGenerator.random_datetime_between(
            incident_start, incident_end
        )

        # Location
        location_type     = random.choice(InsuranceDataConfig.INCIDENT_LOCATIONS)
        incident_location = f"{location_type}, {policyholder['city']}, {policyholder['state']}"

        # Description
        incident_description = random.choice(
            ClaimGenerator.INCIDENT_DESCRIPTIONS[claim_type]
        )

        # Number of vehicles involved (only meaningful for accidents)
        if claim_type == 'ACCIDENT':
            number_of_vehicles_involved = ClaimGenerator.weighted_choice(
                [1, 2, 3, 4], [0.30, 0.50, 0.15, 0.05]
            )
        else:
            number_of_vehicles_involved = 1

        # Payment method
        payment_method = random.choice(ClaimGenerator.PAYMENT_METHODS)

        # Claim status based on how long ago the incident was
        days_since = (datetime.now().date() - incident_date.date()).days
        submitted_date = incident_date + timedelta(hours=random.randint(1, 72))

        if days_since < 7:
            claim_status   = 'SUBMITTED'
            approved_amount = Decimal('0.00')
            paid_amount    = Decimal('0.00')
            reviewed_date  = None
            closed_date    = None
        elif days_since < 30:
            claim_status = ClaimGenerator.weighted_choice(
                ['SUBMITTED', 'UNDER_REVIEW', 'APPROVED'], [0.20, 0.50, 0.30]
            )
            if claim_status == 'APPROVED':
                approved_amount = claimed_amount * Decimal(
                    str(round(random.uniform(0.85, 1.00), 4))
                )
                paid_amount    = Decimal('0.00')
                reviewed_date  = submitted_date + timedelta(days=random.randint(5, 15))
                closed_date    = None
            else:
                approved_amount = Decimal('0.00')
                paid_amount    = Decimal('0.00')
                reviewed_date  = None
                closed_date    = None
        else:
            claim_status = ClaimGenerator.weighted_choice(
                ['APPROVED', 'PAID', 'CLOSED', 'REJECTED'], [0.10, 0.50, 0.35, 0.05]
            )
            if claim_status in ('APPROVED', 'PAID', 'CLOSED'):
                approved_amount = claimed_amount * Decimal(
                    str(round(random.uniform(0.85, 1.00), 4))
                )
                paid_amount    = (
                    approved_amount if claim_status in ('PAID', 'CLOSED') else Decimal('0.00')
                )
                reviewed_date  = submitted_date + timedelta(days=random.randint(5, 20))
                closed_date    = (
                    reviewed_date + timedelta(days=random.randint(5, 15))
                    if claim_status == 'CLOSED' else None
                )
            else:
                approved_amount = Decimal('0.00')
                paid_amount    = Decimal('0.00')
                reviewed_date  = submitted_date + timedelta(days=random.randint(10, 30))
                closed_date    = reviewed_date

        claim = {
            'claim_number':               ClaimGenerator.generate_id('CLM', 12),
            'policy_number':              policy['policy_number'],
            'policyholder_id':            policyholder['policy_holder_id'],
            'vehicle_vin':                vehicle['vin'],
            'claim_type':                 claim_type,
            'claim_status':               claim_status,
            'severity':                   severity,
            'incident_date':              incident_date,
            'incident_location':          incident_location,
            'incident_description':       incident_description,
            # Dropped fields not included:
            #   police_report_filed, police_report_number,
            #   witnesses_present, number_of_witnesses,
            #   number_of_injuries, third_party_involved
            'number_of_vehicles_involved': number_of_vehicles_involved,
            'claimed_amount':             claimed_amount,
            'approved_amount':            approved_amount,
            'paid_amount':                paid_amount,
            'payment_method':             payment_method,
            'incident_evidence':          '',   # empty — no file uploaded yet
            'fraud_score':                round(random.uniform(0.00, 0.30), 4),
            'is_fraudulent':              False,
            'fraud_reason':               None,
            'submitted_date':             submitted_date,
            'reviewed_date':              reviewed_date,
            'closed_date':                closed_date,
        }

        return claim

    # -----------------------------------------------------------------------
    # Fraudulent claim — purely financial / timing anomalies
    # -----------------------------------------------------------------------
    @staticmethod
    def generate_fraudulent_claim(policy: dict, policyholder: dict,
                                   vehicle: dict, index: int) -> dict:
        """Generate a fraudulent claim using financial and timing anomaly patterns"""

        claim = ClaimGenerator.generate_legitimate_claim(
            policy, policyholder, vehicle, index
        )

        fraud_indicators = []
        vehicle_value    = float(vehicle['market_value'])
        coverage_amount  = float(policy['coverage_amount'])

        # ------------------------------------------------------------------
        # Pattern A — Coverage-limit gaming (30%)
        # Claim is suspiciously close to the coverage ceiling.
        # ------------------------------------------------------------------
        if random.random() < 0.30:
            ratio = random.uniform(0.93, 0.99)
            claim['claimed_amount'] = Decimal(
                str(round(coverage_amount * ratio, 2))
            )
            fraud_indicators.append(
                'Claim amount suspiciously close to coverage limit'
            )

        # ------------------------------------------------------------------
        # Pattern B — Amount inflation (28%)
        # Inflate beyond what severity/vehicle_value would justify.
        # ------------------------------------------------------------------
        if random.random() < 0.28:
            multiplier = random.uniform(1.5, 2.5)
            inflated   = float(claim['claimed_amount']) * multiplier
            # Still cap at coverage_amount to pass basic validation
            claim['claimed_amount'] = Decimal(
                str(round(min(inflated, coverage_amount), 2))
            )
            fraud_indicators.append(
                'Claimed amount grossly inflated beyond vehicle proportion'
            )

        # ------------------------------------------------------------------
        # Pattern C — Suspicious timing (22%)
        # Claim filed within the first 14 days of policy inception.
        # ------------------------------------------------------------------
        if random.random() < 0.22:
            policy_start = policy['start_date']
            days_after   = random.randint(1, 14)
            fraudulent_incident = datetime.combine(
                policy_start + timedelta(days=days_after),
                datetime.min.time().replace(hour=random.randint(0, 23))
            )
            claim['incident_date']  = fraudulent_incident
            claim['submitted_date'] = fraudulent_incident + timedelta(
                hours=random.randint(1, 24)
            )
            fraud_indicators.append(
                'Claim filed within first 14 days of policy inception'
            )

        # ------------------------------------------------------------------
        # Pattern D — Value mismatch (18%)
        # High claimed_amount on a heavily depreciated vehicle.
        # ------------------------------------------------------------------
        vehicle_age = datetime.now().year - vehicle['manufacture_year']
        if vehicle_age >= 8 and random.random() < 0.18:
            # Claim exceeds vehicle market value — red flag
            excess_amount = vehicle_value * random.uniform(1.10, 1.40)
            claim['claimed_amount'] = Decimal(
                str(round(min(excess_amount, coverage_amount), 2))
            )
            fraud_indicators.append(
                f'Claim exceeds market value for {vehicle_age}-year-old vehicle'
            )

        # ------------------------------------------------------------------
        # Pattern E — Cross-border incident (18%)
        # Harder to investigate or verify.
        # ------------------------------------------------------------------
        if random.random() < 0.18:
            border_city = random.choice(
                ['Beitbridge', 'Victoria Falls', 'Mutare', 'Chirundu']
            )
            claim['incident_location'] = (
                f"Border Post Area, {border_city}, "
                f"{policyholder['state']}"
            )
            fraud_indicators.append(
                'Incident at border crossing — difficult to verify independently'
            )

        # ------------------------------------------------------------------
        # Pattern F — Vague description (20%)
        # ------------------------------------------------------------------
        if random.random() < 0.20:
            claim['incident_description'] = random.choice(
                ClaimGenerator.VAGUE_DESCRIPTIONS
            )
            fraud_indicators.append('Non-specific incident description')

        # ------------------------------------------------------------------
        # Pattern G — Staged incident in high-risk area with max claim (12%)
        # ------------------------------------------------------------------
        if random.random() < 0.12:
            high_risk = random.choice(
                ['Township Road', 'Industrial Area', 'Commuter Terminus']
            )
            claim['incident_location'] = (
                f"{high_risk}, {policyholder['city']}, {policyholder['state']}"
            )
            # Push claim to near the coverage ceiling
            claim['claimed_amount'] = Decimal(
                str(round(coverage_amount * random.uniform(0.88, 0.99), 2))
            )
            fraud_indicators.append(
                'Staged incident in high-risk location with near-maximum claim'
            )

        # ------------------------------------------------------------------
        # Pattern H — Parts theft inflation (10%)
        # ------------------------------------------------------------------
        if claim['claim_type'] == 'THEFT' and random.random() < 0.10:
            part = random.choice(
                ['Engine', 'Gearbox', 'Wheels', 'Catalytic Converter']
            )
            claim['incident_description'] = (
                f'{part} stolen — replacement cost claimed at premium import price'
            )
            claim['claimed_amount'] = Decimal(
                str(round(min(vehicle_value * random.uniform(0.60, 0.90),
                              coverage_amount), 2))
            )
            fraud_indicators.append(
                f'Parts theft ({part}) with inflated import-price replacement claim'
            )

        # ------------------------------------------------------------------
        # Compute final fraud score
        # ------------------------------------------------------------------
        base_fraud_score    = 0.40
        indicator_boost     = len(fraud_indicators) * 0.12
        claim['fraud_score'] = round(
            min(0.99, base_fraud_score + indicator_boost + random.uniform(-0.05, 0.10)),
            4
        )
        claim['is_fraudulent'] = claim['fraud_score'] > 0.70
        claim['fraud_reason']  = '; '.join(fraud_indicators) if fraud_indicators else None

        # Fraudulent claims skew toward under-review / rejected
        if claim['is_fraudulent']:
            claim['claim_status'] = ClaimGenerator.weighted_choice(
                ['UNDER_REVIEW', 'REJECTED', 'SUBMITTED'], [0.50, 0.30, 0.20]
            )
            if claim['claim_status'] == 'REJECTED':
                claim['approved_amount'] = Decimal('0.00')
                claim['paid_amount']     = Decimal('0.00')
                claim['reviewed_date']   = (
                    claim['submitted_date'] + timedelta(days=random.randint(15, 45))
                )
                claim['closed_date'] = claim['reviewed_date']

        return claim

    # -----------------------------------------------------------------------
    # Batch generation
    # -----------------------------------------------------------------------
    @staticmethod
    def generate_batch(policyholders: list, vehicles: list,
                        policies: list, fraud_percentage: float = 0.15) -> list:
        """
        Generate claims for all eligible policies.

        Args:
            policyholders:     List of policyholder dicts
            vehicles:          List of vehicle dicts
            policies:          List of policy dicts
            fraud_percentage:  Target fraud rate (default 15%)
        """
        print(f"Generating claims with {fraud_percentage * 100:.0f}% fraud rate...")

        policyholder_dict = {ph['policy_holder_id']: ph for ph in policyholders}
        # Keyed by VIN (vehicle_id removed from schema)
        vehicle_dict      = {v['vin']: v for v in vehicles}

        claims                    = []
        policyholder_claim_count  = {}

        eligible_policies = [
            p for p in policies if p['status'] in ('ACTIVE', 'EXPIRED')
        ]
        print(f"  Eligible policies for claims: {len(eligible_policies)}")

        for i, policy in enumerate(eligible_policies):
            # ~40% of policies have no claims at all
            if random.random() < 0.40:
                continue

            num_claims = ClaimGenerator.weighted_choice(
                [1, 2, 3, 4], [0.70, 0.20, 0.08, 0.02]
            )

            policyholder = policyholder_dict[policy['policyholder_id']]
            vehicle      = vehicle_dict[policy['vehicle_vin']]   # lookup by VIN
            ph_id        = policy['policyholder_id']

            policyholder_claim_count.setdefault(ph_id, 0)

            for _ in range(num_claims):
                # Base fraud probability; elevated for repeat claimants
                is_fraud = random.random() < fraud_percentage
                if policyholder_claim_count[ph_id] >= 2:
                    is_fraud = is_fraud or random.random() < 0.30

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
                print(
                    f"  Processed {i + 1}/{len(eligible_policies)} policies, "
                    f"generated {len(claims)} claims"
                )

        # Boost fraud score for policyholders with excessive claim history
        for claim in claims:
            ph_id = claim['policyholder_id']
            if policyholder_claim_count.get(ph_id, 0) >= 3:
                extra_reason = 'Multiple claims history'
                claim['fraud_reason'] = (
                    f"{claim['fraud_reason']}; {extra_reason}"
                    if claim['fraud_reason'] else extra_reason
                )
                claim['fraud_score']   = min(0.99, claim['fraud_score'] + 0.10)
                claim['is_fraudulent'] = claim['fraud_score'] > 0.70

        fraudulent_count = sum(1 for c in claims if c['is_fraudulent'])
        print(f"✓ Generated {len(claims)} total claims")
        print(f"  - Legitimate : {len(claims) - fraudulent_count}")
        print(
            f"  - Fraudulent : {fraudulent_count} "
            f"({fraudulent_count / max(len(claims), 1) * 100:.1f}%)"
        )

        return claims