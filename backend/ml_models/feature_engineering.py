"""
Feature Engineering for ML Models
"""

import pandas as pd
import numpy as np
from datetime import datetime
from sklearn.preprocessing import StandardScaler, LabelEncoder
import joblib


class FeatureEngineer:
    """Feature engineering utilities for insurance data."""

    def __init__(self):
        self.label_encoders: dict = {}
        self.scaler = StandardScaler()

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _is_uuid_column(self, series: pd.Series) -> bool:
        """Return True if the column appears to contain UUID strings."""
        if len(series) == 0:
            return False
        sample = str(series.iloc[0])
        return len(sample) > 20 and '-' in sample

    def _map_uuids_to_int(self, *series_list) -> list:
        """Create {uuid: int} maps for each supplied Series and return them."""
        return [
            {uuid: idx for idx, uuid in enumerate(s.unique())}
            for s in series_list
        ]

    def _encode_categorical(self, series: pd.Series, column_name: str) -> np.ndarray:
        """Label-encode a categorical Series, handling unseen values gracefully."""
        if column_name not in self.label_encoders:
            le = LabelEncoder()
            self.label_encoders[column_name] = le
            return le.fit_transform(series.astype(str))

        le = self.label_encoders[column_name]
        series = series.astype(str)
        mask = series.isin(le.classes_)
        encoded = np.zeros(len(series), dtype=int)
        if mask.any():
            encoded[mask] = le.transform(series[mask])
        return encoded

    # ------------------------------------------------------------------
    # Fraud detection features
    # ------------------------------------------------------------------

    def engineer_fraud_detection_features(
        self,
        claims_df: pd.DataFrame,
        policyholders_df: pd.DataFrame,
        vehicles_df: pd.DataFrame,
        policies_df: pd.DataFrame,
    ) -> pd.DataFrame:
        """
        Engineer features for the fraud detection model.

        Dropped fields (no longer in Claim model):
            police_report_filed, witnesses_present, number_of_witnesses,
            number_of_injuries, third_party_involved
        Vehicle age source: `manufacture_year` (renamed from `year`)
        """
        print("Engineering fraud detection features...")

        claims_df       = claims_df.copy()
        policyholders_df = policyholders_df.copy()
        vehicles_df     = vehicles_df.copy()
        policies_df     = policies_df.copy()

        # ---- UUID / integer ID normalisation ----
        if 'id' in policyholders_df.columns and self._is_uuid_column(policyholders_df['id']):
            print("Detected UUID columns — creating integer mappings...")
            ph_map, pol_map, veh_map = self._map_uuids_to_int(
                policyholders_df['id'], policies_df['id'], vehicles_df['id']
            )

            claims_df['policyholder_id'] = claims_df['policyholder_id'].map(ph_map)
            claims_df['policy_id']       = claims_df['policy_id'].map(pol_map)
            claims_df['vehicle_id']      = claims_df['vehicle_id'].map(veh_map)

            policyholders_df['id']          = policyholders_df['id'].map(ph_map)
            policies_df['id']               = policies_df['id'].map(pol_map)
            policies_df['policyholder_id']  = policies_df['policyholder_id'].map(ph_map)
            policies_df['vehicle_id']       = policies_df['vehicle_id'].map(veh_map)
            vehicles_df['id']               = vehicles_df['id'].map(veh_map)
            print("✓ UUID mappings created")
        else:
            for col, frame in [
                ('policyholder_id', claims_df),
                ('policy_id',       claims_df),
                ('vehicle_id',      claims_df),
                ('id',              policyholders_df),
            ]:
                if col in frame.columns:
                    frame[col] = frame[col].astype('int64')

        # ---- Merge ----
        df = claims_df.copy()
        df = df.merge(policies_df,      left_on='policy_id',      right_on='id', how='left', suffixes=('', '_policy'))
        df = df.merge(policyholders_df, left_on='policyholder_id', right_on='id', how='left', suffixes=('', '_policyholder'))
        df = df.merge(vehicles_df,      left_on='vehicle_id',      right_on='id', how='left', suffixes=('', '_vehicle'))

        # ---- Claim features ----
        df['claimed_amount']   = pd.to_numeric(df['claimed_amount'], errors='coerce')
        df['severity_encoded'] = self._encode_categorical(df['severity'],   'severity')
        df['claim_type_encoded'] = self._encode_categorical(df['claim_type'], 'claim_type')

        # ---- Time-based features ----
        for col in ('incident_date', 'start_date', 'submitted_date'):
            df[col] = pd.to_datetime(df[col]).dt.tz_localize(None)

        df['days_since_policy_start'] = (
            (df['incident_date'] - df['start_date']).dt.days
        ).clip(lower=0)

        df['submission_delay_hours'] = (
            (df['submitted_date'] - df['incident_date']).dt.total_seconds() / 3600
        ).clip(lower=0)

        df['incident_hour']        = df['incident_date'].dt.hour
        df['incident_day_of_week'] = df['incident_date'].dt.dayofweek
        df['incident_month']       = df['incident_date'].dt.month

        # ---- Claim-to-coverage ratio ----
        df['coverage_amount'] = pd.to_numeric(df['coverage_amount'], errors='coerce')
        df['claim_to_coverage_ratio'] = (
            df['claimed_amount'] / df['coverage_amount'].replace(0, np.nan)
        ).fillna(0).clip(upper=2.0)

        # ---- Vehicle features (uses manufacture_year) ----
        df['manufacture_year'] = pd.to_numeric(df['manufacture_year'], errors='coerce')
        current_year = datetime.now().year
        df['vehicle_age'] = (current_year - df['manufacture_year']).clip(lower=0, upper=50)

        df['vehicle_value']  = pd.to_numeric(df['market_value'], errors='coerce').fillna(0)
        df['has_anti_theft'] = df['has_anti_theft'].fillna(False).astype(int)
        df['is_modified']    = df['is_modified'].fillna(False).astype(int)

        # ---- Incident scope (fields still present in Claim model) ----
        df['number_of_vehicles_involved'] = (
            pd.to_numeric(df['number_of_vehicles_involved'], errors='coerce').fillna(1)
        )

        # ---- Policyholder features ----
        df['date_of_birth'] = pd.to_datetime(df['date_of_birth']).dt.tz_localize(None)
        df['policyholder_age'] = (
            (datetime.now() - df['date_of_birth']).dt.days / 365.25
        ).clip(lower=18, upper=100)

        df['credit_score']       = pd.to_numeric(df['credit_score'],       errors='coerce').fillna(650)
        df['years_with_company'] = pd.to_numeric(df['years_with_company'], errors='coerce').fillna(0)

        # ---- Policyholder claim history ----
        claim_counts = df.groupby('policyholder_id').size().to_dict()
        df['policyholder_claim_count'] = df['policyholder_id'].map(claim_counts).fillna(1)

        # ---- Final NaN fill ----
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        df[numeric_cols] = df[numeric_cols].fillna(0)

        print(f"✓ Engineered {len(df)} samples with {len(df.columns)} columns")
        return df

    # ------------------------------------------------------------------
    # Pricing features
    # ------------------------------------------------------------------

    def engineer_pricing_features(
        self,
        policyholders_df: pd.DataFrame,
        vehicles_df: pd.DataFrame,
        policies_df: pd.DataFrame,
    ) -> pd.DataFrame:
        """
        Engineer features for the dynamic pricing model.
        Vehicle age source: `manufacture_year`
        """
        print("Engineering pricing features...")

        policyholders_df = policyholders_df.copy()
        vehicles_df      = vehicles_df.copy()
        policies_df      = policies_df.copy()

        # ---- UUID / integer ID normalisation ----
        if 'id' in policyholders_df.columns and self._is_uuid_column(policyholders_df['id']):
            ph_map, veh_map, pol_map = self._map_uuids_to_int(
                policyholders_df['id'], vehicles_df['id'], policies_df['id']
            )
            policyholders_df['id']         = policyholders_df['id'].map(ph_map)
            vehicles_df['id']              = vehicles_df['id'].map(veh_map)
            policies_df['id']              = policies_df['id'].map(pol_map)
            policies_df['policyholder_id'] = policies_df['policyholder_id'].map(ph_map)
            policies_df['vehicle_id']      = policies_df['vehicle_id'].map(veh_map)

        # ---- Merge ----
        df = policies_df.copy()
        df = df.merge(policyholders_df, left_on='policyholder_id', right_on='id', how='left', suffixes=('', '_policyholder'))
        df = df.merge(vehicles_df,      left_on='vehicle_id',      right_on='id', how='left', suffixes=('', '_vehicle'))

        # ---- Driver features ----
        df['date_of_birth'] = pd.to_datetime(df['date_of_birth']).dt.tz_localize(None)
        df['age'] = (
            (datetime.now() - df['date_of_birth']).dt.days / 365.25
        ).clip(lower=18, upper=100)

        df['gender_encoded']         = self._encode_categorical(df['gender'],         'gender')
        df['marital_status_encoded'] = self._encode_categorical(df['marital_status'], 'marital_status')
        df['occupation_encoded']     = self._encode_categorical(df['occupation'],     'occupation')
        df['state_encoded']          = self._encode_categorical(df['state'],          'state')

        df['credit_score']       = pd.to_numeric(df['credit_score'],       errors='coerce').fillna(650)
        df['years_with_company'] = pd.to_numeric(df['years_with_company'], errors='coerce').fillna(0)

        # ---- Vehicle features (uses manufacture_year) ----
        df['manufacture_year'] = pd.to_numeric(df['manufacture_year'], errors='coerce')
        current_year = datetime.now().year
        df['vehicle_age'] = (current_year - df['manufacture_year']).clip(lower=0, upper=50)

        df['vehicle_value']      = pd.to_numeric(df['market_value'], errors='coerce').fillna(0)
        df['vehicle_type_encoded'] = self._encode_categorical(df['vehicle_type'], 'vehicle_type')
        df['fuel_type_encoded']    = self._encode_categorical(df['fuel_type'],    'fuel_type')

        df['has_anti_theft']   = df['has_anti_theft'].fillna(False).astype(int)
        df['has_airbags']      = df['has_airbags'].fillna(False).astype(int)
        df['has_abs']          = df['has_abs'].fillna(False).astype(int)
        df['is_modified']      = df['is_modified'].fillna(False).astype(int)
        df['odometer_reading'] = pd.to_numeric(df['odometer_reading'], errors='coerce').fillna(0)

        # ---- Policy features ----
        df['policy_type_encoded']    = self._encode_categorical(df['policy_type'],    'policy_type')
        df['coverage_level_encoded'] = self._encode_categorical(df['coverage_level'], 'coverage_level')
        df['coverage_amount']        = pd.to_numeric(df['coverage_amount'], errors='coerce').fillna(0)
        df['deductible']             = pd.to_numeric(df['deductible'],      errors='coerce').fillna(0)

        # ---- Final NaN fill ----
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        df[numeric_cols] = df[numeric_cols].fillna(0)

        print(f"✓ Engineered {len(df)} samples with {len(df.columns)} columns")
        return df

    # ------------------------------------------------------------------
    # Claims estimation features
    # ------------------------------------------------------------------

    def engineer_claims_estimation_features(
        self,
        claims_df: pd.DataFrame,
        vehicles_df: pd.DataFrame,
        policies_df: pd.DataFrame,
    ) -> pd.DataFrame:
        """
        Engineer features for the claims cost estimation model.
        """
        print("Engineering claims estimation features...")

        claims_df   = claims_df.copy()
        vehicles_df = vehicles_df.copy()
        policies_df = policies_df.copy()

        # ---- UUID / integer ID normalisation ----
        if 'id' in policies_df.columns and self._is_uuid_column(policies_df['id']):
            pol_map, veh_map = self._map_uuids_to_int(policies_df['id'], vehicles_df['id'])
            claims_df['policy_id']    = claims_df['policy_id'].map(pol_map)
            claims_df['vehicle_id']   = claims_df['vehicle_id'].map(veh_map)
            policies_df['id']         = policies_df['id'].map(pol_map)
            policies_df['vehicle_id'] = policies_df['vehicle_id'].map(veh_map)
            vehicles_df['id']         = vehicles_df['id'].map(veh_map)

        # ---- Merge ----
        df = claims_df.copy()
        df = df.merge(policies_df, left_on='policy_id',  right_on='id', how='left', suffixes=('', '_policy'))
        df = df.merge(vehicles_df, left_on='vehicle_id', right_on='id', how='left', suffixes=('', '_vehicle'))

        # ---- Claim features ----
        df['claim_type_encoded'] = self._encode_categorical(df['claim_type'], 'claim_type')
        df['severity_encoded']   = self._encode_categorical(df['severity'],   'severity')

        # ---- Vehicle features (uses manufacture_year) ----
        df['manufacture_year'] = pd.to_numeric(df['manufacture_year'], errors='coerce')
        current_year = datetime.now().year
        df['vehicle_age'] = (current_year - df['manufacture_year']).clip(lower=0, upper=50)

        df['vehicle_value']        = pd.to_numeric(df['market_value'], errors='coerce').fillna(0)
        df['vehicle_type_encoded'] = self._encode_categorical(df['vehicle_type'], 'vehicle_type')

        # ---- Incident scope (fields still present in Claim model) ----
        df['number_of_vehicles_involved'] = (
            pd.to_numeric(df['number_of_vehicles_involved'], errors='coerce').fillna(1)
        )

        # ---- Policy financials ----
        df['coverage_amount']     = pd.to_numeric(df['coverage_amount'], errors='coerce').fillna(0)
        df['deductible']          = pd.to_numeric(df['deductible'],      errors='coerce').fillna(0)
        df['policy_type_encoded'] = self._encode_categorical(df['policy_type'], 'policy_type')

        # ---- Final NaN fill ----
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        df[numeric_cols] = df[numeric_cols].fillna(0)

        print(f"✓ Engineered {len(df)} samples with {len(df.columns)} columns")
        return df

    # ------------------------------------------------------------------
    # Scaling helpers
    # ------------------------------------------------------------------

    def scale_features(self, X: pd.DataFrame, fit: bool = True) -> np.ndarray:
        """Scale features using StandardScaler."""
        if fit:
            return self.scaler.fit_transform(X)
        return self.scaler.transform(X)

    # ------------------------------------------------------------------
    # Persistence helpers
    # ------------------------------------------------------------------

    def save_encoders(self, filepath: str) -> None:
        joblib.dump(self.label_encoders, filepath)
        print(f"✓ Saved encoders to {filepath}")

    def load_encoders(self, filepath: str) -> None:
        self.label_encoders = joblib.load(filepath)
        print(f"✓ Loaded encoders from {filepath}")

    def save_scaler(self, filepath: str) -> None:
        joblib.dump(self.scaler, filepath)
        print(f"✓ Saved scaler to {filepath}")

    def load_scaler(self, filepath: str) -> None:
        self.scaler = joblib.load(filepath)
        print(f"✓ Loaded scaler from {filepath}")