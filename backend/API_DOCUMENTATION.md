# Insurance AI Platform - API Documentation

## Base URL
```
http://localhost:8000/api
```

## Authentication

All endpoints (except registration and login) require JWT authentication.

Include the token in the Authorization header:
```
Authorization: Bearer <your_access_token>
```

### Authentication Endpoints

#### Register User
- **URL**: `/dashboard/auth/register/`
- **Method**: `POST`
- **Auth Required**: No
- **Body**:
```json
{
    "username": "johndoe",
    "email": "john@example.com",
    "password": "securepass123",
    "first_name": "John",
    "last_name": "Doe"
}
```

#### Login
- **URL**: `/dashboard/auth/login/`
- **Method**: `POST`
- **Auth Required**: No
- **Body**:
```json
{
    "username": "johndoe",
    "password": "securepass123"
}
```

#### Refresh Token
- **URL**: `/dashboard/auth/token/refresh/`
- **Method**: `POST`
- **Auth Required**: No
- **Body**:
```json
{
    "refresh": "<refresh_token>"
}
```

## Policyholder Endpoints

- `GET /fraud-detection/policyholders/` - List all policyholders
- `POST /fraud-detection/policyholders/` - Create policyholder
- `GET /fraud-detection/policyholders/{id}/` - Get policyholder details
- `PUT /fraud-detection/policyholders/{id}/` - Update policyholder
- `DELETE /fraud-detection/policyholders/{id}/` - Delete policyholder
- `GET /fraud-detection/policyholders/{id}/policies/` - Get policyholder's policies
- `GET /fraud-detection/policyholders/{id}/vehicles/` - Get policyholder's vehicles
- `GET /fraud-detection/policyholders/{id}/claims/` - Get policyholder's claims
- `GET /fraud-detection/policyholders/{id}/statistics/` - Get policyholder statistics
- `GET /fraud-detection/policyholders/high_risk/` - Get high-risk policyholders

## Vehicle Endpoints

- `GET /fraud-detection/vehicles/` - List all vehicles
- `POST /fraud-detection/vehicles/` - Create vehicle
- `GET /fraud-detection/vehicles/{id}/` - Get vehicle details
- `PUT /fraud-detection/vehicles/{id}/` - Update vehicle
- `DELETE /fraud-detection/vehicles/{id}/` - Delete vehicle
- `GET /fraud-detection/vehicles/{id}/policies/` - Get vehicle's policies
- `GET /fraud-detection/vehicles/{id}/claims/` - Get vehicle's claims
- `GET /fraud-detection/vehicles/high_value/` - Get high-value vehicles
- `GET /fraud-detection/vehicles/modified_vehicles/` - Get modified vehicles

## Policy Endpoints

- `GET /fraud-detection/policies/` - List all policies
- `POST /fraud-detection/policies/` - Create policy
- `GET /fraud-detection/policies/{id}/` - Get policy details
- `PUT /fraud-detection/policies/{id}/` - Update policy
- `DELETE /fraud-detection/policies/{id}/` - Delete policy
- `GET /fraud-detection/policies/{id}/claims/` - Get policy's claims
- `GET /fraud-detection/policies/active/` - Get active policies
- `GET /fraud-detection/policies/expiring_soon/` - Get policies expiring in 30 days
- `POST /fraud-detection/policies/{id}/renew/` - Renew policy
- `GET /fraud-detection/policies/statistics/` - Get policy statistics

## Claim Endpoints

- `GET /fraud-detection/claims/` - List all claims
- `POST /fraud-detection/claims/` - Create claim
- `GET /fraud-detection/claims/{id}/` - Get claim details
- `PUT /fraud-detection/claims/{id}/` - Update claim
- `DELETE /fraud-detection/claims/{id}/` - Delete claim
- `GET /fraud-detection/claims/pending/` - Get pending claims
- `GET /fraud-detection/claims/fraudulent/` - Get fraudulent claims
- `GET /fraud-detection/claims/high_value/` - Get high-value claims
- `POST /fraud-detection/claims/{id}/approve/` - Approve claim
- `POST /fraud-detection/claims/{id}/reject/` - Reject claim
- `POST /fraud-detection/claims/{id}/mark_paid/` - Mark claim as paid
- `GET /fraud-detection/claims/{id}/fraud_analysis/` - Get fraud analysis
- `GET /fraud-detection/claims/statistics/` - Get claim statistics
- `GET /fraud-detection/claims/recent_activity/` - Get recent claims

## Dashboard Endpoints

- `GET /dashboard/statistics/` - Get comprehensive dashboard statistics
- `GET /dashboard/auth/profile/` - Get current user profile

## Filtering and Searching

Most list endpoints support filtering, searching, and ordering:

**Example**:
```
GET /fraud-detection/claims/?claim_status=SUBMITTED&ordering=-submitted_date&search=accident
```

**Common Query Parameters**:
- `search` - Search across multiple fields
- `ordering` - Order results (prefix with `-` for descending)
- Filter by model fields (e.g., `claim_status=SUBMITTED`)