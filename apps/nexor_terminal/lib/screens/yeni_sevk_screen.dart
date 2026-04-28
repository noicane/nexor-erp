import 'dart:async';
import 'package:dio/dio.dart';
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';

import '../config.dart';
import '../models/sevk_yeni.dart';
import '../services/api_client.dart';
import '../services/auth_service.dart';
import '../services/scanner_service.dart';
import '../services/sevk_service.dart';
import 'login_screen.dart';

/// Yeni Sevkiyat ekranı (desktop modules/sevkiyat/sevk_yeni.py karşılığı)
///
/// Akış:
///   1. Üst: Araç bilgileri (taşıyıcı/plaka/şoför/not) - daraltılabilir
///   2. Orta: Barkod input (autofocus, Honeywell scanner intent)
///   3. Sevke Hazır Ürünler listesi (filtreli)
///   4. Okutulan Paketler listesi
///   5. Alt: "Sevkiyat Oluştur" butonu
class YeniSevkScreen extends StatefulWidget {
  const YeniSevkScreen({super.key});
  @override
  State<YeniSevkScreen> createState() => _YeniSevkScreenState();
}

class _YeniSevkScreenState extends State<YeniSevkScreen> {
  late final SevkService _sevk;
  late final AuthService _auth;
  StreamSubscription<String>? _scanSub;

  final _barkodCtl = TextEditingController();
  final _barkodFocus = FocusNode();
  final _aramaCtl = TextEditingController();
  final _notCtl = TextEditingController();

  AracBilgileri? _arac;
  String? _tasiyici;
  String? _plaka;
  String? _sofor;
  bool _aracExpanded = false;

  List<HazirUrun> _hazir = [];
  String _aramaText = '';
  final List<HazirUrun> _okutulanlar = [];

  bool _busy = false;
  String? _sonMesaj;
  Color _sonMesajRenk = Colors.greenAccent;

  @override
  void initState() {
    super.initState();
    _sevk = SevkService(ApiClient.instance);
    _auth = AuthService(ApiClient.instance);

    // Honeywell scanner barkod stream'i
    _scanSub = ScannerService.scans.listen((code) {
      if (!mounted) return;
      _barkodCtl.text = code.trim();
      _barkodOkut();
    });

    _yukle();

    // Barkoda autofocus
    WidgetsBinding.instance.addPostFrameCallback((_) {
      _barkodFocus.requestFocus();
    });
  }

  @override
  void dispose() {
    _scanSub?.cancel();
    _barkodCtl.dispose();
    _barkodFocus.dispose();
    _aramaCtl.dispose();
    _notCtl.dispose();
    super.dispose();
  }

  Future<void> _yukle() async {
    setState(() => _busy = true);
    try {
      final results = await Future.wait([
        _sevk.aracBilgileri(),
        _sevk.hazirUrunler(),
      ]);
      if (!mounted) return;
      setState(() {
        _arac = results[0] as AracBilgileri;
        _hazir = results[1] as List<HazirUrun>;
      });
    } on DioException catch (e) {
      _setMesaj(_sevk.errorMessage(e), hata: true);
    } finally {
      if (mounted) setState(() => _busy = false);
    }
  }

  Future<void> _hazirYenile() async {
    try {
      final list = await _sevk.hazirUrunler(arama: _aramaText);
      if (!mounted) return;
      setState(() => _hazir = list);
    } on DioException catch (e) {
      _setMesaj(_sevk.errorMessage(e), hata: true);
    }
  }

  Future<void> _barkodOkut() async {
    final lot = _barkodCtl.text.trim();
    if (lot.isEmpty) return;

    try {
      // Backend lot'u normalize edip (-SEV/-SEVK strip) stok_bakiye'de bulur
      final r = await _sevk.lotDogrula(lot);
      if (!r.bulundu || r.urun == null) {
        _setMesaj(r.mesaj.isEmpty ? 'Lot bulunamadı' : r.mesaj, hata: true);
        return;
      }

      // Duplicate kontrol normalized lot uzerinden (etiket -SEV'siz, bakiye -SEV'li)
      final urun = r.urun!;
      if (_okutulanlar.any((p) => p.lotNo == urun.lotNo)) {
        _setMesaj('Bu lot zaten okutulmuş: ${urun.lotNo}', hata: true);
        return;
      }

      setState(() {
        _okutulanlar.add(urun);
        _hazir.removeWhere((h) => h.lotNo == urun.lotNo);
      });
      _setMesaj(
        '✓ ${urun.lotNo} · ${_kisalt(urun.musteri, 22)} · ${urun.miktar.toStringAsFixed(0)} ad',
      );
    } on DioException catch (e) {
      _setMesaj(_sevk.errorMessage(e), hata: true);
    } finally {
      _barkodCtl.clear();
      _barkodFocus.requestFocus();
    }
  }

  void _hazirEkle(HazirUrun h) {
    if (_okutulanlar.any((p) => p.lotNo == h.lotNo)) return;
    setState(() {
      _okutulanlar.add(h);
      _hazir.removeWhere((x) => x.lotNo == h.lotNo);
    });
    _setMesaj('✓ ${h.lotNo} listeden eklendi');
  }

  void _paketSil(int idx) {
    if (idx < 0 || idx >= _okutulanlar.length) return;
    final paket = _okutulanlar[idx];
    setState(() {
      _okutulanlar.removeAt(idx);
      _hazir.add(paket);
    });
    _setMesaj('✗ ${paket.lotNo} silindi', hata: true);
  }

  Future<void> _temizle() async {
    if (_okutulanlar.isEmpty) return;
    final ok = await _onayAl(
      'Temizle',
      '${_okutulanlar.length} okutulan paket silinsin mi?',
    );
    if (ok != true) return;
    setState(() {
      _hazir.addAll(_okutulanlar);
      _okutulanlar.clear();
      _tasiyici = null;
      _plaka = null;
      _sofor = null;
      _notCtl.clear();
    });
    _hazirYenile();
  }

  Future<void> _sevkiyatOlustur() async {
    if (_okutulanlar.isEmpty) {
      _setMesaj('En az bir lot okutmalısınız!', hata: true);
      return;
    }

    // Müşterilere göre grupla (uyarı için)
    final musteriler = <String>{
      for (final p in _okutulanlar) p.musteri,
    };

    if (musteriler.length > 1) {
      final ok = await _onayAl(
        'Birden fazla müşteri',
        '${musteriler.length} farklı müşteri tespit edildi:\n\n'
            '${musteriler.map((m) => "• $m").join("\n")}\n\n'
            'Her müşteri için AYRI irsaliye oluşturulacak. Devam?',
      );
      if (ok != true) return;
    }

    setState(() => _busy = true);
    try {
      final sonuc = await _sevk.olustur(
        tasiyici: _tasiyici ?? '',
        plaka: _plaka ?? '',
        sofor: _sofor ?? '',
        notlar: _notCtl.text.trim(),
        lotlar: _okutulanlar,
      );

      if (!mounted) return;

      if (sonuc.olusturulan.isNotEmpty) {
        final lines = sonuc.olusturulan
            .map((i) => '• ${i.irsaliyeNo} · ${_kisalt(i.musteri, 25)} · '
                '${i.lotSayisi} paket / ${i.toplamMiktar.toStringAsFixed(0)} ad')
            .join('\n');
        await _bilgi('Sevkiyat tamam', '${sonuc.olusturulan.length} irsaliye oluşturuldu:\n\n$lines');
        setState(() {
          _okutulanlar.clear();
          _notCtl.clear();
        });
        await _hazirYenile();
      }

      if (sonuc.basarisiz.isNotEmpty) {
        final lines = sonuc.basarisiz
            .map((b) => '• ${b['musteri']}: ${b['hata']}')
            .join('\n');
        await _bilgi('Bazı sevkler başarısız', lines);
      }
    } on DioException catch (e) {
      _setMesaj(_sevk.errorMessage(e), hata: true);
    } finally {
      if (mounted) setState(() => _busy = false);
    }
  }

  Future<void> _logout() async {
    await _auth.logout();
    if (!mounted) return;
    Navigator.of(context).pushReplacement(
      MaterialPageRoute(builder: (_) => const LoginScreen()),
    );
  }

  void _setMesaj(String mesaj, {bool hata = false}) {
    if (!mounted) return;
    setState(() {
      _sonMesaj = mesaj;
      _sonMesajRenk = hata
          ? const Color(TerminalConfig.dangerColor)
          : const Color(TerminalConfig.successColor);
    });
  }

  Future<bool?> _onayAl(String baslik, String mesaj) {
    return showDialog<bool>(
      context: context,
      builder: (ctx) => AlertDialog(
        title: Text(baslik),
        content: Text(mesaj),
        actions: [
          TextButton(onPressed: () => Navigator.pop(ctx, false), child: const Text('Vazgeç')),
          TextButton(onPressed: () => Navigator.pop(ctx, true), child: const Text('Devam')),
        ],
      ),
    );
  }

  Future<void> _bilgi(String baslik, String mesaj) {
    return showDialog(
      context: context,
      builder: (ctx) => AlertDialog(
        title: Text(baslik),
        content: SingleChildScrollView(child: Text(mesaj)),
        actions: [
          TextButton(onPressed: () => Navigator.pop(ctx), child: const Text('Tamam')),
        ],
      ),
    );
  }

  String _kisalt(String s, int n) =>
      s.length <= n ? s : '${s.substring(0, n - 1)}…';

  // ---------------------------------------------------------------- BUILD

  @override
  Widget build(BuildContext context) {
    final filtreli = _aramaText.isEmpty
        ? _hazir
        : _hazir.where((h) {
            final s = _aramaText.toLowerCase();
            return h.lotNo.toLowerCase().contains(s) ||
                h.musteri.toLowerCase().contains(s) ||
                h.stokKodu.toLowerCase().contains(s) ||
                h.stokAdi.toLowerCase().contains(s);
          }).toList();

    return Scaffold(
      appBar: AppBar(
        title: const Text('Yeni Sevkiyat'),
        actions: [
          IconButton(icon: const Icon(Icons.refresh), onPressed: _busy ? null : _yukle),
          IconButton(icon: const Icon(Icons.delete_outline), onPressed: _busy ? null : _temizle),
          IconButton(icon: const Icon(Icons.logout), onPressed: _logout),
        ],
      ),
      body: Column(
        children: [
          // Araç bilgileri (daraltılabilir)
          _aracBolumu(),
          const Divider(height: 1),

          // Barkod input
          _barkodBolumu(),

          // Son okutma mesajı
          if (_sonMesaj != null)
            Container(
              width: double.infinity,
              padding: const EdgeInsets.all(8),
              color: _sonMesajRenk.withOpacity(0.15),
              child: Text(
                _sonMesaj!,
                style: TextStyle(color: _sonMesajRenk, fontWeight: FontWeight.w600),
              ),
            ),

          const Divider(height: 1),

          // Tab benzeri: Hazır listesi vs Okutulanlar
          Expanded(
            child: DefaultTabController(
              length: 2,
              child: Column(
                children: [
                  TabBar(
                    tabs: [
                      Tab(text: 'Sevke Hazır (${filtreli.length})'),
                      Tab(text: 'Okutulan (${_okutulanlar.length})'),
                    ],
                  ),
                  Expanded(
                    child: TabBarView(
                      children: [
                        _hazirTab(filtreli),
                        _okutulanTab(),
                      ],
                    ),
                  ),
                ],
              ),
            ),
          ),

          // Alt: Sevkiyat oluştur butonu
          SafeArea(
            top: false,
            child: Padding(
              padding: const EdgeInsets.all(12),
              child: ElevatedButton.icon(
                onPressed: _busy || _okutulanlar.isEmpty ? null : _sevkiyatOlustur,
                icon: const Icon(Icons.local_shipping),
                label: Text(
                  _okutulanlar.isEmpty
                      ? 'Lot okutun'
                      : 'Sevkiyat Oluştur (${_okutulanlar.length})',
                  style: const TextStyle(fontSize: 16, fontWeight: FontWeight.bold),
                ),
                style: ElevatedButton.styleFrom(
                  padding: const EdgeInsets.symmetric(vertical: 16),
                  backgroundColor: const Color(TerminalConfig.successColor),
                  foregroundColor: Colors.white,
                ),
              ),
            ),
          ),
        ],
      ),
    );
  }

  Widget _aracBolumu() {
    return ExpansionTile(
      leading: const Icon(Icons.local_shipping_outlined),
      title: Text(
        _aracOzet(),
        style: const TextStyle(fontWeight: FontWeight.w600),
      ),
      initiallyExpanded: _aracExpanded,
      onExpansionChanged: (v) => setState(() => _aracExpanded = v),
      tilePadding: const EdgeInsets.symmetric(horizontal: 12),
      childrenPadding: const EdgeInsets.fromLTRB(12, 0, 12, 12),
      children: [
        DropdownButtonFormField<String>(
          value: _tasiyici,
          isExpanded: true,
          decoration: const InputDecoration(labelText: 'Taşıyıcı', isDense: true),
          items: [
            const DropdownMenuItem(value: null, child: Text('—')),
            ...?_arac?.tasiyicilar.map(
              (t) => DropdownMenuItem(value: t, child: Text(t, overflow: TextOverflow.ellipsis)),
            ),
          ],
          onChanged: (v) => setState(() => _tasiyici = v),
        ),
        const SizedBox(height: 8),
        DropdownButtonFormField<String>(
          value: _plaka,
          isExpanded: true,
          decoration: const InputDecoration(labelText: 'Plaka', isDense: true),
          items: [
            const DropdownMenuItem(value: null, child: Text('—')),
            ...?_arac?.plakalar.map(
              (p) => DropdownMenuItem(value: p.plaka, child: Text(p.goruntu, overflow: TextOverflow.ellipsis)),
            ),
          ],
          onChanged: (v) => setState(() => _plaka = v),
        ),
        const SizedBox(height: 8),
        DropdownButtonFormField<String>(
          value: _sofor,
          isExpanded: true,
          decoration: const InputDecoration(labelText: 'Şoför', isDense: true),
          items: [
            const DropdownMenuItem(value: null, child: Text('—')),
            ...?_arac?.soforler.map(
              (s) => DropdownMenuItem(value: s.ad, child: Text(s.goruntu, overflow: TextOverflow.ellipsis)),
            ),
          ],
          onChanged: (v) => setState(() => _sofor = v),
        ),
        const SizedBox(height: 8),
        TextField(
          controller: _notCtl,
          maxLines: 2,
          decoration: const InputDecoration(
            labelText: 'Not (opsiyonel)',
            isDense: true,
            border: OutlineInputBorder(),
          ),
        ),
      ],
    );
  }

  String _aracOzet() {
    final p = <String>[];
    if (_tasiyici != null && _tasiyici!.isNotEmpty) p.add(_tasiyici!);
    if (_plaka != null && _plaka!.isNotEmpty) p.add(_plaka!);
    if (_sofor != null && _sofor!.isNotEmpty) p.add(_sofor!);
    return p.isEmpty ? 'Araç bilgileri (opsiyonel)' : p.join(' · ');
  }

  Widget _barkodBolumu() {
    return Container(
      padding: const EdgeInsets.all(12),
      color: const Color(0xFF0F172A),
      child: Row(
        children: [
          const Icon(Icons.qr_code_scanner, color: Color(TerminalConfig.primaryColor)),
          const SizedBox(width: 8),
          Expanded(
            child: TextField(
              controller: _barkodCtl,
              focusNode: _barkodFocus,
              autofocus: true,
              enabled: !_busy,
              keyboardType: TextInputType.text,
              inputFormatters: [
                FilteringTextInputFormatter.allow(RegExp(r'[A-Za-z0-9\-_]')),
              ],
              style: const TextStyle(fontSize: 18, letterSpacing: 1.5),
              decoration: const InputDecoration(
                hintText: 'Lot barkodunu okutun…',
                isDense: true,
                border: OutlineInputBorder(),
                filled: true,
                fillColor: Color(0xFF1E293B),
              ),
              onSubmitted: (_) => _barkodOkut(),
            ),
          ),
        ],
      ),
    );
  }

  Widget _hazirTab(List<HazirUrun> data) {
    return Column(
      children: [
        Padding(
          padding: const EdgeInsets.all(8),
          child: TextField(
            controller: _aramaCtl,
            decoration: const InputDecoration(
              hintText: 'Filtrele (lot/müşteri/stok)…',
              prefixIcon: Icon(Icons.search),
              isDense: true,
              border: OutlineInputBorder(),
            ),
            onChanged: (v) => setState(() => _aramaText = v),
          ),
        ),
        Expanded(
          child: data.isEmpty
              ? const Center(child: Text('Sevke hazır lot yok', style: TextStyle(color: Colors.white54)))
              : ListView.builder(
                  itemCount: data.length,
                  itemBuilder: (_, i) {
                    final h = data[i];
                    return _hazirRow(h);
                  },
                ),
        ),
      ],
    );
  }

  Widget _hazirRow(HazirUrun h) {
    final renk = h.gun >= 14
        ? const Color(0xFFEF4444)
        : h.gun >= 7
            ? const Color(0xFFF59E0B)
            : Colors.white60;
    return ListTile(
      dense: true,
      title: Text(h.lotNo, style: const TextStyle(fontWeight: FontWeight.w600)),
      subtitle: Text(
        '${_kisalt(h.musteri, 30)}\n${h.stokKodu} · ${_kisalt(h.stokAdi, 35)}',
        style: const TextStyle(fontSize: 12),
      ),
      isThreeLine: true,
      trailing: Column(
        mainAxisSize: MainAxisSize.min,
        crossAxisAlignment: CrossAxisAlignment.end,
        children: [
          Text('${h.miktar.toStringAsFixed(0)} ad',
              style: const TextStyle(fontWeight: FontWeight.bold)),
          Text('${h.gun} gün', style: TextStyle(fontSize: 11, color: renk)),
        ],
      ),
      onTap: () => _hazirEkle(h),
    );
  }

  Widget _okutulanTab() {
    if (_okutulanlar.isEmpty) {
      return const Center(
        child: Text('Henüz lot okutulmadı', style: TextStyle(color: Colors.white54)),
      );
    }
    return ListView.builder(
      itemCount: _okutulanlar.length,
      itemBuilder: (_, i) {
        final p = _okutulanlar[i];
        return ListTile(
          dense: true,
          leading: CircleAvatar(
            backgroundColor: const Color(TerminalConfig.primaryColor),
            radius: 14,
            child: Text('${i + 1}', style: const TextStyle(fontSize: 11, color: Colors.white)),
          ),
          title: Text(p.lotNo, style: const TextStyle(fontWeight: FontWeight.w600)),
          subtitle: Text(
            '${_kisalt(p.musteri, 30)}\n${p.stokKodu} · ${_kisalt(p.stokAdi, 30)}',
            style: const TextStyle(fontSize: 12),
          ),
          isThreeLine: true,
          trailing: Row(
            mainAxisSize: MainAxisSize.min,
            children: [
              Text('${p.miktar.toStringAsFixed(0)} ad',
                  style: const TextStyle(fontWeight: FontWeight.bold)),
              IconButton(
                icon: const Icon(Icons.close, size: 18),
                onPressed: () => _paketSil(i),
              ),
            ],
          ),
        );
      },
    );
  }
}
