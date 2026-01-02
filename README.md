# Intelligent Insurance Operations Platform

An AI-powered insurance management system featuring fraud detection, dynamic pricing, and automated claims processing.

## Features

- **Fraud Detection**: Machine learning models to identify suspicious claims using XGBoost and Isolation Forest algorithms
- **Dynamic Pricing**: Risk-based premium calculation considering multiple factors
- **Claims Automation**: Automated claims processing with cost estimation
- **Real-time Dashboard**: Interactive analytics and monitoring interface

## Technology Stack

### Backend
- Django 4.2+ with Django REST Framework
- PostgreSQL database
- Redis for caching
- Celery for background tasks
- scikit-learn, XGBoost, TensorFlow for ML models

### Frontend
- React.js 18+
- Material-UI components
- Axios for API communication
- Chart.js for visualizations

## Project Structure
```
insurance-ai-platform/
├── backend/                 # Django project
│   ├── config/             # Django settings
│   ├── apps/               # Application modules
│   ├── ml_models/          # ML model files
│   └── data/               # Data generation scripts
├── frontend/               # React application
│   └── src/                # Source code
└── README.md
```

## Getting Started

### Prerequisites
- Python 3.10+
- Node.js 16+
- PostgreSQL 13+
- Git

### Installation

Instructions will be provided in subsequent setup steps.

## Authors

[Your Name] - Final Year Project

## License

This project is created for educational purposes.