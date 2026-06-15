import time
import threading
import socket
import urllib.request
import urllib.error
import json
import os
from concurrent.futures import ThreadPoolExecutor, as_completed

_STREAMS = 6
_DURATION = 10
_CONNECT_TIMEOUT = 25

_DL_URL = "http://speedtest.tele2.net/100MB.zip"
_UL_URL = "http://speedtest.tele2.net/upload.php"

_DL_FALLBACKS = [
    "http://speedtest.tele2.net/10MB.zip",
    "http://speedtest.tele2.net/5MB.zip",
    "https://proof.ovh.net/files/10Mb.dat",
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


_progress = {"status": "idle", "download": 0, "upload": 0, "ping": 0, "server": "", "ip": ""}
_lock = threading.Lock()


def get_progress():
    with _lock:
        return dict(_progress)


def _set(k, v):
    with _lock:
        _progress[k] = v


def _fetch_public_ip():
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


def _parallel_download(url, duration, streams):
    total = [0]
    stop = [False]

    def worker():
        deadline = time.time() + duration
        while time.time() < deadline and not stop[0]:
            try:
                req = urllib.request.Request(url, method="GET")
                req.add_header("User-Agent", "TechBot/1.0")
                resp = urllib.request.urlopen(req, timeout=_CONNECT_TIMEOUT)
                while time.time() < deadline and not stop[0]:
                    try:
                        chunk = resp.read(65536)
                        if not chunk:
                            break
                        total[0] += len(chunk)
                    except:
                        break
                resp.close()
            except:
                pass

    threads = [threading.Thread(target=worker, daemon=True) for _ in range(streams)]
    for t in threads: t.start()
    for t in threads: t.join(timeout=duration + _CONNECT_TIMEOUT + 5)
    stop[0] = True
    return total[0]


def _parallel_upload(url, duration, streams):
    total = [0]
    stop = [False]
    chunk_size = 262144

    def worker():
        deadline = time.time() + duration
        while time.time() < deadline and not stop[0]:
            try:
                data = os.urandom(chunk_size)
                req = urllib.request.Request(url, method="POST", data=data)
                req.add_header("User-Agent", "TechBot/1.0")
                req.add_header("Content-Type", "application/octet-stream")
                resp = urllib.request.urlopen(req, timeout=_CONNECT_TIMEOUT)
                resp.read()
                resp.close()
                total[0] += len(data)
            except:
                pass

    threads = [threading.Thread(target=worker, daemon=True) for _ in range(streams)]
    for t in threads: t.start()
    for t in threads: t.join(timeout=duration + _CONNECT_TIMEOUT + 5)
    stop[0] = True
    return total[0]


def _try_download(dl_url, streams, duration):
    total_bytes = _parallel_download(dl_url, duration, streams)
    if total_bytes > 0:
        bps = int(total_bytes * 8 / duration)
        return bps, total_bytes
    return 0, 0


def run_speedtest(custom_url=None):
    try:
        _set("status", "Obteniendo IP pública...")
        public_ip = _fetch_public_ip()
        _set("ip", public_ip)

        _set("status", "Midiendo latencia...")
        pings = [p for p in [_tcp_ping(h, p) for h, p in _PING_HOSTS] if p is not None]
        avg_ping = round(sum(pings) / len(pings), 1) if pings else 0
        _set("ping", avg_ping)
        best_ping = _PING_HOSTS[pings.index(min(pings))][0] if pings else "N/A"
        server_name = custom_url or f"{best_ping} (multi-stream)"
        _set("server", server_name)

        _set("status", "Descargando (6 streams)...")
        dl_url = custom_url or _DL_URL
        dl_bps, dl_bytes = 0, 0

        if custom_url:
            dl_bps, dl_bytes = _try_download(custom_url, _STREAMS, _DURATION)
        if dl_bps == 0:
            for fallback in [dl_url] + _DL_FALLBACKS:
                dl_bps, dl_bytes = _try_download(fallback, _STREAMS, _DURATION)
                if dl_bps > 0:
                    break
        _set("download", dl_bps)

        _set("status", "Subiendo (6 streams)...")
        total_bytes = _parallel_upload(_UL_URL, _DURATION, _STREAMS)
        ul_bps = int(total_bytes * 8 / _DURATION) if total_bytes > 0 else 0
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
