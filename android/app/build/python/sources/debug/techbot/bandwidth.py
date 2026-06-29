import time
import threading
from .snmp import snmp_get, get_interfaces


STORAGE = {}
LOCK = threading.Lock()


def _get_counter(host, community, oid):
    """Obtiene contador SNMP como entero."""
    val = snmp_get(host, community, oid)
    if val is None:
        return None
    try:
        return int(val)
    except (ValueError, TypeError):
        return None


def poll_interface(host, community, ifindex, name):
    """Pollea tráfico de una interfaz SNMP."""

    oid_in = f"1.3.6.1.2.1.2.2.1.10.{ifindex}"
    oid_out = f"1.3.6.1.2.1.2.2.1.16.{ifindex}"
    in_bytes = _get_counter(host, community, oid_in)
    out_bytes = _get_counter(host, community, oid_out)
    now = time.time()
    key = f"{host}_{ifindex}"
    result = {"host": host, "ifindex": ifindex, "name": name}

    if in_bytes is None and out_bytes is None:
        result["error"] = f"No se pudo obtener contadores SNMP de {host}. Verificá que el dispositivo responda y la community sea correcta."
        return result

    with LOCK:
        entry = STORAGE.get(key)
        if not entry:
            STORAGE[key] = {
                "host": host, "ifindex": ifindex, "name": name,
                "history": [], "last_in": in_bytes, "last_out": out_bytes, "last_time": now,
            }
            result["in_bytes"] = in_bytes
            result["out_bytes"] = out_bytes
            return result

        if entry["last_in"] is not None and in_bytes is not None:
            elapsed = now - entry["last_time"]
            if elapsed > 0:
                delta_in = in_bytes - entry["last_in"]
                delta_out = out_bytes - entry["last_out"]
                if delta_in < 0: delta_in += 2**32
                if delta_out < 0: delta_out += 2**32
                in_bps = int(delta_in * 8 / elapsed)
                out_bps = int(delta_out * 8 / elapsed)
                entry["history"].append({"time": now, "in_bps": in_bps, "out_bps": out_bps})
                if len(entry["history"]) > 600:
                    entry["history"] = entry["history"][-600:]
                result["in_bps"] = in_bps
                result["out_bps"] = out_bps

        entry["last_in"] = in_bytes
        entry["last_out"] = out_bytes
        entry["last_time"] = now
        result["in_bytes"] = in_bytes
        result["out_bytes"] = out_bytes

    return result


def get_traffic(host, ifindex):
    """Retorna datos históricos de tráfico."""
    key = f"{host}_{ifindex}"
    with LOCK:
        entry = STORAGE.get(key)
        if not entry or not entry["history"]:
            return None
        history = entry["history"]
        latest = history[-1]
        in_mbps = round(latest["in_bps"] / 1_000_000, 2)
        out_mbps = round(latest["out_bps"] / 1_000_000, 2)
        in_rates = [p["in_bps"] for p in history]
        out_rates = [p["out_bps"] for p in history]
        avg_in = round(sum(in_rates) / len(in_rates) / 1_000_000, 2)
        avg_out = round(sum(out_rates) / len(out_rates) / 1_000_000, 2)
        max_in = round(max(in_rates) / 1_000_000, 2)
        max_out = round(max(out_rates) / 1_000_000, 2)
        points = [{"t": p["time"], "in": round(p["in_bps"] / 1_000_000, 2), "out": round(p["out_bps"] / 1_000_000, 2)} for p in history[-120:]]
        return {
            "host": host, "ifindex": ifindex, "name": entry["name"],
            "latest": {"in_mbps": in_mbps, "out_mbps": out_mbps},
            "avg_in_mbps": avg_in, "avg_out_mbps": avg_out,
            "max_in_mbps": max_in, "max_out_mbps": max_out,
            "points": points,
        }
