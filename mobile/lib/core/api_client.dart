import 'package:dio/dio.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';

class ApiClient {
  static const String baseUrl = 'http://192.168.253.31:8001/api';
  final Dio _dio = Dio(BaseOptions(baseUrl: baseUrl));
  final FlutterSecureStorage _storage = const FlutterSecureStorage();

  ApiClient() {
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

  Dio get dio => _dio;

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
