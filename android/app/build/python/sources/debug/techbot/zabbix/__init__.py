import requests
import json
import os
import time
import threading
from datetime import datetime

ZABBIX_API_URL = "http://localhost:8080/api_jsonrpc.php"
ZABBIX_DEFAULT_USER = "Admin"
ZABBIX_DEFAULT_PASS = "zabbix"

TOPOLOGIA = """
SISTEMA DE TELEMETRIA DE ENERGIA CRITICA — TOPOLOGIA ABSOLUTA
═══════════════════════════════════════════════════════════════

  NOC CENTRAL (SERVER DEBIAN 12)
  ┌──────────────────────────────────────────┐
  │  Zabbix 6.4 LTS                          │
  │  PostgreSQL (Pool Telemetria)            │
  │  Nginx Frontend (:80/:443)               │
  │  IP VPN: 10.0.0.1 (WireGuard Endpoint)  │
  │  Puerto 10051 — Polling + Traps          │
  └──────────┬───────────────────────────────┘
             │ WireGuard VPN (UDP 51820)
             │ Cifrado E2E — Tunnel
             │ 10.0.0.1 <> 10.0.0.2
  ┌──────────▼───────────────────────────────┐
  │  SUCURSAL REMOTA (CLIENTE MSP)           │
  │                                          │
  │  ┌──────────────────────────────────┐    │
  │  │  UPS INDUSTRIAL (via SNMPv3)     │    │
  │  │  192.168.10.50                   │    │
  │  │  SNMPv3 AuthPriv SHA/AES         │    │
  │  │  UDP :161 — Monitoreo Remoto     │    │
  │  └──────────────────────────────────┘    │
  │                                          │
  │  ┌──────────────────────────────────┐    │
  │  │  UPS LOCAL (via USB)             │    │
  │  │  Conectado al Gateway            │    │
  │  │  NUT / apcupsd / pwrstat         │    │
  │  │  Monitoreo via Zabbix Agent      │    │
  │  │  UserParameter — TCP :10050      │    │
  │  └──────────────────────────────────┘    │
  │                                          │
  │  ┌──────────────────────────────────┐    │
  │  │  SONDA AMBIENTAL                 │    │
  │  │  Temp | Hum | Contactos Secos    │    │
  │  │  (Puertas/Agua)                 │    │
  │  └──────────────────────────────────┘    │
  │                                          │
  │  Gateway — Zabbix Agent (TCP :10050)     │
  │  IP VPN: 10.0.0.2 — Polling Items        │
  └──────────────────────────────────────────┘

  Dashboard SLAs :80/:443 via Nginx Frontend
  SQL Indexado en PostgreSQL — zabbix DB
"""

SEVERIDAD_NOMBRES = ["Sin clasificar", "Informacion", "Advertencia", "Media", "Alta", "Desastre"]


class ZabbixAPIError(Exception):
    pass


class ZabbixAPI:
    def __init__(self, api_url=ZABBIX_API_URL, user=ZABBIX_DEFAULT_USER, password=ZABBIX_DEFAULT_PASS):
        self.api_url = api_url
        self.user = user
        self.password = password
        self.auth_token = None
        self._req_id = 0

    def _call(self, method, params=None):
        self._req_id += 1
        payload = {
            "jsonrpc": "2.0",
            "method": method,
            "params": params or {},
            "id": self._req_id,
        }
        if self.auth_token:
            payload["auth"] = self.auth_token
        try:
            r = requests.post(self.api_url, json=payload, timeout=15)
            r.raise_for_status()
            data = r.json()
        except requests.exceptions.ConnectionError:
            raise ZabbixAPIError("No se pudo conectar al servidor Zabbix")
        except requests.exceptions.Timeout:
            raise ZabbixAPIError("Timeout al conectar con Zabbix")
        except requests.exceptions.RequestException as e:
            raise ZabbixAPIError(f"Error de conexion: {e}")
        except json.JSONDecodeError:
            raise ZabbixAPIError("Respuesta invalida del servidor Zabbix")
        if "error" in data:
            err = data["error"]
            raise ZabbixAPIError(f"Error Zabbix API: {err.get('message','')} ({err.get('code','')})")
        return data.get("result")

    def login(self):
        self.auth_token = None
        result = self._call("user.login", {
            "username": self.user,
            "password": self.password,
        })
        if isinstance(result, str):
            self.auth_token = result
            return True
        return False

    def logout(self):
        if self.auth_token:
            self._call("user.logout")
            self.auth_token = None

    def api_version(self):
        return self._call("apiinfo.version")

    def check_connection(self):
        try:
            v = self.api_version()
            self.login()
            return {"connected": True, "version": v, "user": self.user}
        except ZabbixAPIError as e:
            return {"connected": False, "error": str(e)}

    def get_hosts(self, host=None):
        params = {
            "output": ["hostid", "host", "name", "status"],
            "selectInterfaces": ["interfaceid", "ip", "dns", "port", "type"],
            "selectGroups": ["groupid", "name"],
            "selectParentTemplates": ["templateid", "name"],
            "selectItems": ["itemid", "name", "key_", "lastvalue", "lastclock", "value_type", "units"],
            "selectTriggers": ["triggerid", "description", "priority", "value", "lastchange"],
            "selectInventory": ["model", "serial_no", "location"],
        }
        if host:
            params["filter"] = {"host": host}
        return self._call("host.get", params)

    def get_problems(self, recent=True, severity=None, limit=50):
        params = {
            "output": "extend",
            "selectTags": ["tag", "value"],
            "sortfield": ["eventid"],
            "sortorder": "DESC",
            "limit": limit,
        }
        if recent:
            params["recent"] = "true"
        if severity is not None:
            params["severities"] = [severity] if isinstance(severity, int) else severity
        return self._call("problem.get", params)

    def get_events(self, limit=50, severities=None):
        params = {
            "output": "extend",
            "selectHosts": ["hostid", "host", "name"],
            "selectRelatedObject": ["triggerid", "description", "priority"],
            "sortfield": ["clock"],
            "sortorder": "DESC",
            "limit": limit,
        }
        if severities:
            params["severities"] = severities
        return self._call("event.get", params)

    def get_alerts(self, limit=50):
        params = {
            "output": "extend",
            "selectHosts": ["hostid", "host", "name"],
            "sortfield": ["clock"],
            "sortorder": "DESC",
            "limit": limit,
        }
        return self._call("alert.get", params)

    def acknowledge_event(self, eventid, message=""):
        return self._call("event.acknowledge", {
            "eventids": eventid,
            "message": message or "Visto por TechBot",
        })

    def get_history(self, itemid, limit=100, history_type=0):
        params = {
            "output": "extend",
            "itemids": itemid,
            "history": history_type,
            "sortfield": "clock",
            "sortorder": "DESC",
            "limit": limit,
        }
        return self._call("history.get", params)

    def get_item(self, item_key, hostid=None):
        params = {
            "output": ["itemid", "name", "key_", "lastvalue", "lastclock", "value_type", "units"],
            "filter": {"key_": item_key},
        }
        if hostid:
            params["hostids"] = hostid
        return self._call("item.get", params)

    def get_trigger(self, triggerid=None, hostid=None):
        params = {
            "output": ["triggerid", "description", "expression", "priority", "value", "lastchange", "status"],
            "selectHosts": ["hostid", "host", "name"],
        }
        if triggerid:
            params["triggerids"] = triggerid
        if hostid:
            params["hostids"] = hostid
        return self._call("trigger.get", params)


# ─── NOTIFICACIONES ────────────────────────────────────────────


def get_notificaciones(api, severity_min=None, limit=20):
    try:
        api.login()
        problems = api.get_problems(recent=True, limit=limit)
        notificaciones = []
        for p in problems:
            severity = int(p.get("severity", 0))
            if severity_min is not None and severity < severity_min:
                continue
            notificaciones.append({
                "eventid": p.get("eventid"),
                "source": p.get("source"),
                "object": p.get("object"),
                "objectid": p.get("objectid"),
                "clock": datetime.fromtimestamp(int(p.get("clock", 0))).strftime("%d/%m/%Y %H:%M:%S") if p.get("clock") else "N/A",
                "name": p.get("name", "Sin nombre"),
                "severity": severity,
                "severity_name": SEVERIDAD_NOMBRES[severity] if severity <= 5 else "Desconocida",
                "acknowledged": p.get("acknowledged", "0"),
                "tags": p.get("tags", []),
            })
        return notificaciones
    except ZabbixAPIError as e:
        return {"error": str(e)}


def format_notificaciones(notificaciones):
    if isinstance(notificaciones, dict) and "error" in notificaciones:
        return f"  Error: {notificaciones['error']}"
    if not notificaciones:
        return "  No hay problemas activos"
    lines = []
    for n in notificaciones:
        sev = n.get("severity", 0)
        marker = {0: "○", 1: "●", 2: "●", 3: "●", 4: "●", 5: "●"}.get(sev, "●")
        ack = "NO ACK" if n.get("acknowledged") == "0" else "ACK"
        lines.append(f"  {marker} [{n.get('severity_name','?')}] {n.get('name','?')}")
        lines.append(f"     ID: {n.get('eventid','?')} | {n.get('clock','?')} | {ack}")
    return "\n".join(lines)


# ─── CONFIGURACION DE ALERTAS ─────────────────────────────────

CONFIG_FILE = os.path.join(os.path.dirname(__file__), "alertas_config.json")

CONFIG_DEFAULT = {
    "zabbix": {"api_url": ZABBIX_API_URL, "user": ZABBIX_DEFAULT_USER, "password": ZABBIX_DEFAULT_PASS},
    "ntfy": {"enabled": False, "topic": "", "server": "https://ntfy.sh"},
    "intervalo_seg": 60,
    "severidad_min": 2,
    "activo": False,
}


def _cargar_config():
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE) as f:
                cfg = json.load(f)
            for k, v in CONFIG_DEFAULT.items():
                cfg.setdefault(k, v)
            return cfg
        except:
            return dict(CONFIG_DEFAULT)
    return dict(CONFIG_DEFAULT)


def _guardar_config(cfg):
    with open(CONFIG_FILE, "w") as f:
        json.dump(cfg, f, indent=2)


def configurar_alertas():
    cfg = _cargar_config()
    print("  ── Notificaciones Push (ntfy.sh) ──")
    print("  Instala la app ntfy en tu celular (Android/iOS)")
    print("  Suscribite a un topic, ej: tus_ups_alertas")
    print()
    topic = input(f"  Topic [{cfg['ntfy']['topic']}]: ").strip() or cfg['ntfy']['topic']
    server = input(f"  Servidor ntfy [{cfg['ntfy']['server']}]: ").strip() or cfg['ntfy']['server']
    cfg["ntfy"]["topic"] = topic
    cfg["ntfy"]["server"] = server
    cfg["ntfy"]["enabled"] = bool(topic)
    print(f"  Push: {'ACTIVADO' if cfg['ntfy']['enabled'] else 'DESACTIVADO'}")

    print("  ── General ──")
    intervalo = input(f"  Intervalo de chequeo (segundos) [{cfg['intervalo_seg']}]: ").strip()
    sev = input(f"  Severidad minima (0-5, 5=desastre) [{cfg['severidad_min']}]: ").strip()
    if intervalo:
        cfg["intervalo_seg"] = int(intervalo)
    if sev:
        cfg["severidad_min"] = int(sev)
    cfg["zabbix"]["api_url"] = input(f"  URL Zabbix API [{cfg['zabbix']['api_url']}]: ").strip() or cfg['zabbix']['api_url']
    cfg["zabbix"]["user"] = input(f"  Usuario Zabbix [{cfg['zabbix']['user']}]: ").strip() or cfg['zabbix']['user']
    cfg["zabbix"]["password"] = input(f"  Password Zabbix [{cfg['zabbix']['password']}]: ").strip() or cfg['zabbix']['password']

    _guardar_config(cfg)
    return cfg


def ver_config_alertas():
    cfg = _cargar_config()
    print(f"  Zabbix: {cfg['zabbix']['api_url']}")
    print(f"  Push (ntfy): {'ACTIVADO' if cfg['ntfy']['enabled'] else 'DESACTIVADO'}")
    if cfg['ntfy']['enabled']:
        print(f"    Servidor: {cfg['ntfy']['server']}")
        print(f"    Topic: {cfg['ntfy']['topic']}")
    print(f"  Intervalo: {cfg['intervalo_seg']}s")
    print(f"  Severidad min: {cfg['severidad_min']} ({SEVERIDAD_NOMBRES[cfg['severidad_min']]})")
    print(f"  Monitoreo activo: {'SI' if cfg['activo'] else 'NO'}")


def enviar_push(titulo, mensaje, prioridad=4):
    cfg = _cargar_config()
    if not cfg["ntfy"]["enabled"] or not cfg["ntfy"]["topic"]:
        return False
    try:
        url = f"{cfg['ntfy']['server'].rstrip('/')}/{cfg['ntfy']['topic']}"
        headers = {"Title": titulo, "Priority": str(prioridad), "Tags": "zap"}
        r = requests.post(url, data=mensaje.encode("utf-8"), headers=headers, timeout=10)
        return r.status_code in (200, 201)
    except:
        return False


_alerta_activo = False
_alerta_thread = None
_alerta_ultimos_ids = set()


def _loop_alertas():
    global _alerta_activo, _alerta_ultimos_ids
    cfg = _cargar_config()
    while _alerta_activo:
        try:
            cfg = _cargar_config()
            api = ZabbixAPI(cfg["zabbix"]["api_url"], cfg["zabbix"]["user"], cfg["zabbix"]["password"])
            problemas = get_notificaciones(api, severity_min=cfg["severidad_min"], limit=20)
            if isinstance(problemas, list):
                nuevos = [p for p in problemas if p["eventid"] not in _alerta_ultimos_ids]
                for p in nuevos:
                    sev = p.get("severity", 2)
                    prioridad = 5 if sev >= 4 else 4 if sev >= 2 else 3
                    titulo = f"\u26a1 UPS {p['severity_name']}"
                    msg = (
                        f"Problema: {p['name']}\n"
                        f"Severidad: {p['severity_name']}\n"
                        f"ID: {p['eventid']}\n"
                        f"Fecha: {p['clock']}"
                    )
                    enviar_push(titulo, msg, prioridad)
                    _alerta_ultimos_ids.add(p["eventid"])
            if len(_alerta_ultimos_ids) > 500:
                _alerta_ultimos_ids = set(list(_alerta_ultimos_ids)[-200:])
        except:
            pass
        for _ in range(cfg.get("intervalo_seg", 60)):
            if not _alerta_activo:
                break
            time.sleep(1)


def iniciar_monitoreo():
    global _alerta_activo, _alerta_thread
    cfg = _cargar_config()
    if not cfg["ntfy"]["enabled"]:
        return {"status": "error", "msg": "Configurar ntfy.sh primero (opcion [7])"}
    if _alerta_activo:
        return {"status": "error", "msg": "Ya esta en ejecucion"}
    try:
        api = ZabbixAPI(cfg["zabbix"]["api_url"], cfg["zabbix"]["user"], cfg["zabbix"]["password"])
        r = api.check_connection()
        if not r.get("connected"):
            return {"status": "error", "msg": f"No se pudo conectar a Zabbix: {r.get('error','')}"}
    except Exception as e:
        return {"status": "error", "msg": str(e)}
    _alerta_activo = True
    _alerta_thread = threading.Thread(target=_loop_alertas, daemon=True)
    _alerta_thread.start()
    cfg = _cargar_config()
    cfg["activo"] = True
    _guardar_config(cfg)
    return {"status": "ok", "msg": "Monitoreo de alertas iniciado"}


def detener_monitoreo():
    global _alerta_activo, _alerta_thread
    _alerta_activo = False
    if _alerta_thread:
        _alerta_thread.join(timeout=5)
        _alerta_thread = None
    cfg = _cargar_config()
    cfg["activo"] = False
    _guardar_config(cfg)
    return {"status": "ok", "msg": "Monitoreo detenido"}


def probar_push():
    ok = enviar_push("PRUEBA TechBot", "Sistema de alertas UPS funcionando correctamente")
    return {"status": "ok" if ok else "error", "msg": "Notificacion enviada al celular" if ok else "Error al enviar"}


def resumir_notificaciones(notificaciones):
    if isinstance(notificaciones, dict) and "error" in notificaciones:
        return {"error": notificaciones["error"]}
    total = len(notificaciones)
    por_severidad = {}
    for n in notificaciones:
        s = n.get("severity_name", "Desconocida")
        por_severidad[s] = por_severidad.get(s, 0) + 1
    return {
        "total": total,
        "por_severidad": por_severidad,
        "no_acknowledged": sum(1 for n in notificaciones if n.get("acknowledged") == "0"),
    }
