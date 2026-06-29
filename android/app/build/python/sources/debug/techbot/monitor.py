import threading
import time
import json
import urllib.request
import urllib.parse

from techbot.scanner import discover_hosts

_monitors = {}
_lock = threading.Lock()


def start_monitor(subnet, interval=300, ntfy_topic=None):
    """Inicia monitoreo de subred."""
    with _lock:
        if subnet in _monitors:
            return {"error": f"Ya se está monitoreando {subnet}", "running": True}
        mon = {
            "subnet": subnet,
            "interval": interval,
            "ntfy_topic": ntfy_topic,
            "running": True,
            "last_hosts": [],
            "last_check": None,
            "checks": 0,
            "changes": [],
            "stop_event": threading.Event(),
        }
        _monitors[subnet] = mon
        t = threading.Thread(target=_run_monitor, args=(subnet,), daemon=True)
        t.start()
        return {"subnet": subnet, "interval": interval, "status": "started"}


def stop_monitor(subnet):
    """Detiene monitoreo de subred."""
    with _lock:
        mon = _monitors.get(subnet)
        if not mon:
            return {"error": f"No se monitorea {subnet}"}
        mon["stop_event"].set()
        del _monitors[subnet]
        return {"subnet": subnet, "status": "stopped"}


def list_monitors():
    """Lista subredes monitoreadas."""
    with _lock:
        result = {}
        for subnet, mon in _monitors.items():
            result[subnet] = {
                "interval": mon["interval"],
                "running": mon["running"],
                "last_check": mon["last_check"],
                "checks": mon["checks"],
                "hosts_found": len(mon["last_hosts"]),
                "changes": mon["changes"][-5:],
                "ntfy_topic": mon.get("ntfy_topic"),
            }
        return result


def _run_monitor(subnet):
    """Loop de monitoreo."""
    with _lock:
        mon = _monitors.get(subnet)
        if not mon:
            return
        interval = mon["interval"]
        ntfy_topic = mon["ntfy_topic"]
        stop = mon["stop_event"]

    while not stop.is_set():
        try:
            hosts = discover_hosts(subnet, timeout=1.5)
            with _lock:
                mon = _monitors.get(subnet)
                if not mon:
                    return
                mon["last_check"] = time.time()
                mon["checks"] += 1
                previous = set(mon["last_hosts"])
                current = set(h["host"] for h in hosts)
                new_hosts = current - previous
                gone_hosts = previous - current
                if new_hosts or gone_hosts:
                    change = {
                        "time": time.time(),
                        "new": list(new_hosts),
                        "gone": list(gone_hosts),
                    }
                    mon["changes"].append(change)
                    mon["last_hosts"] = list(current)
                    if ntfy_topic and (new_hosts or gone_hosts):
                        _send_notification(ntfy_topic, subnet, new_hosts, gone_hosts)
                else:
                    mon["last_hosts"] = list(current)
        except Exception:
            pass
        stop.wait(interval)


def _send_notification(topic, subnet, new_hosts, gone_hosts):
    """Envía notificación vía ntfy.sh."""
    lines = []
    if new_hosts:
        lines.append(f"Nuevos: {', '.join(new_hosts)}")
    if gone_hosts:
        lines.append(f"Desconectados: {', '.join(gone_hosts)}")
    msg = f"📡 {subnet}\n" + "\n".join(lines)
    try:
        req = urllib.request.Request(
            f"https://ntfy.sh/{urllib.parse.quote(topic)}",
            data=msg.encode(),
            headers={"Title": "TechBot Monitor"},
        )
        urllib.request.urlopen(req, timeout=5)
    except Exception:
        pass
