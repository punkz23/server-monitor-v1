# API Versioning Guide for Django ServerWatch

## Overview

This Django ServerWatch project implements a comprehensive API versioning strategy to ensure backward compatibility and smooth migration paths for mobile applications. The versioning system supports multiple strategies and provides clear deprecation timelines.

## Versioning Strategy

### 1. Supported Versioning Methods

#### URL Path Versioning (Recommended)
```bash
# Version 1
/api/v1/mobile/dashboard/
/api/v1/auth/login/

# Version 2
/api/v2/mobile/dashboard/
/api/v2/auth/login/
```

#### Header Versioning
```bash
# Using Accept header
Accept: application/vnd.api+json;version=1
Accept: application/vnd.api+json;version=2

# Using custom header
X-API-Version: 1
X-API-Version: 2
```

#### Query Parameter Versioning
```bash
# Query parameter
/api/mobile/dashboard/?version=1
/api/mobile/dashboard/?version=2
```

### 2. Version Priority

The system detects versions in this priority order:
1. **URL Path** (highest priority)
2. **Accept Header**
3. **Query Parameter**
4. **Custom Header** (lowest priority)

### 3. Version Status

| Version | Status | Deprecated | Sunset Date |
|---------|--------|------------|-------------|
| v1 | Current | No | None |
| v2 | Beta | No | None |

## API Endpoints by Version

### Version 1 (Current)

#### Authentication
- `POST /api/auth/login/` - User login
- `POST /api/auth/register/` - User registration
- `POST /api/auth/logout/` - User logout
- `GET /api/auth/token/info/` - Token information
- `POST /api/auth/token/refresh/` - Token refresh
- `GET /api/auth/profile/` - User profile
- `PUT /api/auth/profile/update/` - Update profile
- `POST /api/auth/profile/change-password/` - Change password

#### Mobile API
- `GET /api/v1/mobile/dashboard/` - Dashboard summary
- `GET /api/v1/mobile/server-status/` - Server status list
- `GET /api/v1/mobile/network-devices/` - Network devices
- `GET /api/v1/mobile/server/{id}/` - Server details
- `GET /api/v1/mobile/alerts/` - Alerts list
- `GET /api/v1/mobile/server/{id}/metrics/` - Server metrics
- `POST /api/v1/mobile/agent/ingest/` - Agent data ingestion

#### REST Endpoints
- `GET /api/v1/servers/` - Servers CRUD
- `GET /api/v1/network-devices/` - Network devices CRUD
- `GET /api/v1/alerts/` - Alerts (read-only)
- `GET /api/v1/isp-connections/` - ISP connections CRUD
- `GET /api/v1/cctv-devices/` - CCTV devices CRUD

### Version 2 (Beta)

#### Enhanced Mobile API
- `GET /api/v2/mobile/dashboard/` - Enhanced dashboard with health metrics
- `GET /api/v2/mobile/server-status/` - Enhanced server status with health scoring
- `GET /api/v2/mobile/server-status/v2/` - V2 specific endpoint
- `GET /api/v2/mobile/server/{id}/` - Enhanced server details with recommendations
- `GET /api/v2/mobile/alerts/` - Enhanced alerts with impact analysis

#### V2 New Features
- **Health Scoring**: Server health scores (0-100)
- **Performance Metrics**: Response time analysis and performance ratings
- **Trend Analysis**: Historical trends and patterns
- **Recommendations**: Automated server recommendations
- **Enhanced Filtering**: Better alert filtering and metadata
- **Historical Analysis**: 24h status history, 7d performance trends

## Data Format Differences

### Server Status Response

#### V1 Format
```json
{
  "servers": [
    {
      "id": 1,
      "name": "Web Server 1",
      "server_type": "WEB",
      "last_status": "UP",
      "last_cpu_percent": 45.2,
      "last_ram_percent": 67.8,
      "last_latency_ms": 12,
      "last_checked": "2026-01-02T14:30:00Z"
    }
  ],
  "timestamp": "2026-01-02T14:30:00Z"
}
```

#### V2 Format
```json
{
  "servers": [
    {
      "id": 1,
      "name": "Web Server 1",
      "server_type": "WEB",
      "last_status": "UP",
      "last_cpu_percent": 45.2,
      "last_ram_percent": 67.8,
      "last_latency_ms": 12,
      "last_checked": "2026-01-02T14:30:00Z",
      "health_score": 85,
      "uptime_percentage": 99.9,
      "response_time_ms": 12,
      "status_trend": "stable",
      "performance_rating": "good"
    }
  ],
  "summary": {
    "total_servers": 1,
    "online_servers": 1,
    "offline_servers": 0,
    "average_health_score": 85.0
  },
  "timestamp": "2026-01-02T14:30:00Z",
  "api_version": "2"
}
```

### Dashboard Response

#### V1 Format
```json
{
  "servers": {
    "total": 12,
    "enabled": 12,
    "online": 10,
    "offline": 2
  },
  "network_devices": {
    "total": 49,
    "active": 49,
    "inactive": 0
  },
  "alerts": {
    "recent_24h": 0,
    "critical": 0
  },
  "timestamp": "2026-01-02T14:30:00Z"
}
```

#### V2 Format
```json
{
  "servers": {
    "total": 12,
    "enabled": 12,
    "online": 10,
    "offline": 2
  },
  "network_devices": {
    "total": 49,
    "active": 49,
    "inactive": 0
  },
  "alerts": {
    "recent_24h": 0,
    "critical": 0
  },
  "health_metrics": {
    "average_health_score": 82.5,
    "healthy_servers": 8,
    "warning_servers": 2,
    "critical_servers": 0
  },
  "performance_metrics": {
    "average_response_time": 45.2,
    "fast_servers": 8,
    "slow_servers": 2
  },
  "trends": {
    "server_status_trend": "stable",
    "alert_trend": "decreasing",
    "performance_trend": "improving"
  },
  "timestamp": "2026-01-02T14:30:00Z",
  "api_version": "2",
  "enhanced_features": ["health_scoring", "performance_metrics", "trend_analysis"]
}
```

## Mobile App Integration

### React Native Example

#### API Service with Versioning
```javascript
// src/services/api.js
class APIService {
  constructor(apiVersion = '1') {
    this.baseURL = 'http://localhost:8000/api';
    this.version = apiVersion;
    this.token = null;
  }

  setVersion(version) {
    this.version = version;
  }

  async request(endpoint, options = {}) {
    const url = `${this.baseURL}/v${this.version}${endpoint}`;
    const headers = {
      'Content-Type': 'application/json',
      'Accept': `application/vnd.api+json;version=${this.version}`,
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

  async getDashboard() {
    return this.request('/mobile/dashboard/');
  }

  async getServerStatus() {
    return this.request('/mobile/server-status/');
  }

  // V2 specific methods
  async getEnhancedDashboard() {
    this.setVersion('2');
    return this.request('/mobile/dashboard/');
  }

  async getServerHealth() {
    this.setVersion('2');
    return this.request('/mobile/server-status/');
  }
}
```

#### Version Detection and Migration
```javascript
// src/utils/versionManager.js
class VersionManager {
  constructor(apiService) {
    this.apiService = apiService;
    this.currentVersion = '1';
  }

  async detectBestVersion() {
    try {
      // Try V2 first
      this.apiService.setVersion('2');
      await this.apiService.getDashboard();
      this.currentVersion = '2';
      return '2';
    } catch (error) {
      // Fall back to V1
      this.apiService.setVersion('1');
      this.currentVersion = '1';
      return '1';
    }
  }

  async migrateToV2() {
    if (this.currentVersion === '2') return;

    try {
      // Test V2 compatibility
      this.apiService.setVersion('2');
      await this.apiService.getDashboard();
      
      // Migration successful
      this.currentVersion = '2';
      return true;
    } catch (error) {
      // Migration failed, stay with V1
      this.apiService.setVersion('1');
      return false;
    }
  }

  shouldShowV2Features() {
    return this.currentVersion === '2';
  }
}
```

### Version-Aware Components

#### Server Status Component
```javascript
// src/components/ServerStatus.js
import React from 'react';
import { View, Text, StyleSheet } from 'react-native';

const ServerStatus = ({ server, apiVersion }) => {
  const isV2 = apiVersion === '2';

  return (
    <View style={styles.card}>
      <Text style={styles.name}>{server.name}</Text>
      <Text style={styles.status}>{server.last_status}</Text>
      
      {/* V1 fields */}
      <Text>CPU: {server.last_cpu_percent}%</Text>
      <Text>RAM: {server.last_ram_percent}%</Text>
      
      {/* V2 enhanced fields */}
      {isV2 && (
        <>
          <Text>Health: {server.health_score}/100</Text>
          <Text>Performance: {server.performance_rating}</Text>
          <Text>Uptime: {server.uptime_percentage}%</Text>
        </>
      )}
    </View>
  );
};
```

## Migration Guide

### From V1 to V2

#### 1. Update API Calls
```javascript
// Before (V1)
const response = await api.getDashboard();

// After (V2)
const response = await api.getEnhancedDashboard();
```

#### 2. Handle New Response Format
```javascript
// V1 response handling
const servers = response.servers;

// V2 response handling
const servers = response.servers;
const healthMetrics = response.health_metrics;
const performanceMetrics = response.performance_metrics;
```

#### 3. Update UI Components
```javascript
// Add version-aware rendering
{apiVersion === '2' && (
  <HealthMetrics data={response.health_metrics} />
)}
```

### Backward Compatibility

#### Feature Detection
```javascript
const hasHealthScoring = response.api_version === '2';
const hasTrends = response.trends !== undefined;

if (hasHealthScoring) {
  // Use V2 features
} else {
  // Use V1 fallback
}
```

#### Graceful Degradation
```javascript
const getServerHealth = (server) => {
  if (server.health_score !== undefined) {
    return server.health_score;
  }
  
  // Calculate approximate health from V1 data
  if (server.last_status === 'UP') {
    return 90;
  } else if (server.last_status === 'WARNING') {
    return 60;
  } else {
    return 30;
  }
};
```

## Version Headers

All API responses include version information headers:

```
API-Version: 2
API-Version-Status: beta
API-Supported-Versions: 1,2
API-Default-Version: 1
```

### Deprecated Versions
When a version is deprecated:

```
API-Version-Deprecated: true
API-Version-Sunset: 2026-12-31
API-Version-Migration-Guide: /api/v2/docs/migration-from-v1
API-Version-Warning: Enhanced features available in V2
```

## Testing Versioning

### Test Different Versions
```bash
# Test V1
curl -H "Accept: application/vnd.api+json;version=1" \
     http://localhost:8000/api/mobile/dashboard/

# Test V2
curl -H "Accept: application/vnd.api+json;version=2" \
     http://localhost:8000/api/mobile/dashboard/

# Test URL versioning
curl http://localhost:8000/api/v1/mobile/dashboard/
curl http://localhost:8000/api/v2/mobile/dashboard/
```

### Version Compatibility Test
```javascript
// Test version compatibility
const testVersionCompatibility = async () => {
  const versions = ['1', '2'];
  
  for (const version of versions) {
    try {
      apiService.setVersion(version);
      const response = await apiService.getDashboard();
      console.log(`Version ${version}: OK`);
    } catch (error) {
      console.log(`Version ${version}: Failed - ${error.message}`);
    }
  }
};
```

## Best Practices

### For Mobile Developers

1. **Always Check API Version**: Verify the API version before using new features
2. **Feature Detection**: Use feature detection rather than version detection
3. **Graceful Degradation**: Provide fallbacks for older API versions
4. **Version Migration**: Implement smooth migration paths
5. **Error Handling**: Handle version-specific errors appropriately

### For Server Developers

1. **Semantic Versioning**: Use semantic versioning for breaking changes
2. **Deprecation Timeline**: Provide clear deprecation timelines
3. **Migration Guides**: Create comprehensive migration guides
4. **Backward Compatibility**: Maintain backward compatibility when possible
5. **Version Testing**: Test all supported versions thoroughly

## Troubleshooting

### Common Issues

#### Version Not Detected
```bash
# Check response headers
curl -I http://localhost:8000/api/mobile/dashboard/

# Expected headers:
# API-Version: 1
# API-Supported-Versions: 1,2
```

#### Deprecated Version Warning
```bash
# Check deprecation headers
curl -I http://localhost:8000/api/v1/mobile/dashboard/

# Look for:
# API-Version-Deprecated: true
# API-Version-Sunset: 2026-12-31
```

#### Unsupported Version
```json
{
  "error": "unsupported_version",
  "message": "API version 3 is not supported",
  "supported_versions": ["1", "2"],
  "default_version": "1"
}
```

### Debugging Version Issues

1. **Check Headers**: Verify version headers in responses
2. **Test Different Methods**: Try different versioning methods
3. **Review Logs**: Check server logs for version detection issues
4. **Validate Format**: Ensure proper version format (numbers only)

This versioning system ensures that your mobile applications can continue working with existing API versions while taking advantage of new features in newer versions.
