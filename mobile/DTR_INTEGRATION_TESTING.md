# DTR Monitoring Integration - Testing Guide

## 🧪 Testing the Integration

### 1. API Configuration
Before testing, ensure you have:
- Valid API key for the DTR API
- Proper authentication credentials
- Network access to `https://www.api.dailyoverland.com/dtr_api`

### 2. Manual Testing Steps

#### Step 1: Verify API Connection
1. Open the server monitor app
2. Navigate to the Dashboard tab
3. Check the DTR Monitoring widget
4. Verify it shows data or appropriate error handling

#### Step 2: Test DTR Monitoring Screen
1. Tap on the DTR tab in bottom navigation
2. Verify the comprehensive DTR monitoring screen loads
3. Check all tabs: Overview, Performance, Devices, Locations, Security
4. Test refresh functionality

#### Step 3: Test Real-time Updates
1. Keep the app open on dashboard
2. Wait 2 minutes for automatic refresh
3. Verify DTR metrics update
4. Test manual refresh by tapping refresh icon

### 3. Expected Behavior

#### ✅ Successful Connection
- DTR metrics show real data
- Active users count updates
- Clock-in/out statistics display
- System health shows "System Healthy"
- Real-time updates every 2 minutes

#### ⚠️ API Unavailable
- Shows "DTR API Error" message
- Displays mock data with zeros
- System health shows "System Issues"
- Graceful degradation without app crash

#### 🔄 Loading States
- Shows loading spinner during data fetch
- Displays cached data during refresh
- Handles network interruptions gracefully

### 4. Troubleshooting

#### Common Issues
1. **API Key Missing**
   - Error: "401 Unauthorized"
   - Fix: Add proper API-KEY to headers

2. **Network Issues**
   - Error: "Network error"
   - Fix: Check internet connection and firewall

3. **CORS Issues**
   - Error: "CORS policy error"
   - Fix: Ensure DTR API allows your domain

4. **Token Issues**
   - Error: "401 Unauthorized" for DTR endpoints
   - Fix: Implement proper DTR authentication flow

### 5. Debug Information

#### Enable Debug Logging
Add these lines to your API client for debugging:
```dart
_dtrDio.interceptors.add(LogInterceptor(
  requestBody: true,
  responseBody: true,
  logPrint: (obj) => print('DTR API: $obj'),
));
```

#### Monitor Network Requests
Use Flutter DevTools or browser network tab to monitor:
- Request URLs
- Headers
- Response codes
- Response data

### 6. Performance Testing

#### Test Scenarios
1. **Slow Network**: Test with 3G/4G simulation
2. **API Latency**: Measure response times
3. **Large Data**: Test with many DTR logs
4. **Memory Usage**: Monitor app memory consumption

#### Expected Performance
- API calls should complete within 2-3 seconds
- UI should remain responsive during refresh
- Memory usage should stay stable

### 7. Production Deployment

#### Before Release
- [ ] Configure production API key
- [ ] Test with production DTR API
- [ ] Verify SSL certificate validation
- [ ] Test error handling scenarios
- [ ] Performance testing on target devices

#### Environment Configuration
```dart
// For development
const String _dtrApiBaseUrl = 'https://dev-api.dailyoverland.com/dtr_api';

// For production  
const String _dtrApiBaseUrl = 'https://www.api.dailyoverland.com/dtr_api';
```

## 📞 Support

If you encounter issues:
1. Check API key configuration
2. Verify network connectivity
3. Review DTR API documentation
4. Test with curl/Postman first
5. Check Flutter logs for detailed errors

## 🎯 Success Criteria

The integration is successful when:
- ✅ App builds without errors
- ✅ DTR metrics display on dashboard
- ✅ Real-time updates work correctly
- ✅ Error handling is graceful
- ✅ Performance is acceptable
- ✅ All DTR monitoring features function
