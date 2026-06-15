import time
import threading
import socket
import urllib.request
import urllib.error
import json
import os

_TEST_FILES = [
    ("http://speedtest.tele2.net/100MB.zip", 100_000_000),
    ("http://speedtest.tele2.net/10MB.zip",  10_000_000),
    ("http://speedtest.tele2.net/5MB.zip",    5_000_000),
    ("http://speedtest.tele2.net/1MB.zip",    1_000_000),
    ("http://speedtest.tele2.net/100KB.zip",    100_000),
    ("https://proof.ovh.net/files/10Mb.dat", 10_000_000),
    ("https://proof.ovh.net/files/1Mb.dat",   1_000_000),
]

_PING_HOSTS = [
    ("8.8.8.8", 443),
    ("1.1.1.1", 443),
    ("208.67.222.222", 443),
    ("9.9.9.9", 443),
]

_IP_SERVICES = [
    ("https://api.ipify.org?format=json", "json", "ip"),
    ("https://httpbin.org/ip", "json", "origin"),
    ("http://ifconfig.me/ip", "text", None),
    ("https://icanhazip.com", "text", None),
    ("https://ip-api.com/line/?fields=query", "text", None),
]


def _format_bps(bps):
    if bps is None: return "\u2014"
    if bps >= 1_000_000_000: return f"{bps / 1_000_000_000:.1f} Gbps"
    if bps >= 1_000_000: return f"{bps / 1_000_000:.1f} Mbps"
    if bps >= 1_000: return f"{bps / 1_000:.1f} Kbps"
    return f"{bps:.0f} bps"


def _format_bytes(bytes_val):
    if bytes_val is None: return "\u2014"
    if bytes_val >= 1_073_741_824: return f"{bytes_val / 1_073_741_824:.1f} GB"
    if bytes_val >= 1_048_576: return f"{bytes_val / 1_048_576:.1f} MB"
    if bytes_val >= 1_024: return f"{bytes_val / 1_024:.1f} KB"
    return f"{bytes_val} B"


_UPLOAD_SIZES = [1_048_576, 5_242_880, 10_485_760]  # 1MB, 5MB, 10MB
_UPLOAD_URL = "http://speedtest.tele2.net/upload.php"

_progress = {"status": "idle", "download": 0, "upload": 0, "ping": 0, "server": "", "ip": ""}
_lock = threading.Lock()


def get_progress():
    with _lock:
        return dict(_progress)


def _set(k, v):
    with _lock:
        _progress[k] = v


def _fetch_public_ip():
    """Obtiene IP pública desde múltiples servicios."""
    for url, fmt, key in _IP_SERVICES:
        try:
            req = urllib.request.Request(url, method="GET")
            req.add_header("User-Agent", "TechBot/1.0")
            resp = urllib.request.urlopen(req, timeout=5)
            text = resp.read().decode("utf-8", errors="replace").strip()
            resp.close()
            if fmt == "text":
                ip = text.split("\n")[0].strip()
                if ip: return ip
            else:
                data = json.loads(text)
                ip = data.get(key, "").strip()
                if ip: return ip
        except:
            pass
    return ""


def _tcp_ping(host, port, timeout=3):
    try:
        start = time.time()
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(timeout)
        s.connect((host, port))
        elapsed = (time.time() - start) * 1000
        s.close()
        return round(elapsed, 1)
    except:
        return None


def _download_speed(url, expected_size, duration=8):
    try:
        req = urllib.request.Request(url, method="GET")
        req.add_header("User-Agent", "TechBot/1.0")
        start = time.time()
        resp = urllib.request.urlopen(req, timeout=duration + 15)
        total = 0
        deadline = start + duration
        while time.time() < deadline:
            try:
                chunk = resp.read(65536)
                if not chunk: break
                total += len(chunk)
            except:
                break
        elapsed = time.time() - start
        resp.close()
        if elapsed > 0 and total > 0:
            bps = int(total * 8 / elapsed)
            return bps, total
        return 0, total
    except Exception as e:
        return 0, 0


def _upload_speed(url, size, duration=8):
    try:
        data = os.urandom(size)
        req = urllib.request.Request(url, method="POST", data=data)
        req.add_header("User-Agent", "TechBot/1.0")
        req.add_header("Content-Type", "application/octet-stream")
        start = time.time()
        resp = urllib.request.urlopen(req, timeout=duration + 15)
        elapsed = time.time() - start
        resp.read()
        resp.close()
        if elapsed > 0:
            bps = int(size * 8 / elapsed)
            return bps, size
        return 0, 0
    except Exception as e:
        return 0, 0


def run_speedtest():
    try:
        _set("status", "Obteniendo IP pública...")
        public_ip = _fetch_public_ip()
        _set("ip", public_ip)

        _set("status", "Midiendo latencia...")
        pings = [p for p in [_tcp_ping(h, p) for h, p in _PING_HOSTS] if p is not None]
        avg_ping = round(sum(pings) / len(pings), 1) if pings else 0
        _set("ping", avg_ping)
        best_ping_host = _PING_HOSTS[pings.index(min(pings))][0] if pings else "N/A"
        _set("server", f"{best_ping_host} (TCP ping)")

        _set("status", "Probando descarga...")
        dl_bps, dl_bytes = 0, 0
        for url, size in _TEST_FILES:
            _set("status", f"Descargando {url.split('/')[-1]}...")
            bps, total = _download_speed(url, size)
            if bps > dl_bps:
                dl_bps = bps
                dl_bytes = total
            if dl_bps > 0:
                break

        _set("download", dl_bps)

        _set("status", "Probando subida...")
        ul_bps = 0
        for size in _UPLOAD_SIZES:
            _set("status", f"Subiendo {_format_bytes(size)}...")
            bps, _ = _upload_speed(_UPLOAD_URL, size)
            if bps > ul_bps:
                ul_bps = bps
            if ul_bps > 0:
                break

        _set("upload", ul_bps)
        _set("status", "Completado")

        return {
            "status": "ok",
            "download_bps": dl_bps,
            "upload_bps": ul_bps,
            "ping_ms": avg_ping,
            "server": _progress["server"],
            "ip": public_ip,
            "download_human": _format_bps(dl_bps),
            "upload_human": _format_bps(ul_bps),
        }
    except Exception as e:
        _set("status", f"Error: {e}")
        return {"status": "error", "error": str(e)}
