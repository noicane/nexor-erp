import 'package:dio/dio.dart';
import 'api_client.dart';

class AuthResult {
  AuthResult({
    required this.success,
    required this.message,
    this.kullaniciId,
    this.kullaniciAdi,
    this.adSoyad,
  });

  final bool success;
  final String message;
  final int? kullaniciId;
  final String? kullaniciAdi;
  final String? adSoyad;
}

class AuthService {
  AuthService(this._client);
  final ApiClient _client;

  Future<AuthResult> loginWithKart(String kartId) async {
    try {
      final r = await _client.dio.post(
        '/auth/kart',
        data: {'kart_id': kartId.trim()},
      );
      final data = r.data as Map<String, dynamic>;
      await _client.setToken(data['token']);
      await _client.setUser(data);
      return AuthResult(
        success: true,
        message: 'Giris basarili',
        kullaniciId: data['kullanici_id'],
        kullaniciAdi: data['kullanici_adi'],
        adSoyad: data['ad_soyad'],
      );
    } on DioException catch (e) {
      return AuthResult(success: false, message: _errMessage(e));
    }
  }

  Future<AuthResult> loginWithPin(String kullaniciAdi, String pin) async {
    try {
      final r = await _client.dio.post(
        '/auth/pin',
        data: {'kullanici_adi': kullaniciAdi.trim(), 'pin': pin},
      );
      final data = r.data as Map<String, dynamic>;
      await _client.setToken(data['token']);
      await _client.setUser(data);
      return AuthResult(
        success: true,
        message: 'Giris basarili',
        kullaniciId: data['kullanici_id'],
        kullaniciAdi: data['kullanici_adi'],
        adSoyad: data['ad_soyad'],
      );
    } on DioException catch (e) {
      return AuthResult(success: false, message: _errMessage(e));
    }
  }

  Future<bool> hasValidSession() async {
    final tok = await _client.getToken();
    if (tok == null || tok.isEmpty) return false;
    try {
      await _client.dio.get('/auth/me');
      return true;
    } catch (_) {
      return false;
    }
  }

  Future<void> logout() async {
    await _client.clearToken();
  }

  String _errMessage(DioException e) {
    if (e.response != null) {
      final body = e.response?.data;
      if (body is Map && body['detail'] is String) {
        return body['detail'];
      }
      return 'Sunucu hatasi (${e.response?.statusCode})';
    }
    if (e.type == DioExceptionType.connectionTimeout ||
        e.type == DioExceptionType.receiveTimeout) {
      return 'Sunucuya ulasilamadi (timeout)';
    }
    return 'Baglanti hatasi: ${e.message ?? ''}';
  }
}
