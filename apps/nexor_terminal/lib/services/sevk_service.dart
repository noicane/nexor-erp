import 'package:dio/dio.dart';
import '../models/sevk_yeni.dart';
import 'api_client.dart';

class SevkService {
  SevkService(this._client);
  final ApiClient _client;

  /// Taşıyıcı/plaka/şoför dropdownları
  Future<AracBilgileri> aracBilgileri() async {
    final r = await _client.dio.get('/sevk-yeni/arac-bilgileri');
    return AracBilgileri.fromJson(r.data as Map<String, dynamic>);
  }

  /// Sevke hazır lot listesi (filtre opsiyonel)
  Future<List<HazirUrun>> hazirUrunler({String? arama}) async {
    final r = await _client.dio.get(
      '/sevk-yeni/hazir-urunler',
      queryParameters: arama != null && arama.isNotEmpty ? {'arama': arama} : null,
    );
    final list = (r.data as List).cast<Map<String, dynamic>>();
    return list.map(HazirUrun.fromJson).toList();
  }

  /// Tek lot bilgisini doğrula (barkod okuma)
  Future<LotDogrulaSonuc> lotDogrula(String lotNo) async {
    final r = await _client.dio.post(
      '/sevk-yeni/lot-dogrula',
      data: {'lot_no': lotNo},
    );
    return LotDogrulaSonuc.fromJson(r.data as Map<String, dynamic>);
  }

  /// Sevkiyat oluştur — backend cari'ye göre gruplar, her grup için ayrı irsaliye
  Future<SevkOlusturSonuc> olustur({
    String tasiyici = '',
    String plaka = '',
    String sofor = '',
    String notlar = '',
    required List<HazirUrun> lotlar,
  }) async {
    final r = await _client.dio.post(
      '/sevk-yeni/olustur',
      data: {
        'tasiyici': tasiyici,
        'plaka': plaka,
        'sofor': sofor,
        'notlar': notlar,
        'lotlar': lotlar.map((l) => l.toSevkLotInput()).toList(),
      },
    );
    return SevkOlusturSonuc.fromJson(r.data as Map<String, dynamic>);
  }

  String errorMessage(DioException e) {
    if (e.response?.data is Map && e.response!.data['detail'] is String) {
      return e.response!.data['detail'];
    }
    return e.message ?? 'Bilinmeyen hata';
  }
}
