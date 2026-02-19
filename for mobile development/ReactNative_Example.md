# React Native Mobile App Example

This folder contains example code for a React Native mobile app that consumes the Django REST Framework API.

## Features

- Server monitoring dashboard
- Real-time server status
- Alert management
- Network device overview
- Authentication with token-based auth

## API Integration

The app connects to the Django API at `/api/mobile/` endpoints.

### Setup

1. Install dependencies:
```bash
npm install
# or
yarn install
```

2. Configure API URL in `src/config/api.js`:
```javascript
export const API_BASE_URL = 'http://your-server-url:8000/api';
```

3. Run the app:
```bash
npx react-native run-android
# or
npx react-native run-ios
```

## Project Structure

```
react-native-app/
├── src/
│   ├── components/
│   │   ├── ServerCard.js
│   │   ├── AlertItem.js
│   │   └── DeviceCard.js
│   ├── screens/
│   │   ├── Dashboard.js
│   │   ├── Servers.js
│   │   ├── Alerts.js
│   │   └── Settings.js
│   ├── services/
│   │   └── api.js
│   ├── config/
│   │   └── api.js
│   └── utils/
│       └── auth.js
├── App.js
└── package.json
```

## Authentication

The app uses token-based authentication. Tokens are stored securely on the device and automatically included in API requests.

## Key Screens

### Dashboard
- Shows server status overview
- Displays recent alerts
- Network device summary

### Servers
- List of all servers with status
- Detailed server information
- Real-time metrics

### Alerts
- Recent alerts list
- Alert filtering
- Alert details

## API Service Example

```javascript
// src/services/api.js
import { API_BASE_URL } from '../config/api';

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

  async getDashboardSummary() {
    return this.request('/mobile/dashboard/');
  }

  async getServerStatus() {
    return this.request('/mobile/server-status/');
  }

  async getAlerts(params = {}) {
    const query = new URLSearchParams(params).toString();
    return this.request(`/mobile/alerts/?${query}`);
  }

  async getServerDetail(serverId) {
    return this.request(`/mobile/server/${serverId}/`);
  }
}

export default new APIService();
```

## Usage Examples

### Fetching Server Status
```javascript
import APIService from '../services/api';

const loadServerStatus = async () => {
  try {
    const data = await APIService.getServerStatus();
    setServers(data.servers);
  } catch (error) {
    console.error('Failed to load server status:', error);
  }
};
```

### Authentication
```javascript
const login = async (username, password) => {
  try {
    const response = await fetch(`${API_BASE_URL}/auth/token/`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ username, password }),
    });
    
    const data = await response.json();
    APIService.setToken(data.token);
    await SecureStore.setItemAsync('auth_token', data.token);
    
    return true;
  } catch (error) {
    console.error('Login failed:', error);
    return false;
  }
};
```

## Components

### ServerCard Component
```javascript
import React from 'react';
import { View, Text, StyleSheet } from 'react-native';

const ServerCard = ({ server }) => {
  const statusColor = server.last_status === 'UP' ? '#4CAF50' : '#F44336';
  
  return (
    <View style={styles.card}>
      <View style={styles.header}>
        <Text style={styles.name}>{server.name}</Text>
        <View style={[styles.statusIndicator, { backgroundColor: statusColor }]} />
      </View>
      
      <Text style={styles.type}>{server.server_type_display}</Text>
      <Text style={styles.ip}>{server.ip_address}</Text>
      
      <View style={styles.metrics}>
        <Text style={styles.metric}>CPU: {server.last_cpu_percent}%</Text>
        <Text style={styles.metric}>RAM: {server.last_ram_percent}%</Text>
      </View>
    </View>
  );
};

const styles = StyleSheet.create({
  card: {
    backgroundColor: 'white',
    padding: 16,
    marginVertical: 8,
    marginHorizontal: 16,
    borderRadius: 8,
    elevation: 2,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
  },
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 8,
  },
  name: {
    fontSize: 18,
    fontWeight: 'bold',
  },
  statusIndicator: {
    width: 12,
    height: 12,
    borderRadius: 6,
  },
  type: {
    fontSize: 14,
    color: '#666',
    marginBottom: 4,
  },
  ip: {
    fontSize: 12,
    color: '#888',
    marginBottom: 8,
  },
  metrics: {
    flexDirection: 'row',
    justifyContent: 'space-between',
  },
  metric: {
    fontSize: 12,
    color: '#333',
  },
});

export default ServerCard;
```

## Notes

- This is example code and should be adapted for production use
- Add proper error handling and loading states
- Implement offline support for better user experience
- Add unit tests for API services
- Consider using Redux or Context API for state management
