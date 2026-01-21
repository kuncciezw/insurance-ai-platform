# Insurance Fraud Detection - Model Training Documentation

## Table of Contents
1. [Overview](#overview)
2. [Data Generation Pipeline](#data-generation-pipeline)
3. [Feature Engineering](#feature-engineering)
4. [Model Selection & Architecture](#model-selection--architecture)
5. [Training Process](#training-process)
6. [Handling Class Imbalance](#handling-class-imbalance)
7. [Model Evaluation](#model-evaluation)
8. [Tools & Technologies](#tools--technologies)
9. [Zimbabwe Market Considerations](#zimbabwe-market-considerations)
10. [Best Practices & Recommendations](#best-practices--recommendations)

---

## Overview

This document describes the machine learning model training pipeline for detecting fraudulent insurance claims in the Zimbabwe market. The system uses supervised learning techniques to classify claims as legitimate or fraudulent based on historical patterns and risk indicators.

### Objectives
- **Accuracy**: Achieve high detection rates (target: >85% fraud detection)
- **Low False Positives**: Minimize legitimate claims flagged as fraud
- **Interpretability**: Provide explainable predictions for compliance
- **Scalability**: Handle growing datasets efficiently
- **Real-time**: Enable fast predictions for claim processing

---

## Data Generation Pipeline

### Synthetic Data Generation
Our training data is generated synthetically to simulate realistic Zimbabwe insurance scenarios while maintaining privacy and compliance.

#### Data Modules

**1. Policyholders** (`generate_policyholders.py`)
- Zimbabwe-specific demographics (Shona/Ndebele names, local phone formats)
- National ID generation (format: YY-NNNNNNANN)
- Location data (10 provinces, major cities)
- Income ranges in USD (monthly: $150-$5,000)
- Credit scoring (qualitative + numeric for ML)

**2. Vehicles** (`generate_vehicles.py`)
- Common Zimbabwe makes/models (Toyota, Nissan, Isuzu dominant)
- Vehicle age distribution (weighted toward 10-20 year old vehicles)
- Zimbabwe registration plates (format: AAA 1234)
- Market value depreciation modeling
- Safety features (anti-theft, ABS, airbags)

**3. Policies** (`generate_policies.py`)
- Policy types: Comprehensive, Third-Party, Collision, Liability
- Coverage levels: Basic, Standard, Premium
- Premium calculation based on multiple risk factors
- Policy lifecycle management (Active, Expired, Cancelled)

**4. Claims** (`generate_claims.py`)
- Claim types: Accident, Theft, Vandalism, Natural Disaster, Fire, Other
- Severity levels: Minor, Moderate, Major, Total Loss
- **Fraud pattern injection** (15% default fraud rate)
- Temporal fraud indicators (suspicious timing patterns)

### Fraud Pattern Generation

The system implements **10 distinct fraud patterns**:

| Pattern | Weight | Description |
|---------|--------|-------------|
| Amount Inflation | 30% | Claimed amount 1.5-2.5x higher than expected |
| Suspicious Timing | 20% | Claim filed 1-15 days after policy inception |
| No Police Report | 25% | Severe claims without official documentation |
| Multiple Claims | 15% | 3+ claims per year from same policyholder |
| Cross-Border Incidents | 18% | Claims at border areas (Beitbridge, Chirundu) |
| Staged Hijacking | 12% | High-risk area patterns (CBD night, townships) |
| Parts Theft Inflation | 10% | Inflated values for stolen components |
| Vague Descriptions | 20% | Unclear incident narratives |
| High Amount for Old Vehicle | 10% | Claims exceeding vehicle depreciated value |
| Theft Without Security | 10% | Theft claims on vehicles lacking anti-theft |

### Data Volume
- **Default Configuration**: 1,000 policyholders
- **Vehicles**: ~1,200 (weighted 1-2 per policyholder)
- **Policies**: ~1,200 (one per vehicle)
- **Claims**: ~720-800 (60% of policies have claims)
- **Fraud Distribution**: 15% fraudulent, 85% legitimate

---

## Feature Engineering

### Feature Categories

#### **1. Policyholder Features**
```python
- age (calculated from date_of_birth)
- gender (M/F)
- marital_status (SINGLE, MARRIED, DIVORCED, WIDOWED)
- occupation (EMPLOYED, SELF_EMPLOYED, RETIRED, STUDENT, UNEMPLOYED)
- annual_income (USD)
- credit_score (300-850 range)
- years_with_company (tenure)
- province/city (categorical)
```

#### **2. Vehicle Features**
```python
- make, model (categorical)
- year, vehicle_age (derived)
- vehicle_type (SEDAN, SUV, TRUCK, VAN, KOMBI)
- market_value (USD)
- odometer_reading (kilometers)
- fuel_type (PETROL, DIESEL, HYBRID)
- has_anti_theft (boolean)
- has_airbags (boolean)
- has_abs (boolean)
- is_modified (boolean)
```

#### **3. Policy Features**
```python
- policy_type (COMPREHENSIVE, THIRD_PARTY, COLLISION, LIABILITY)
- coverage_level (BASIC, STANDARD, PREMIUM)
- premium_amount (annual USD)
- coverage_amount (USD)
- deductible (USD)
- policy_duration_days (derived)
- has_roadside_assistance (boolean)
- has_rental_coverage (boolean)
- has_glass_coverage (boolean)
```

#### **4. Claim Features**
```python
- claim_type (ACCIDENT, THEFT, VANDALISM, etc.)
- severity (MINOR, MODERATE, MAJOR, TOTAL_LOSS)
- claimed_amount (USD)
- police_report_filed (boolean)
- witnesses_present (boolean)
- number_of_witnesses (integer)
- number_of_vehicles_involved (integer)
- number_of_injuries (integer)
- third_party_involved (boolean)
- days_since_policy_start (derived)
- claim_to_value_ratio (derived: claimed_amount / market_value)
- claim_to_coverage_ratio (derived: claimed_amount / coverage_amount)
```

### Derived Features (Feature Engineering)

**Temporal Features**:
- Days between policy start and incident
- Days between incident and submission
- Hour of day, day of week of incident
- Policy age at time of claim

**Financial Ratios**:
- Claim amount / Vehicle value
- Claim amount / Coverage limit
- Premium / Income ratio
- Deductible / Claim amount ratio

**Risk Scores**:
- Vehicle age risk score
- Location risk score (based on incident location)
- Policyholder claim history count
- Previous claim frequency

**Categorical Encoding**:
- One-hot encoding for low-cardinality features
- Target encoding for high-cardinality features (make, model, city)
- Frequency encoding for rare categories

---

## Model Selection & Architecture

### Recommended Models for Insurance Fraud Detection

Based on current research and industry best practices, the following models are recommended:

#### **1. Gradient Boosting Models (Primary)**

**XGBoost** (Extreme Gradient Boosting)
```python
from xgboost import XGBClassifier

model = XGBClassifier(
    max_depth=6,
    learning_rate=0.1,
    n_estimators=200,
    objective='binary:logistic',
    scale_pos_weight=5.67,  # Ratio of negative to positive classes
    gamma=0.1,
    min_child_weight=1,
    subsample=0.8,
    colsample_bytree=0.8,
    random_state=42
)
```

**Advantages**:
- Excellent performance on tabular data
- Built-in handling of missing values
- Feature importance extraction
- Handles non-linear relationships well
- Fast training and prediction

**LightGBM** (Light Gradient Boosting Machine)
```python
from lightgbm import LGBMClassifier

model = LGBMClassifier(
    num_leaves=31,
    learning_rate=0.05,
    n_estimators=300,
    class_weight='balanced',
    random_state=42
)
```

**Advantages**:
- Faster training than XGBoost on large datasets
- Lower memory usage
- Better handling of categorical features
- Excellent for high-dimensional data

**CatBoost** (Categorical Boosting)
```python
from catboost import CatBoostClassifier

model = CatBoostClassifier(
    iterations=500,
    learning_rate=0.03,
    depth=6,
    cat_features=['make', 'model', 'city', 'occupation'],
    auto_class_weights='Balanced',
    random_seed=42,
    verbose=False
)
```

**Advantages**:
- Native categorical feature support (no encoding needed)
- Robust to overfitting
- Built-in cross-validation
- Excellent interpretability with SHAP values

#### **2. Random Forest (Baseline & Ensemble)**

```python
from sklearn.ensemble import RandomForestClassifier

model = RandomForestClassifier(
    n_estimators=200,
    max_depth=15,
    min_samples_split=10,
    min_samples_leaf=4,
    class_weight='balanced',
    random_state=42,
    n_jobs=-1
)
```

**Use Case**: Strong baseline model, good for ensemble stacking

#### **3. Logistic Regression (Interpretable Baseline)**

```python
from sklearn.linear_model import LogisticRegression

model = LogisticRegression(
    penalty='l2',
    C=1.0,
    class_weight='balanced',
    max_iter=1000,
    random_state=42
)
```

**Use Case**: Highly interpretable, regulatory compliance, baseline comparison

#### **4. Neural Networks (Advanced)**

**For Complex Patterns**:
```python
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Dense, Dropout, BatchNormalization

model = Sequential([
    Dense(128, activation='relu', input_dim=n_features),
    BatchNormalization(),
    Dropout(0.3),
    Dense(64, activation='relu'),
    BatchNormalization(),
    Dropout(0.3),
    Dense(32, activation='relu'),
    Dropout(0.2),
    Dense(1, activation='sigmoid')
])

model.compile(
    optimizer='adam',
    loss='binary_crossentropy',
    metrics=['AUC', 'Precision', 'Recall']
)
```

**Bi-LSTM for Sequential Patterns**:
```python
from tensorflow.keras.layers import LSTM, Bidirectional

# For temporal claim sequences
model = Sequential([
    Bidirectional(LSTM(64, return_sequences=True), input_shape=(timesteps, features)),
    Dropout(0.3),
    Bidirectional(LSTM(32)),
    Dropout(0.3),
    Dense(16, activation='relu'),
    Dense(1, activation='sigmoid')
])
```

### Ensemble Approaches

**Voting Classifier** (Recommended for Production):
```python
from sklearn.ensemble import VotingClassifier

ensemble = VotingClassifier(
    estimators=[
        ('xgb', xgb_model),
        ('lgb', lgb_model),
        ('rf', rf_model)
    ],
    voting='soft',  # Use probability predictions
    weights=[2, 2, 1]  # Weight by validation performance
)
```

**Stacking Classifier**:
```python
from sklearn.ensemble import StackingClassifier

stacking = StackingClassifier(
    estimators=[
        ('xgb', xgb_model),
        ('lgb', lgb_model),
        ('cat', catboost_model)
    ],
    final_estimator=LogisticRegression(),
    cv=5
)
```

---

## Training Process

### Step 1: Data Preparation

```python
import pandas as pd
from sklearn.model_selection import train_test_split

# Load generated data
claims_df = pd.read_csv('data/generated/claims.csv')
policyholders_df = pd.read_csv('data/generated/policyholders.csv')
vehicles_df = pd.read_csv('data/generated/vehicles.csv')
policies_df = pd.read_csv('data/generated/policies.csv')

# Merge datasets
data = claims_df.merge(policies_df, on='policy_number') \
                .merge(policyholders_df, on='policyholder_id') \
                .merge(vehicles_df, on='vehicle_id')

# Feature engineering
data['policy_age_days'] = (pd.to_datetime(data['incident_date']) - 
                           pd.to_datetime(data['start_date'])).dt.days
data['claim_to_value_ratio'] = data['claimed_amount'] / data['market_value']
data['vehicle_age'] = pd.to_datetime('now').year - data['year']

# Select features
feature_columns = [
    # Policyholder features
    'annual_income', 'credit_score', 'years_with_company',
    # Vehicle features
    'vehicle_age', 'market_value', 'odometer_reading',
    'has_anti_theft', 'has_airbags', 'has_abs', 'is_modified',
    # Policy features
    'premium_amount', 'coverage_amount', 'deductible',
    # Claim features
    'claimed_amount', 'police_report_filed', 'witnesses_present',
    'number_of_witnesses', 'number_of_vehicles_involved', 'number_of_injuries',
    # Derived features
    'policy_age_days', 'claim_to_value_ratio'
]

categorical_features = [
    'gender', 'marital_status', 'occupation', 'state',
    'make', 'model', 'vehicle_type', 'fuel_type',
    'policy_type', 'coverage_level', 'claim_type', 'severity'
]

X = data[feature_columns + categorical_features]
y = data['is_fraudulent']

# Train-test split (stratified to maintain fraud ratio)
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42, stratify=y
)
```

### Step 2: Preprocessing

```python
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline

# Preprocessing pipeline
preprocessor = ColumnTransformer(
    transformers=[
        ('num', StandardScaler(), feature_columns),
        ('cat', OneHotEncoder(handle_unknown='ignore'), categorical_features)
    ]
)

# For tree-based models, scaling is optional
X_train_processed = preprocessor.fit_transform(X_train)
X_test_processed = preprocessor.transform(X_test)
```

### Step 3: Model Training

```python
from xgboost import XGBClassifier
from sklearn.model_selection import cross_val_score

# Calculate class weight
fraud_ratio = (y_train == 0).sum() / (y_train == 1).sum()

# Train XGBoost
xgb_model = XGBClassifier(
    max_depth=6,
    learning_rate=0.1,
    n_estimators=200,
    scale_pos_weight=fraud_ratio,
    random_state=42
)

# Cross-validation
cv_scores = cross_val_score(
    xgb_model, X_train, y_train, 
    cv=5, scoring='f1', n_jobs=-1
)
print(f"Cross-validation F1 scores: {cv_scores}")
print(f"Mean F1: {cv_scores.mean():.3f} (+/- {cv_scores.std():.3f})")

# Train on full training set
xgb_model.fit(X_train, y_train)
```

### Step 4: Hyperparameter Tuning

```python
from sklearn.model_selection import RandomizedSearchCV
from scipy.stats import randint, uniform

param_distributions = {
    'max_depth': randint(3, 10),
    'learning_rate': uniform(0.01, 0.3),
    'n_estimators': randint(100, 500),
    'min_child_weight': randint(1, 10),
    'subsample': uniform(0.6, 0.4),
    'colsample_bytree': uniform(0.6, 0.4),
    'gamma': uniform(0, 0.5)
}

random_search = RandomizedSearchCV(
    XGBClassifier(scale_pos_weight=fraud_ratio, random_state=42),
    param_distributions=param_distributions,
    n_iter=50,
    cv=5,
    scoring='f1',
    n_jobs=-1,
    random_state=42,
    verbose=1
)

random_search.fit(X_train, y_train)
best_model = random_search.best_estimator_
print(f"Best parameters: {random_search.best_params_}")
print(f"Best F1 score: {random_search.best_score_:.3f}")
```

---

## Handling Class Imbalance

Class imbalance (15% fraud, 85% legitimate) is critical in fraud detection. The system employs multiple strategies:

### **1. SMOTE (Synthetic Minority Over-sampling Technique)**

```python
from imblearn.over_sampling import SMOTE

smote = SMOTE(random_state=42, k_neighbors=5)
X_train_balanced, y_train_balanced = smote.fit_resample(X_train, y_train)

print(f"Original: {y_train.value_counts()}")
print(f"After SMOTE: {pd.Series(y_train_balanced).value_counts()}")
```

### **2. ADASYN (Adaptive Synthetic Sampling)**

```python
from imblearn.over_sampling import ADASYN

adasyn = ADASYN(random_state=42)
X_train_balanced, y_train_balanced = adasyn.fit_resample(X_train, y_train)
```

### **3. Class Weights**

```python
from sklearn.utils.class_weight import compute_class_weight

class_weights = compute_class_weight(
    'balanced', 
    classes=np.unique(y_train), 
    y=y_train
)
class_weight_dict = dict(enumerate(class_weights))

# Use in model
model = XGBClassifier(scale_pos_weight=class_weight_dict[1]/class_weight_dict[0])
```

### **4. Threshold Adjustment**

```python
# Instead of default 0.5 threshold
y_pred_proba = model.predict_proba(X_test)[:, 1]

# Use optimal threshold from ROC curve
from sklearn.metrics import roc_curve

fpr, tpr, thresholds = roc_curve(y_test, y_pred_proba)
optimal_idx = np.argmax(tpr - fpr)
optimal_threshold = thresholds[optimal_idx]

y_pred = (y_pred_proba >= optimal_threshold).astype(int)
```

---

## Model Evaluation

### Metrics for Fraud Detection

**Primary Metrics**:
- **F1 Score**: Harmonic mean of precision and recall
- **F2 Score**: Weights recall 2x higher than precision (prioritizes catching fraud)
- **AUC-ROC**: Area under receiver operating characteristic curve
- **Precision-Recall AUC**: Better for imbalanced datasets

**Secondary Metrics**:
- Precision (minimize false positives)
- Recall/Sensitivity (catch all fraud cases)
- Specificity (don't flag legitimate claims)

```python
from sklearn.metrics import (
    classification_report, confusion_matrix, 
    roc_auc_score, f1_score, fbeta_score,
    precision_recall_curve, auc
)

# Predictions
y_pred = model.predict(X_test)
y_pred_proba = model.predict_proba(X_test)[:, 1]

# Evaluation
print("Classification Report:")
print(classification_report(y_test, y_pred, target_names=['Legitimate', 'Fraud']))

print(f"\nF1 Score: {f1_score(y_test, y_pred):.3f}")
print(f"F2 Score: {fbeta_score(y_test, y_pred, beta=2):.3f}")
print(f"ROC-AUC: {roc_auc_score(y_test, y_pred_proba):.3f}")

# Precision-Recall AUC
precision, recall, _ = precision_recall_curve(y_test, y_pred_proba)
pr_auc = auc(recall, precision)
print(f"PR-AUC: {pr_auc:.3f}")

# Confusion Matrix
cm = confusion_matrix(y_test, y_pred)
print(f"\nConfusion Matrix:")
print(f"TN: {cm[0,0]}, FP: {cm[0,1]}")
print(f"FN: {cm[1,0]}, TP: {cm[1,1]}")
```

### Feature Importance & Interpretability

```python
import shap
import matplotlib.pyplot as plt

# SHAP values for model explanation
explainer = shap.TreeExplainer(model)
shap_values = explainer.shap_values(X_test)

# Summary plot
shap.summary_plot(shap_values, X_test, plot_type="bar")

# Feature importance from model
feature_importance = pd.DataFrame({
    'feature': X_train.columns,
    'importance': model.feature_importances_
}).sort_values('importance', ascending=False)

print(feature_importance.head(10))
```

---

## Tools & Technologies

### Core ML Libraries

| Tool | Purpose | Version |
|------|---------|---------|
| **scikit-learn** | Classical ML algorithms, preprocessing, evaluation | >=1.3.0 |
| **XGBoost** | Gradient boosting (primary model) | >=2.0.0 |
| **LightGBM** | Fast gradient boosting | >=4.0.0 |
| **CatBoost** | Categorical boosting | >=1.2.0 |
| **imbalanced-learn** | SMOTE, ADASYN for class imbalance | >=0.11.0 |

### Deep Learning (Optional)

| Tool | Purpose |
|------|---------|
| **TensorFlow/Keras** | Neural networks, Bi-LSTM |
| **PyTorch** | Alternative deep learning framework |

### Model Interpretation

| Tool | Purpose |
|------|---------|
| **SHAP** | Model-agnostic explanations |
| **LIME** | Local interpretable model explanations |
| **ELI5** | Feature importance visualization |

### Experiment Tracking

| Tool | Purpose |
|------|---------|
| **MLflow** | Experiment tracking, model registry |
| **Weights & Biases** | Advanced experiment management |
| **TensorBoard** | Visualization for deep learning |

### Hyperparameter Optimization

| Tool | Purpose |
|------|---------|
| **Optuna** | Bayesian optimization |
| **Hyperopt** | Distributed hyperparameter search |
| **scikit-optimize** | Sequential model-based optimization |

### Data Tools

| Tool | Purpose |
|------|---------|
| **Pandas** | Data manipulation |
| **NumPy** | Numerical computing |
| **Faker** | Synthetic data generation |

### Production Deployment

| Tool | Purpose |
|------|---------|
| **Django** | Web framework integration |
| **Celery** | Asynchronous task processing |
| **Redis** | Caching, message broker |
| **Docker** | Containerization |

---

## Zimbabwe Market Considerations

### Data Localization

1. **Currency**: All financial values in USD (primary currency for insurance in Zimbabwe)
2. **Names**: Shona (70%), Ndebele (20%), English (10%) name distributions
3. **Locations**: 10 provinces, weighted by population density
4. **Vehicles**: Emphasis on Toyota, Nissan, Isuzu (common in Zimbabwe market)
5. **Vehicle Age**: Higher proportion of 10-20 year old vehicles due to import market

### Fraud Patterns Specific to Zimbabwe

- **Cross-border fraud**: Claims at Beitbridge, Victoria Falls, Chirundu
- **Parts inflation**: Common for gearbox, engine, catalytic converter theft
- **Staged incidents**: Higher risk in CBD areas, townships
- **Multiple small claims**: Pattern of 3-6 claims per year
- **Policy timing**: Claims within 30 days of policy inception

### Economic Factors

- **Income levels**: Monthly income range $150-$5,000 USD
- **Vehicle values**: Depreciation adjusted for Zimbabwe market conditions
- **Premium calculations**: Factor in economic volatility, forex rates

---

## Best Practices & Recommendations

### Model Development

1. **Start Simple**: Begin with Logistic Regression baseline, then tree models
2. **Ensemble Methods**: XGBoost/LightGBM + Random Forest voting ensemble
3. **Cross-Validation**: Use 5-fold stratified CV for reliable evaluation
4. **Feature Selection**: Use SHAP values to identify top 20-30 features
5. **Regular Retraining**: Monthly retraining on new fraud patterns

### Handling Imbalance

1. **Preferred Method**: Combine SMOTE with class weights
2. **Evaluation**: Use F2 score (prioritizes recall over precision)
3. **Threshold Tuning**: Adjust decision threshold based on business cost of false negatives vs false positives

### Interpretability

1. **SHAP Values**: Mandatory for explaining individual predictions
2. **Feature Importance**: Document top 10 features influencing fraud detection
3. **Compliance**: Maintain audit trail of model decisions for regulatory requirements

### Production Considerations

1. **Model Versioning**: Use MLflow to track all model versions
2. **A/B Testing**: Deploy new models alongside existing for comparison
3. **Monitoring**: Track model performance drift, retrain when F1 < 0.80
4. **Latency**: Ensure predictions < 100ms for real-time claim processing

### Evaluation Standards

**Minimum Performance Thresholds**:
- F1 Score: ≥ 0.85
- Recall (Fraud Detection): ≥ 0.90 (catch 90% of fraud)
- Precision: ≥ 0.75 (minimize false positives)
- ROC-AUC: ≥ 0.95

**Model Selection Criteria**:
1. F2 Score (primary metric)
2. ROC-AUC (discriminative ability)
3. Training time (< 5 minutes on 10K samples)
4. Inference latency (< 100ms per prediction)
5. Model interpretability (SHAP compatibility)

---

## Next Steps

### Immediate Actions
1. ✅ Generate 5,000 policyholder dataset
2. ⏳ Train baseline models (Logistic Regression, Random Forest)
3. ⏳ Implement XGBoost with hyperparameter tuning
4. ⏳ Set up MLflow for experiment tracking
5. ⏳ Create SHAP visualization dashboard

### Advanced Enhancements
- Implement Bi-LSTM for temporal claim sequences
- Build real-time prediction API
- Create model monitoring dashboard
- Implement automated retraining pipeline
- Develop explainability report generator

### Research & Improvement
- Explore graph neural networks for policyholder networks
- Investigate anomaly detection (Isolation Forest, Autoencoders)
- Test ensemble stacking with meta-learners
- Benchmark against commercial fraud detection solutions

---

**Document Version**: 1.0  
