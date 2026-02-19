# CORS Configuration Guide for Mobile Development

## Overview

This Django ServerWatch project has been configured with comprehensive Cross-Origin Resource Sharing (CORS) support to enable seamless communication between mobile applications and the REST API.

## CORS Implementation

### 1. Django CORS Headers Package

The project uses `django-cors-headers` for robust CORS management:

```bash
pip install django-cors-headers
```

### 2. Configuration Settings

#### Development Configuration
```python
# settings.py

# Add to INSTALLED_APPS
INSTALLED_APPS = [
    # ... other apps
    'corsheaders',
    # ... other apps
]

# Add middleware at the top
MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    # ... other middleware
]

# CORS settings for mobile apps
CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",  # React Native development
    "http://localhost:19006",  # Expo development
    "http://127.0.0.1:3000",
    "http://127.0.0.1:19006",
]

CORS_ALLOW_ALL_ORIGINS = DEBUG  # Allow all origins in development

CORS_ALLOW_CREDENTIALS = True

CORS_ALLOWED_HEADERS = [
    'accept',
    'accept-encoding',
    'authorization',
    'content-type',
    'dnt',
    'origin',
    'user-agent',
    'x-csrftoken',
    'x-requested-with',
]

CORS_ALLOW_METHODS = [
    'DELETE',
    'GET',
    'OPTIONS',
    'PATCH',
    'POST',
    'PUT',
]

# CORS settings for API endpoints
CORS_URLS_REGEX = r'^/api/.*$'

# Allow preflight requests for authentication endpoints
CORS_PREFLIGHT_MAX_AGE = 86400  # 24 hours
```

#### Production Configuration
```python
# Production CORS settings
CORS_ALLOWED_ORIGINS = [
    "https://yourapp.com",        # Production React Native app
    "https://staging.yourapp.com", # Staging environment
    "exp://yourapp.expo.app",     # Expo production
]

CORS_ALLOW_ALL_ORIGINS = False  # Disable in production
CORS_ALLOW_CREDENTIALS = True

# More restrictive headers for production
CORS_ALLOWED_HEADERS = [
    'accept',
    'authorization',
    'content-type',
]

# More restrictive methods for production
CORS_ALLOW_METHODS = [
    'GET',
    'POST',
    'PUT',
    'DELETE',
]
```

## Mobile App Integration

### React Native Configuration

#### 1. API Service Setup
```javascript
// src/services/api.js
import { Platform } from 'react-native';

const API_BASE_URL = Platform.select({
  ios: 'http://localhost:8000/api',
  android: 'http://10.0.2.2:8000/api',  # For Android emulator
  default: 'http://localhost:8000/api',
});

class APIService {
  constructor() {
    this.baseURL = API_BASE_URL;
    this.token = null;
  }

  setToken(token) {
    this.token = token;
  }

  async request(endpoint, options = {}) {
    const url = `${this.baseURL}${endpoint}`;
    const headers = {
      'Content-Type': 'application/json',
      'Accept': 'application/json',
      ...options.headers,
    };

    if (this.token) {
      headers.Authorization = `Token ${this.token}`;
    }

    const response = await fetch(url, {
      ...options,
      headers,
      mode: 'cors',  # Explicitly enable CORS
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.message || `HTTP ${response.status}`);
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

export default new APIService();
```

#### 2. Handling CORS Errors
```javascript
// src/utils/apiErrorHandler.js
export const handleAPIError = (error) => {
  if (error.message.includes('CORS')) {
    console.error('CORS Error: Make sure the server allows requests from your origin');
    return {
      type: 'CORS_ERROR',
      message: 'Unable to connect to server. Please check your network connection.',
    };
  }
  
  if (error.message.includes('Failed to fetch')) {
    console.error('Network Error: Unable to reach server');
    return {
      type: 'NETWORK_ERROR',
      message: 'Unable to connect to server. Please check your internet connection.',
    };
  }
  
  return {
    type: 'API_ERROR',
    message: error.message || 'An unexpected error occurred.',
  };
};
```

### Expo Configuration

#### 1. App Configuration
```json
// app.json
{
  "expo": {
    "name": "ServerWatch Mobile",
    "slug": "serverwatch-mobile",
    "version": "1.0.0",
    "platforms": ["ios", "android"],
    "scheme": "serverwatch",
    "ios": {
      "bundleIdentifier": "com.yourcompany.serverwatch"
    },
    "android": {
      "package": "com.yourcompany.serverwatch"
    },
    "web": {
      "bundler": "metro",
      "output": "static"
    }
  }
}
```

#### 2. Metro Configuration for CORS
```javascript
// metro.config.js
const { getDefaultConfig } = require('expo/metro-config');

const config = getDefaultConfig(__dirname);

// Add CORS support for development
config.resolver.assetExts.push(
  // Add any additional asset extensions if needed
);

module.exports = config;
```

## Testing CORS Configuration

### 1. Manual Testing with curl

#### Test Preflight Request
```bash
# Test OPTIONS preflight request
curl -X OPTIONS http://localhost:8000/api/auth/login/ \
  -H "Origin: http://localhost:3000" \
  -H "Access-Control-Request-Method: POST" \
  -H "Access-Control-Request-Headers: authorization, content-type" \
  -v
```

#### Test Actual Request
```bash
# Test actual POST request with CORS headers
curl -X POST http://localhost:8000/api/auth/login/ \
  -H "Origin: http://localhost:3000" \
  -H "Content-Type: application/json" \
  -d '{"username":"testuser","password":"testpass"}' \
  -v
```

### 2. Browser Testing

Open the browser developer tools and check for:

1. **Network Tab**: Look for CORS headers in response
2. **Console Tab**: Check for CORS errors
3. **Headers Tab**: Verify `Access-Control-Allow-Origin` header

### 3. Mobile App Testing

#### React Native Debugging
```javascript
// Add debugging to your API calls
const debugRequest = async (endpoint, options) => {
  console.log('Making request to:', endpoint);
  console.log('Headers:', options.headers);
  
  try {
    const response = await fetch(endpoint, options);
    console.log('Response headers:', response.headers);
    return response;
  } catch (error) {
    console.error('Request failed:', error);
    throw error;
  }
};
```

## Common CORS Issues and Solutions

### 1. "No 'Access-Control-Allow-Origin' header is present"

**Problem**: Server not configured to allow requests from your origin.

**Solution**: Add your origin to `CORS_ALLOWED_ORIGINS`:
```python
CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",  # Add your development origin
    "http://localhost:19006",  # Add Expo origin
]
```

### 2. "Request header field authorization is not allowed"

**Problem**: Authorization header not in allowed headers list.

**Solution**: Ensure 'authorization' is in `CORS_ALLOWED_HEADERS`:
```python
CORS_ALLOWED_HEADERS = [
    'accept',
    'authorization',  # Make sure this is included
    'content-type',
]
```

### 3. "Method PUT is not allowed by Access-Control-Allow-Methods"

**Problem**: HTTP method not in allowed methods list.

**Solution**: Add the method to `CORS_ALLOW_METHODS`:
```python
CORS_ALLOW_METHODS = [
    'GET',
    'POST',
    'PUT',  # Add PUT method
    'DELETE',
]
```

### 4. Credentials not allowed

**Problem**: Trying to send credentials (cookies, authorization headers) without proper configuration.

**Solution**: Enable credentials:
```python
CORS_ALLOW_CREDENTIALS = True
```

And ensure your client includes credentials:
```javascript
fetch(url, {
  credentials: 'include',  // For cookies
  headers: {
    'Authorization': `Token ${token}`
  }
});
```

## Security Considerations

### 1. Production Security

In production, avoid using `CORS_ALLOW_ALL_ORIGINS = True`. Instead, specify exact origins:

```python
# Production - Only allow specific origins
CORS_ALLOWED_ORIGINS = [
    "https://yourapp.com",
    "exp://yourapp.expo.app",
]

CORS_ALLOW_ALL_ORIGINS = False
```

### 2. Environment-Specific Configuration

```python
# settings.py
import os

if DEBUG:
    # Development - More permissive
    CORS_ALLOWED_ORIGINS = [
        "http://localhost:3000",
        "http://localhost:19006",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:19006",
    ]
    CORS_ALLOW_ALL_ORIGINS = True
else:
    # Production - Restrictive
    CORS_ALLOWED_ORIGINS = [
        os.environ.get('CORS_ALLOWED_ORIGIN', ''),
    ]
    CORS_ALLOW_ALL_ORIGINS = False
```

### 3. Rate Limiting

The project includes rate limiting middleware to prevent abuse:

```python
# Rate limits per user per minute
RATE_LIMITS = {
    'default': 1000,  # 1000 requests per minute
    'auth': 100,      # 100 auth requests per minute
    'agent': 2000,   # 2000 agent requests per minute
}
```

## Troubleshooting

### 1. Check Server Logs

Monitor Django logs for CORS-related messages:
```bash
python manage.py runserver --log-level=debug
```

### 2. Verify Middleware Order

Ensure `CorsMiddleware` is at the top of MIDDLEWARE list:
```python
MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',  # Must be first
    # ... other middleware
]
```

### 3. Test with Different Origins

Test requests from different origins to ensure proper CORS handling:
```bash
# Test with allowed origin
curl -H "Origin: http://localhost:3000" http://localhost:8000/api/mobile/dashboard/

# Test with disallowed origin
curl -H "Origin: http://malicious-site.com" http://localhost:8000/api/mobile/dashboard/
```

### 4. Network Inspector

Use browser network inspector or mobile app debugging tools to inspect:
- Request headers
- Response headers
- CORS preflight requests
- Actual requests

## Best Practices

1. **Environment-Specific Configuration**: Use different CORS settings for development and production
2. **Minimal Origins**: Only allow origins that actually need access
3. **Specific Headers**: Only allow headers that are actually needed
4. **Specific Methods**: Only allow HTTP methods that are actually needed
5. **Monitor Usage**: Keep track of which origins are accessing your API
6. **Regular Updates**: Review and update CORS settings as needed
7. **Security Headers**: Combine CORS with other security headers for comprehensive protection

## Testing Checklist

- [ ] Registration works from mobile app
- [ ] Login works and returns token
- [ ] Token authentication works for protected endpoints
- [ ] CORS headers are present in responses
- [ ] Preflight requests are handled correctly
- [ ] Error responses include proper CORS headers
- [ ] Rate limiting works appropriately
- [ ] Production configuration is secure
- [ ] Mobile app can handle CORS errors gracefully
- [ ] Network failures are handled appropriately

This CORS configuration ensures that your Django ServerWatch API can be securely accessed from mobile applications while maintaining security best practices.
