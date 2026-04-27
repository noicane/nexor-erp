import 'package:flutter/material.dart';

import 'config.dart';
import 'screens/login_screen.dart';
import 'screens/sevk_liste_screen.dart';
import 'services/api_client.dart';
import 'services/auth_service.dart';
import 'services/scanner_service.dart';

void main() async {
  WidgetsFlutterBinding.ensureInitialized();
  await ScannerService.start();
  runApp(const NexorTerminalApp());
}

class NexorTerminalApp extends StatelessWidget {
  const NexorTerminalApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'NEXOR Terminal',
      debugShowCheckedModeBanner: false,
      theme: ThemeData(
        useMaterial3: true,
        colorScheme: ColorScheme.fromSeed(
          seedColor: const Color(TerminalConfig.primaryColor),
          brightness: Brightness.dark,
        ),
        scaffoldBackgroundColor: const Color(0xFF0F172A),
        appBarTheme: const AppBarTheme(
          backgroundColor: Color(0xFF1E293B),
          foregroundColor: Colors.white,
          elevation: 0,
        ),
      ),
      home: const _Bootstrap(),
    );
  }
}

/// Token varsa direkt sevk listesine, yoksa login'e yonlendir.
class _Bootstrap extends StatefulWidget {
  const _Bootstrap();

  @override
  State<_Bootstrap> createState() => _BootstrapState();
}

class _BootstrapState extends State<_Bootstrap> {
  bool _checking = true;

  @override
  void initState() {
    super.initState();
    _check();
  }

  Future<void> _check() async {
    final auth = AuthService(ApiClient.instance);
    final ok = await auth.hasValidSession();
    if (!mounted) return;
    Navigator.of(context).pushReplacement(
      MaterialPageRoute(
        builder: (_) => ok ? const SevkListeScreen() : const LoginScreen(),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: Center(
        child: _checking
            ? const CircularProgressIndicator()
            : const SizedBox.shrink(),
      ),
    );
  }
}
