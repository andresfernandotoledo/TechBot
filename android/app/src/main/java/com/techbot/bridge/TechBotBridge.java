package com.techbot.bridge;

import android.Manifest;
import android.content.Context;
import android.content.pm.PackageManager;
import android.net.wifi.ScanResult;
import android.net.wifi.WifiManager;
import android.os.Build;
import android.util.Log;

import androidx.core.content.ContextCompat;

import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

/**
 * Bridge Java para que Python (Chaquopy) acceda a APIs nativas de Android.
 * Llamado desde techbot/wifi.py cuando se detecta entorno Android.
 */
public class TechBotBridge {

    private static final String TAG = "TechBotBridge";
    private static Context appContext = null;

    /**
     * Inicializar con el Application Context (llamar desde MainActivity.onCreate).
     */
    public static void init(Context context) {
        appContext = context.getApplicationContext();
        Log.d(TAG, "Bridge inicializado");
    }

    /**
     * Escanea redes WiFi usando WiFiManager nativo de Android.
     * Retorna JSON string con lista de redes.
     */
    public static String wifiScan() {
        if (appContext == null) {
            return "{\"error\":\"Bridge no inicializado. Llamar TechBotBridge.init() primero\"}";
        }

        try {
            WifiManager wifi = (WifiManager) appContext.getSystemService(Context.WIFI_SERVICE);
            if (wifi == null) {
                return "{\"error\":\"WiFiManager no disponible\"}";
            }

            if (!wifi.isWifiEnabled()) {
                return "{\"error\":\"WiFi desactivado\"}";
            }

            // Verificar permiso ubicación (Android 10+)
            if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.Q) {
                if (ContextCompat.checkSelfPermission(appContext,
                        Manifest.permission.ACCESS_FINE_LOCATION)
                        != PackageManager.PERMISSION_GRANTED) {
                    return "{\"error\":\"Permiso ACCESS_FINE_LOCATION requerido\"}";
                }
            }

            boolean started = wifi.startScan();
            if (!started) {
                return "{\"error\":\"startScan() falló\"}";
            }

            try { Thread.sleep(2000); } catch (InterruptedException e) {}

            List<ScanResult> results = wifi.getScanResults();
            List<Map<String, Object>> networks = new ArrayList<>();

            for (ScanResult r : results) {
                Map<String, Object> net = new HashMap<>();
                net.put("ssid", r.SSID != null ? r.SSID : "");
                net.put("bssid", r.BSSID != null ? r.BSSID : "");
                // signal: r.level es RSSI en dBm (-30 a -100)
                int signal = Math.max(0, Math.min(100, (int)((r.level + 100) * 100 / 70)));
                net.put("signal_pct", signal);
                net.put("channel", freqToChannel(r.frequency));
                net.put("frequency", r.frequency);
                net.put("frequency_ghz", Math.round(r.frequency / 1000.0 * 100.0) / 100.0);
                String caps = r.capabilities != null ? r.capabilities.toUpperCase() : "";
                if (caps.contains("WPA2")) net.put("wpa", "WPA2");
                else if (caps.contains("WPA")) net.put("wpa", "WPA");
                else if (caps.contains("WEP")) net.put("wpa", "WEP");
                else net.put("wpa", "Open");
                net.put("encrypted", !caps.isEmpty() && !caps.equals("[]") && !caps.contains("ESS"));
                networks.add(net);
            }

            // Convertir a JSON manualmente (sin Gson)
            StringBuilder json = new StringBuilder("[");
            for (int i = 0; i < networks.size(); i++) {
                if (i > 0) json.append(",");
                Map<String, Object> n = networks.get(i);
                json.append("{");
                int j = 0;
                for (Map.Entry<String, Object> e : n.entrySet()) {
                    if (j++ > 0) json.append(",");
                    json.append("\"").append(e.getKey()).append("\":");
                    Object v = e.getValue();
                    if (v instanceof String) {
                        json.append("\"").append(escapeJson((String) v)).append("\"");
                    } else if (v instanceof Number) {
                        json.append(v);
                    } else if (v instanceof Boolean) {
                        json.append(v);
                    } else {
                        json.append("\"\"");
                    }
                }
                json.append("}");
            }
            json.append("]");
            return json.toString();

        } catch (Exception e) {
            Log.e(TAG, "Error en wifiScan", e);
            return "{\"error\":\"" + escapeJson(e.getMessage()) + "\"}";
        }
    }

    /**
     * Obtiene información de la conexión WiFi actual.
     */
    public static String wifiConnectionInfo() {
        if (appContext == null) return "{}";
        try {
            WifiManager wifi = (WifiManager) appContext.getSystemService(Context.WIFI_SERVICE);
            if (wifi == null) return "{}";

            if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.Q) {
                // Android 10+: getConnectionInfo() sin permiso de ubicación
                android.net.wifi.WifiInfo info = wifi.getConnectionInfo();
                Map<String, Object> data = new HashMap<>();
                data.put("ssid", info.getSSID() != null ? info.getSSID().replace("\"", "") : "");
                data.put("bssid", info.getBSSID() != null ? info.getBSSID() : "");
                data.put("rssi", info.getRssi());
                data.put("frequency", info.getFrequency());
                data.put("speed_mbps", info.getLinkSpeed());
                return mapToJson(data);
            }
            return "{}";
        } catch (Exception e) {
            return "{\"error\":\"" + escapeJson(e.getMessage()) + "\"}";
        }
    }

    // ─── Utils ────────────────────────────────────────────────

    private static int freqToChannel(int freq) {
        if (freq >= 2412 && freq <= 2484) return (freq - 2412) / 5 + 1;
        if (freq >= 5160 && freq <= 5885) return (freq - 5180) / 5 + 36;
        if (freq >= 5955 && freq <= 7115) return (freq - 5950) / 5;
        return 0;
    }

    private static String mapToJson(Map<String, Object> map) {
        StringBuilder json = new StringBuilder("{");
        int i = 0;
        for (Map.Entry<String, Object> e : map.entrySet()) {
            if (i++ > 0) json.append(",");
            json.append("\"").append(e.getKey()).append("\":");
            Object v = e.getValue();
            if (v instanceof String) json.append("\"").append(escapeJson((String) v)).append("\"");
            else if (v instanceof Number) json.append(v);
            else if (v instanceof Boolean) json.append(v);
            else json.append("\"\"");
        }
        json.append("}");
        return json.toString();
    }

    private static String escapeJson(String s) {
        if (s == null) return "";
        return s.replace("\\", "\\\\")
                .replace("\"", "\\\"")
                .replace("\n", "\\n")
                .replace("\r", "\\r")
                .replace("\t", "\\t");
    }
}
