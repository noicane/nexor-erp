import 'package:dio/dio.dart';
import 'package:shared_preferences/shared_preferences.dart';

import '../config.dart';

/// Singleton Dio client; auth token interceptor'i ekler.
///
/// Storage: SharedPreferences (web + native ayni davranis).
/// flutter_secure_storage web'de localStorage uzerinde tutarsiz davranistigi
/// icin tum platformlarda SharedPreferences kullaniyoruz. Token JWT, sunucu
/// tarafinda imzali ve expire'li - LAN icinde gizlilik kritik degil.
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
        final token = await getToken();
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
  Dio get dio => _dio;

  Future<SharedPreferences> get _prefs => SharedPreferences.getInstance();

  Future<void> setToken(String token) async {
    final p = await _prefs;
    await p.setString(TerminalConfig.tokenKey, token);
  }

  Future<String?> getToken() async {
    final p = await _prefs;
    return p.getString(TerminalConfig.tokenKey);
  }

  Future<void> clearToken() async {
    final p = await _prefs;
    await p.remove(TerminalConfig.tokenKey);
    await p.remove(TerminalConfig.userKey);
  }

  Future<void> setUser(Map<String, dynamic> user) async {
    final p = await _prefs;
    await p.setString(
      TerminalConfig.userKey,
      '${user['id'] ?? user['kullanici_id']}|${user['kullanici_adi']}|${user['ad_soyad']}',
    );
  }

  Future<Map<String, String>?> getUser() async {
    final p = await _prefs;
    final s = p.getString(TerminalConfig.userKey);
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
