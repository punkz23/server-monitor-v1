import 'package:flutter/foundation.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';

class DtrApiConfig {
  // Production API Configuration
  static const String _baseUrl = 'https://www.api.dailyoverland.com/dtr_api';
  static const String _apiKey = 'bd1a4793b63255f34f845a82a798e9160cc69274b9289f8abc1020b0e158dfaa';
  
  // Environment-specific configuration
  static String get baseUrl {
    if (kDebugMode) {
      // In debug mode, you might want to use a different endpoint
      return _baseUrl;
    }
    return _baseUrl;
  }
  
  static String get apiKey {
    if (kDebugMode) {
      // In debug mode, you might want to use a different key
      return _apiKey;
    }
    return _apiKey;
  }
  
  // Headers for DTR API requests
  static Map<String, String> get headers => {
    'Accept': 'application/json',
    'Content-Type': 'application/json',
    'API-KEY': apiKey,
  };
  
  // For security: Consider moving API key to secure storage
  static Future<String> getSecureApiKey() async {
    const storage = FlutterSecureStorage();
    final storedKey = await storage.read(key: 'dtr_api_key');
    return storedKey ?? apiKey;
  }
  
  static Future<void> setSecureApiKey(String key) async {
    const storage = FlutterSecureStorage();
    await storage.write(key: 'dtr_api_key', value: key);
  }
}
