import 'package:flutter/material.dart';

import '../config.dart';
import '../models/irsaliye.dart';
import '../services/api_client.dart';
import '../services/auth_service.dart';
import '../services/sevk_service.dart';
import 'login_screen.dart';
import 'sevk_detay_screen.dart';

class SevkListeScreen extends StatefulWidget {
  const SevkListeScreen({super.key});
  @override
  State<SevkListeScreen> createState() => _SevkListeScreenState();
}

class _SevkListeScreenState extends State<SevkListeScreen> {
  late final SevkService _sevk;
  late final AuthService _auth;
  Future<List<IrsaliyeOzet>>? _fut;
  String _arama = '';

  @override
  void initState() {
    super.initState();
    _sevk = SevkService(ApiClient.instance);
    _auth = AuthService(ApiClient.instance);
    _fut = _sevk.acikIrsaliyeler();
  }

  void _yenile() {
    setState(() {
      _fut = _sevk.acikIrsaliyeler(arama: _arama);
    });
  }

  Future<void> _logout() async {
    await _auth.logout();
    if (!mounted) return;
    Navigator.of(context).pushReplacement(
      MaterialPageRoute(builder: (_) => const LoginScreen()),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Sevkiyat - Yukleme'),
        actions: [
          IconButton(
            icon: const Icon(Icons.refresh),
            onPressed: _yenile,
          ),
          IconButton(
            icon: const Icon(Icons.logout),
            onPressed: _logout,
          ),
        ],
      ),
      body: Column(
        children: [
          Padding(
            padding: const EdgeInsets.all(12),
            child: TextField(
              decoration: InputDecoration(
                hintText: 'Irsaliye no / cari / plaka ara...',
                prefixIcon: const Icon(Icons.search),
                border: OutlineInputBorder(
                  borderRadius: BorderRadius.circular(8),
                ),
              ),
              onSubmitted: (v) {
                _arama = v;
                _yenile();
              },
            ),
          ),
          Expanded(
            child: FutureBuilder<List<IrsaliyeOzet>>(
              future: _fut,
              builder: (context, snap) {
                if (snap.connectionState == ConnectionState.waiting) {
                  return const Center(child: CircularProgressIndicator());
                }
                if (snap.hasError) {
                  return Center(
                    child: Padding(
                      padding: const EdgeInsets.all(24),
                      child: Text(
                        'Hata: ${snap.error}',
                        textAlign: TextAlign.center,
                      ),
                    ),
                  );
                }
                final data = snap.data ?? [];
                if (data.isEmpty) {
                  return const Center(
                    child: Text(
                      'Yuklenmeyi bekleyen irsaliye yok',
                      style: TextStyle(color: Colors.white70),
                    ),
                  );
                }
                return RefreshIndicator(
                  onRefresh: () async => _yenile(),
                  child: ListView.separated(
                    padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
                    itemCount: data.length,
                    separatorBuilder: (_, __) => const SizedBox(height: 8),
                    itemBuilder: (_, i) => _IrsaliyeCard(
                      irsaliye: data[i],
                      onTap: () async {
                        await Navigator.of(context).push(
                          MaterialPageRoute(
                            builder: (_) => SevkDetayScreen(irsaliyeId: data[i].id),
                          ),
                        );
                        _yenile();
                      },
                    ),
                  ),
                );
              },
            ),
          ),
        ],
      ),
    );
  }
}

class _IrsaliyeCard extends StatelessWidget {
  const _IrsaliyeCard({required this.irsaliye, required this.onTap});
  final IrsaliyeOzet irsaliye;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    final progress = irsaliye.satirSayisi > 0
        ? (irsaliye.okutulanLotSayisi / irsaliye.satirSayisi).clamp(0.0, 1.0)
        : 0.0;
    return Card(
      color: const Color(0xFF1E293B),
      child: InkWell(
        onTap: onTap,
        borderRadius: BorderRadius.circular(12),
        child: Padding(
          padding: const EdgeInsets.all(14),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Row(
                children: [
                  Expanded(
                    child: Text(
                      irsaliye.irsaliyeNo,
                      style: const TextStyle(fontSize: 16, fontWeight: FontWeight.bold),
                    ),
                  ),
                  Container(
                    padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 2),
                    decoration: BoxDecoration(
                      color: const Color(TerminalConfig.warningColor).withOpacity(0.2),
                      borderRadius: BorderRadius.circular(4),
                    ),
                    child: Text(
                      irsaliye.durum,
                      style: const TextStyle(
                        fontSize: 11,
                        color: Color(TerminalConfig.warningColor),
                        fontWeight: FontWeight.bold,
                      ),
                    ),
                  ),
                ],
              ),
              const SizedBox(height: 6),
              Text(
                irsaliye.cariAdi ?? '-',
                style: const TextStyle(color: Colors.white70),
                maxLines: 1,
                overflow: TextOverflow.ellipsis,
              ),
              const SizedBox(height: 6),
              Row(
                children: [
                  if (irsaliye.aracPlaka.isNotEmpty) ...[
                    const Icon(Icons.local_shipping, size: 14, color: Colors.white54),
                    const SizedBox(width: 4),
                    Text(irsaliye.aracPlaka, style: const TextStyle(fontSize: 12, color: Colors.white60)),
                    const SizedBox(width: 12),
                  ],
                  Text(
                    '${irsaliye.satirSayisi} kalem',
                    style: const TextStyle(fontSize: 12, color: Colors.white60),
                  ),
                  const Spacer(),
                  Text(
                    '${irsaliye.okutulanLotSayisi}/${irsaliye.satirSayisi} okutuldu',
                    style: TextStyle(
                      fontSize: 12,
                      color: progress >= 1.0
                          ? const Color(TerminalConfig.successColor)
                          : Colors.white60,
                      fontWeight: FontWeight.bold,
                    ),
                  ),
                ],
              ),
              const SizedBox(height: 8),
              ClipRRect(
                borderRadius: BorderRadius.circular(4),
                child: LinearProgressIndicator(
                  value: progress,
                  backgroundColor: const Color(0xFF334155),
                  color: progress >= 1.0
                      ? const Color(TerminalConfig.successColor)
                      : const Color(TerminalConfig.primaryColor),
                  minHeight: 6,
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}
