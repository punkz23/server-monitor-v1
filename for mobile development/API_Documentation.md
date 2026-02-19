# Django REST Framework API Documentation

## Overview
This project now includes Django REST Framework (DRF) APIs for mobile development. The API endpoints are organized into two main categories:

1. **Standard REST APIs** - Full CRUD operations using ViewSets
2. **Mobile APIs** - Optimized endpoints for mobile applications

## Base URL
All API endpoints are prefixed with `/api/`

## Authentication
The API supports two authentication methods:
- Session Authentication (for web interface)
- Token Authentication (for mobile apps)

### Getting an Auth Token
```
POST /api/auth/token/
Content-Type: application/json

{
    "username": "your_username",
    "password": "your_password"
}
```

Response:
```json
{
    "token": "your_auth_token_here"
}
```

Use the token in subsequent requests:
```
Authorization: Token your_auth_token_here
```

## Standard REST Endpoints

### Servers
- `GET /api/servers/` - List all servers
- `POST /api/servers/` - Create new server
- `GET /api/servers/{id}/` - Get server details
- `PUT /api/servers/{id}/` - Update server
- `DELETE /api/servers/{id}/` - Delete server

**Query Parameters:**
- `enabled` - Filter by enabled status (true/false)
- `server_type` - Filter by server type

### Network Devices
- `GET /api/network-devices/` - List all network devices
- `POST /api/network-devices/` - Create new network device
- `GET /api/network-devices/{id}/` - Get device details
- `PUT /api/network-devices/{id}/` - Update device
- `DELETE /api/network-devices/{id}/` - Delete device

**Query Parameters:**
- `device_type` - Filter by device type
- `is_active` - Filter by active status (true/false)

### Alerts
- `GET /api/alerts/` - List all alerts (read-only)
- `GET /api/alerts/{id}/` - Get alert details

**Query Parameters:**
- `server_id` - Filter by server ID
- `severity` - Filter by severity level

### ISP Connections
- `GET /api/isp-connections/` - List all ISP connections
- `POST /api/isp-connections/` - Create new ISP connection
- `GET /api/isp-connections/{id}/` - Get connection details
- `PUT /api/isp-connections/{id}/` - Update connection
- `DELETE /api/isp-connections/{id}/` - Delete connection

### CCTV Devices
- `GET /api/cctv-devices/` - List all CCTV devices
- `POST /api/cctv-devices/` - Create new CCTV device
- `GET /api/cctv-devices/{id}/` - Get device details
- `PUT /api/cctv-devices/{id}/` - Update device
- `DELETE /api/cctv-devices/{id}/` - Delete device

## Mobile API Endpoints

### Dashboard Summary
```
GET /api/mobile/dashboard/
```
Returns summary statistics for the mobile dashboard.

**Response:**
```json
{
    "servers": {
        "total": 10,
        "enabled": 8,
        "online": 6,
        "offline": 2
    },
    "network_devices": {
        "total": 25,
        "active": 20,
        "inactive": 5
    },
    "alerts": {
        "recent_24h": 5,
        "critical": 2
    },
    "timestamp": "2026-01-02T14:30:00Z"
}
```

### Server Status
```
GET /api/mobile/server-status/
```
Get status summary of all enabled servers.

**Response:**
```json
{
    "servers": [
        {
            "id": 1,
            "name": "Web Server 1",
            "server_type": "WEB",
            "server_type_display": "Web Server",
            "ip_address": "192.168.1.10",
            "last_status": "UP",
            "last_status_display": "Up",
            "last_cpu_percent": 45.2,
            "last_ram_percent": 67.8,
            "last_latency_ms": 12,
            "last_checked": "2026-01-02T14:25:00Z"
        }
    ],
    "timestamp": "2026-01-02T14:30:00Z"
}
```

### Network Devices
```
GET /api/mobile/network-devices/
```
Get summary of active network devices.

**Response:**
```json
{
    "devices": [
        {
            "id": 1,
            "name": "Sophos Firewall",
            "device_type": "FIREWALL",
            "device_type_display": "Firewall",
            "ip_address": "192.168.253.2",
            "mac_address": "00:11:22:33:44:55",
            "vendor": "Sophos",
            "is_active": true,
            "last_seen": "2026-01-02T14:30:00Z"
        }
    ],
    "timestamp": "2026-01-02T14:30:00Z"
}
```

### Server Detail
```
GET /api/mobile/server/{server_id}/
```
Get detailed information about a specific server including recent metrics.

### Alerts
```
GET /api/mobile/alerts/
```
Get recent alerts with filtering options.

**Query Parameters:**
- `limit` - Number of alerts to return (default: 50, max: 200)
- `server_id` - Filter by server ID
- `severity` - Filter by severity level

### Metrics History
```
GET /api/mobile/server/{server_id}/metrics/
```
Get historical metrics for a server.

**Query Parameters:**
- `range` - Time range: "30" (last 30 points), "24h" (last 24 hours), "7d" (last 7 days)

### Agent Data Ingestion
```
POST /api/mobile/agent/ingest/
```
Endpoint for mobile agents to submit monitoring data.

**Request Body:**
```json
{
    "server_id": 1,
    "cpu": {
        "percent": 45.2
    },
    "memory": {
        "percent": 67.8
    },
    "load": {
        "1": 1.2,
        "5": 1.1,
        "15": 0.9
    }
}
```

## Mobile Development Files

All mobile development related files are located in the `for mobile development` folder:

- API documentation
- Mobile app examples
- Test scripts
- Configuration files

## Error Handling

All API endpoints return consistent error responses:

```json
{
    "error": "error_description",
    "detail": "detailed_error_message"
}
```

Common HTTP status codes:
- `200` - Success
- `201` - Created
- `400` - Bad Request
- `401` - Unauthorized
- `403` - Forbidden
- `404` - Not Found
- `500` - Server Error

## Pagination

List endpoints support pagination with 20 items per page by default.

**Response format:**
```json
{
    "count": 100,
    "next": "http://localhost:8000/api/servers/?page=2",
    "previous": null,
    "results": [...]
}
```

## Testing the API

You can test the API using tools like:
- Postman
- curl
- Django REST Framework's built-in API browser (when authenticated)

Example curl command:
```bash
curl -H "Authorization: Token your_token_here" \
     http://localhost:8000/api/mobile/server-status/
```
