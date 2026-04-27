package com.nexor.terminal

import android.content.BroadcastReceiver
import android.content.Context
import android.content.Intent
import android.content.IntentFilter
import android.os.Build
import io.flutter.embedding.android.FlutterActivity
import io.flutter.embedding.engine.FlutterEngine
import io.flutter.plugin.common.EventChannel
import io.flutter.plugin.common.MethodChannel

/**
 * NEXOR Terminal MainActivity
 *
 * Honeywell scanner broadcast intent'ini yakalar ve Flutter tarafina event olarak iletir.
 * Honeywell olmayan cihazlarda da calisir (sadece intent gelmez, mobile_scanner kamera kullanilabilir).
 *
 * Honeywell EDA51 ayarlarinda Scanner > Wedge / Intent moduna alinmali:
 *   - Output to: Intent
 *   - Action: com.honeywell.scan.broadcast.data.scan
 *   - Extra: data, codeId, charset, ...
 */
class MainActivity : FlutterActivity() {

    companion object {
        private const val SCANNER_EVENT_CHANNEL = "com.nexor.terminal/scanner"
        private const val DEVICE_INFO_CHANNEL = "com.nexor.terminal/device"
        private const val HONEYWELL_ACTION = "com.honeywell.scan.broadcast.data.scan"
    }

    private var scannerEventSink: EventChannel.EventSink? = null
    private var scannerReceiver: BroadcastReceiver? = null

    override fun configureFlutterEngine(flutterEngine: FlutterEngine) {
        super.configureFlutterEngine(flutterEngine)

        // EventChannel: barkod stream
        EventChannel(flutterEngine.dartExecutor.binaryMessenger, SCANNER_EVENT_CHANNEL)
            .setStreamHandler(object : EventChannel.StreamHandler {
                override fun onListen(arguments: Any?, events: EventChannel.EventSink?) {
                    scannerEventSink = events
                    registerScannerReceiver()
                }

                override fun onCancel(arguments: Any?) {
                    scannerEventSink = null
                    unregisterScannerReceiver()
                }
            })

        // MethodChannel: cihaz bilgisi (Honeywell mu?)
        MethodChannel(flutterEngine.dartExecutor.binaryMessenger, DEVICE_INFO_CHANNEL)
            .setMethodCallHandler { call, result ->
                when (call.method) {
                    "getDeviceInfo" -> {
                        result.success(
                            mapOf(
                                "manufacturer" to Build.MANUFACTURER,
                                "model" to Build.MODEL,
                                "isHoneywell" to Build.MANUFACTURER.equals("Honeywell", ignoreCase = true),
                            )
                        )
                    }
                    else -> result.notImplemented()
                }
            }
    }

    private fun registerScannerReceiver() {
        if (scannerReceiver != null) return
        scannerReceiver = object : BroadcastReceiver() {
            override fun onReceive(context: Context?, intent: Intent?) {
                if (intent == null) return
                if (intent.action != HONEYWELL_ACTION) return
                val data = intent.getStringExtra("data") ?: ""
                if (data.isNotEmpty()) {
                    scannerEventSink?.success(data)
                }
            }
        }
        val filter = IntentFilter(HONEYWELL_ACTION)
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.TIRAMISU) {
            registerReceiver(scannerReceiver, filter, RECEIVER_EXPORTED)
        } else {
            registerReceiver(scannerReceiver, filter)
        }
    }

    private fun unregisterScannerReceiver() {
        scannerReceiver?.let {
            try { unregisterReceiver(it) } catch (_: Exception) {}
        }
        scannerReceiver = null
    }

    override fun onDestroy() {
        unregisterScannerReceiver()
        super.onDestroy()
    }
}
