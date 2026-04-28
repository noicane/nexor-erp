import 'package:flutter/foundation.dart' show kIsWeb;

/// NEXOR Terminal - Konfigurasyon
///
/// API_BASE_URL kaynak sirasi:
///   1. dart-define ile gecirilen API_BASE_URL (CI build'de set edilir)
///   2. Web build: tarayici origin'i (Uri.base.origin) - same-origin API
///   3. Native build: hard-coded LAN IP (http://192.168.10.66:8002)
class TerminalConfig {
  static const String _apiBaseUrlFromEnv = String.fromEnvironment(
    'API_BASE_URL',
    defaultValue: '',
  );

  static String get apiBaseUrl {
    if (_apiBaseUrlFromEnv.isNotEmpty) return _apiBaseUrlFromEnv;
    if (kIsWeb) return Uri.base.origin;     // http(s)://host:port
    return 'http://192.168.10.66:8002';      // EDA51 default
  }

  /// Token storage anahtari (web'de localStorage, native'de KeyStore)
  static const String tokenKey = 'nexor_terminal_token';
  static const String userKey = 'nexor_terminal_user';

  /// API timeout
  static const Duration apiTimeout = Duration(seconds: 12);

  /// Brand renkler (NEXOR uyumlu)
  static const int primaryColor = 0xFF0EA5E9;
  static const int dangerColor = 0xFFEF4444;
  static const int successColor = 0xFF10B981;
  static const int warningColor = 0xFFF59E0B;
}
