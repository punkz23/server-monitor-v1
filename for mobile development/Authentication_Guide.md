# Token-Based Authentication Guide

## Overview

This Django ServerWatch project implements comprehensive token-based authentication for mobile applications using Django REST Framework (DRF) tokens. The authentication system provides secure API access for mobile apps with features like user registration, login, logout, token management, and profile management.

## Authentication Features

### 1. Token-Based Authentication
- Uses DRF's built-in TokenAuthentication
- Tokens are generated automatically on login/registration
- Tokens are stored securely in the database
- Optional token expiration (30 days by default)

### 2. User Registration
- Mobile users can register new accounts
- Password strength validation (minimum 8 characters)
- Email uniqueness validation
- Automatic token generation on successful registration

### 3. Login/Logout
- Secure login with username/password
- Token returned on successful authentication
- Logout deletes the token (requires re-login)
- Token refresh functionality

### 4. Profile Management
- View user profile information
- Update profile details (email, name)
- Change password with old password verification
- Password change invalidates all tokens

### 5. Role-Based Permissions
- Different permission levels for different user types
- Staff users have full access
- Regular users have limited access
- Agent users for data ingestion

## API Endpoints

### Authentication Endpoints

#### Register New User
```
POST /api/auth/register/
```

**Request Body:**
```json
{
    "username": "newuser",
    "password": "securepassword123",
    "email": "user@example.com",
    "first_name": "John",
    "last_name": "Doe"
}
```

**Response (201 Created):**
```json
{
    "token": "abc123def456...",
    "user_id": 1,
    "username": "newuser",
    "email": "user@example.com",
    "first_name": "John",
    "last_name": "Doe",
    "message": "Registration successful"
}
```

#### Login
```
POST /api/auth/login/
```

**Request Body:**
```json
{
    "username": "existinguser",
    "password": "userpassword"
}
```

**Response (200 OK):**
```json
{
    "token": "xyz789abc123...",
    "user_id": 2,
    "username": "existinguser",
    "email": "user@example.com",
    "first_name": "Jane",
    "last_name": "Smith",
    "is_staff": false,
    "token_created": "2026-01-02T14:30:00Z",
    "message": "Login successful"
}
```

#### Logout
```
POST /api/auth/logout/
Authorization: Token xyz789abc123...
```

**Response (200 OK):**
```json
{
    "message": "Logout successful"
}
```

#### Get Token Info
```
GET /api/auth/token/info/
Authorization: Token xyz789abc123...
```

**Response (200 OK):**
```json
{
    "token": "xyz789abc123...",
    "user_id": 2,
    "username": "existinguser",
    "email": "user@example.com",
    "token_created": "2026-01-02T14:30:00Z",
    "token_age_days": 5
}
```

#### Refresh Token
```
POST /api/auth/token/refresh/
Authorization: Token xyz789abc123...
```

**Response (200 OK):**
```json
{
    "token": "newtoken456def...",
    "message": "Token refreshed successfully",
    "token_created": "2026-01-07T10:15:00Z"
}
```

#### Get Profile
```
GET /api/auth/profile/
Authorization: Token xyz789abc123...
```

**Response (200 OK):**
```json
{
    "user_id": 2,
    "username": "existinguser",
    "email": "user@example.com",
    "first_name": "Jane",
    "last_name": "Smith",
    "is_staff": false,
    "is_active": true,
    "date_joined": "2026-01-01T12:00:00Z",
    "last_login": "2026-01-07T10:15:00Z"
}
```

#### Update Profile
```
PUT /api/auth/profile/update/
Authorization: Token xyz789abc123...
```

**Request Body:**
```json
{
    "email": "newemail@example.com",
    "first_name": "Jane",
    "last_name": "Wilson"
}
```

**Response (200 OK):**
```json
{
    "message": "Profile updated successfully",
    "user": {
        "user_id": 2,
        "username": "existinguser",
        "email": "newemail@example.com",
        "first_name": "Jane",
        "last_name": "Wilson"
    }
}
```

#### Change Password
```
POST /api/auth/profile/change-password/
Authorization: Token xyz789abc123...
```

**Request Body:**
```json
{
    "old_password": "oldpassword123",
    "new_password": "newsecurepassword456"
}
```

**Response (200 OK):**
```json
{
    "message": "Password changed successfully. Please login again."
}
```

## Using Tokens in API Requests

Once you have a token, include it in the `Authorization` header for all authenticated requests:

```
Authorization: Token your_token_here
```

### Example Request
```bash
curl -H "Authorization: Token xyz789abc123" \
     http://localhost:8000/api/mobile/server-status/
```

### JavaScript Example
```javascript
const token = 'xyz789abc123';
fetch('/api/mobile/dashboard/', {
    headers: {
        'Authorization': `Token ${token}`,
        'Content-Type': 'application/json'
    }
})
.then(response => response.json())
.then(data => console.log(data));
```

### React Native Example
```javascript
const API_BASE_URL = 'http://your-server.com/api';

class APIService {
    constructor() {
        this.token = null;
    }

    setToken(token) {
        this.token = token;
    }

    async request(endpoint, options = {}) {
        const url = `${API_BASE_URL}${endpoint}`;
        const headers = {
            'Content-Type': 'application/json',
            ...options.headers,
        };

        if (this.token) {
            headers.Authorization = `Token ${this.token}`;
        }

        const response = await fetch(url, {
            ...options,
            headers,
        });

        if (!response.ok) {
            throw new Error(`API Error: ${response.status}`);
        }

        return response.json();
    }

    async login(username, password) {
        const data = await this.request('/auth/login/', {
            method: 'POST',
            body: JSON.stringify({ username, password }),
        });
        
        this.setToken(data.token);
        return data;
    }

    async getDashboard() {
        return this.request('/mobile/dashboard/');
    }
}
```

## Permission System

### Permission Classes

1. **IsAuthenticated** - User must be logged in
2. **HasMobileAppPermission** - Custom permission for mobile app users
3. **CanManageServers** - Can manage servers (staff only for write operations)
4. **CanViewAlerts** - Can view alerts (all authenticated users)
5. **CanManageNetworkDevices** - Can manage network devices (staff only for write operations)
6. **IsAgentUser** - Special permission for agent users (data ingestion)

### Permission Matrix

| Endpoint | Read Access | Write Access | Notes |
|----------|-------------|--------------|-------|
| `/api/servers/` | All authenticated | Staff only | Server management |
| `/api/network-devices/` | All authenticated | Staff only | Network device management |
| `/api/alerts/` | All authenticated | Staff only | Alert viewing/management |
| `/api/mobile/*` | All authenticated | Varies | Mobile-specific endpoints |
| `/api/mobile/agent/ingest/` | Agent users only | Agent users only | Data ingestion |

## Security Features

### Token Security
- Tokens are randomly generated 40-character strings
- Tokens are stored hashed in the database
- Tokens can be revoked/deleted on logout
- Optional token expiration (configurable)

### Password Security
- Minimum 8-character password requirement
- Passwords are hashed using Django's default password hashing
- Old password verification for password changes
- Password change invalidates all user tokens

### Input Validation
- All inputs are validated using Django forms and DRF serializers
- SQL injection protection through Django ORM
- XSS protection through proper escaping
- CSRF protection for web-based requests

## Error Handling

### Authentication Errors

#### Invalid Credentials (401)
```json
{
    "error": "invalid_credentials",
    "message": "Invalid username or password"
}
```

#### Missing Token (401)
```json
{
    "detail": "Authentication credentials were not provided."
}
```

#### Invalid Token (401)
```json
{
    "detail": "Invalid token."
}
```

#### Account Disabled (401)
```json
{
    "error": "account_disabled",
    "message": "Account is disabled"
}
```

### Registration Errors

#### Missing Fields (400)
```json
{
    "error": "missing_fields",
    "message": "Username and password are required"
}
```

#### Weak Password (400)
```json
{
    "error": "weak_password",
    "message": "Password must be at least 8 characters long"
}
```

#### Username Exists (409)
```json
{
    "error": "username_exists",
    "message": "Username already exists"
}
```

## Configuration

### Django Settings

```python
# settings.py
INSTALLED_APPS = [
    # ... other apps
    'rest_framework',
    'rest_framework.authtoken',
    # ... other apps
]

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.SessionAuthentication',
        'rest_framework.authentication.TokenAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 20,
    'TOKEN_EXPIRE_SECONDS': 86400 * 30,  # 30 days (optional)
}
```

### Token Management

To manually create tokens for users:

```python
from rest_framework.authtoken.models import Token
from django.contrib.auth.models import User

# Create token for existing user
user = User.objects.get(username='existinguser')
token = Token.objects.create(user=user)
print(f"Token: {token.key}")
```

To list all tokens:

```python
tokens = Token.objects.all()
for token in tokens:
    print(f"User: {token.user.username}, Token: {token.key[:8]}...")
```

## Best Practices

### For Mobile Developers

1. **Token Storage**: Store tokens securely on the device (Keychain on iOS, Keystore on Android)
2. **Token Refresh**: Implement token refresh logic to handle expired tokens
3. **Error Handling**: Handle authentication errors gracefully and redirect to login
4. **Offline Support**: Cache authentication state for offline usage
5. **Security**: Never store tokens in plain text or insecure storage

### For Server Administrators

1. **Token Cleanup**: Regularly clean up unused tokens
2. **Monitoring**: Monitor authentication failures for security breaches
3. **User Management**: Regularly review user accounts and permissions
4. **Backup**: Backup user accounts and tokens regularly
5. **Security**: Use HTTPS in production to protect tokens in transit

## Testing Authentication

### Test Script

Use the provided test script to test authentication:

```bash
python "for mobile development/test_api.py" --token YOUR_TOKEN
```

### Manual Testing

1. Register a new user:
```bash
curl -X POST http://localhost:8000/api/auth/register/ \
     -H "Content-Type: application/json" \
     -d '{"username":"testuser","password":"testpass123","email":"test@example.com"}'
```

2. Login with the new user:
```bash
curl -X POST http://localhost:8000/api/auth/login/ \
     -H "Content-Type: application/json" \
     -d '{"username":"testuser","password":"testpass123"}'
```

3. Use the returned token to access protected endpoints:
```bash
curl -H "Authorization: Token YOUR_TOKEN_HERE" \
     http://localhost:8000/api/mobile/dashboard/
```

## Troubleshooting

### Common Issues

1. **Token Not Working**: Ensure the token is included in the `Authorization` header with the correct format
2. **CORS Errors**: Configure CORS settings for mobile app domains
3. **401 Unauthorized**: Check if the user account is active and the token is valid
4. **Permission Denied**: Verify the user has the required permissions for the endpoint

### Debug Mode

Enable debug mode for more detailed error messages:

```python
# settings.py
DEBUG = True
REST_FRAMEWORK['DEFAULT_RENDERER_CLASSES'] = [
    'rest_framework.renderers.JSONRenderer',
    'rest_framework.renderers.BrowsableAPIRenderer',
]
```

This will enable DRF's browsable API which provides better error messages and testing interface.
