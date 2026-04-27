/// Backend `IrsaliyeOzet` modeline karsilik gelen Dart modeli.
class IrsaliyeOzet {
  IrsaliyeOzet({
    required this.id,
    required this.irsaliyeNo,
    required this.durum,
    this.tarih,
    this.cariId,
    this.cariAdi,
    this.tasiyiciFirma = '',
    this.aracPlaka = '',
    this.soforAdi = '',
    this.satirSayisi = 0,
    this.okutulanLotSayisi = 0,
  });

  final int id;
  final String irsaliyeNo;
  final String durum;
  final String? tarih;
  final int? cariId;
  final String? cariAdi;
  final String tasiyiciFirma;
  final String aracPlaka;
  final String soforAdi;
  final int satirSayisi;
  final int okutulanLotSayisi;

  factory IrsaliyeOzet.fromJson(Map<String, dynamic> j) => IrsaliyeOzet(
        id: j['id'] as int,
        irsaliyeNo: j['irsaliye_no'] as String,
        durum: j['durum'] as String,
        tarih: j['tarih'] as String?,
        cariId: j['cari_id'] as int?,
        cariAdi: j['cari_adi'] as String?,
        tasiyiciFirma: (j['tasiyici_firma'] ?? '') as String,
        aracPlaka: (j['arac_plaka'] ?? '') as String,
        soforAdi: (j['sofor_adi'] ?? '') as String,
        satirSayisi: (j['satir_sayisi'] ?? 0) as int,
        okutulanLotSayisi: (j['okutulan_lot_sayisi'] ?? 0) as int,
      );
}

class SatirDetay {
  SatirDetay({
    required this.id,
    required this.satirNo,
    required this.miktar,
    required this.lotNo,
    required this.durum,
    this.urunId,
    this.urunKodu = '',
    this.urunAdi = '',
    this.koliAdedi = 0,
  });

  final int id;
  final int satirNo;
  final double miktar;
  final String lotNo;
  final String durum; // BEKLIYOR, OKUTULDU, EKSIK, FAZLA
  final int? urunId;
  final String urunKodu;
  final String urunAdi;
  final int koliAdedi;

  factory SatirDetay.fromJson(Map<String, dynamic> j) => SatirDetay(
        id: j['id'] as int,
        satirNo: (j['satir_no'] ?? 0) as int,
        miktar: ((j['miktar'] ?? 0) as num).toDouble(),
        lotNo: (j['lot_no'] ?? '') as String,
        durum: (j['durum'] ?? 'BEKLIYOR') as String,
        urunId: j['urun_id'] as int?,
        urunKodu: (j['urun_kodu'] ?? '') as String,
        urunAdi: (j['urun_adi'] ?? '') as String,
        koliAdedi: (j['koli_adedi'] ?? 0) as int,
      );
}

class IrsaliyeDetay {
  IrsaliyeDetay({required this.ozet, required this.satirlar});
  final IrsaliyeOzet ozet;
  final List<SatirDetay> satirlar;

  factory IrsaliyeDetay.fromJson(Map<String, dynamic> j) => IrsaliyeDetay(
        ozet: IrsaliyeOzet.fromJson(j['ozet'] as Map<String, dynamic>),
        satirlar: (j['satirlar'] as List)
            .cast<Map<String, dynamic>>()
            .map(SatirDetay.fromJson)
            .toList(),
      );
}

class LotTaraSonuc {
  LotTaraSonuc({
    required this.lotNo,
    required this.bulundu,
    required this.mesaj,
    this.satirId,
    this.urunKodu,
    this.urunAdi,
    this.miktar,
    this.oncedenOkutulmus = false,
  });

  final String lotNo;
  final bool bulundu;
  final String mesaj;
  final int? satirId;
  final String? urunKodu;
  final String? urunAdi;
  final double? miktar;
  final bool oncedenOkutulmus;

  factory LotTaraSonuc.fromJson(Map<String, dynamic> j) => LotTaraSonuc(
        lotNo: (j['lot_no'] ?? '') as String,
        bulundu: (j['bulundu'] ?? false) as bool,
        mesaj: (j['mesaj'] ?? '') as String,
        satirId: j['satir_id'] as int?,
        urunKodu: j['urun_kodu'] as String?,
        urunAdi: j['urun_adi'] as String?,
        miktar: j['miktar'] != null ? ((j['miktar'] as num).toDouble()) : null,
        oncedenOkutulmus: (j['onceden_okutulmus'] ?? false) as bool,
      );
}

class YuklenmeSonucu {
  YuklenmeSonucu({
    required this.irsaliyeId,
    required this.yeniDurum,
    required this.eksikSatirSayisi,
    required this.mesaj,
  });

  final int irsaliyeId;
  final String yeniDurum;
  final int eksikSatirSayisi;
  final String mesaj;

  factory YuklenmeSonucu.fromJson(Map<String, dynamic> j) => YuklenmeSonucu(
        irsaliyeId: j['irsaliye_id'] as int,
        yeniDurum: (j['yeni_durum'] ?? '') as String,
        eksikSatirSayisi: (j['eksik_satir_sayisi'] ?? 0) as int,
        mesaj: (j['mesaj'] ?? '') as String,
      );
}
