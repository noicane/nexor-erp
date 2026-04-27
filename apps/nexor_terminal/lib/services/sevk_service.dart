import 'package:dio/dio.dart';
import '../models/irsaliye.dart';
import 'api_client.dart';

class SevkService {
  SevkService(this._client);
  final ApiClient _client;

  Future<List<IrsaliyeOzet>> acikIrsaliyeler({String? arama}) async {
    final r = await _client.dio.get(
      '/sevk/acik',
      queryParameters: arama != null && arama.isNotEmpty ? {'arama': arama} : null,
    );
    final list = (r.data as List).cast<Map<String, dynamic>>();
    return list.map(IrsaliyeOzet.fromJson).toList();
  }

  Future<IrsaliyeDetay> detay(int id) async {
    final r = await _client.dio.get('/sevk/$id');
    return IrsaliyeDetay.fromJson(r.data as Map<String, dynamic>);
  }

  Future<LotTaraSonuc> lotTara(int id, String lotNo) async {
    final r = await _client.dio.post(
      '/sevk/$id/lot-tara',
      data: {'lot_no': lotNo},
    );
    return LotTaraSonuc.fromJson(r.data as Map<String, dynamic>);
  }

  /// Yukleme tamam onayi. Eksik lot varsa [zorla] ile yine de tamamlanabilir.
  Future<YuklenmeSonucu> yukle(int id, {bool zorla = false}) async {
    final r = await _client.dio.post(
      '/sevk/$id/yukle',
      queryParameters: {'zorla': zorla.toString()},
    );
    return YuklenmeSonucu.fromJson(r.data as Map<String, dynamic>);
  }

  String errorMessage(DioException e) {
    if (e.response?.data is Map && e.response!.data['detail'] is String) {
      return e.response!.data['detail'];
    }
    return e.message ?? 'Bilinmeyen hata';
  }
}
