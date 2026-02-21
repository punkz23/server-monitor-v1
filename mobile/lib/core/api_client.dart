import 'package:dio/dio.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'package:shared_preferences/shared_preferences.dart';

class ApiClient {
  static const String _baseUrlKey = 'api_base_url';
  static const String _defaultBaseUrl = 'http://192.168.253.31:8001/api';

  late Dio _dio;
  late String _baseUrl;
  final FlutterSecureStorage _storage = const FlutterSecureStorage();

  ApiClient._internal(this._baseUrl) {
    _dio = Dio(BaseOptions(baseUrl: _baseUrl));
    _dio.interceptors.add(InterceptorsWrapper(
      onRequest: (options, handler) async {
        final token = await _storage.read(key: 'auth_token');
        if (token != null) {
          options.headers['Authorization'] = 'Token $token';
        }
        return handler.next(options);
      },
      onError: (DioException e, handler) {
        if (e.response?.statusCode == 401) {
          // Handle logout/token expiry here
        }
        return handler.next(e);
      },
    ));
  }

  static Future<ApiClient> create() async {
    final prefs = await SharedPreferences.getInstance();
    final baseUrl = prefs.getString(_baseUrlKey) ?? _defaultBaseUrl;
    return ApiClient._internal(baseUrl);
  }

  Dio get dio => _dio;
  String get baseUrl => _baseUrl;

  Future<void> setBaseUrl(String newUrl) async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.setString(_baseUrlKey, newUrl);
    _baseUrl = newUrl;
    _dio.options.baseUrl = _baseUrl; // Update the base URL for the existing Dio instance
  }

  Future<void> saveToken(String token) async {
    await _storage.write(key: 'auth_token', value: token);
  }

  Future<void> deleteToken() async {
    await _storage.delete(key: 'auth_token');
  }

  Future<bool> hasToken() async {
    final token = await _storage.read(key: 'auth_token');
    return token != null;
  }
}
