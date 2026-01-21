"""
Feature Engineering for ML Models
"""

import pandas as pd
import numpy as np
from datetime import datetime
from sklearn.preprocessing import StandardScaler, LabelEncoder
import joblib


class FeatureEngineer:
    """Feature engineering utilities for insurance data"""
    
    def __init__(self):
        self.label_encoders = {}
        self.scaler = StandardScaler()
    
    def _is_uuid_column(self, series):
        """Check if a column contains UUIDs"""
        if len(series) == 0:
            return False
        sample = str(series.iloc[0])
        # UUID format: 8-4-4-4-12 characters (36 total with hyphens)
        return len(sample) > 20 and '-' in sample
    
    def engineer_fraud_detection_features(self, claims_df, policyholders_df, vehicles_df, policies_df):
        """
        Engineer features for fraud detection model
        
        Args:
            claims_df: DataFrame with claims data
            policyholders_df: DataFrame with policyholder data
            vehicles_df: DataFrame with vehicle data
            policies_df: DataFrame with policy data
        
        Returns:
            DataFrame with engineered features
        """
        print("Engineering fraud detection features...")
        
        # Make copies to avoid modifying originals
        claims_df = claims_df.copy()
        policyholders_df = policyholders_df.copy()
        vehicles_df = vehicles_df.copy()
        policies_df = policies_df.copy()
        
        # Handle UUID vs integer IDs
        if 'id' in policyholders_df.columns and self._is_uuid_column(policyholders_df['id']):
            print("Detected UUID columns - creating integer mappings...")
            
            # Create integer mappings for UUIDs
            policyholder_id_map = {uuid: idx for idx, uuid in enumerate(policyholders_df['id'].unique())}
            policy_id_map = {uuid: idx for idx, uuid in enumerate(policies_df['id'].unique())}
            vehicle_id_map = {uuid: idx for idx, uuid in enumerate(vehicles_df['id'].unique())}
            
            # Convert UUIDs to integers using mapping
            claims_df['policyholder_id'] = claims_df['policyholder_id'].map(policyholder_id_map)
            claims_df['policy_id'] = claims_df['policy_id'].map(policy_id_map)
            claims_df['vehicle_id'] = claims_df['vehicle_id'].map(vehicle_id_map)
            
            policyholders_df['id'] = policyholders_df['id'].map(policyholder_id_map)
            policies_df['id'] = policies_df['id'].map(policy_id_map)
            policies_df['policyholder_id'] = policies_df['policyholder_id'].map(policyholder_id_map)
            policies_df['vehicle_id'] = policies_df['vehicle_id'].map(vehicle_id_map)
            vehicles_df['id'] = vehicles_df['id'].map(vehicle_id_map)
            
            print("✓ UUID mappings created")
        else:
            # Already integers (from API synthetic data), ensure int64 type
            if 'policyholder_id' in claims_df.columns:
                claims_df['policyholder_id'] = claims_df['policyholder_id'].astype('int64')
            if 'id' in policyholders_df.columns:
                policyholders_df['id'] = policyholders_df['id'].astype('int64')
            if 'policy_id' in claims_df.columns:
                claims_df['policy_id'] = claims_df['policy_id'].astype('int64')
            if 'vehicle_id' in claims_df.columns:
                claims_df['vehicle_id'] = claims_df['vehicle_id'].astype('int64')
        
        # Merge all data
        df = claims_df.copy()
        
        # Merge policies
        df = df.merge(
            policies_df, 
            left_on='policy_id', 
            right_on='id', 
            how='left', 
            suffixes=('', '_policy')
        )
        
        # Merge policyholders using 'id' column
        df = df.merge(
            policyholders_df, 
            left_on='policyholder_id',
            right_on='id',
            how='left',
            suffixes=('', '_policyholder')
        )
        
        # Merge vehicles
        df = df.merge(
            vehicles_df, 
            left_on='vehicle_id', 
            right_on='id', 
            how='left', 
            suffixes=('', '_vehicle')
        )
        
        # Claim features
        df['claimed_amount'] = pd.to_numeric(df['claimed_amount'], errors='coerce')
        df['severity_encoded'] = self._encode_categorical(df['severity'], 'severity')
        df['claim_type_encoded'] = self._encode_categorical(df['claim_type'], 'claim_type')
        
        # Time-based features
        df['incident_date'] = pd.to_datetime(df['incident_date']).dt.tz_localize(None)
        df['start_date'] = pd.to_datetime(df['start_date']).dt.tz_localize(None)
        df['submitted_date'] = pd.to_datetime(df['submitted_date']).dt.tz_localize(None)
        
        df['days_since_policy_start'] = (df['incident_date'] - df['start_date']).dt.days
        df['days_since_policy_start'] = df['days_since_policy_start'].clip(lower=0)
        
        # Submission delay
        df['submission_delay_hours'] = (df['submitted_date'] - df['incident_date']).dt.total_seconds() / 3600
        df['submission_delay_hours'] = df['submission_delay_hours'].clip(lower=0)
        
        # Incident time features
        df['incident_hour'] = df['incident_date'].dt.hour
        df['incident_day_of_week'] = df['incident_date'].dt.dayofweek
        df['incident_month'] = df['incident_date'].dt.month
        
        # Claim to coverage ratio
        df['coverage_amount'] = pd.to_numeric(df['coverage_amount'], errors='coerce')
        df['claim_to_coverage_ratio'] = df['claimed_amount'] / df['coverage_amount'].replace(0, np.nan)
        df['claim_to_coverage_ratio'] = df['claim_to_coverage_ratio'].fillna(0).clip(upper=2.0)
        
        # Vehicle features
        df['year'] = pd.to_numeric(df['year'], errors='coerce')
        current_year = datetime.now().year
        df['vehicle_age'] = current_year - df['year']
        df['vehicle_age'] = df['vehicle_age'].clip(lower=0, upper=50)
        
        df['vehicle_value'] = pd.to_numeric(df['market_value'], errors='coerce').fillna(0)
        df['has_anti_theft'] = df['has_anti_theft'].fillna(False).astype(int)
        df['is_modified'] = df['is_modified'].fillna(False).astype(int)
        
        # Incident features
        df['police_report_filed'] = df['police_report_filed'].fillna(False).astype(int)
        df['witnesses_present'] = df['witnesses_present'].fillna(False).astype(int)
        df['number_of_witnesses'] = pd.to_numeric(df['number_of_witnesses'], errors='coerce').fillna(0)
        df['number_of_vehicles_involved'] = pd.to_numeric(df['number_of_vehicles_involved'], errors='coerce').fillna(1)
        df['number_of_injuries'] = pd.to_numeric(df['number_of_injuries'], errors='coerce').fillna(0)
        df['third_party_involved'] = df['third_party_involved'].fillna(False).astype(int)
        
        # Policyholder features
        df['date_of_birth'] = pd.to_datetime(df['date_of_birth']).dt.tz_localize(None)
        df['policyholder_age'] = (datetime.now() - df['date_of_birth']).dt.days / 365.25
        df['policyholder_age'] = df['policyholder_age'].clip(lower=18, upper=100)
        
        df['credit_score'] = pd.to_numeric(df['credit_score'], errors='coerce').fillna(650)
        df['years_with_company'] = pd.to_numeric(df['years_with_company'], errors='coerce').fillna(0)
        
        # Policyholder claim history
        claim_counts = df.groupby('policyholder_id').size().to_dict()
        df['policyholder_claim_count'] = df['policyholder_id'].map(claim_counts).fillna(1)
        
        # Fill any remaining NaN values
        numeric_columns = df.select_dtypes(include=[np.number]).columns
        df[numeric_columns] = df[numeric_columns].fillna(0)
        
        print(f"✓ Engineered {len(df)} samples with {len(df.columns)} features")
        return df
    
    def engineer_pricing_features(self, policyholders_df, vehicles_df, policies_df):
        """
        Engineer features for pricing model
        
        Args:
            policyholders_df: DataFrame with policyholder data
            vehicles_df: DataFrame with vehicle data
            policies_df: DataFrame with policy data
        
        Returns:
            DataFrame with engineered features
        """
        print("Engineering pricing features...")
        
        # Make copies
        policyholders_df = policyholders_df.copy()
        vehicles_df = vehicles_df.copy()
        policies_df = policies_df.copy()
        
        # Handle UUID vs integer IDs
        if 'id' in policyholders_df.columns and self._is_uuid_column(policyholders_df['id']):
            policyholder_id_map = {uuid: idx for idx, uuid in enumerate(policyholders_df['id'].unique())}
            vehicle_id_map = {uuid: idx for idx, uuid in enumerate(vehicles_df['id'].unique())}
            policy_id_map = {uuid: idx for idx, uuid in enumerate(policies_df['id'].unique())}
            
            policyholders_df['id'] = policyholders_df['id'].map(policyholder_id_map)
            vehicles_df['id'] = vehicles_df['id'].map(vehicle_id_map)
            policies_df['id'] = policies_df['id'].map(policy_id_map)
            policies_df['policyholder_id'] = policies_df['policyholder_id'].map(policyholder_id_map)
            policies_df['vehicle_id'] = policies_df['vehicle_id'].map(vehicle_id_map)
        
        # Start with policies
        df = policies_df.copy()
        df = df.merge(policyholders_df, left_on='policyholder_id', right_on='id', how='left', suffixes=('', '_policyholder'))
        df = df.merge(vehicles_df, left_on='vehicle_id', right_on='id', how='left', suffixes=('', '_vehicle'))
        
        # Driver features
        df['date_of_birth'] = pd.to_datetime(df['date_of_birth']).dt.tz_localize(None)
        df['age'] = (datetime.now() - df['date_of_birth']).dt.days / 365.25
        df['age'] = df['age'].clip(lower=18, upper=100)
        
        df['gender_encoded'] = self._encode_categorical(df['gender'], 'gender')
        df['marital_status_encoded'] = self._encode_categorical(df['marital_status'], 'marital_status')
        df['occupation_encoded'] = self._encode_categorical(df['occupation'], 'occupation')
        df['state_encoded'] = self._encode_categorical(df['state'], 'state')
        
        df['credit_score'] = pd.to_numeric(df['credit_score'], errors='coerce').fillna(650)
        df['years_with_company'] = pd.to_numeric(df['years_with_company'], errors='coerce').fillna(0)
        
        # Vehicle features
        df['year'] = pd.to_numeric(df['year'], errors='coerce')
        current_year = datetime.now().year
        df['vehicle_age'] = current_year - df['year']
        df['vehicle_age'] = df['vehicle_age'].clip(lower=0, upper=50)
        
        df['vehicle_value'] = pd.to_numeric(df['market_value'], errors='coerce').fillna(0)
        df['vehicle_type_encoded'] = self._encode_categorical(df['vehicle_type'], 'vehicle_type')
        df['fuel_type_encoded'] = self._encode_categorical(df['fuel_type'], 'fuel_type')
        
        df['has_anti_theft'] = df['has_anti_theft'].fillna(False).astype(int)
        df['has_airbags'] = df['has_airbags'].fillna(False).astype(int)
        df['has_abs'] = df['has_abs'].fillna(False).astype(int)
        df['is_modified'] = df['is_modified'].fillna(False).astype(int)
        df['odometer_reading'] = pd.to_numeric(df['odometer_reading'], errors='coerce').fillna(0)
        
        # Policy features
        df['policy_type_encoded'] = self._encode_categorical(df['policy_type'], 'policy_type')
        df['coverage_level_encoded'] = self._encode_categorical(df['coverage_level'], 'coverage_level')
        df['coverage_amount'] = pd.to_numeric(df['coverage_amount'], errors='coerce').fillna(0)
        df['deductible'] = pd.to_numeric(df['deductible'], errors='coerce').fillna(0)
        
        # Fill any remaining NaN values
        numeric_columns = df.select_dtypes(include=[np.number]).columns
        df[numeric_columns] = df[numeric_columns].fillna(0)
        
        print(f"✓ Engineered {len(df)} samples with {len(df.columns)} features")
        return df
    
    def engineer_claims_estimation_features(self, claims_df, vehicles_df, policies_df):
        """
        Engineer features for claims cost estimation
        
        Args:
            claims_df: DataFrame with claims data
            vehicles_df: DataFrame with vehicle data
            policies_df: DataFrame with policy data
        
        Returns:
            DataFrame with engineered features
        """
        print("Engineering claims estimation features...")
        
        # Make copies
        claims_df = claims_df.copy()
        vehicles_df = vehicles_df.copy()
        policies_df = policies_df.copy()
        
        # Handle UUID vs integer IDs
        if 'id' in policies_df.columns and self._is_uuid_column(policies_df['id']):
            policy_id_map = {uuid: idx for idx, uuid in enumerate(policies_df['id'].unique())}
            vehicle_id_map = {uuid: idx for idx, uuid in enumerate(vehicles_df['id'].unique())}
            
            claims_df['policy_id'] = claims_df['policy_id'].map(policy_id_map)
            claims_df['vehicle_id'] = claims_df['vehicle_id'].map(vehicle_id_map)
            policies_df['id'] = policies_df['id'].map(policy_id_map)
            policies_df['vehicle_id'] = policies_df['vehicle_id'].map(vehicle_id_map)
            vehicles_df['id'] = vehicles_df['id'].map(vehicle_id_map)
        
        df = claims_df.copy()
        
        # Merge with policies using policy_id
        df = df.merge(policies_df, left_on='policy_id', right_on='id', how='left', suffixes=('', '_policy'))
        
        # Merge with vehicles using vehicle_id
        df = df.merge(vehicles_df, left_on='vehicle_id', right_on='id', how='left', suffixes=('', '_vehicle'))
        
        # Claim features
        df['claim_type_encoded'] = self._encode_categorical(df['claim_type'], 'claim_type')
        df['severity_encoded'] = self._encode_categorical(df['severity'], 'severity')
        
        # Vehicle features
        df['year'] = pd.to_numeric(df['year'], errors='coerce')
        current_year = datetime.now().year
        df['vehicle_age'] = current_year - df['year']
        df['vehicle_age'] = df['vehicle_age'].clip(lower=0, upper=50)
        
        df['vehicle_value'] = pd.to_numeric(df['market_value'], errors='coerce').fillna(0)
        df['vehicle_type_encoded'] = self._encode_categorical(df['vehicle_type'], 'vehicle_type')
        
        # Incident features
        df['number_of_vehicles_involved'] = pd.to_numeric(df['number_of_vehicles_involved'], errors='coerce').fillna(1)
        df['number_of_injuries'] = pd.to_numeric(df['number_of_injuries'], errors='coerce').fillna(0)
        df['third_party_involved'] = df['third_party_involved'].fillna(False).astype(int)
        df['police_report_filed'] = df['police_report_filed'].fillna(False).astype(int)
        
        # Policy features
        df['coverage_amount'] = pd.to_numeric(df['coverage_amount'], errors='coerce').fillna(0)
        df['deductible'] = pd.to_numeric(df['deductible'], errors='coerce').fillna(0)
        df['policy_type_encoded'] = self._encode_categorical(df['policy_type'], 'policy_type')
        
        # Fill any remaining NaN values
        numeric_columns = df.select_dtypes(include=[np.number]).columns
        df[numeric_columns] = df[numeric_columns].fillna(0)
        
        print(f"✓ Engineered {len(df)} samples with {len(df.columns)} features")
        return df
    
    def _encode_categorical(self, series, column_name):
        """Encode categorical variable"""
        if column_name not in self.label_encoders:
            self.label_encoders[column_name] = LabelEncoder()
            return self.label_encoders[column_name].fit_transform(series.astype(str))
        else:
            # Handle unseen categories
            le = self.label_encoders[column_name]
            series = series.astype(str)
            mask = series.isin(le.classes_)
            encoded = np.zeros(len(series), dtype=int)
            encoded[mask] = le.transform(series[mask])
            return encoded
    
    def scale_features(self, X, fit=True):
        """Scale features using StandardScaler"""
        if fit:
            return self.scaler.fit_transform(X)
        else:
            return self.scaler.transform(X)
    
    def save_encoders(self, filepath):
        """Save label encoders"""
        joblib.dump(self.label_encoders, filepath)
        print(f"✓ Saved encoders to {filepath}")
    
    def load_encoders(self, filepath):
        """Load label encoders"""
        self.label_encoders = joblib.load(filepath)
        print(f"✓ Loaded encoders from {filepath}")
    
    def save_scaler(self, filepath):
        """Save scaler"""
        joblib.dump(self.scaler, filepath)
        print(f"✓ Saved scaler to {filepath}")
    
    def load_scaler(self, filepath):
        """Load scaler"""
        self.scaler = joblib.load(filepath)
        print(f"✓ Loaded scaler from {filepath}")