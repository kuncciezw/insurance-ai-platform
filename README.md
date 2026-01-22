# Intelligent Insurance Operations Platform

> An AI-powered insurance management system demonstrating practical applications of machine learning in fraud detection, dynamic pricing, and automated claims processing. Built as a final year college project using Django 6.0, React 18, and XGBoost.

![Django](https://img.shields.io/badge/Django-6.0-green?logo=django)
![React](https://img.shields.io/badge/React-18.2-blue?logo=react)
![Python](https://img.shields.io/badge/Python-3.12%2B-blue?logo=python)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-13%2B-blue?logo=postgresql)
![License](https://img.shields.io/badge/License-Educational-orange)

---

## Table of Contents

- [Overview](#overview)
- [Key Features](#key-features)
- [Technology Stack](#technology-stack)
- [Machine Learning Models](#machine-learning-models)
- [System Architecture](#system-architecture)
- [Prerequisites](#prerequisites)
- [Installation Guide](#installation-guide)
- [Running the Application](#running-the-application)
- [User Roles & Permissions](#user-roles--permissions)
- [API Documentation](#api-documentation)
- [Project Structure](#project-structure)
- [Troubleshooting](#troubleshooting)
- [License](#license)

---

## Overview

The Intelligent Insurance Operations Platform automates critical insurance processes using machine learning. The system addresses three major challenges: fraudulent claims detection, risk-based premium calculation, and manual claims processing delays.

**Educational Context**: This is a final year college project demonstrating production-grade implementation of AI/ML in the insurance sector. While built for educational purposes, it follows industry best practices and uses enterprise-level technologies.

**Localization**: Uses Zimbabwe-centric demonstration data (Harare location, USD currency) while maintaining international insurance standards.

---

## Key Features

### 🔍 Fraud Detection
- **95%+ accuracy** using XGBoost + Isolation Forest ensemble
- Detects **10 distinct fraud patterns** (amount inflation, timing fraud, missing documentation, etc.)
- Real-time fraud probability scoring with risk level classification
- ~50ms prediction latency per claim

### 💰 Dynamic Pricing
- ML-based premium calculation with **25+ risk factors**
- **R² > 0.95** prediction accuracy, **MAPE ~8%**
- Transparent premium breakdowns showing risk factor contributions
- Historical price tracking and comparison tools

### ⚡ Claims Automation
- Automated settlement amount estimation
- Intelligent claim triage (low/medium/high complexity)
- Processing recommendations for claims adjusters
- **70% faster** routine claim processing

### 👥 Role-Based Access Control
- **6 user roles**: Super Admin, Admin, Claims Adjuster, Underwriter, Fraud Investigator, Viewer
- **25 granular permissions** across 7 functional categories
- Two-tier permission system (database overrides + hardcoded defaults)
- JWT authentication with automatic token refresh

### 📊 Real-time Analytics
- Interactive dashboard with KPIs and trend analysis
- Claims activity visualization
- Fraud detection statistics
- Role-based data filtering

---

## Technology Stack

### Backend
- **Django 6.0** - Latest stable release (December 2025)
- **Django REST Framework** - RESTful API development
- **PostgreSQL 13+** - Primary database with UUID keys
- **Redis** - Caching and message broker
- **Celery** - Background task processing
- **JWT** - Stateless authentication with refresh tokens

### Machine Learning
- **XGBoost 3.1+** - Primary model (fraud, pricing, claims)
- **scikit-learn 1.8+** - Feature engineering and preprocessing
- **Isolation Forest** - Anomaly detection for fraud
- **Pandas & NumPy** - Data manipulation
- **Matplotlib & Seaborn** - Model visualization

### Frontend
- **React 18.2** - UI framework with functional components
- **Tailwind CSS 3.3** - Utility-first styling
- **React Router v6** - Client-side routing
- **Axios** - HTTP client with auto token refresh
- **Lucide React** - Icon library

### Design System
- Primary: `#2C3E50` (Dark blue)
- Accent: `#FF6B4A` (Orange)
- Background: `#F8F9FA` (Light gray)

---

## Machine Learning Models

### Fraud Detection Model
**Architecture**: XGBoost Classifier + Isolation Forest ensemble

**Performance**:
- Accuracy: ~95%
- Precision: >75% (minimize false positives)
- Recall: >90% (catch fraud cases)
- F1 Score: >0.85
- ROC-AUC: >0.95

**Features**: 20+ including claim-to-value ratio, policy age, police reports, witness patterns, vehicle age, security features, geographic location

**Fraud Patterns Detected**:
1. Amount inflation (1.5-2.5x expected)
2. Suspicious timing (claims 1-15 days after policy inception)
3. Missing police reports on severe claims
4. Suspicious witness patterns
5. Vague incident descriptions
6. Claims near coverage limits
7. Multiple claims history (3+ per year)
8. High claims on old vehicles
9. Theft without security measures
10. Inconsistent injury claims

### Dynamic Pricing Model
**Architecture**: XGBoost Regressor

**Performance**:
- R² Score: >0.95
- MAPE: ~8%
- Prediction time: ~30ms

**Features**: 25+ including driver demographics, vehicle specifications, coverage selections, claim history, credit score, income level

### Claims Cost Estimator
**Architecture**: XGBoost Regressor

**Performance**:
- R² Score: >0.70
- Accuracy within ±10%: 40% of claims
- Accuracy within ±20%: 60% of claims
- Prediction time: ~40ms

**Features**: 12+ including severity, damage extent, injuries, liability, repair costs, market value

---

## System Architecture

### Three-Tier Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    PRESENTATION LAYER                        │
│  React 18 SPA │ Tailwind CSS │ Axios │ React Router         │
│  - JWT Token Management                                      │
│  - Permission-based UI Rendering                             │
│  - 10-minute Inactivity Timeout                              │
└──────────────────────────┬──────────────────────────────────┘
                           │ REST API (JSON)
┌──────────────────────────▼──────────────────────────────────┐
│                     BUSINESS LOGIC LAYER                     │
│  Django 6.0 │ DRF │ JWT Auth │ Role-Based Access Control    │
│  - API ViewSets & Endpoints                                  │
│  - ML Model Loader (Singleton)                               │
│  - Request Validation & Serialization                        │
└──────────────────────────┬──────────────────────────────────┘
                           │
┌──────────────────────────▼──────────────────────────────────┐
│                        DATA LAYER                            │
│  PostgreSQL │ Redis Cache │ ML Models (.pkl files)           │
│  - Relational Data (UUID PKs)                                │
│  - Cache (5-min TTL)                                         │
│  - Trained XGBoost Models                                    │
└─────────────────────────────────────────────────────────────┘
```

### Security Architecture
- **Authentication**: JWT with HMAC-SHA256 signing
- **Authorization**: Role-based permissions (6 roles, 25 permissions)
- **Token Lifecycle**: 24-hour access, 7-day refresh with rotation
- **API Protection**: Permission classes on all endpoints
- **SQL Injection**: Django ORM parameterized queries
- **XSS Protection**: React's built-in escaping + Django CSRF tokens

---

## Prerequisites

### System Requirements
- **OS**: Windows 10/11, macOS 10.15+, or Ubuntu 20.04+
- **RAM**: 8GB minimum (16GB recommended for ML training)
- **Disk**: 5GB free space
- **Internet**: Required for initial setup

### Required Software

| Software | Version | Purpose |
|----------|---------|---------|
| Python | 3.12+ | Backend runtime |
| Node.js | 16+ | Frontend build tools |
| PostgreSQL | 13+ | Primary database |
| Redis | 6+ | Cache & task queue |
| Git | 2.0+ | Version control |

---

## Installation Guide

### Step 1: Install Python 3.12+

**Windows**:
```bash
# Download from https://www.python.org/downloads/
# During installation, check "Add Python to PATH"
# Verify installation:
python --version
pip --version
```

**macOS** (using Homebrew):
```bash
brew install python@3.12
python3 --version
```

**Ubuntu/Debian**:
```bash
sudo apt update
sudo apt install python3.12 python3.12-venv python3-pip
python3.12 --version
```

### Step 2: Install PostgreSQL 13+

**Windows**:
```bash
# Download from https://www.postgresql.org/download/windows/
# Remember the password you set for 'postgres' user
# Verify installation:
psql --version
```

**macOS**:
```bash
brew install postgresql@13
brew services start postgresql@13
psql --version
```

**Ubuntu/Debian**:
```bash
sudo apt install postgresql postgresql-contrib
sudo systemctl start postgresql
sudo systemctl enable postgresql
psql --version
```

**Create Database**:
```bash
# Access PostgreSQL (password: the one you set during installation)
sudo -u postgres psql

# Inside psql shell:
CREATE DATABASE insurance_ai_db;
CREATE USER insurance_admin WITH PASSWORD 'your_secure_password';
ALTER ROLE insurance_admin SET client_encoding TO 'utf8';
ALTER ROLE insurance_admin SET default_transaction_isolation TO 'read committed';
ALTER ROLE insurance_admin SET timezone TO 'UTC';
GRANT ALL PRIVILEGES ON DATABASE insurance_ai_db TO insurance_admin;
\q
```

### Step 3: Install Redis 6+

**Windows** (using WSL or download pre-built):
```bash
# Option 1: WSL (recommended)
wsl --install
# Then follow Ubuntu instructions

# Option 2: Download from https://github.com/microsoftarchive/redis/releases
```

**macOS**:
```bash
brew install redis
brew services start redis
redis-cli ping  # Should return "PONG"
```

**Ubuntu/Debian**:
```bash
sudo apt install redis-server
sudo systemctl start redis
sudo systemctl enable redis
redis-cli ping  # Should return "PONG"
```

### Step 4: Install Node.js 16+

**Windows/macOS**:
```bash
# Download LTS from https://nodejs.org/
# Verify installation:
node --version
npm --version
```

**Ubuntu/Debian**:
```bash
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt install -y nodejs
node --version
npm --version
```

### Step 5: Clone Repository

```bash
# Clone the project
git clone https://github.com/yourusername/insurance-ai-platform.git
cd insurance-ai-platform

# Project structure
# insurance-ai-platform/
# ├── backend/          # Django project
# └── frontend/         # React project
```

### Step 6: Backend Setup

```bash
# Navigate to backend
cd backend

# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

# Upgrade pip
pip install --upgrade pip

# Install dependencies
pip install -r requirements.txt

# Create .env file
# Windows:
copy .env.example .env
# macOS/Linux:
cp .env.example .env

# Edit .env file with your settings:
# DB_NAME=insurance_ai_db
# DB_USER=insurance_admin
# DB_PASSWORD=your_secure_password  # From Step 2
# DB_HOST=localhost
# DB_PORT=5432
# SECRET_KEY=your-secret-key-here  # Generate with: python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
# DEBUG=True
# REDIS_URL=redis://localhost:6379/0

# Run migrations
python manage.py makemigrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser
# Username: admin
# Email: admin@example.com
# Password: (your choice, min 8 characters)

# Set superuser role
python manage.py shell
>>> from django.contrib.auth.models import User
>>> user = User.objects.get(username='admin')
>>> user.profile.role = 'SUPER_ADMIN'
>>> user.profile.is_active = True
>>> user.profile.save()
>>> exit()

# Generate synthetic data
python generate_data.py
# This creates:
# - 1,000 policyholders
# - 1,355 vehicles
# - 1,355 policies
# - 216 claims (15% fraudulent)

# Train ML models (takes 10-20 minutes)
python ml_models/train_all_models.py
# This creates:
# - 10 model files (.pkl)
# - 15 visualization plots (.png)
# Models saved to: ml_models/saved_models/
```

### Step 7: Frontend Setup

```bash
# Open NEW terminal (keep backend terminal open)
# Navigate to frontend
cd frontend

# Install dependencies
npm install

# Create .env file
# Windows:
copy .env.example .env
# macOS/Linux:
cp .env.example .env

# Edit frontend/.env:
REACT_APP_API_BASE_URL=http://localhost:8000/api
REACT_APP_API_TIMEOUT=30000
REACT_APP_NAME=Insurance AI Platform
REACT_APP_VERSION=1.0.0
```

---

## Running the Application

### Start Backend Server

```bash
# Terminal 1 - Activate venv and start Django
cd backend
source venv/bin/activate  # or venv\Scripts\activate on Windows
python manage.py runserver

# Server starts at: http://localhost:8000
# Admin panel: http://localhost:8000/admin
# API docs: http://localhost:8000/api/docs/
```

### Start Frontend Server

```bash
# Terminal 2 - Start React
cd frontend
npm start

# App opens at: http://localhost:3000
# Login with superuser credentials created in Step 6
```

### Access Points

| Service | URL | Credentials |
|---------|-----|-------------|
| React App | http://localhost:3000 | admin / (your password) |
| Django Admin | http://localhost:8000/admin | admin / (your password) |
| API Docs (Swagger) | http://localhost:8000/api/docs/ | - |
| API Docs (ReDoc) | http://localhost:8000/api/redoc/ | - |

---

## User Roles & Permissions

### User Roles

| Role | Code | Capabilities |
|------|------|--------------|
| **Super Admin** | `SUPER_ADMIN` | Full system access, can create other Super Admins, customize permissions |
| **Admin** | `ADMIN` | System management, cannot create Super Admins |
| **Claims Adjuster** | `CLAIMS_ADJUSTER` | Process claims, approve/reject, fraud detection |
| **Underwriter** | `UNDERWRITER` | Manage policies, calculate premiums, policyholder management |
| **Fraud Investigator** | `FRAUD_INVESTIGATOR` | Fraud detection and analysis only |
| **Viewer** | `VIEWER` | Read-only access to most data |

### Permission Categories (25 total)

1. **User Management** (5): Create/manage/delete users
2. **View Permissions** (5): View policyholders/vehicles/policies/claims/fraud
3. **Policyholder Management** (3): Create/edit/delete policyholders
4. **Policy Management** (3): Create/edit/delete policies
5. **Claims Management** (3): Process/approve/delete claims
6. **Fraud Detection** (2): Use fraud detection, flag fraud
7. **Premium & Estimation** (2): Calculate premiums, estimate claims
8. **Reports** (1): Export data

### User Creation Flows

**Admin-Created Users** (Active immediately):
1. Super Admin/Admin → System Settings → User Management
2. Click "Add New User"
3. Fill details (username, email, password, role)
4. User can log in immediately

**Self-Registration** (Requires approval):
1. Public → /register page
2. Fill registration form
3. Account created with `is_active=False`
4. Admin must approve in User Management
5. User can then log in

---

## API Documentation

### Base URL
```
http://localhost:8000/api
```

### Authentication
All endpoints (except login/register) require JWT token:
```http
Authorization: Bearer <your_access_token>
```

### Key Endpoints

**Authentication**:
- `POST /dashboard/auth/register/` - Self-registration
- `POST /dashboard/auth/login/` - User login
- `POST /dashboard/auth/logout/` - User logout
- `POST /dashboard/auth/token/refresh/` - Refresh access token
- `GET /dashboard/auth/profile/` - Get current user profile

**Fraud Detection**:
- `POST /fraud-detection/fraud/analyze-claim/` - Analyze single claim
- `POST /fraud-detection/fraud/batch-analyze/` - Batch analysis
- `GET /fraud-detection/fraud/high-risk-claims/` - List high-risk claims
- `GET /fraud-detection/fraud/statistics/` - Fraud statistics

**Dynamic Pricing**:
- `POST /dynamic-pricing/calculate-premium/` - Calculate premium
- `POST /dynamic-pricing/generate-quote/` - Generate quote
- `GET /dynamic-pricing/quotes/` - List quotes
- `GET /dynamic-pricing/price-comparison/` - Compare prices

**Claims Automation**:
- `POST /claims-automation/estimate-cost/` - Estimate claim cost
- `POST /claims-automation/auto-triage/` - Auto-triage claims
- `GET /claims-automation/estimates/` - List estimates
- `POST /claims-automation/claims/{id}/auto-process/` - Auto-process claim

**Full API Documentation**: Visit http://localhost:8000/api/docs/ after starting the backend.

---

## Project Structure

```
insurance-ai-platform/
├── backend/                          # Django 6.0 Project
│   ├── config/                       # Django Configuration
│   │   ├── settings.py              # Main settings (DB, JWT, CORS, ML paths)
│   │   ├── urls.py                  # URL routing + Swagger docs
│   │   └── wsgi.py                  # WSGI configuration
│   │
│   ├── apps/                         # Django Applications
│   │   ├── fraud_detection/         # Fraud Detection App
│   │   │   ├── models.py           # Policyholder, Vehicle, Policy, Claim models
│   │   │   ├── serializers.py      # DRF serializers with validation
│   │   │   ├── views.py            # ViewSets with custom actions
│   │   │   ├── ml_views.py         # ML-powered fraud endpoints
│   │   │   ├── urls.py             # API routes
│   │   │   └── admin.py            # Django admin configuration
│   │   │
│   │   ├── dynamic_pricing/         # Premium Calculation App
│   │   │   ├── models.py           # Quote, PriceHistory models
│   │   │   ├── serializers.py      # DRF serializers
│   │   │   ├── views.py            # Pricing endpoints
│   │   │   └── urls.py             # API routes
│   │   │
│   │   ├── claims_automation/       # Claims Automation App
│   │   │   ├── models.py           # ClaimEstimate, ProcessingLog models
│   │   │   ├── serializers.py      # DRF serializers
│   │   │   ├── views.py            # Claims estimation endpoints
│   │   │   └── urls.py             # API routes
│   │   │
│   │   └── dashboard/               # Dashboard & Auth App
│   │       ├── models.py           # UserProfile, RolePermission models
│   │       ├── serializers.py      # User serializers
│   │       ├── views.py            # Auth, stats, user management
│   │       └── urls.py             # Auth & dashboard routes
│   │
│   ├── ml_models/                   # Machine Learning
│   │   ├── ml_config.py            # ML configuration
│   │   ├── feature_engineering.py  # Feature utilities
│   │   ├── train_fraud_detection.py # Fraud model trainer
│   │   ├── train_pricing_model.py   # Pricing model trainer
│   │   ├── train_claims_estimator.py # Claims model trainer
│   │   ├── model_loader.py          # Prediction utilities (Singleton)
│   │   ├── train_all_models.py      # Master training script
│   │   └── saved_models/            # Trained models
│   │       ├── fraud_xgb_model.pkl
│   │       ├── fraud_isolation_forest.pkl
│   │       ├── pricing_model.pkl
│   │       ├── claims_estimator.pkl
│   │       ├── *.pkl (6 more encoders/scalers)
│   │       └── *.png (15 visualization plots)
│   │
│   ├── data/                        # Synthetic Data Generation
│   │   ├── base_generator.py       # Common utilities
│   │   ├── generate_policyholders.py # Policyholder data
│   │   ├── generate_vehicles.py     # Vehicle data
│   │   ├── generate_policies.py     # Policy data
│   │   ├── generate_claims.py       # Claims with fraud patterns
│   │   ├── generate_all_data.py     # Master generation script
│   │   ├── view_statistics.py       # Data statistics viewer
│   │   └── generated/               # CSV output directory
│   │       ├── policyholders.csv
│   │       ├── vehicles.csv
│   │       ├── policies.csv
│   │       └── claims.csv
│   │
│   ├── requirements.txt             # Python dependencies
│   ├── generate_data.py             # Quick data generation script
│   ├── test_api.py                  # API testing script
│   ├── .env                         # Environment variables (create from .env.example)
│   └── manage.py                    # Django management script
│
├── frontend/                        # React 18 Application
│   ├── public/
│   │   └── index.html              # HTML template
│   │
│   ├── src/
│   │   ├── components/             # React Components
│   │   │   ├── Login.jsx          # Login page
│   │   │   ├── Register.jsx       # Registration page
│   │   │   ├── Dashboard.jsx      # Main dashboard
│   │   │   ├── Sidebar.jsx        # Navigation sidebar
│   │   │   ├── Policyholders.jsx  # Policyholder management
│   │   │   ├── Vehicles.jsx       # Vehicle management
│   │   │   ├── Policies.jsx       # Policy management
│   │   │   ├── ClaimsList.jsx     # Claims list
│   │   │   ├── FraudDetection.jsx # Fraud detection interface
│   │   │   ├── PremiumCalculator.jsx # Premium calculator
│   │   │   ├── ClaimsEstimator.jsx   # Claims cost estimator
│   │   │   └── SystemSettings.jsx    # Admin settings
│   │   │
│   │   ├── contexts/
│   │   │   └── AuthContext.jsx    # Authentication context provider
│   │   │
│   │   ├── services/
│   │   │   └── api.js             # Axios API service (auto token refresh)
│   │   │
│   │   ├── App.jsx                 # Main app with routing
│   │   ├── index.js                # React entry point
│   │   └── index.css               # Tailwind CSS imports
│   │
│   ├── package.json                # npm dependencies
│   ├── tailwind.config.js          # Tailwind configuration
│   ├── .env                         # Environment variables (create from .env.example)
│   └── README.md                    # Create React App readme
│
├── .gitignore                       # Git ignore rules
├── README.md                        # This file
└── LICENSE                          # MIT License (optional)
```

---

## Troubleshooting

### Common Issues

**Issue**: `ModuleNotFoundError: No module named 'django'`
```bash
# Solution: Activate virtual environment
cd backend
source venv/bin/activate  # macOS/Linux
venv\Scripts\activate      # Windows
pip install -r requirements.txt
```

**Issue**: `psycopg2.OperationalError: could not connect to server`
```bash
# Solution: Start PostgreSQL
# macOS:
brew services start postgresql@13
# Linux:
sudo systemctl start postgresql
# Windows: Start from Services app
```

**Issue**: `redis.exceptions.ConnectionError: Error connecting to Redis`
```bash
# Solution: Start Redis
# macOS:
brew services start redis
# Linux:
sudo systemctl start redis
# Windows WSL: sudo service redis-server start
```

**Issue**: Frontend shows "Unable to connect to server"
```bash
# Solution: Check backend is running
# Terminal 1: cd backend && python manage.py runserver
# Verify: http://localhost:8000/api/docs/ loads

# Check .env files match
# backend/.env: DEBUG=True
# frontend/.env: REACT_APP_API_BASE_URL=http://localhost:8000/api
```

**Issue**: ML models not found
```bash
# Solution: Train models
cd backend
python ml_models/train_all_models.py
# Wait 10-20 minutes
# Check: ml_models/saved_models/ contains .pkl files
```

**Issue**: Database migration errors
```bash
# Solution: Reset migrations
python manage.py migrate fraud_detection zero
python manage.py migrate dashboard zero
python manage.py migrate
```

### Performance Tips

1. **Development**: Use SQLite for faster development (edit settings.py)
2. **ML Training**: Use GPU if available (install tensorflow-gpu)
3. **Data Volume**: Start with 100 policyholders for testing, scale to 1000+ for demo
4. **Browser**: Use Chrome/Edge for best React performance
5. **Cache**: Clear Redis cache if data seems stale: `redis-cli FLUSHALL`

---

## License

This project is created for **educational purposes** as a final year college project. It demonstrates the application of modern web development and machine learning technologies in the insurance domain.

**MIT License** - Feel free to use this code for learning and educational purposes. For commercial use, please consult with the authors.

---

## Authors

**[Your Name]** - Final Year Computer Science Student  
**Project Type**: Final Year Project (InsurTech AI Platform)  
**Institution**: [Your University Name]  
**Academic Year**: 2024/2025  
**Supervisor**: [Supervisor Name] (if applicable)

---

## Acknowledgments

- **Django** community for excellent documentation
- **XGBoost** team for the powerful ML library
- **React** team for the modern UI framework
- **Zimbabwe Insurance Industry** for domain insights
- **Faker** library for synthetic data generation
- **Academic Supervisors** for guidance and feedback

---

## Quick Start Summary

```bash
# 1. Prerequisites
✓ Python 3.12+
✓ Node.js 16+
✓ PostgreSQL 13+
✓ Redis 6+

# 2. Clone & Setup
git clone https://github.com/yourusername/insurance-ai-platform.git
cd insurance-ai-platform

# 3. Backend (Terminal 1)
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
# Edit .env file with your DB credentials
python manage.py migrate
python manage.py createsuperuser
python generate_data.py
python ml_models/train_all_models.py
python manage.py runserver

# 4. Frontend (Terminal 2)
cd frontend
npm install
npm start

# 5. Access
http://localhost:3000  # React App
http://localhost:8000/admin  # Django Admin
http://localhost:8000/api/docs/  # API Docs
```

---

**Need Help?** 
- Check [Troubleshooting](#troubleshooting) section
- Review API docs at http://localhost:8000/api/docs/
- Consult Django/React documentation
- Review code comments for inline explanations

**Happy Coding! 🚀**