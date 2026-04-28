import 'dart:async';
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';

import '../config.dart';
import '../services/api_client.dart';
import '../services/auth_service.dart';
import '../services/scanner_service.dart';
import 'yeni_sevk_screen.dart';

class LoginScreen extends StatefulWidget {
  const LoginScreen({super.key});
  @override
  State<LoginScreen> createState() => _LoginScreenState();
}

class _LoginScreenState extends State<LoginScreen> {
  final _kartCtl = TextEditingController();
  final _userCtl = TextEditingController();
  final _pinCtl = TextEditingController();
  final _kartFocus = FocusNode();

  late final AuthService _auth;
  StreamSubscription<String>? _scanSub;
  bool _busy = false;
  bool _showPin = false;
  String? _err;

  @override
  void initState() {
    super.initState();
    _auth = AuthService(ApiClient.instance);

    // Honeywell scanner'dan gelen barkodu kart olarak yorumla
    _scanSub = ScannerService.scans.listen((code) {
      if (!mounted) return;
      _kartCtl.text = code.trim();
      _loginKart();
    });

    // Klavye USB okuyucusu da kart input'una odakli olsun
    WidgetsBinding.instance.addPostFrameCallback((_) {
      _kartFocus.requestFocus();
    });
  }

  @override
  void dispose() {
    _scanSub?.cancel();
    _kartCtl.dispose();
    _userCtl.dispose();
    _pinCtl.dispose();
    _kartFocus.dispose();
    super.dispose();
  }

  Future<void> _loginKart() async {
    final kart = _kartCtl.text.trim();
    if (kart.isEmpty) return;
    setState(() {
      _busy = true;
      _err = null;
    });
    final r = await _auth.loginWithKart(kart);
    if (!mounted) return;
    setState(() => _busy = false);
    if (r.success) {
      _gotoSevk();
    } else {
      setState(() => _err = r.message);
      _kartCtl.clear();
      _kartFocus.requestFocus();
    }
  }

  Future<void> _loginPin() async {
    final user = _userCtl.text.trim();
    final pin = _pinCtl.text.trim();
    if (user.isEmpty || pin.length < 4) {
      setState(() => _err = 'Kullanici adi ve 4-6 haneli PIN girin');
      return;
    }
    setState(() {
      _busy = true;
      _err = null;
    });
    final r = await _auth.loginWithPin(user, pin);
    if (!mounted) return;
    setState(() => _busy = false);
    if (r.success) {
      _gotoSevk();
    } else {
      setState(() => _err = r.message);
    }
  }

  void _gotoSevk() {
    Navigator.of(context).pushReplacement(
      MaterialPageRoute(builder: (_) => const YeniSevkScreen()),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: SafeArea(
        child: SingleChildScrollView(
          padding: const EdgeInsets.all(24),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              const SizedBox(height: 40),
              const Text(
                'NEXOR',
                textAlign: TextAlign.center,
                style: TextStyle(fontSize: 42, fontWeight: FontWeight.bold, letterSpacing: 4),
              ),
              const Text(
                'Terminal',
                textAlign: TextAlign.center,
                style: TextStyle(fontSize: 18, color: Colors.white60),
              ),
              const SizedBox(height: 50),

              // Kart girisi
              Container(
                padding: const EdgeInsets.all(20),
                decoration: BoxDecoration(
                  color: const Color(0xFF1E293B),
                  borderRadius: BorderRadius.circular(12),
                  border: Border.all(color: const Color(0xFF334155)),
                ),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.stretch,
                  children: [
                    const Row(
                      children: [
                        Icon(Icons.contactless, color: Color(TerminalConfig.primaryColor)),
                        SizedBox(width: 8),
                        Text(
                          'Kart Okutun',
                          style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold),
                        ),
                      ],
                    ),
                    const SizedBox(height: 16),
                    TextField(
                      controller: _kartCtl,
                      focusNode: _kartFocus,
                      autofocus: true,
                      enabled: !_busy,
                      keyboardType: TextInputType.text,
                      inputFormatters: [
                        FilteringTextInputFormatter.allow(RegExp(r'[A-Za-z0-9\-_]')),
                      ],
                      style: const TextStyle(fontSize: 22, letterSpacing: 2),
                      decoration: const InputDecoration(
                        hintText: 'Karti okuyucuya tutun...',
                        border: OutlineInputBorder(),
                      ),
                      onSubmitted: (_) => _loginKart(),
                    ),
                  ],
                ),
              ),

              const SizedBox(height: 16),
              if (_err != null)
                Container(
                  padding: const EdgeInsets.all(12),
                  decoration: BoxDecoration(
                    color: const Color(TerminalConfig.dangerColor).withOpacity(0.15),
                    border: Border.all(color: const Color(TerminalConfig.dangerColor)),
                    borderRadius: BorderRadius.circular(8),
                  ),
                  child: Text(
                    _err!,
                    style: const TextStyle(color: Color(TerminalConfig.dangerColor)),
                  ),
                ),

              const SizedBox(height: 24),
              TextButton.icon(
                onPressed: () => setState(() => _showPin = !_showPin),
                icon: Icon(_showPin ? Icons.expand_less : Icons.expand_more),
                label: Text(_showPin ? 'PIN ile girisi kapat' : 'Kart yok? PIN ile giris'),
              ),

              if (_showPin) ...[
                const SizedBox(height: 8),
                Container(
                  padding: const EdgeInsets.all(20),
                  decoration: BoxDecoration(
                    color: const Color(0xFF1E293B),
                    borderRadius: BorderRadius.circular(12),
                    border: Border.all(color: const Color(0xFF334155)),
                  ),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.stretch,
                    children: [
                      TextField(
                        controller: _userCtl,
                        enabled: !_busy,
                        decoration: const InputDecoration(
                          labelText: 'Kullanici Adi',
                          border: OutlineInputBorder(),
                        ),
                      ),
                      const SizedBox(height: 12),
                      TextField(
                        controller: _pinCtl,
                        enabled: !_busy,
                        obscureText: true,
                        keyboardType: TextInputType.number,
                        maxLength: 6,
                        inputFormatters: [FilteringTextInputFormatter.digitsOnly],
                        decoration: const InputDecoration(
                          labelText: 'PIN (4-6 hane)',
                          border: OutlineInputBorder(),
                          counterText: '',
                        ),
                        onSubmitted: (_) => _loginPin(),
                      ),
                      const SizedBox(height: 12),
                      ElevatedButton(
                        onPressed: _busy ? null : _loginPin,
                        style: ElevatedButton.styleFrom(
                          padding: const EdgeInsets.symmetric(vertical: 16),
                          backgroundColor: const Color(TerminalConfig.primaryColor),
                        ),
                        child: _busy
                            ? const SizedBox(
                                width: 20,
                                height: 20,
                                child: CircularProgressIndicator(strokeWidth: 2, color: Colors.white),
                              )
                            : const Text('Giris', style: TextStyle(fontSize: 16)),
                      ),
                    ],
                  ),
                ),
              ],
            ],
          ),
        ),
      ),
    );
  }
}
