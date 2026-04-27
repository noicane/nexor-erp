import 'package:dio/dio.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';

import '../config.dart';

/// Singleton Dio client; auth token interceptor'i ekler.
class ApiClient {
  ApiClient._() {
    _dio = Dio(BaseOptions(
      baseUrl: TerminalConfig.apiBaseUrl,
      connectTimeout: TerminalConfig.apiTimeout,
      receiveTimeout: TerminalConfig.apiTimeout,
      sendTimeout: TerminalConfig.apiTimeout,
      contentType: 'application/json',
    ));

    _dio.interceptors.add(InterceptorsWrapper(
      onRequest: (options, handler) async {
        final token = await _storage.read(key: TerminalConfig.tokenKey);
        if (token != null && token.isNotEmpty) {
          options.headers['Authorization'] = 'Bearer $token';
        }
        handler.next(options);
      },
      onError: (e, handler) {
        handler.next(e);
      },
    ));
  }

  static final ApiClient _instance = ApiClient._();
  static ApiClient get instance => _instance;

  late final Dio _dio;
  final _storage = const FlutterSecureStorage();

  Dio get dio => _dio;

  Future<void> setToken(String token) async {
    await _storage.write(key: TerminalConfig.tokenKey, value: token);
  }

  Future<String?> getToken() async {
    return _storage.read(key: TerminalConfig.tokenKey);
  }

  Future<void> clearToken() async {
    await _storage.delete(key: TerminalConfig.tokenKey);
    await _storage.delete(key: TerminalConfig.userKey);
  }

  Future<void> setUser(Map<String, dynamic> user) async {
    await _storage.write(
      key: TerminalConfig.userKey,
      value: '${user['id']}|${user['kullanici_adi']}|${user['ad_soyad']}',
    );
  }

  Future<Map<String, String>?> getUser() async {
    final s = await _storage.read(key: TerminalConfig.userKey);
    if (s == null) return null;
    final parts = s.split('|');
    if (parts.length != 3) return null;
    return {
      'id': parts[0],
      'kullanici_adi': parts[1],
      'ad_soyad': parts[2],
    };
  }
}
