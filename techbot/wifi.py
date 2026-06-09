import subprocess
import re
import platform
import sys
import json
import os
import shutil

OS = platform.system()

# ─── Android bridge (Chaquopy) ──────────────────────────────
_ANDROID = hasattr(sys, 'getandroidapilevel') or 'ANDROID_ROOT' in os.environ
_techbot_bridge = None

def _android_wifi_scan():
    """Usa TechBotBridge Java para WiFi scan nativo Android."""
    global _techbot_bridge
    try:
        from com.techbot.bridge import TechBotBridge
        _techbot_bridge = TechBotBridge
        result = TechBotBridge.wifiScan()
        data = json.loads(result)
        if isinstance(data, list):
            return data
        return None
    except Exception as e:
        return None

def _android_wifi_connection():
    """Usa TechBotBridge Java para info de conexión WiFi."""
    try:
        if _techbot_bridge is not None:
            result = _techbot_bridge.wifiConnectionInfo()
            return json.loads(result)
    except:
        pass
    return None

def _is_termux():
    return "com.termux" in os.environ.get("PREFIX", "") or os.path.exists("/data/data/com.termux")


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
        if m: net["frequency_ghz"] = float(m.group(1))
        m = re.search(r"Quality[= ](\d+)/?(\d*)", block)
        if m:
            sig = int(m.group(1))
            denom = int(m.group(2)) if m.group(2) else 100
            net["quality"] = f"{sig}/{denom}"
            net["signal_pct"] = round((sig / denom) * 100)
        m = re.search(r"Encryption key[= ](\w+)", block)
        if m: net["encrypted"] = m.group(1).lower() == "on"
        m = re.search(r"IE:.*WPA", block)
        net["wpa"] = "WPA2" if "WPA2" in block else "WPA" if m else "Open" if not net.get("encrypted", True) else "WEP"
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
            if m: net["frequency_ghz"] = round(int(m.group(1)) / 1000, 2)
            m = re.search(r"signal: (-\d+)", line)
            if m:
                sig = int(m.group(1))
                net["signal_pct"] = max(0, min(100, round((sig + 100) * 1.25)))
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
            if len(parts) == 2: current["channel"] = int(parts[1].strip())
        elif "Signal" in line and "%" in line:
            parts = line.split(":", 1)
            if len(parts) == 2:
                pct = parts[1].strip().replace("%", "")
                current["signal_pct"] = int(pct)
                current["quality"] = f"{pct}/100"
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


def _termux_scan():
    """Escanea WiFi usando termux-wifi-scaninfo (Termux API)."""
    try:
        # Check if termux-wifi-scaninfo is available
        if not shutil.which("termux-wifi-scaninfo"):
            return None
        result = subprocess.run(
            ["termux-wifi-scaninfo"],
            capture_output=True, text=True, timeout=15
        )
        if result.returncode != 0 or not result.stdout.strip():
            return None
        data = json.loads(result.stdout)
        networks = []
        for net in data:
            networks.append({
                "ssid": net.get("ssid", ""),
                "bssid": net.get("bssid", ""),
                "signal_pct": net.get("rssi", 0),
                "channel": net.get("frequency", ""),
                "frequency_ghz": round(net.get("frequency", 0) / 1000, 2) if net.get("frequency") else None,
                "wpa": "WPA2" if net.get("capabilities", "").upper() == "WPA2" else "WPA",
                "encrypted": True,
            })
        return networks
    except (FileNotFoundError, subprocess.TimeoutExpired, json.JSONDecodeError):
        return None


def scan_wifi(interface=None):
    """Escanea redes WiFi disponibles. Compatible con Linux, Windows, macOS, Termux y Android nativo."""
    try:
        # Prioridad 1: Android nativo (Chaquopy + WifiManager) — NO requiere root ni subprocess
        if _ANDROID:
            nets = _android_wifi_scan()
            if nets is not None:
                return {"networks": nets, "count": len(nets), "interface": "android-native", "method": "WifiManager"}
            # Fallback a Termux API si no hay bridge
            termux_nets = _termux_scan()
            if termux_nets is not None:
                return {"networks": termux_nets, "count": len(termux_nets), "interface": "termux-api", "method": "termux-wifi-scaninfo"}

        # Prioridad 2: Termux API (no requiere root)
        if _is_termux() or OS == "Linux":
            termux_nets = _termux_scan()
            if termux_nets is not None:
                return {"networks": termux_nets, "count": len(termux_nets), "interface": "termux-api", "method": "termux-wifi-scaninfo"}

        if OS == "Linux":
            iface = interface or "wlan0"

            # Prioridad 3: iw (mejor que iwlist, funciona en Android con root)
            iw_path = shutil.which("iw")
            if iw_path:
                try:
                    result = subprocess.run(
                        [iw_path, "dev", iface, "scan"],
                        capture_output=True, text=True, timeout=15
                    )
                    if result.returncode == 0 and result.stdout:
                        networks = _parse_iw_scan(result.stdout)
                        return {"networks": networks, "count": len(networks), "interface": iface, "method": "iw"}
                except:
                    pass

            # Prioridad 4: iwlist (Linux estándar)
            iwlist_path = shutil.which("iwlist")
            if iwlist_path:
                try:
                    result = subprocess.run(
                        [iwlist_path, iface, "scan"],
                        capture_output=True, text=True, timeout=15
                    )
                    if result.returncode == 0 and result.stdout:
                        networks = _parse_iwlist(result.stdout)
                        return {"networks": networks, "count": len(networks), "interface": iface, "method": "iwlist"}
                except:
                    pass

            # Intentar con sudo iwlist
            try:
                result = subprocess.run(
                    ["sudo", iwlist_path or "iwlist", iface, "scan"],
                    capture_output=True, text=True, timeout=15
                )
                if result.returncode == 0 and result.stdout:
                    networks = _parse_iwlist(result.stdout)
                    return {"networks": networks, "count": len(networks), "interface": iface, "method": "sudo-iwlist"}
            except:
                pass

            return {"error": f"No se pudo escanear. Instalá 'iw' o 'iwlist' (Termux: pkg install iw)", "networks": [], "count": 0}

        elif OS == "Windows":
            result = subprocess.run(
                ["netsh", "wlan", "show", "networks", "mode=bssid"],
                capture_output=True, text=True, timeout=15
            )
            if result.returncode == 0:
                networks = _parse_netsh(result.stdout)
                return {"networks": networks, "count": len(networks), "interface": "wlan", "method": "netsh"}
            return {"error": f"Error netsh: {result.stderr[:200]}", "networks": [], "count": 0}

        elif OS == "Darwin":
            result = subprocess.run(
                ["/System/Library/PrivateFrameworks/Apple80211.framework/Versions/Current/Resources/airport", "-s"],
                capture_output=True, text=True, timeout=15
            )
            if result.returncode == 0:
                networks = []
                for line in result.stdout.strip().split("\n")[1:]:
                    parts = line.split()
                    if len(parts) >= 7:
                        networks.append({
                            "ssid": " ".join(parts[:-6]),
                            "bssid": parts[-6],
                            "signal_pct": min(100, max(0, int(parts[-3]) + 100)) if parts[-3].lstrip("-").isdigit() else 0,
                            "channel": parts[-2],
                            "standard": parts[-1],
                        })
                return {"networks": networks, "count": len(networks), "interface": "airport", "method": "airport"}
            return {"error": "airport no disponible", "networks": [], "count": 0}
        else:
            return {"error": f"Sistema no soportado: {OS}", "networks": [], "count": 0}

    except FileNotFoundError:
        return {"error": "Comando WiFi no encontrado. En Termux: pkg install iw termux-api", "networks": [], "count": 0}
    except subprocess.TimeoutExpired:
        return {"error": "Tiempo de espera agotado", "networks": [], "count": 0}
    except Exception as e:
        return {"error": str(e), "networks": [], "count": 0}


def interface_info():
    """Obtiene información de interfaces de red."""
    try:
        if _is_termux():
            try:
                result = subprocess.run(["termux-wifi-connectioninfo"], capture_output=True, text=True, timeout=5)
                if result.returncode == 0 and result.stdout.strip():
                    return {"interfaces": [json.loads(result.stdout)]}
            except:
                pass

        if OS == "Linux":
            result = subprocess.run(["iwconfig"], capture_output=True, text=True, timeout=5)
            interfaces = []
            if result.returncode == 0:
                for block in result.stdout.strip().split("\n\n"):
                    if not block.strip(): continue
                    lines = block.split("\n")
                    iface = {"name": lines[0].split()[0] if lines else "?"}
                    for line in lines:
                        m = re.search(r'ESSID:"([^"]*)"', line)
                        if m: iface["ssid"] = m.group(1)
                        m = re.search(r"Frequency[= :]*([\d.]+)", line)
                        if m: iface["frequency"] = float(m.group(1))
                        m = re.search(r"Mode[=:](\w+)", line)
                        if m: iface["mode"] = m.group(1)
                        m = re.search(r"Quality[= ](\d+)/(\d+)", line)
                        if m: iface["quality"] = f"{m.group(1)}/{m.group(2)}"
                    interfaces.append(iface)
            return {"interfaces": interfaces}
        elif OS == "Windows":
            result = subprocess.run(["netsh", "wlan", "show", "interfaces"], capture_output=True, text=True, timeout=5)
            return {"raw": result.stdout[:500]} if result.stdout else {"error": "No info"}
        else:
            return {"error": f"No soportado en {OS}"}
    except Exception as e:
        return {"error": str(e)}
