import 'dart:async';
import 'package:dio/dio.dart';
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';

import '../config.dart';
import '../models/irsaliye.dart';
import '../services/api_client.dart';
import '../services/scanner_service.dart';
import '../services/sevk_service.dart';

class SevkDetayScreen extends StatefulWidget {
  const SevkDetayScreen({super.key, required this.irsaliyeId});
  final int irsaliyeId;

  @override
  State<SevkDetayScreen> createState() => _SevkDetayScreenState();
}

class _SevkDetayScreenState extends State<SevkDetayScreen> {
  late final SevkService _sevk;
  IrsaliyeDetay? _detay;
  bool _yukleniyor = true;
  String? _hata;

  StreamSubscription<String>? _scanSub;
  final _manuelLotCtl = TextEditingController();
  final _manuelLotFocus = FocusNode();
  String? _sonMesaj;
  bool _sonOk = true;

  @override
  void initState() {
    super.initState();
    _sevk = SevkService(ApiClient.instance);
    _yukle();

    _scanSub = ScannerService.scans.listen((code) {
      _lotTara(code);
    });
  }

  @override
  void dispose() {
    _scanSub?.cancel();
    _manuelLotCtl.dispose();
    _manuelLotFocus.dispose();
    super.dispose();
  }

  Future<void> _yukle() async {
    setState(() {
      _yukleniyor = true;
      _hata = null;
    });
    try {
      final d = await _sevk.detay(widget.irsaliyeId);
      if (!mounted) return;
      setState(() {
        _detay = d;
        _yukleniyor = false;
      });
    } catch (e) {
      if (!mounted) return;
      setState(() {
        _hata = 'Detay yuklenemedi: $e';
        _yukleniyor = false;
      });
    }
  }

  Future<void> _lotTara(String lot) async {
    if (lot.trim().isEmpty) return;
    try {
      final r = await _sevk.lotTara(widget.irsaliyeId, lot.trim());
      HapticFeedback.lightImpact();
      if (!mounted) return;
      setState(() {
        _sonMesaj = r.bulundu
            ? '${r.urunKodu ?? ''}  -  ${r.mesaj}'
            : r.mesaj;
        _sonOk = r.bulundu;
        _manuelLotCtl.clear();
      });
      // Detayi tazele (durum kolonlari guncellensin)
      _yukle();
    } on DioException catch (e) {
      HapticFeedback.heavyImpact();
      if (!mounted) return;
      setState(() {
        _sonMesaj = _sevk.errorMessage(e);
        _sonOk = false;
      });
    }
  }

  Future<void> _yuklemeTamam({bool zorla = false}) async {
    try {
      final r = await _sevk.yukle(widget.irsaliyeId, zorla: zorla);
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          backgroundColor: const Color(TerminalConfig.successColor),
          content: Text('${r.mesaj} (durum: ${r.yeniDurum})'),
        ),
      );
      Navigator.of(context).pop();
    } on DioException catch (e) {
      if (!mounted) return;
      final msg = _sevk.errorMessage(e);
      // Eksik var, kullaniciya zorla soruyu sor
      if (msg.contains('lot okutulmamis')) {
        final ok = await showDialog<bool>(
          context: context,
          builder: (_) => AlertDialog(
            title: const Text('Eksik Lot'),
            content: Text('$msg\n\nYine de yuklendi olarak isaretleyelim mi?'),
            actions: [
              TextButton(
                onPressed: () => Navigator.of(context).pop(false),
                child: const Text('Iptal'),
              ),
              ElevatedButton(
                onPressed: () => Navigator.of(context).pop(true),
                style: ElevatedButton.styleFrom(
                  backgroundColor: const Color(TerminalConfig.dangerColor),
                ),
                child: const Text('Zorla Yukle'),
              ),
            ],
          ),
        );
        if (ok == true) _yuklemeTamam(zorla: true);
      } else {
        ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(msg)));
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    if (_yukleniyor) {
      return Scaffold(
        appBar: AppBar(title: const Text('Yukleniyor...')),
        body: const Center(child: CircularProgressIndicator()),
      );
    }
    if (_hata != null) {
      return Scaffold(
        appBar: AppBar(title: const Text('Hata')),
        body: Center(child: Text(_hata!)),
      );
    }
    final d = _detay!;
    final tamam = d.satirlar.where((s) => s.durum == 'OKUTULDU').length;
    final progress = d.satirlar.isEmpty ? 0.0 : tamam / d.satirlar.length;

    return Scaffold(
      appBar: AppBar(title: Text(d.ozet.irsaliyeNo)),
      body: Column(
        children: [
          // Header info
          Container(
            color: const Color(0xFF1E293B),
            padding: const EdgeInsets.all(12),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  d.ozet.cariAdi ?? '-',
                  style: const TextStyle(fontSize: 14, fontWeight: FontWeight.bold),
                ),
                const SizedBox(height: 4),
                Row(
                  children: [
                    if (d.ozet.aracPlaka.isNotEmpty) ...[
                      const Icon(Icons.local_shipping, size: 14, color: Colors.white54),
                      const SizedBox(width: 4),
                      Text(d.ozet.aracPlaka, style: const TextStyle(fontSize: 12, color: Colors.white60)),
                      const SizedBox(width: 12),
                    ],
                    if (d.ozet.soforAdi.isNotEmpty) ...[
                      const Icon(Icons.person, size: 14, color: Colors.white54),
                      const SizedBox(width: 4),
                      Expanded(
                        child: Text(d.ozet.soforAdi,
                            style: const TextStyle(fontSize: 12, color: Colors.white60),
                            overflow: TextOverflow.ellipsis),
                      ),
                    ],
                  ],
                ),
                const SizedBox(height: 8),
                Row(
                  children: [
                    Text('$tamam / ${d.satirlar.length} kalem',
                        style: const TextStyle(fontSize: 13)),
                    const SizedBox(width: 8),
                    Expanded(
                      child: ClipRRect(
                        borderRadius: BorderRadius.circular(4),
                        child: LinearProgressIndicator(
                          value: progress,
                          backgroundColor: const Color(0xFF334155),
                          color: progress >= 1.0
                              ? const Color(TerminalConfig.successColor)
                              : const Color(TerminalConfig.primaryColor),
                          minHeight: 8,
                        ),
                      ),
                    ),
                  ],
                ),
              ],
            ),
          ),

          // Manuel lot input
          Padding(
            padding: const EdgeInsets.all(12),
            child: Row(
              children: [
                Expanded(
                  child: TextField(
                    controller: _manuelLotCtl,
                    focusNode: _manuelLotFocus,
                    decoration: const InputDecoration(
                      hintText: 'Lot okut veya yaz',
                      prefixIcon: Icon(Icons.qr_code_scanner),
                      border: OutlineInputBorder(),
                    ),
                    onSubmitted: (v) {
                      _lotTara(v);
                      _manuelLotFocus.requestFocus();
                    },
                  ),
                ),
                const SizedBox(width: 8),
                ElevatedButton(
                  onPressed: () {
                    _lotTara(_manuelLotCtl.text);
                    _manuelLotFocus.requestFocus();
                  },
                  style: ElevatedButton.styleFrom(
                    padding: const EdgeInsets.symmetric(vertical: 16, horizontal: 12),
                  ),
                  child: const Icon(Icons.send),
                ),
              ],
            ),
          ),

          // Son mesaj banneri
          if (_sonMesaj != null)
            Container(
              margin: const EdgeInsets.symmetric(horizontal: 12),
              padding: const EdgeInsets.all(10),
              decoration: BoxDecoration(
                color: (_sonOk
                        ? const Color(TerminalConfig.successColor)
                        : const Color(TerminalConfig.dangerColor))
                    .withOpacity(0.18),
                border: Border.all(
                  color: _sonOk
                      ? const Color(TerminalConfig.successColor)
                      : const Color(TerminalConfig.dangerColor),
                ),
                borderRadius: BorderRadius.circular(8),
              ),
              child: Row(
                children: [
                  Icon(
                    _sonOk ? Icons.check_circle : Icons.error,
                    color: _sonOk
                        ? const Color(TerminalConfig.successColor)
                        : const Color(TerminalConfig.dangerColor),
                  ),
                  const SizedBox(width: 8),
                  Expanded(child: Text(_sonMesaj!)),
                ],
              ),
            ),

          // Satir listesi
          Expanded(
            child: ListView.separated(
              padding: const EdgeInsets.all(12),
              itemCount: d.satirlar.length,
              separatorBuilder: (_, __) => const SizedBox(height: 6),
              itemBuilder: (_, i) => _SatirTile(satir: d.satirlar[i]),
            ),
          ),

          // Alt buton
          SafeArea(
            child: Padding(
              padding: const EdgeInsets.all(12),
              child: ElevatedButton.icon(
                onPressed: () => _yuklemeTamam(),
                style: ElevatedButton.styleFrom(
                  padding: const EdgeInsets.symmetric(vertical: 18),
                  backgroundColor: progress >= 1.0
                      ? const Color(TerminalConfig.successColor)
                      : const Color(TerminalConfig.primaryColor),
                ),
                icon: const Icon(Icons.check_circle),
                label: Text(
                  progress >= 1.0
                      ? 'Yukleme Tamam - SEVK_EDILDI'
                      : 'Yukleme Tamam (${d.satirlar.length - tamam} eksik)',
                  style: const TextStyle(fontSize: 16, fontWeight: FontWeight.bold),
                ),
              ),
            ),
          ),
        ],
      ),
    );
  }
}

class _SatirTile extends StatelessWidget {
  const _SatirTile({required this.satir});
  final SatirDetay satir;

  @override
  Widget build(BuildContext context) {
    final ok = satir.durum == 'OKUTULDU';
    return Card(
      color: ok
          ? const Color(TerminalConfig.successColor).withOpacity(0.12)
          : const Color(0xFF1E293B),
      child: ListTile(
        leading: Icon(
          ok ? Icons.check_circle : Icons.radio_button_unchecked,
          color: ok ? const Color(TerminalConfig.successColor) : Colors.white60,
          size: 28,
        ),
        title: Text(
          '${satir.urunKodu} ${satir.urunAdi}',
          style: const TextStyle(fontWeight: FontWeight.bold),
          maxLines: 1,
          overflow: TextOverflow.ellipsis,
        ),
        subtitle: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text('Lot: ${satir.lotNo}',
                style: const TextStyle(fontSize: 11, color: Colors.white60),
                maxLines: 2,
                overflow: TextOverflow.ellipsis),
            Text('Miktar: ${satir.miktar.toStringAsFixed(2)}'
                '${satir.koliAdedi > 0 ? '  ·  ${satir.koliAdedi} koli' : ''}',
                style: const TextStyle(fontSize: 11)),
          ],
        ),
      ),
    );
  }
}
