/// NEXOR Terminal - Konfigurasyon
///
/// Production deployment'ta bu degerler env'den ya da derleme zamani
/// `--dart-define` ile gecirilmeli.
class TerminalConfig {
  /// FastAPI sunucusu (NEXOR ile ayni makine, varsayilan port 8002)
  static const String apiBaseUrl = String.fromEnvironment(
    'API_BASE_URL',
    defaultValue: 'http://192.168.10.66:8002',
  );

  /// Token storage anahtari
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
