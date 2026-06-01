import time
import threading


def _format_bps(bps):
    if bps is None:
        return "—"
    if bps >= 1_000_000_000:
        return f"{bps / 1_000_000_000:.1f} Gbps"
    if bps >= 1_000_000:
        return f"{bps / 1_000_000:.1f} Mbps"
    if bps >= 1_000:
        return f"{bps / 1_000:.1f} Kbps"
    return f"{bps:.0f} bps"


def _format_bytes(bytes_val):
    if bytes_val is None:
        return "—"
    if bytes_val >= 1_073_741_824:
        return f"{bytes_val / 1_073_741_824:.1f} GB"
    if bytes_val >= 1_048_576:
        return f"{bytes_val / 1_048_576:.1f} MB"
    if bytes_val >= 1_024:
        return f"{bytes_val / 1_024:.1f} KB"
    return f"{bytes_val} B"


_progress = {"status": "idle", "download": 0, "upload": 0, "ping": 0, "server": "", "ip": ""}
_lock = threading.Lock()


def get_progress():
    with _lock:
        return dict(_progress)


def _set(k, v):
    with _lock:
        _progress[k] = v


def run_speedtest():
    try:
        import speedtest

        _set("status", "Buscando servidores...")
        st = speedtest.Speedtest(secure=True)
        st.get_servers()
        _set("status", "Seleccionando mejor servidor...")
        best = st.get_best_server()
        _set("server", f"{best['host']} ({best['sponsor']})")
        try:
            _set("ping", round(float(best.get("lat", 0)), 1))
        except (ValueError, TypeError):
            _set("ping", 0)
        _set("ip", st.results.client.get("ip", ""))

        _set("status", "Probando descarga...")
        _set("download", 0)
        st.download(threads=4)
        dl = st.results.download
        _set("download", int(dl))

        _set("status", "Probando subida...")
        _set("upload", 0)
        st.upload(threads=4)
        ul = st.results.upload
        _set("upload", int(ul))

        _set("status", "Completado")
        return {
            "status": "ok",
            "download_bps": int(dl) if dl else 0,
            "upload_bps": int(ul) if ul else 0,
            "ping_ms": _progress["ping"],
            "server": _progress["server"],
            "ip": _progress["ip"],
            "download_human": _format_bps(dl),
            "upload_human": _format_bps(ul),
        }
    except Exception as e:
        _set("status", f"Error: {e}")
        return {"status": "error", "error": str(e)}
