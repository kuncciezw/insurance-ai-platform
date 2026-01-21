"""
Alternative way to run training using Django management command
Create this file: backend/apps/fraud_detection/management/commands/train_claims.py
"""

from django.core.management.base import BaseCommand
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime
import joblib
import warnings
import os

warnings.filterwarnings('ignore')

from apps.fraud_detection.models import Claim, Policy, Vehicle, Policyholder
from ml_models.ml_config import MLConfig
from ml_models.feature_engineering import FeatureEngineer

from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
import xgboost as xgb


class Command(BaseCommand):
    help = 'Train claims cost estimation model'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('\n' + '='*70))
        self.stdout.write(self.style.SUCCESS('CLAIMS COST ESTIMATION MODEL TRAINING'))
        self.stdout.write(self.style.SUCCESS('='*70))
        
        trainer = ClaimsEstimatorTrainer(self.stdout, self.style)
        success = trainer.run_training_pipeline()
        
        if success:
            self.stdout.write(self.style.SUCCESS('\n✓ Training completed successfully!'))
        else:
            self.stdout.write(self.style.ERROR('\n❌ Training failed!'))


class ClaimsEstimatorTrainer:
    """Trains and evaluates claims cost estimation model"""
    
    def __init__(self, stdout, style):
        """Initialize trainer with configuration"""
        self.stdout = stdout
        self.style = style
        self.config = MLConfig()
        self.feature_engineer = FeatureEngineer()
        self.model = None
        self.feature_importance = None
        
        # Create directories
        os.makedirs(self.config.MODEL_DIR, exist_ok=True)
        os.makedirs('ml_models/visualizations', exist_ok=True)
    
    def load_data(self):
        """Load claims data from database with related information"""
        self.stdout.write('\n' + '='*70)
        self.stdout.write('LOADING CLAIMS DATA FROM DATABASE')
        self.stdout.write('='*70)
        
        # Get all claims with related data
        claims = Claim.objects.select_related(
            'policy__vehicle',
            'policy__policyholder'
        ).all()
        
        self.stdout.write(f'✓ Loaded {claims.count()} claims from database')
        
        # Convert to DataFrame
        data = []
        for claim in claims:
            try:
                policy = claim.policy
                vehicle = policy.vehicle
                policyholder = policy.policyholder
                
                record = {
                    # Claim information
                    'claim_id': claim.id,
                    'incident_date': claim.incident_date,
                    'incident_type': claim.incident_type,
                    'incident_severity': claim.incident_severity,
                    'incident_location': claim.incident_location,
                    'claim_amount': claim.claim_amount,
                    'police_report': claim.police_report_available,
                    'witnesses': claim.witnesses,
                    'property_damage': claim.property_damage,
                    'bodily_injuries': claim.bodily_injuries,
                    'is_fraud': claim.is_fraud,
                    
                    # Policy information
                    'policy_type': policy.policy_type,
                    'coverage_level': policy.coverage_level,
                    'annual_premium': float(policy.annual_premium),
                    'deductible': float(policy.deductible),
                    'liability_coverage': float(policy.liability_coverage),
                    'collision_coverage': float(policy.collision_coverage),
                    'comprehensive_coverage': float(policy.comprehensive_coverage),
                    
                    # Vehicle information
                    'vehicle_age': (datetime.now().date() - vehicle.year).days // 365 if hasattr(vehicle.year, 'days') else datetime.now().year - vehicle.year,
                    'vehicle_value': float(vehicle.market_value),
                    'safety_rating': vehicle.safety_rating,
                    
                    # Policyholder information
                    'policyholder_age': policyholder.age,
                    'driving_experience': policyholder.driving_experience,
                    'previous_claims': policyholder.previous_claims,
                    'credit_score': policyholder.credit_score,
                }
                
                data.append(record)
            except Exception as e:
                self.stdout.write(f"  Warning: Skipping claim {claim.id} due to error: {str(e)}")
                continue
        
        df = pd.DataFrame(data)
        
        self.stdout.write(f'\n✓ Created DataFrame with {len(df)} claims')
        self.stdout.write(f'✓ Features: {len(df.columns)} columns')
        self.stdout.write(f'✓ Target variable: claim_amount')
        self.stdout.write(f'\nClaim Amount Statistics:')
        self.stdout.write(f'  Mean: ${df["claim_amount"].mean():,.2f}')
        self.stdout.write(f'  Median: ${df["claim_amount"].median():,.2f}')
        self.stdout.write(f'  Std Dev: ${df["claim_amount"].std():,.2f}')
        self.stdout.write(f'  Min: ${df["claim_amount"].min():,.2f}')
        self.stdout.write(f'  Max: ${df["claim_amount"].max():,.2f}')
        
        return df
    
    def prepare_features(self, df):
        """Prepare features for claims estimation"""
        self.stdout.write('\n' + '='*70)
        self.stdout.write('FEATURE ENGINEERING')
        self.stdout.write('='*70)
        
        # Separate features and target
        X = df[self.config.CLAIMS_ESTIMATION_FEATURES].copy()
        y = df['claim_amount'].values
        
        self.stdout.write(f'\n✓ Features prepared: {X.shape[1]} features')
        self.stdout.write(f'✓ Target variable: claim_amount ({len(y)} samples)')
        
        # Apply feature engineering
        X_processed = self.feature_engineer.prepare_claims_features(X)
        
        self.stdout.write(f'✓ Features processed: {X_processed.shape[1]} features after encoding')
        
        return X_processed, y
    
    def train_model(self, X_train, y_train, X_test, y_test):
        """Train XGBoost regressor for claims estimation"""
        self.stdout.write('\n' + '='*70)
        self.stdout.write('TRAINING CLAIMS COST ESTIMATION MODEL')
        self.stdout.write('='*70)
        
        self.stdout.write('\nTraining XGBoost Regressor...')
        self.stdout.write(f'Training samples: {len(X_train)}')
        self.stdout.write(f'Testing samples: {len(X_test)}')
        
        # Train XGBoost model
        self.model = xgb.XGBRegressor(
            n_estimators=self.config.CLAIMS_PARAMS['n_estimators'],
            max_depth=self.config.CLAIMS_PARAMS['max_depth'],
            learning_rate=self.config.CLAIMS_PARAMS['learning_rate'],
            min_child_weight=self.config.CLAIMS_PARAMS['min_child_weight'],
            subsample=self.config.CLAIMS_PARAMS['subsample'],
            colsample_bytree=self.config.CLAIMS_PARAMS['colsample_bytree'],
            random_state=42,
            n_jobs=-1
        )
        
        self.model.fit(
            X_train, y_train,
            eval_set=[(X_test, y_test)],
            verbose=False
        )
        
        self.stdout.write('✓ Model training completed')
        
        # Get feature importance
        self.feature_importance = pd.DataFrame({
            'feature': self.feature_engineer.feature_names_,
            'importance': self.model.feature_importances_
        }).sort_values('importance', ascending=False)
        
        return self.model
    
    def evaluate_model(self, X_train, y_train, X_test, y_test):
        """Evaluate model performance"""
        self.stdout.write('\n' + '='*70)
        self.stdout.write('MODEL EVALUATION')
        self.stdout.write('='*70)
        
        # Make predictions
        y_train_pred = self.model.predict(X_train)
        y_test_pred = self.model.predict(X_test)
        
        # Calculate metrics
        train_rmse = np.sqrt(mean_squared_error(y_train, y_train_pred))
        test_rmse = np.sqrt(mean_squared_error(y_test, y_test_pred))
        
        train_mae = mean_absolute_error(y_train, y_train_pred)
        test_mae = mean_absolute_error(y_test, y_test_pred)
        
        train_r2 = r2_score(y_train, y_train_pred)
        test_r2 = r2_score(y_test, y_test_pred)
        
        # Calculate percentage errors
        train_mape = np.mean(np.abs((y_train - y_train_pred) / y_train)) * 100
        test_mape = np.mean(np.abs((y_test - y_test_pred) / y_test)) * 100
        
        self.stdout.write('\nTraining Set Performance:')
        self.stdout.write(f'  RMSE: ${train_rmse:,.2f}')
        self.stdout.write(f'  MAE: ${train_mae:,.2f}')
        self.stdout.write(f'  R² Score: {train_r2:.4f}')
        self.stdout.write(f'  MAPE: {train_mape:.2f}%')
        
        self.stdout.write('\nTest Set Performance:')
        self.stdout.write(f'  RMSE: ${test_rmse:,.2f}')
        self.stdout.write(f'  MAE: ${test_mae:,.2f}')
        self.stdout.write(f'  R² Score: {test_r2:.4f}')
        self.stdout.write(f'  MAPE: {test_mape:.2f}%')
        
        # Cross-validation
        self.stdout.write('\nPerforming 5-Fold Cross-Validation...')
        cv_scores = cross_val_score(
            self.model, X_train, y_train,
            cv=5, scoring='r2', n_jobs=-1
        )
        
        self.stdout.write(f'  Mean CV R² Score: {cv_scores.mean():.4f} (+/- {cv_scores.std() * 2:.4f})')
        
        # Store metrics
        metrics = {
            'train_rmse': train_rmse,
            'test_rmse': test_rmse,
            'train_mae': train_mae,
            'test_mae': test_mae,
            'train_r2': train_r2,
            'test_r2': test_r2,
            'train_mape': train_mape,
            'test_mape': test_mape,
            'cv_mean': cv_scores.mean(),
            'cv_std': cv_scores.std()
        }
        
        return metrics, y_test_pred
    
    def save_model(self):
        """Save trained model and artifacts"""
        self.stdout.write('\n' + '='*70)
        self.stdout.write('SAVING MODEL ARTIFACTS')
        self.stdout.write('='*70)
        
        # Save model
        model_path = self.config.CLAIMS_MODEL_PATH
        joblib.dump(self.model, model_path)
        self.stdout.write(f'✓ Saved model: {model_path}')
        
        # Save feature engineer
        encoder_path = self.config.CLAIMS_ENCODER_PATH
        joblib.dump(self.feature_engineer, encoder_path)
        self.stdout.write(f'✓ Saved feature encoder: {encoder_path}')
        
        # Save feature importance
        importance_path = os.path.join(self.config.MODEL_DIR, 'claims_feature_importance.csv')
        self.feature_importance.to_csv(importance_path, index=False)
        self.stdout.write(f'✓ Saved feature importance: {importance_path}')
        
        self.stdout.write('\n✓ All artifacts saved successfully')
    
    def run_training_pipeline(self):
        """Execute complete training pipeline"""
        start_time = datetime.now()
        
        try:
            # Step 1: Load data
            df = self.load_data()
            
            # Step 2: Prepare features
            X, y = self.prepare_features(df)
            
            # Step 3: Split data
            self.stdout.write('\n' + '='*70)
            self.stdout.write('SPLITTING DATA')
            self.stdout.write('='*70)
            
            X_train, X_test, y_train, y_test = train_test_split(
                X, y, test_size=0.2, random_state=42
            )
            
            self.stdout.write(f'✓ Training set: {len(X_train)} samples ({len(X_train)/len(X)*100:.1f}%)')
            self.stdout.write(f'✓ Test set: {len(X_test)} samples ({len(X_test)/len(X)*100:.1f}%)')
            
            # Step 4: Train model
            self.train_model(X_train, y_train, X_test, y_test)
            
            # Step 5: Evaluate model
            metrics, y_pred = self.evaluate_model(X_train, y_train, X_test, y_test)
            
            # Step 6: Save model
            self.save_model()
            
            # Training complete
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            
            self.stdout.write('\n' + '='*70)
            self.stdout.write(self.style.SUCCESS('TRAINING COMPLETED SUCCESSFULLY'))
            self.stdout.write('='*70)
            self.stdout.write(f'Total Duration: {duration:.2f} seconds')
            self.stdout.write(f'\nModel Performance Summary:')
            self.stdout.write(f'  • Test R² Score: {metrics["test_r2"]:.4f}')
            self.stdout.write(f'  • Test RMSE: ${metrics["test_rmse"]:,.2f}')
            self.stdout.write(f'  • Test MAE: ${metrics["test_mae"]:,.2f}')
            self.stdout.write(f'  • Test MAPE: {metrics["test_mape"]:.2f}%')
            
            return True
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'\n❌ Error during training: {str(e)}'))
            import traceback
            traceback.print_exc()
            return False