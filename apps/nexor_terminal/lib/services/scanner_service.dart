import 'dart:async';
import 'package:flutter/services.dart';

/// Honeywell EDA51 scanner intent stream'ini Flutter'a tasir.
/// Honeywell olmayan cihazlarda da hata vermez; sadece event akmaz.
class ScannerService {
  static const _eventChannel = EventChannel('com.nexor.terminal/scanner');
  static const _methodChannel = MethodChannel('com.nexor.terminal/device');

  static final _streamController = StreamController<String>.broadcast();
  static StreamSubscription? _platformSub;
  static bool _started = false;

  /// Platform'dan gelen barkod stream'i. Tek bir broadcast kanal,
  /// birden fazla widget abone olabilir.
  static Stream<String> get scans => _streamController.stream;

  static Future<void> start() async {
    if (_started) return;
    _started = true;
    try {
      _platformSub = _eventChannel.receiveBroadcastStream().listen(
        (event) {
          if (event is String && event.isNotEmpty) {
            _streamController.add(event);
          }
        },
        onError: (e) {
          // Honeywell olmayan cihazlarda hata gelebilir; sessizce yut
        },
      );
    } catch (_) {
      // ignore
    }
  }

  static Future<void> stop() async {
    await _platformSub?.cancel();
    _platformSub = null;
    _started = false;
  }

  static Future<Map<String, dynamic>> getDeviceInfo() async {
    try {
      final r = await _methodChannel.invokeMethod('getDeviceInfo');
      return Map<String, dynamic>.from(r as Map);
    } catch (_) {
      return {'manufacturer': 'unknown', 'model': 'unknown', 'isHoneywell': false};
    }
  }

  /// Test/UI tetiklemesi (mock barkod, debug)
  static void emitForTest(String code) {
    _streamController.add(code);
  }
}
