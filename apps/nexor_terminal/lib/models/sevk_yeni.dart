/// NEXOR Terminal - Yeni Sevkiyat modelleri
///
/// Backend: apps/terminal_api/routers/sevk_yeni_router.py

class AracBilgileri {
  final List<String> tasiyicilar;
  final List<PlakaTanim> plakalar;
  final List<SoforTanim> soforler;

  const AracBilgileri({
    this.tasiyicilar = const [],
    this.plakalar = const [],
    this.soforler = const [],
  });

  factory AracBilgileri.fromJson(Map<String, dynamic> j) => AracBilgileri(
        tasiyicilar: (j['tasiyicilar'] as List? ?? []).cast<String>(),
        plakalar: (j['plakalar'] as List? ?? [])
            .map((e) => PlakaTanim.fromJson(e as Map<String, dynamic>))
            .toList(),
        soforler: (j['soforler'] as List? ?? [])
            .map((e) => SoforTanim.fromJson(e as Map<String, dynamic>))
            .toList(),
      );
}

class PlakaTanim {
  final String plaka;
  final String detay;
  PlakaTanim({required this.plaka, this.detay = ''});
  factory PlakaTanim.fromJson(Map<String, dynamic> j) => PlakaTanim(
        plaka: j['plaka'] ?? '',
        detay: j['detay'] ?? '',
      );
  String get goruntu => detay.isEmpty ? plaka : '$plaka ($detay)';
}

class SoforTanim {
  final String ad;
  final String telefon;
  SoforTanim({required this.ad, this.telefon = ''});
  factory SoforTanim.fromJson(Map<String, dynamic> j) => SoforTanim(
        ad: j['ad'] ?? '',
        telefon: j['telefon'] ?? '',
      );
  String get goruntu => telefon.isEmpty ? ad : '$ad ($telefon)';
}

/// Sevke hazır bir lot (hem listeden hem barkod doğrulamadan gelir)
class HazirUrun {
  final int stokBakiyeId;
  final String lotNo;
  final String musteri;
  final String stokKodu;
  final String stokAdi;
  final double miktar;
  final int? cariId;
  final int? isEmriId;
  final int gun;

  const HazirUrun({
    required this.stokBakiyeId,
    required this.lotNo,
    required this.musteri,
    this.stokKodu = '',
    this.stokAdi = '',
    required this.miktar,
    this.cariId,
    this.isEmriId,
    this.gun = 0,
  });

  factory HazirUrun.fromJson(Map<String, dynamic> j) => HazirUrun(
        stokBakiyeId: (j['stok_bakiye_id'] as num).toInt(),
        lotNo: j['lot_no'] ?? '',
        musteri: j['musteri'] ?? 'Tanimsiz',
        stokKodu: j['stok_kodu'] ?? '',
        stokAdi: j['stok_adi'] ?? '',
        miktar: (j['miktar'] as num? ?? 0).toDouble(),
        cariId: (j['cari_id'] as num?)?.toInt(),
        isEmriId: (j['is_emri_id'] as num?)?.toInt(),
        gun: (j['gun'] as num? ?? 0).toInt(),
      );

  /// Backend'in beklediği SevkLotInput payload'ı (sevkiyat oluştururken)
  Map<String, dynamic> toSevkLotInput() => {
        'lot_no': lotNo,
        'miktar': miktar,
        'cari_id': cariId,
        'is_emri_id': isEmriId,
        'stok_kodu': stokKodu,
        'musteri': musteri,
      };
}

class LotDogrulaSonuc {
  final bool bulundu;
  final String mesaj;
  final HazirUrun? urun;

  const LotDogrulaSonuc({
    required this.bulundu,
    required this.mesaj,
    this.urun,
  });

  factory LotDogrulaSonuc.fromJson(Map<String, dynamic> j) => LotDogrulaSonuc(
        bulundu: j['bulundu'] == true,
        mesaj: j['mesaj'] ?? '',
        urun: j['urun'] == null
            ? null
            : HazirUrun.fromJson(j['urun'] as Map<String, dynamic>),
      );
}

class SevkOlusturItem {
  final int irsaliyeId;
  final String irsaliyeNo;
  final int? cariId;
  final String musteri;
  final int lotSayisi;
  final double toplamMiktar;

  const SevkOlusturItem({
    required this.irsaliyeId,
    required this.irsaliyeNo,
    this.cariId,
    required this.musteri,
    required this.lotSayisi,
    required this.toplamMiktar,
  });

  factory SevkOlusturItem.fromJson(Map<String, dynamic> j) => SevkOlusturItem(
        irsaliyeId: (j['irsaliye_id'] as num).toInt(),
        irsaliyeNo: j['irsaliye_no'] ?? '',
        cariId: (j['cari_id'] as num?)?.toInt(),
        musteri: j['musteri'] ?? '',
        lotSayisi: (j['lot_sayisi'] as num? ?? 0).toInt(),
        toplamMiktar: (j['toplam_miktar'] as num? ?? 0).toDouble(),
      );
}

class SevkOlusturSonuc {
  final List<SevkOlusturItem> olusturulan;
  final List<Map<String, dynamic>> basarisiz;

  const SevkOlusturSonuc({
    this.olusturulan = const [],
    this.basarisiz = const [],
  });

  factory SevkOlusturSonuc.fromJson(Map<String, dynamic> j) => SevkOlusturSonuc(
        olusturulan: (j['olusturulan'] as List? ?? [])
            .map((e) => SevkOlusturItem.fromJson(e as Map<String, dynamic>))
            .toList(),
        basarisiz: (j['basarisiz'] as List? ?? [])
            .map((e) => (e as Map).cast<String, dynamic>())
            .toList(),
      );
}
