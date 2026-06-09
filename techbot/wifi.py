import subprocess
import re
import platform
import sys
import json
import os
import shutil

OS = platform.system()
_ANDROID = hasattr(sys, 'getandroidapilevel') or 'ANDROID_ROOT' in os.environ


def _is_termux():
    return "com.termux" in os.environ.get("PREFIX", "") or os.path.exists("/data/data/com.termux")


# ─── Android bridge (Chaquopy) ──────────────────────────────

def _android_wifi_scan():
    """Usa TechBotBridge Java para WiFi scan nativo Android."""
    try:
        from com.techbot.bridge import TechBotBridge
        result = TechBotBridge.wifiScan()
        data = json.loads(result)
        if isinstance(data, list):
            return data
        if isinstance(data, dict) and "error" in data:
            return None  # bridge returned error, fallback
        return None
    except Exception:
        return None


def _android_wifi_connection():
    try:
        from com.techbot.bridge import TechBotBridge
        result = TechBotBridge.wifiConnectionInfo()
        return json.loads(result)
    except Exception:
        return None


# ─── Termux API ─────────────────────────────────────────────

def _termux_scan():
    if not shutil.which("termux-wifi-scaninfo"):
        return None
    try:
        result = subprocess.run(
            ["termux-wifi-scaninfo"],
            capture_output=True, text=True, timeout=15
        )
        if result.returncode != 0 or not result.stdout.strip():
            return None
        data = json.loads(result.stdout)
        networks = []
        for net in data:
            freq = net.get("frequency", 0) or 0
            rssi = net.get("rssi", 0) or 0
            networks.append({
                "ssid": net.get("ssid", ""),
                "bssid": net.get("bssid", ""),
                "signal_pct": max(0, min(100, int((rssi + 100) * 100 / 70))),
                "channel": _freq_to_channel(int(freq)) if freq else 0,
                "frequency": int(freq) if freq else 0,
                "frequency_ghz": round(int(freq) / 1000, 2) if freq else None,
                "wpa": "WPA2" if "WPA2" in (net.get("capabilities", "") or "") else "WPA",
                "encrypted": True,
            })
        return networks
    except (FileNotFoundError, subprocess.TimeoutExpired, json.JSONDecodeError):
        return None


# ─── Parser helpers ─────────────────────────────────────────

def _freq_to_channel(freq):
    if 2412 <= freq <= 2484: return (freq - 2412) // 5 + 1
    if 5160 <= freq <= 5885: return (freq - 5180) // 5 + 36
    if 5955 <= freq <= 7115: return (freq - 5950) // 5
    return 0


def _parse_iwlist(text):
    networks = []
    blocks = text.split("Cell ")
    for block in blocks[1:]:
        net = {}
        m = re.search(r"Address: ([0-9A-Fa-f:]+)", block)
        if m: net["bssid"] = m.group(1)
        m = re.search(r'ESSID:"([^"]*)"', block)
        if m: net["ssid"] = m.group(1)
        m = re.search(r"Channel[ :]*(\d+)", block)
        if m: net["channel"] = int(m.group(1))
        m = re.search(r"Frequency[ :]*([\d.]+)", block)
        if m:
            freq = float(m.group(1))
            net["frequency_ghz"] = freq
            net["frequency"] = int(freq * 1000)
        m = re.search(r"Quality[= ](\d+)/?(\d*)", block)
        if m:
            sig = int(m.group(1))
            denom = int(m.group(2)) if m.group(2) else 100
            net["quality"] = f"{sig}/{denom}"
            net["signal_pct"] = round((sig / denom) * 100)
        m = re.search(r"IE:.*WPA", block)
        net["encrypted"] = "Encryption key:on" in block
        wpa = "WPA2" if "WPA2" in block else "WPA" if "WPA" in block else "Open" if not net.get("encrypted", True) else "WEP"
        net["wpa"] = wpa
        if net.get("ssid"):
            networks.append(net)
    return networks


def _parse_iw_scan(text):
    networks = []
    blocks = text.split("BSS ")
    for block in blocks[1:]:
        net = {}
        lines = block.split("\n")
        first = lines[0].strip().rstrip(")")
        if "(" in first: first = first[:first.index("(")].strip()
        if ":" in first or re.match(r"^[0-9a-f]{2}", first):
            net["bssid"] = first.split()[0] if first else ""
        for line in lines:
            m = re.search(r"SSID: (.*)", line)
            if m: net["ssid"] = m.group(1).strip()
            m = re.search(r"freq: (\d+)", line)
            if m:
                freq = int(m.group(1))
                net["frequency"] = freq
                net["frequency_ghz"] = round(freq / 1000, 2)
                net["channel"] = _freq_to_channel(freq)
            m = re.search(r"signal: (-\d+)", line)
            if m:
                sig = int(m.group(1))
                net["signal_pct"] = max(0, min(100, int((sig + 100) * 100 / 70)))
            m = re.search(r"channel (\d+)", line)
            if m: net["channel"] = int(m.group(1))
            if "WPA" in line: net["wpa"] = "WPA"
            if "RSN" in line: net["wpa"] = "WPA2"
            if "WEP" in line: net["wpa"] = "WEP"
        if "wpa" not in net: net["wpa"] = "Open"
        if net.get("ssid"):
            networks.append(net)
    return networks


def _parse_netsh(text):
    networks = []
    current = {}
    for line in text.split("\n"):
        line = line.strip()
        if "SSID" in line and ":" in line and "BSSID" not in line:
            parts = line.split(":", 1)
            if len(parts) == 2 and parts[1].strip():
                if current.get("ssid"):
                    networks.append(current)
                current = {"ssid": parts[1].strip()}
        elif "BSSID" in line and ":" in line:
            parts = line.split(":", 1)
            if len(parts) == 2: current["bssid"] = parts[1].strip()
        elif "Channel" in line and ":" in line:
            parts = line.split(":", 1)
            if len(parts) == 2:
                try: current["channel"] = int(parts[1].strip())
                except: pass
        elif "Signal" in line and "%" in line:
            parts = line.split(":", 1)
            if len(parts) == 2:
                try:
                    pct = int(parts[1].strip().replace("%", ""))
                    current["signal_pct"] = pct
                except: pass
        elif "Radio type" in line and ":" in line:
            parts = line.split(":", 1)
            if len(parts) == 2:
                v = parts[1].strip()
                if "802.11" in v: current["standard"] = v
        elif "Authentication" in line and ":" in line:
            parts = line.split(":", 1)
            if len(parts) == 2:
                auth = parts[1].strip()
                current["wpa"] = auth if auth != "Open" else "Open"
                current["encrypted"] = auth != "Open"
    if current.get("ssid"):
        networks.append(current)
    return networks


def _parse_airport(text):
    networks = []
    for line in text.strip().split("\n")[1:]:
        parts = line.split()
        if len(parts) >= 7:
            ssid = " ".join(parts[:-6])
            sig_raw = parts[-3]
            try:
                sig = int(sig_raw)
                signal = max(0, min(100, int((sig + 100) * 100 / 70)))
            except:
                signal = 0
            try:
                ch = int(parts[-2])
            except:
                ch = 0
            networks.append({
                "ssid": ssid,
                "bssid": parts[-6],
                "signal_pct": signal,
                "channel": ch,
                "standard": parts[-1],
            })
    return networks


# ─── Main scan entry point ──────────────────────────────────

def scan_wifi(interface=None):
    """Escanea redes WiFi en las 4 plataformas con fallbacks progresivos."""
    result = {"networks": [], "count": 0}

    try:
        # ── Android (Chaquopy APK) ──
        if _ANDROID:
            nets = _android_wifi_scan()
            if nets is not None and len(nets) > 0:
                return {**result, "networks": nets, "count": len(nets), "interface": "android-native", "method": "WifiManager"}
            # bridge no disponible o sin redes → fallback

        # ── Termux API ──
        if _is_termux() or shutil.which("termux-wifi-scaninfo"):
            nets = _termux_scan()
            if nets is not None and len(nets) > 0:
                return {**result, "networks": nets, "count": len(nets), "interface": "termux-api", "method": "termux-wifi-scaninfo"}

        # ── Linux: iw, luego iwlist (sin sudo) ──
        if OS == "Linux":
            iface = interface or _detect_wifi_iface() or "wlan0"
            iw = shutil.which("iw")
            if iw:
                try:
                    r = subprocess.run([iw, "dev", iface, "scan"], capture_output=True, text=True, timeout=15)
                    if r.returncode == 0 and r.stdout:
                        nets = _parse_iw_scan(r.stdout)
                        if nets:
                            return {**result, "networks": nets, "count": len(nets), "interface": iface, "method": "iw"}
                except: pass
            iwlist = shutil.which("iwlist")
            if iwlist:
                try:
                    r = subprocess.run([iwlist, iface, "scan"], capture_output=True, text=True, timeout=15)
                    if r.returncode == 0 and r.stdout:
                        nets = _parse_iwlist(r.stdout)
                        if nets:
                            return {**result, "networks": nets, "count": len(nets), "interface": iface, "method": "iwlist"}
                except: pass
            return {**result, "error": "WiFi scan requiere 'iw' o 'iwlist' con permisos. En Termux: pkg install iw"}

        # ── Windows: netsh ──
        if OS == "Windows":
            r = subprocess.run(["netsh", "wlan", "show", "networks", "mode=bssid"],
                               capture_output=True, text=True, timeout=15)
            if r.returncode == 0 and r.stdout:
                nets = _parse_netsh(r.stdout)
                return {**result, "networks": nets, "count": len(nets), "interface": "wlan", "method": "netsh"}
            return {**result, "error": "netsh: " + (r.stderr[:200] or "Sin redes disponibles")}

        # ── macOS: airport ──
        if OS == "Darwin":
            airport = "/System/Library/PrivateFrameworks/Apple80211.framework/Versions/Current/Resources/airport"
            if os.path.exists(airport):
                r = subprocess.run([airport, "-s"], capture_output=True, text=True, timeout=15)
                if r.returncode == 0 and r.stdout:
                    nets = _parse_airport(r.stdout)
                    return {**result, "networks": nets, "count": len(nets), "interface": "airport", "method": "airport"}
            return {**result, "error": "airport no disponible"}

        return {**result, "error": f"Sistema no soportado: {OS}"}

    except FileNotFoundError:
        return {**result, "error": "Comando WiFi no encontrado"}
    except subprocess.TimeoutExpired:
        return {**result, "error": "Tiempo de espera agotado"}
    except Exception as e:
        return {**result, "error": str(e)}


def _detect_wifi_iface():
    try:
        r = subprocess.run(["iw", "dev"], capture_output=True, text=True, timeout=5)
        for m in re.finditer(r"Interface\s+(\w+)", r.stdout):
            return m.group(1)
    except: pass
    try:
        r = subprocess.run(["iwconfig"], capture_output=True, text=True, timeout=5)
        for line in r.stdout.split("\n"):
            if "IEEE 802.11" in line:
                return line.split()[0]
    except: pass
    return None


# ─── Interface info ─────────────────────────────────────────

def interface_info():
    """Obtiene información de interfaces WiFi."""
    try:
        if _ANDROID:
            info = _android_wifi_connection()
            if info and "ssid" in info:
                return {"interfaces": [info]}

        if _is_termux():
            try:
                r = subprocess.run(["termux-wifi-connectioninfo"], capture_output=True, text=True, timeout=5)
                if r.returncode == 0 and r.stdout.strip():
                    return {"interfaces": [json.loads(r.stdout)]}
            except: pass

        if OS == "Linux":
            iface = _detect_wifi_iface()
            if iface:
                r = subprocess.run(["iwconfig"], capture_output=True, text=True, timeout=5)
                interfaces = []
                for block in r.stdout.strip().split("\n\n"):
                    if not block.strip(): continue
                    lines = block.split("\n")
                    i = {"name": lines[0].split()[0] if lines else "?"}
                    for line in lines:
                        m = re.search(r'ESSID:"([^"]*)"', line)
                        if m: i["ssid"] = m.group(1)
                        m = re.search(r"Frequency[= :]*([\d.]+)", line)
                        if m: i["frequency"] = float(m.group(1))
                        m = re.search(r"Mode[=:](\w+)", line)
                        if m: i["mode"] = m.group(1)
                        m = re.search(r"Quality[= ](\d+)/(\d+)", line)
                        if m: i["quality"] = f"{m.group(1)}/{m.group(2)}"
                    interfaces.append(i)
                return {"interfaces": interfaces}
        elif OS == "Windows":
            r = subprocess.run(["netsh", "wlan", "show", "interfaces"], capture_output=True, text=True, timeout=5)
            return {"raw": r.stdout[:500]} if r.stdout else {"error": "No info"}
        elif OS == "Darwin":
            airport = "/System/Library/PrivateFrameworks/Apple80211.framework/Versions/Current/Resources/airport"
            if os.path.exists(airport):
                r = subprocess.run([airport, "-I"], capture_output=True, text=True, timeout=5)
                return {"raw": r.stdout[:500]} if r.stdout else {"error": "No info"}
        return {"error": f"No soportado en {OS}"}
    except Exception as e:
        return {"error": str(e)}
