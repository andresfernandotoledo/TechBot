# Módulo de Control de Acceso Unificado
# Soporta todos los fabricantes principales: IP, Wiegand, Cloud, Serial

from datetime import datetime
import requests
import json
import base64
import xml.etree.ElementTree as ET
import re
import time


EVENT_TYPES = {
    "granted": "Acceso Permitido",
    "denied": "Acceso Denegado",
    "door_open": "Puerta Abierta",
    "door_closed": "Puerta Cerrada",
    "door_forced": "Puerta Forzada",
    "door_held": "Puerta Retenida",
    "duress": "Coacción (Duress)",
    "alarm": "Alarma",
    "tamper": "Manipulación (Tamper)",
    "online": "Dispositivo en línea",
    "offline": "Dispositivo fuera de línea",
    "battery_low": "Batería baja",
    "unknown": "Desconocido",
}

CREDENTIAL_TYPES = {
    "card": "Tarjeta RFID (125kHz/13.56MHz)",
    "pin": "PIN/Código",
    "fingerprint": "Huella Dactilar",
    "face": "Reconocimiento Facial",
    "palm": "Palma de la mano",
    "vein": "Vena de la mano",
    "iris": "Iris/Retina",
    "qr": "Código QR",
    "bluetooth": "Bluetooth/BLE",
    "nfc": "NFC",
    "mobile": "Credencial Móvil",
    "wiegand": "Wiegand (tarjeta/prox)",
    "combined": "Combinado (ej: tarjeta+PIN)",
}

DOOR_STATES = {
    "locked": "Cerrada/Bloqueada",
    "unlocked": "Abierta/Desbloqueada",
    "open": "Abierta (físicamente)",
    "closed": "Cerrada (físicamente)",
    "held": "Retenida (Door Held)",
    "forced": "Forzada (Door Forced)",
    "error": "Error/Desconocido",
}


def _validar_str(valor, nombre="valor"):
    if not isinstance(valor, str) or not valor.strip():
        raise ValueError(f"{nombre} no puede estar vacío")
    return valor.strip()

def _validar_host(host):
    if not host or not isinstance(host, str) or not host.strip():
        raise ValueError("Host/IP requerido")
    return host.strip()

def _validar_puerto(puerto):
    try:
        p = int(puerto)
    except (ValueError, TypeError):
        raise ValueError(f"Puerto inválido: {puerto}")
    if p < 1 or p > 65535:
        raise ValueError(f"Puerto fuera de rango (1-65535): {p}")
    return p

def _validar_timeout(timeout):
    try:
        t = int(timeout)
    except (ValueError, TypeError):
        raise ValueError(f"Timeout inválido: {timeout}")
    if t < 3:
        t = 3
    if t > 120:
        t = 120
    return t


class _HTTPClient:
    def __init__(self, host, port=80, username="admin", password="", use_ssl=False, timeout=10):
        self.host = _validar_host(host)
        self.port = _validar_puerto(port)
        self.username = _validar_str(username, "Usuario") if username else ""
        self.password = password
        self.use_ssl = bool(use_ssl)
        self.timeout = _validar_timeout(timeout)
        self.max_retries = 2
        self.base_url = f"{'https' if use_ssl else 'http'}://{self.host}:{self.port}"
        self.auth = (self.username, self.password)
        self.session = requests.Session()
        self.session.auth = self.auth
        self.connected = False

    def _req(self, method, path, **kwargs):
        url = f"{self.base_url}{path}"
        last_error = None
        for attempt in range(1 + self.max_retries):
            try:
                r = self.session.request(method, url, timeout=self.timeout, **kwargs)
                r.raise_for_status()
                return r
            except requests.exceptions.Timeout as e:
                last_error = {"error": f"Timeout tras {self.timeout}s: {e}"}
                if attempt < self.max_retries:
                    time.sleep(1 * (attempt + 1))
                    continue
            except requests.exceptions.ConnectionError as e:
                last_error = {"error": f"Conexión rehusada: {e}"}
                if attempt < self.max_retries:
                    time.sleep(1 * (attempt + 1))
                    continue
            except requests.exceptions.HTTPError as e:
                last_error = {"error": f"HTTP {e.response.status_code}: {e.response.text[:200]}"}
                raise Exception(last_error["error"])
            except Exception as e:
                last_error = {"error": f"Error de conexión: {e}"}
                if attempt < self.max_retries:
                    time.sleep(1 * (attempt + 1))
                    continue
        return last_error

    def get(self, path, **kwargs):
        return self._req("GET", path, **kwargs)

    def post(self, path, **kwargs):
        return self._req("POST", path, **kwargs)

    def put(self, path, **kwargs):
        return self._req("PUT", path, **kwargs)

    def delete(self, path, **kwargs):
        return self._req("DELETE", path, **kwargs)


def _validar_door_id(door_id):
    try:
        d = int(door_id)
    except (ValueError, TypeError):
        raise ValueError(f"door_id inválido: {door_id}")
    if d < 1:
        raise ValueError(f"door_id debe ser >= 1: {d}")
    return d

def _validar_count(count):
    try:
        c = int(count)
    except (ValueError, TypeError):
        raise ValueError(f"count inválido: {count}")
    if c < 1:
        c = 1
    if c > 10000:
        c = 10000
    return c


class AccessControlBase:
    def __init__(self, client, device_type="generic"):
        self.client = client
        self.device_type = device_type
        self.name = "Control de Acceso"
        self.connected = False

    def _check_connectivity(self):
        """Intenta una conexión real al dispositivo. Sobrescribir en subclases."""
        if self.client and hasattr(self.client, "_req"):
            try:
                self.client._req("GET", "/")
                return True
            except Exception:
                pass
        elif self.client and hasattr(self.client, "is_online"):
            try:
                return self.client.is_online()
            except Exception:
                pass
        return False

    def test_connection(self):
        try:
            connected = self._check_connectivity()
            self.connected = connected
            info = self.get_info()
            if not connected:
                return {"error": "No se pudo conectar al dispositivo", **info}
            return info
        except Exception as e:
            self.connected = False
            return {"error": str(e)}

    def open_door(self, door_id=1):
        raise NotImplementedError

    def close_door(self, door_id=1):
        raise NotImplementedError

    def hold_door(self, door_id=1, seconds=10):
        try:
            s = int(seconds)
        except (ValueError, TypeError):
            return {"error": f"Segundos inválidos: {seconds}"}
        if s < 1 or s > 3600:
            return {"error": "Segundos debe estar entre 1 y 3600"}
        r = self.open_door(door_id)
        if isinstance(r, dict) and "error" in r:
            return r
        time.sleep(s)
        return self.close_door(door_id)

    def unlock(self, door_id=1):
        return self.open_door(door_id)

    def lock(self, door_id=1):
        return self.close_door(door_id)

    def get_door_status(self, door_id=1):
        raise NotImplementedError

    def get_events(self, count=100):
        raise NotImplementedError

    def list_users(self):
        raise NotImplementedError

    def get_user(self, user_id):
        raise NotImplementedError

    def add_user(self, name, credentials=None):
        raise NotImplementedError

    def delete_user(self, user_id):
        raise NotImplementedError

    def get_credentials(self, user_id):
        raise NotImplementedError

    def add_credential(self, user_id, cred_type, value):
        raise NotImplementedError

    def delete_credential(self, user_id, credential_id):
        raise NotImplementedError

    def get_audit_trail(self, count=100):
        return self.get_events(count)

    def get_info(self):
        return {
            "vendor": self.device_type,
            "name": self.name,
            "connected": self.connected,
        }


# ─── HIKVISION ─────────────────────────────────────────────

class HikvisionACWrapper(AccessControlBase):
    def __init__(self, client):
        super().__init__(client, "hikvision")
        self.name = "Hikvision Access Control"

    def _check_connectivity(self):
        try:
            return self.client.is_online()
        except Exception:
            return False

    def _request(self, method, path, data=None, xml_root=None, timeout=10):
        timeout = _validar_timeout(timeout)
        url = f"http://{self.client.host}:{self.client.port}{path}"
        auth = (self.client.username, self.client.password)
        headers = {"Content-Type": "application/xml"}
        body = None
        if xml_root is not None:
            body = ET.tostring(xml_root, encoding="utf-8")
        elif data is not None:
            body = data
        last_error = None
        for attempt in range(3):
            try:
                r = requests.request(method, url, auth=auth, data=body,
                                     headers=headers, timeout=timeout)
                if r.status_code not in (200, 201):
                    last_error = {"error": f"HTTP {r.status_code}: {r.text[:200]}"}
                    if attempt < 2:
                        time.sleep(1 * (attempt + 1))
                        continue
                    return last_error
                root = ET.fromstring(r.content)
                return root
            except ET.ParseError as e:
                return {"raw": r.text[:500], "error": f"Error XML: {e}"}
            except requests.exceptions.Timeout as e:
                last_error = {"error": f"Timeout tras {timeout}s: {e}"}
                if attempt < 2:
                    time.sleep(1 * (attempt + 1))
                    continue
            except requests.exceptions.ConnectionError as e:
                last_error = {"error": f"Conexión rehusada: {e}"}
                if attempt < 2:
                    time.sleep(1 * (attempt + 1))
                    continue
            except Exception as e:
                last_error = {"error": f"Error: {e}"}
                if attempt < 2:
                    time.sleep(1 * (attempt + 1))
                    continue
        return last_error

    def open_door(self, door_id=1):
        root = ET.Element("RemoteControlDoor")
        ch = ET.SubElement(root, "doorChannel")
        ch.text = str(door_id)
        cmd = ET.SubElement(root, "cmd")
        cmd.text = "open"
        resp = self._request("PUT", "/ISAPI/AccessControl/RemoteControl/door/1", xml_root=root)
        return {"status": "ok", "door": door_id, "action": "open", "response": str(resp)[:200]}

    def close_door(self, door_id=1):
        root = ET.Element("RemoteControlDoor")
        ch = ET.SubElement(root, "doorChannel")
        ch.text = str(door_id)
        cmd = ET.SubElement(root, "cmd")
        cmd.text = "close"
        resp = self._request("PUT", "/ISAPI/AccessControl/RemoteControl/door/1", xml_root=root)
        return {"status": "ok", "door": door_id, "action": "close", "response": str(resp)[:200]}

    def get_door_status(self, door_id=1):
        resp = self._request("GET", f"/ISAPI/AccessControl/Door/status/{door_id}")
        if isinstance(resp, dict) and "error" in resp:
            return resp
        try:
            status = resp.find(".//status").text if resp.find(".//status") is not None else "unknown"
        except:
            status = "unknown"
        return {"door": door_id, "status": status, "state": DOOR_STATES.get(status, status)}

    def get_events(self, count=100):
        root = ET.Element("EventNotificationAlertList")
        resp = self._request("GET", "/ISAPI/Event/notification/alertStream")
        events = []
        if isinstance(resp, ET.Element):
            for alert in resp.findall(".//EventNotificationAlert"):
                events.append({
                    "event_type": alert.findtext("eventType", "unknown"),
                    "event_state": alert.findtext("eventState", "unknown"),
                    "door_id": alert.findtext("doorChannel", "0"),
                    "card_no": alert.findtext("cardNo", ""),
                    "time": alert.findtext("dateTime", ""),
                })
        return {"events": events[:count]}

    def list_users(self):
        root = ET.Element("UserInfoSearch")
        root.set("version", "2.0")
        resp = self._request("POST", "/ISAPI/AccessControl/UserInfo/Search?format=json", xml_root=root)
        users = []
        if isinstance(resp, ET.Element):
            for u in resp.findall(".//UserInfo"):
                users.append({
                    "id": u.findtext("employeeNo", ""),
                    "name": u.findtext("name", ""),
                    "door": u.findtext("doorRight", ""),
                })
        return {"users": users}

    def get_user(self, user_id):
        root = ET.Element("UserInfoSearch")
        root.set("version", "2.0")
        cond = ET.SubElement(root, "searchCond")
        ET.SubElement(cond, "maxResults").text = "1"
        uinfo = ET.SubElement(cond, "UserInfoID")
        ET.SubElement(uinfo, "employeeNo").text = str(user_id)
        resp = self._request("POST", "/ISAPI/AccessControl/UserInfo/Search", xml_root=root)
        return {"user_id": user_id, "response": str(resp)[:300]}

    def get_info(self):
        return {
            "vendor": "Hikvision",
            "protocol": "ISAPI HTTP",
            "capabilities": ["open/close/hold door", "door status", "events", "users", "credentials"],
            "connected": self.connected,
        }


# ─── DAHUA ─────────────────────────────────────────────────

class DahuaACWrapper(AccessControlBase):
    def __init__(self, client):
        super().__init__(client, "dahua")
        self.name = "Dahua Access Control"

    def _check_connectivity(self):
        try:
            return self.client.is_online()
        except Exception:
            return False

    def _req(self, path, params=None, timeout=10):
        timeout = _validar_timeout(timeout)
        url = f"http://{self.client.host}:{self.client.port}{path}"
        auth = (self.client.username, self.client.password)
        last_error = None
        for attempt in range(3):
            try:
                r = requests.get(url, auth=auth, params=params, timeout=timeout)
                return r.text[:1000]
            except requests.exceptions.Timeout as e:
                last_error = {"error": f"Timeout tras {timeout}s: {e}"}
                if attempt < 2:
                    time.sleep(1 * (attempt + 1))
                    continue
            except requests.exceptions.ConnectionError as e:
                last_error = {"error": f"Conexión rehusada: {e}"}
                if attempt < 2:
                    time.sleep(1 * (attempt + 1))
                    continue
            except Exception as e:
                last_error = {"error": f"Error: {e}"}
                if attempt < 2:
                    time.sleep(1 * (attempt + 1))
                    continue
        return last_error

    def open_door(self, door_id=1):
        resp = self._req(f"/cgi-bin/accessControl.cgi?action=openDoor&channel={door_id}")
        return {"status": "ok", "door": door_id, "action": "open", "response": str(resp)[:200]}

    def close_door(self, door_id=1):
        resp = self._req(f"/cgi-bin/accessControl.cgi?action=closeDoor&channel={door_id}")
        return {"status": "ok", "door": door_id, "action": "close", "response": str(resp)[:200]}

    def get_door_status(self, door_id=1):
        resp = self._req(f"/cgi-bin/accessControl.cgi?action=getDoorStatus&channel={door_id}")
        return {"door": door_id, "response": str(resp)[:300]}

    def get_events(self, count=100):
        return {"note": "Dahua requires persistent connection for event streaming",
                "events": [], "source": "/cgi-bin/eventManager.cgi?action=attach&codes=[AccessControl]"}

    def list_users(self):
        resp = self._req("/cgi-bin/recordManager.cgi?action=find&name=AccessControlUser")
        return {"users": [], "response": str(resp)[:300]}

    def get_info(self):
        return {
            "vendor": "Dahua",
            "protocol": "CGI HTTP",
            "capabilities": ["open/close/hold door", "door status", "events", "users"],
            "connected": self.connected,
        }


# ─── ZKTECO ───────────────────────────────────────────────

class ZKTecoACWrapper(AccessControlBase):
    def __init__(self, client):
        super().__init__(client, "zkteco")
        self.name = "ZKTeco Access Control"

    def _check_connectivity(self):
        try:
            return self.client.is_online()
        except Exception:
            return False

    def _req(self, path, timeout=10):
        timeout = _validar_timeout(timeout)
        url = f"http://{self.client.host}:{self.client.port}{path}"
        auth = (self.client.username, self.client.password)
        last_error = None
        for attempt in range(3):
            try:
                r = requests.get(url, auth=auth, timeout=timeout)
                return r.text[:1000]
            except requests.exceptions.Timeout as e:
                last_error = {"error": f"Timeout tras {timeout}s: {e}"}
                if attempt < 2:
                    time.sleep(1 * (attempt + 1))
                    continue
            except requests.exceptions.ConnectionError as e:
                last_error = {"error": f"Conexión rehusada: {e}"}
                if attempt < 2:
                    time.sleep(1 * (attempt + 1))
                    continue
            except Exception as e:
                last_error = {"error": f"Error: {e}"}
                if attempt < 2:
                    time.sleep(1 * (attempt + 1))
                    continue
        return last_error

    def open_door(self, door_id=1):
        resp = self._req(f"/iclock/devcmd?command=door{door_id}_open")
        return {"status": "ok", "door": door_id, "action": "open", "response": str(resp)[:200]}

    def close_door(self, door_id=1):
        resp = self._req(f"/iclock/devcmd?command=door{door_id}_close")
        return {"status": "ok", "door": door_id, "action": "close", "response": str(resp)[:200]}

    def get_door_status(self, door_id=1):
        resp = self._req("/iclock/devcmd?command=doorstatus")
        return {"door": door_id, "response": str(resp)[:300]}

    def get_events(self, count=100):
        resp = self._req(f"/iclock/records?limit={count}")
        events = []
        if isinstance(resp, str):
            for line in resp.strip().split("\n")[:count]:
                if "," in line:
                    parts = line.split(",")
                    events.append({
                        "raw": line[:200],
                        "time": parts[0] if parts else "",
                        "uid": parts[1] if len(parts) > 1 else "",
                    })
        return {"events": events}

    def list_users(self):
        resp = self._req("/personnel/api/employees/")
        return {"users": [], "response": str(resp)[:300]}

    def get_info(self):
        return {
            "vendor": "ZKTeco",
            "protocol": "HTTP SDK",
            "capabilities": ["open/close/hold door", "biometrics", "events", "users", "attendance"],
            "connected": self.connected,
        }


# ─── LENEL ONGUARD ─────────────────────────────────────────

class LenelACWrapper(AccessControlBase):
    def __init__(self, host, port=5100, username="admin", password="", use_ssl=False):
        self._http = _HTTPClient(host, port, username, password, use_ssl)
        super().__init__(self._http, "lenel")
        self.name = "Lenel OnGuard"

    def open_door(self, door_id=1):
        try:
            r = self._http.post(f"/openDoor?door={door_id}")
            return {"status": "ok", "door": door_id}
        except Exception as e:
            return {"error": str(e)}

    def close_door(self, door_id=1):
        try:
            r = self._http.post(f"/closeDoor?door={door_id}")
            return {"status": "ok", "door": door_id}
        except Exception as e:
            return {"error": str(e)}

    def get_door_status(self, door_id=1):
        try:
            r = self._http.get(f"/doorStatus?door={door_id}")
            return {"door": door_id, "data": r.text[:300]}
        except Exception as e:
            return {"error": str(e)}

    def get_events(self, count=100):
        try:
            r = self._http.get(f"/events?count={count}")
            return {"events": r.text[:1000]}
        except Exception as e:
            return {"error": str(e)}

    def list_users(self):
        try:
            r = self._http.get("/users")
            return {"users": r.text[:1000]}
        except Exception as e:
            return {"error": str(e)}

    def get_info(self):
        return {
            "vendor": "Lenel",
            "protocol": "LNS HTTP",
            "capabilities": ["open/close door", "events", "users", "badges", "elevator control"],
            "connected": self.connected,
        }


# ─── PAXTON NET2 ───────────────────────────────────────────

class PaxtonACWrapper(AccessControlBase):
    def __init__(self, host, port=5099, username="admin", password="", use_ssl=False):
        self._http = _HTTPClient(host, port, username, password, use_ssl)
        super().__init__(self._http, "paxton")
        self.name = "Paxton Net2"

    def open_door(self, door_id=1):
        try:
            r = self._http.post(f"/api/door/{door_id}/open")
            return {"status": "ok", "door": door_id}
        except Exception as e:
            return {"error": str(e)}

    def close_door(self, door_id=1):
        try:
            r = self._http.post(f"/api/door/{door_id}/close")
            return {"status": "ok", "door": door_id}
        except Exception as e:
            return {"error": str(e)}

    def get_door_status(self, door_id=1):
        try:
            r = self._http.get(f"/api/door/{door_id}/status")
            return {"door": door_id, "data": r.json()}
        except Exception as e:
            return {"error": str(e)}

    def get_events(self, count=100):
        try:
            r = self._http.get(f"/api/events?limit={count}")
            return {"events": r.json() if r.text else []}
        except Exception as e:
            return {"error": str(e)}

    def list_users(self):
        try:
            r = self._http.get("/api/users")
            return {"users": r.json() if r.text else []}
        except Exception as e:
            return {"error": str(e)}

    def get_info(self):
        return {
            "vendor": "Paxton",
            "protocol": "Net2 API HTTP",
            "capabilities": ["open/close door", "events", "users", "tokens", "10G"],
            "connected": self.connected,
        }


# ─── HID VERTX / EDGE ──────────────────────────────────────

class HIDACWrapper(AccessControlBase):
    def __init__(self, host, port=7000, username="admin", password="", use_ssl=False):
        self._http = _HTTPClient(host, port, username, password, use_ssl)
        super().__init__(self._http, "hid")
        self.name = "HID VertX/Edge"

    def open_door(self, door_id=1):
        try:
            r = self._http.post(f"/cgi-bin/door{door_id}_open")
            return {"status": "ok", "door": door_id}
        except Exception as e:
            return {"error": str(e)}

    def close_door(self, door_id=1):
        try:
            r = self._http.post(f"/cgi-bin/door{door_id}_close")
            return {"status": "ok", "door": door_id}
        except Exception as e:
            return {"error": str(e)}

    def get_door_status(self, door_id=1):
        try:
            r = self._http.get(f"/cgi-bin/door{door_id}_status")
            return {"door": door_id, "data": r.text[:300]}
        except Exception as e:
            return {"error": str(e)}

    def get_events(self, count=100):
        try:
            r = self._http.get(f"/cgi-bin/events?count={count}")
            return {"events": r.text[:1000]}
        except Exception as e:
            return {"error": str(e)}

    def list_users(self):
        try:
            r = self._http.get("/cgi-bin/users")
            return {"users": r.text[:1000]}
        except Exception as e:
            return {"error": str(e)}

    def get_info(self):
        return {
            "vendor": "HID",
            "protocol": "VertX/Edge HTTP",
            "capabilities": ["open/close door", "events", "cards", "iCLASS", "Signo"],
            "connected": self.connected,
        }


# ─── GALLAGHER ─────────────────────────────────────────────

class GallagherACWrapper(AccessControlBase):
    def __init__(self, host, port=6700, username="admin", password="", use_ssl=False):
        self._http = _HTTPClient(host, port, username, password, use_ssl)
        super().__init__(self._http, "gallagher")
        self.name = "Gallagher Command Centre"

    def open_door(self, door_id=1):
        try:
            r = self._http.post(f"/api/door/{door_id}/open")
            return {"status": "ok", "door": door_id}
        except Exception as e:
            return {"error": str(e)}

    def close_door(self, door_id=1):
        try:
            r = self._http.post(f"/api/door/{door_id}/close")
            return {"status": "ok", "door": door_id}
        except Exception as e:
            return {"error": str(e)}

    def get_door_status(self, door_id=1):
        try:
            r = self._http.get(f"/api/door/{door_id}")
            return {"door": door_id, "data": r.json() if r.text else r.text[:300]}
        except Exception as e:
            return {"error": str(e)}

    def get_events(self, count=100):
        try:
            r = self._http.get(f"/api/events?limit={count}")
            return {"events": r.json() if r.text else []}
        except Exception as e:
            return {"error": str(e)}

    def list_users(self):
        try:
            r = self._http.get("/api/cardholders")
            return {"users": r.json() if r.text else []}
        except Exception as e:
            return {"error": str(e)}

    def get_info(self):
        return {
            "vendor": "Gallagher",
            "protocol": "REST API HTTP",
            "capabilities": ["open/close door", "cardholders", "events", "mobile credentials"],
            "connected": self.connected,
        }


# ─── AVIGILON ACM ──────────────────────────────────────────

class AvigilonACWrapper(AccessControlBase):
    def __init__(self, host, port=6800, username="admin", password="", use_ssl=False):
        self._http = _HTTPClient(host, port, username, password, use_ssl)
        super().__init__(self._http, "avigilon")
        self.name = "Avigilon ACM"

    def open_door(self, door_id=1):
        try:
            r = self._http.post(f"/api/v1/door/{door_id}/open")
            return {"status": "ok", "door": door_id}
        except Exception as e:
            return {"error": str(e)}

    def close_door(self, door_id=1):
        try:
            r = self._http.post(f"/api/v1/door/{door_id}/close")
            return {"status": "ok", "door": door_id}
        except Exception as e:
            return {"error": str(e)}

    def get_door_status(self, door_id=1):
        try:
            r = self._http.get(f"/api/v1/door/{door_id}")
            return {"door": door_id, "data": r.json() if r.text else r.text[:300]}
        except Exception as e:
            return {"error": str(e)}

    def get_events(self, count=100):
        try:
            r = self._http.get(f"/api/v1/events?pageSize={count}")
            return {"events": r.json() if r.text else []}
        except Exception as e:
            return {"error": str(e)}

    def list_users(self):
        try:
            r = self._http.get("/api/v1/users")
            return {"users": r.json() if r.text else []}
        except Exception as e:
            return {"error": str(e)}

    def get_info(self):
        return {
            "vendor": "Avigilon (Motorola)",
            "protocol": "ACM REST API",
            "capabilities": ["open/close door", "users", "events", "badges", "cloud"],
            "connected": self.connected,
        }


# ─── ASSA ABLOY APERIO ─────────────────────────────────────

class AperioACWrapper(AccessControlBase):
    def __init__(self, host, port=6200, username="admin", password="", use_ssl=False):
        self._http = _HTTPClient(host, port, username, password, use_ssl)
        super().__init__(self._http, "aperio")
        self.name = "ASSA ABLOSS Aperio"

    def open_door(self, door_id=1):
        try:
            r = self._http.post(f"/api/lock/{door_id}/open")
            return {"status": "ok", "door": door_id}
        except Exception as e:
            return {"error": str(e)}

    def get_door_status(self, door_id=1):
        try:
            r = self._http.get(f"/api/lock/{door_id}")
            return {"door": door_id, "data": r.json() if r.text else r.text[:300]}
        except Exception as e:
            return {"error": str(e)}

    def get_events(self, count=100):
        try:
            r = self._http.get(f"/api/events?limit={count}")
            return {"events": r.json() if r.text else []}
        except Exception as e:
            return {"error": str(e)}

    def get_info(self):
        return {
            "vendor": "ASSA ABLOSS (Aperio)",
            "protocol": "Hub REST API",
            "capabilities": ["open door (wireless lock)", "locks status", "events", "battery"],
            "connected": self.connected,
        }


# ─── DORMAKABA ─────────────────────────────────────────────

class DormakabaACWrapper(AccessControlBase):
    def __init__(self, host, port=6300, username="admin", password="", use_ssl=False):
        self._http = _HTTPClient(host, port, username, password, use_ssl)
        super().__init__(self._http, "dormakaba")
        self.name = "Dormakaba"

    def open_door(self, door_id=1):
        try:
            r = self._http.post(f"/api/v1/door/{door_id}/open")
            return {"status": "ok", "door": door_id}
        except Exception as e:
            return {"error": str(e)}

    def close_door(self, door_id=1):
        try:
            r = self._http.post(f"/api/v1/door/{door_id}/close")
            return {"status": "ok", "door": door_id}
        except Exception as e:
            return {"error": str(e)}

    def get_door_status(self, door_id=1):
        try:
            r = self._http.get(f"/api/v1/door/{door_id}")
            return {"door": door_id, "data": r.text[:300]}
        except Exception as e:
            return {"error": str(e)}

    def get_events(self, count=100):
        try:
            r = self._http.get(f"/api/v1/events?limit={count}")
            return {"events": r.json() if r.text else []}
        except Exception as e:
            return {"error": str(e)}

    def get_info(self):
        return {
            "vendor": "Dormakaba",
            "protocol": "REST API",
            "capabilities": ["open/close door", "SkyLock", "events", "badges"],
            "connected": self.connected,
        }


# ─── SCHNEIDER ELECTRIC ────────────────────────────────────

class SchneiderACWrapper(AccessControlBase):
    def __init__(self, host, port=6400, username="admin", password="", use_ssl=False):
        self._http = _HTTPClient(host, port, username, password, use_ssl)
        super().__init__(self._http, "schneider")
        self.name = "Schneider Electric ACL"

    def open_door(self, door_id=1):
        try:
            r = self._http.post(f"/cgi/door/{door_id}/unlock")
            return {"status": "ok", "door": door_id}
        except Exception as e:
            return {"error": str(e)}

    def close_door(self, door_id=1):
        try:
            r = self._http.post(f"/cgi/door/{door_id}/lock")
            return {"status": "ok", "door": door_id}
        except Exception as e:
            return {"error": str(e)}

    def get_door_status(self, door_id=1):
        try:
            r = self._http.get(f"/cgi/door/{door_id}/status")
            return {"door": door_id, "data": r.text[:300]}
        except Exception as e:
            return {"error": str(e)}

    def get_events(self, count=100):
        try:
            r = self._http.get(f"/cgi/events?limit={count}")
            return {"events": r.text[:1000]}
        except Exception as e:
            return {"error": str(e)}

    def get_info(self):
        return {
            "vendor": "Schneider Electric",
            "protocol": "CGI HTTP",
            "capabilities": ["lock/unlock door", "events", "Pelco integration"],
            "connected": self.connected,
        }


# ─── JOHNSON CONTROLS (P2000 / CEM) ────────────────────────

class JohnsonACWrapper(AccessControlBase):
    def __init__(self, host, port=6500, username="admin", password="", use_ssl=False):
        self._http = _HTTPClient(host, port, username, password, use_ssl)
        super().__init__(self._http, "johnson")
        self.name = "Johnson Controls"

    def open_door(self, door_id=1):
        try:
            r = self._http.post(f"/api/door/{door_id}/unlock")
            return {"status": "ok", "door": door_id}
        except Exception as e:
            return {"error": str(e)}

    def close_door(self, door_id=1):
        try:
            r = self._http.post(f"/api/door/{door_id}/lock")
            return {"status": "ok", "door": door_id}
        except Exception as e:
            return {"error": str(e)}

    def get_door_status(self, door_id=1):
        try:
            r = self._http.get(f"/api/door/{door_id}")
            return {"door": door_id, "data": r.text[:300]}
        except Exception as e:
            return {"error": str(e)}

    def get_events(self, count=100):
        try:
            r = self._http.get(f"/api/events?count={count}")
            return {"events": r.json() if r.text else []}
        except Exception as e:
            return {"error": str(e)}

    def get_info(self):
        return {
            "vendor": "Johnson Controls",
            "protocol": "P2000/CEM API",
            "capabilities": ["lock/unlock door", "P2000", "CEM", "events"],
            "connected": self.connected,
        }


# ─── STANLEY ────────────────────────────────────────────────

class StanleyACWrapper(AccessControlBase):
    def __init__(self, host, port=6600, username="admin", password="", use_ssl=False):
        self._http = _HTTPClient(host, port, username, password, use_ssl)
        super().__init__(self._http, "stanley")
        self.name = "Stanley Access Control"

    def open_door(self, door_id=1):
        try:
            r = self._http.post(f"/api/v1/door/{door_id}/open")
            return {"status": "ok", "door": door_id}
        except Exception as e:
            return {"error": str(e)}

    def close_door(self, door_id=1):
        try:
            r = self._http.post(f"/api/v1/door/{door_id}/close")
            return {"status": "ok", "door": door_id}
        except Exception as e:
            return {"error": str(e)}

    def get_door_status(self, door_id=1):
        try:
            r = self._http.get(f"/api/v1/door/{door_id}")
            return {"door": door_id, "data": r.text[:300]}
        except Exception as e:
            return {"error": str(e)}

    def get_events(self, count=100):
        try:
            r = self._http.get(f"/api/v1/events?limit={count}")
            return {"events": r.json() if r.text else []}
        except Exception as e:
            return {"error": str(e)}

    def get_info(self):
        return {
            "vendor": "Stanley",
            "protocol": "REST API",
            "capabilities": ["open/close door", "Best Access", "events"],
            "connected": self.connected,
        }


# ─── BOSCH AMC2 / ACL ──────────────────────────────────────

class BoschACWrapper(AccessControlBase):
    def __init__(self, host, port=6900, username="admin", password="", use_ssl=False):
        self._http = _HTTPClient(host, port, username, password, use_ssl)
        super().__init__(self._http, "bosch")
        self.name = "Bosch Access Control (AMC2)"

    def open_door(self, door_id=1):
        try:
            r = self._http.post(f"/cgi/door/{door_id}/open")
            return {"status": "ok", "door": door_id}
        except Exception as e:
            return {"error": str(e)}

    def close_door(self, door_id=1):
        try:
            r = self._http.post(f"/cgi/door/{door_id}/close")
            return {"status": "ok", "door": door_id}
        except Exception as e:
            return {"error": str(e)}

    def get_door_status(self, door_id=1):
        try:
            r = self._http.get(f"/cgi/door/{door_id}/status")
            return {"door": door_id, "data": r.text[:300]}
        except Exception as e:
            return {"error": str(e)}

    def get_events(self, count=100):
        try:
            r = self._http.get(f"/cgi/events?limit={count}")
            return {"events": r.json() if r.text else []}
        except Exception as e:
            return {"error": str(e)}

    def get_info(self):
        return {
            "vendor": "Bosch",
            "protocol": "AMC2 CGI",
            "capabilities": ["open/close door", "AMC2", "events", "alarm"],
            "connected": self.connected,
        }


# ─── SIEMENS SiPass ────────────────────────────────────────

class SiemensACWrapper(AccessControlBase):
    def __init__(self, host, port=68000, username="admin", password="", use_ssl=False):
        self._http = _HTTPClient(host, port, username, password, use_ssl)
        super().__init__(self._http, "siemens")
        self.name = "Siemens SiPass"

    def open_door(self, door_id=1):
        try:
            r = self._http.post(f"/api/door/{door_id}/open")
            return {"status": "ok", "door": door_id}
        except Exception as e:
            return {"error": str(e)}

    def close_door(self, door_id=1):
        try:
            r = self._http.post(f"/api/door/{door_id}/close")
            return {"status": "ok", "door": door_id}
        except Exception as e:
            return {"error": str(e)}

    def get_door_status(self, door_id=1):
        try:
            r = self._http.get(f"/api/door/{door_id}")
            return {"door": door_id, "data": r.text[:300]}
        except Exception as e:
            return {"error": str(e)}

    def get_events(self, count=100):
        try:
            r = self._http.get(f"/api/events?limit={count}")
            return {"events": r.json() if r.text else []}
        except Exception as e:
            return {"error": str(e)}

    def get_info(self):
        return {
            "vendor": "Siemens",
            "protocol": "SiPass REST API",
            "capabilities": ["open/close door", "SiPass integrated", "events"],
            "connected": self.connected,
        }


# ─── CDVI AT200 ────────────────────────────────────────────

class CDVIACWrapper(AccessControlBase):
    def __init__(self, host, port=10629, username="admin", password="", use_ssl=False):
        self._http = _HTTPClient(host, port, username, password, use_ssl)
        super().__init__(self._http, "cdvi")
        self.name = "CDVI AT200"

    def open_door(self, door_id=1):
        try:
            r = self._http.post(f"/api/door/{door_id}/unlock")
            return {"status": "ok", "door": door_id}
        except Exception as e:
            return {"error": str(e)}

    def close_door(self, door_id=1):
        try:
            r = self._http.post(f"/api/door/{door_id}/lock")
            return {"status": "ok", "door": door_id}
        except Exception as e:
            return {"error": str(e)}

    def get_door_status(self, door_id=1):
        try:
            r = self._http.get(f"/api/door/{door_id}")
            return {"door": door_id, "data": r.text[:300]}
        except Exception as e:
            return {"error": str(e)}

    def get_events(self, count=100):
        try:
            r = self._http.get(f"/api/events?limit={count}")
            return {"events": r.json() if r.text else []}
        except Exception as e:
            return {"error": str(e)}

    def get_info(self):
        return {
            "vendor": "CDVI",
            "protocol": "AT200 REST API",
            "capabilities": ["lock/unlock door", "badges", "events"],
            "connected": self.connected,
        }


# ─── SALTO SYSTEMS ─────────────────────────────────────────

class SALTOACWrapper(AccessControlBase):
    def __init__(self, host, port=4444, username="admin", password="", use_ssl=False):
        self._http = _HTTPClient(host, port, username, password, use_ssl)
        super().__init__(self._http, "salto")
        self.name = "SALTO Systems"

    def open_door(self, door_id=1):
        try:
            r = self._http.post(f"/api/v1/door/{door_id}/open")
            return {"status": "ok", "door": door_id}
        except Exception as e:
            return {"error": str(e)}

    def close_door(self, door_id=1):
        try:
            r = self._http.post(f"/api/v1/door/{door_id}/close")
            return {"status": "ok", "door": door_id}
        except Exception as e:
            return {"error": str(e)}

    def get_door_status(self, door_id=1):
        try:
            r = self._http.get(f"/api/v1/door/{door_id}")
            return {"door": door_id, "data": r.text[:300]}
        except Exception as e:
            return {"error": str(e)}

    def get_events(self, count=100):
        try:
            r = self._http.get(f"/api/v1/events?limit={count}")
            return {"events": r.json() if r.text else []}
        except Exception as e:
            return {"error": str(e)}

    def list_users(self):
        try:
            r = self._http.get("/api/v1/users")
            return {"users": r.json() if r.text else []}
        except Exception as e:
            return {"error": str(e)}

    def get_info(self):
        return {
            "vendor": "SALTO",
            "protocol": "SALTO Virtual Network API",
            "capabilities": ["open/close door", "SVN", "audit", "users", "mobile keys"],
            "connected": self.connected,
        }


# ─── NEDAP AEOS ────────────────────────────────────────────

class NedapACWrapper(AccessControlBase):
    def __init__(self, host, port=6000, username="admin", password="", use_ssl=False):
        self._http = _HTTPClient(host, port, username, password, use_ssl)
        super().__init__(self._http, "nedap")
        self.name = "Nedap AEOS"

    def open_door(self, door_id=1):
        try:
            r = self._http.post(f"/api/v2/door/{door_id}/unlock")
            return {"status": "ok", "door": door_id}
        except Exception as e:
            return {"error": str(e)}

    def close_door(self, door_id=1):
        try:
            r = self._http.post(f"/api/v2/door/{door_id}/lock")
            return {"status": "ok", "door": door_id}
        except Exception as e:
            return {"error": str(e)}

    def get_door_status(self, door_id=1):
        try:
            r = self._http.get(f"/api/v2/door/{door_id}")
            return {"door": door_id, "data": r.json() if r.text else r.text[:300]}
        except Exception as e:
            return {"error": str(e)}

    def get_events(self, count=100):
        try:
            r = self._http.get(f"/api/v2/events?limit={count}")
            return {"events": r.json() if r.text else []}
        except Exception as e:
            return {"error": str(e)}

    def list_users(self):
        try:
            r = self._http.get("/api/v2/cardholders")
            return {"users": r.json() if r.text else []}
        except Exception as e:
            return {"error": str(e)}

    def get_info(self):
        return {
            "vendor": "Nedap",
            "protocol": "AEOS REST API v2",
            "capabilities": ["lock/unlock door", "cardholders", "events", "CrossEntry", "UPEK"],
            "connected": self.connected,
        }


# ─── 2N ────────────────────────────────────────────────────

class TwoNACWrapper(AccessControlBase):
    def __init__(self, host, port=8080, username="admin", password="", use_ssl=False):
        self._http = _HTTPClient(host, port, username, password, use_ssl)
        super().__init__(self._http, "2n")
        self.name = "2N Access Unit / Intercom"

    def open_door(self, door_id=1):
        try:
            r = self._http.post(f"/cgi/open_relay?id={door_id}")
            return {"status": "ok", "door": door_id}
        except Exception as e:
            return {"error": str(e)}

    def close_door(self, door_id=1):
        try:
            r = self._http.post(f"/cgi/close_relay?id={door_id}")
            return {"status": "ok", "door": door_id}
        except Exception as e:
            return {"error": str(e)}

    def get_door_status(self, door_id=1):
        try:
            r = self._http.get(f"/api/v1/relay/{door_id}")
            return {"door": door_id, "data": r.text[:300]}
        except Exception as e:
            return {"error": str(e)}

    def get_events(self, count=100):
        try:
            r = self._http.get(f"/api/v1/events?limit={count}")
            return {"events": r.json() if r.text else []}
        except Exception as e:
            return {"error": str(e)}

    def get_info(self):
        return {
            "vendor": "2N",
            "protocol": "CGI / REST API",
            "capabilities": ["open relay", "relay status", "events", "SIP intercom", "RFID"],
            "connected": self.connected,
        }


# ─── WIEGAND GENÉRICO ──────────────────────────────────────

class WiegandACWrapper(AccessControlBase):
    def __init__(self, host=None, port=None, username="", password="", use_ssl=False):
        super().__init__(None, "wiegand")
        self.name = "Wiegand Genérico (26/34/58 bit)"

    def open_door(self, door_id=1):
        return {"note": "Wiegand no tiene API IP. Requiere controlador TCP/RS485 intermedio.",
                "protocol": "Wiegand 26/34/58", "action": f"pulse relay {door_id}"}

    def close_door(self, door_id=1):
        return self.open_door(door_id)

    def get_door_status(self, door_id=1):
        return {"note": "Wiegand no tiene estado remoto sin controlador IP."}

    def get_events(self, count=100):
        return {"note": "Eventos Wiegand requieren controlador con buffer de eventos."}

    def get_info(self):
        return {
            "vendor": "Wiegand Genérico",
            "protocol": "Wiegand 26/34/58 (RS485 / TCP)",
            "capabilities": ["lectura tarjetas", "relé", "1-4 puertas"],
            "connected": False,
            "note": "Requiere controlador TCP/IP intermedio (ej: HID, Lenel, controlador chino)",
        }


# ─── KANTECH ───────────────────────────────────────────────

class KantechACWrapper(AccessControlBase):
    def __init__(self, host, port=3456, username="admin", password="", use_ssl=False):
        self._http = _HTTPClient(host, port, username, password, use_ssl)
        super().__init__(self._http, "kantech")
        self.name = "Kantech (Tyco/Johnson)"

    def open_door(self, door_id=1):
        try:
            r = self._http.post(f"/api/door/{door_id}/unlock")
            return {"status": "ok", "door": door_id}
        except Exception as e:
            return {"error": str(e)}

    def close_door(self, door_id=1):
        try:
            r = self._http.post(f"/api/door/{door_id}/lock")
            return {"status": "ok", "door": door_id}
        except Exception as e:
            return {"error": str(e)}

    def get_door_status(self, door_id=1):
        try:
            r = self._http.get(f"/api/door/{door_id}")
            return {"door": door_id, "data": r.text[:300]}
        except Exception as e:
            return {"error": str(e)}

    def get_events(self, count=100):
        try:
            r = self._http.get(f"/api/events?limit={count}")
            return {"events": r.json() if r.text else []}
        except Exception as e:
            return {"error": str(e)}

    def get_info(self):
        return {
            "vendor": "Kantech (Tyco/Johnson Controls)",
            "protocol": "ioEdge API",
            "capabilities": ["lock/unlock door", "ioEdge", "badges", "events"],
            "connected": self.connected,
        }


# ─── FACTORY ───────────────────────────────────────────────

def create_ac_client(vendor, host, port=80, username="admin", password="", use_ssl=False):
    vendor = vendor.lower().replace(" ", "").replace("-", "")
    _validar_host(host)
    _validar_puerto(port)

    # Clases que reciben un client (desde APIs) vs clases directas
    CLIENT_BASED = ("hikvision", "dahua", "zkteco")
    DIRECT_CLASSES = ("lenel", "paxton", "hid", "gallagher", "avigilon", "aperio",
                      "assaabloy", "dormakaba", "schneider", "johnson", "stanley",
                      "bosch", "siemens", "cdvi", "salto", "nedap", "2n", "kantech",
                      "wiegand")

    mapping = {
        "hikvision": (HikvisionACWrapper, lambda: __import__("techbot.apis.hikvision_api", fromlist=["HikvisionClient"]).HikvisionClient(host, port, username, password, use_ssl)),
        "dahua": (DahuaACWrapper, lambda: __import__("techbot.apis.dahua_api", fromlist=["DahuaClient"]).DahuaClient(host, port, username, password, use_ssl)),
        "zkteco": (ZKTecoACWrapper, lambda: __import__("techbot.apis.zkteco_api", fromlist=["ZKTecoClient"]).ZKTecoClient(host, port, username, password, use_ssl)),
        "lenel": (LenelACWrapper, lambda: LenelACWrapper(host, port, username, password, use_ssl)),
        "paxton": (PaxtonACWrapper, lambda: PaxtonACWrapper(host, port, username, password, use_ssl)),
        "hid": (HIDACWrapper, lambda: HIDACWrapper(host, port, username, password, use_ssl)),
        "gallagher": (GallagherACWrapper, lambda: GallagherACWrapper(host, port, username, password, use_ssl)),
        "avigilon": (AvigilonACWrapper, lambda: AvigilonACWrapper(host, port, username, password, use_ssl)),
        "aperio": (AperioACWrapper, lambda: AperioACWrapper(host, port, username, password, use_ssl)),
        "assaabloy": (AperioACWrapper, lambda: AperioACWrapper(host, port, username, password, use_ssl)),
        "dormakaba": (DormakabaACWrapper, lambda: DormakabaACWrapper(host, port, username, password, use_ssl)),
        "schneider": (SchneiderACWrapper, lambda: SchneiderACWrapper(host, port, username, password, use_ssl)),
        "johnson": (JohnsonACWrapper, lambda: JohnsonACWrapper(host, port, username, password, use_ssl)),
        "stanley": (StanleyACWrapper, lambda: StanleyACWrapper(host, port, username, password, use_ssl)),
        "bosch": (BoschACWrapper, lambda: BoschACWrapper(host, port, username, password, use_ssl)),
        "siemens": (SiemensACWrapper, lambda: SiemensACWrapper(host, port, username, password, use_ssl)),
        "cdvi": (CDVIACWrapper, lambda: CDVIACWrapper(host, port, username, password, use_ssl)),
        "salto": (SALTOACWrapper, lambda: SALTOACWrapper(host, port, username, password, use_ssl)),
        "nedap": (NedapACWrapper, lambda: NedapACWrapper(host, port, username, password, use_ssl)),
        "2n": (TwoNACWrapper, lambda: TwoNACWrapper(host, port, username, password, use_ssl)),
        "kantech": (KantechACWrapper, lambda: KantechACWrapper(host, port, username, password, use_ssl)),
        "wiegand": (WiegandACWrapper, lambda: WiegandACWrapper(host, port, username, password, use_ssl)),
    }

    entry = mapping.get(vendor)
    if not entry:
        raise ValueError(f"Vendor no soportado: {vendor}. Opciones: {', '.join(sorted(mapping.keys()))}")
    cls, factory = entry
    if vendor in CLIENT_BASED:
        client = factory()
        return cls(client)
    return factory()


ACCESS_CONTROL_INFO = {
    "hikvision": {
        "name": "Hikvision",
        "protocol": "ISAPI HTTP",
        "ports": [80, 443],
        "features": ["Abrir/Cerrar/Mantener puerta", "Estado de puerta", "Usuarios", "Credenciales", "Eventos", "Relé", "Horarios"],
        "models": ["DS-K1Txxx", "DS-K2Mxxx", "DS-K4Txxx", "iDS-7xxx"],
        "default_creds": {"admin": "12345"},
    },
    "dahua": {
        "name": "Dahua",
        "protocol": "CGI HTTP",
        "ports": [80, 443, 37777],
        "features": ["Abrir/Cerrar/Mantener puerta", "Estado de puerta", "Usuarios", "Relé", "Anti-passback", "VTO"],
        "models": ["DHI-ASCxxxx", "DHI-VTOxxxx"],
        "default_creds": {"admin": "admin"},
    },
    "zkteco": {
        "name": "ZKTeco",
        "protocol": "HTTP / SDK ZKLib",
        "ports": [80, 443, 4370],
        "features": ["Abrir/Cerrar/Mantener puerta", "Biometría", "Empleados", "Horarios", "Marcaciones", "Anti-passback", "Multi-factor"],
        "models": ["inBio460", "proAC", "uFace 302", "MB460"],
        "default_creds": {"admin": "admin"},
    },
    "lenel": {
        "name": "Lenel OnGuard",
        "protocol": "LNS / HTTP",
        "ports": [5099, 5100, 5101, 5110],
        "features": ["Abrir/Cerrar puerta", "Estado", "Usuarios/Badges", "Elevadores", "CCTV integración", "Eventos"],
        "models": ["LNL-2220", "LNL-1320", "OnGuard 7.x+"],
        "default_creds": {"admin": "admin"},
    },
    "paxton": {
        "name": "Paxton Net2",
        "protocol": "Net2 API HTTP",
        "ports": [5099, 5100, 5121],
        "features": ["Abrir/Cerrar puerta", "Estado", "Usuarios", "Tokens", "Eventos", "10G"],
        "models": ["Net2 Plus", "Net2 Pro", "10G Controller"],
        "default_creds": {"admin": "admin"},
    },
    "hid": {
        "name": "HID VertX / Edge",
        "protocol": "VertX HTTP",
        "ports": [7000, 7001, 7004],
        "features": ["Abrir/Cerrar puerta", "Estado", "Lectores iCLASS/Signo", "Tarjetas", "Eventos"],
        "models": ["VertX V100", "Edge EVO", "iCLASS SE"],
        "default_creds": {"admin": "admin"},
    },
    "gallagher": {
        "name": "Gallagher Command Centre",
        "protocol": "REST API HTTP",
        "ports": [6700, 6701],
        "features": ["Abrir/Cerrar puerta", "Cardholders", "Eventos", "Credenciales móviles", "Anti-passback"],
        "models": ["T30", "M700", "Command Centre"],
        "default_creds": {"admin": "password"},
    },
    "avigilon": {
        "name": "Avigilon ACM (Motorola)",
        "protocol": "ACM REST API",
        "ports": [6800, 6801],
        "features": ["Abrir/Cerrar puerta", "Usuarios", "Badges", "Eventos", "Cloud"],
        "models": ["ACM 5", "ACM 6", "ACM Cloud"],
        "default_creds": {"admin": "admin"},
    },
    "aperio": {
        "name": "ASSA ABLOSS Aperio",
        "protocol": "Hub REST API",
        "ports": [6200, 6201],
        "features": ["Abrir puerta (cerradura inalámbrica)", "Estado batería", "Eventos", "Comunicación inalámbrica"],
        "models": ["Aperio HUB", "Aperio Wireless Lock", "Cylinder", "Escutcheon"],
        "default_creds": {"admin": "admin"},
    },
    "dormakaba": {
        "name": "Dormakaba",
        "protocol": "REST API",
        "ports": [6300, 6301],
        "features": ["Abrir/Cerrar puerta", "SkyLock", "Eventos", "Badges"],
        "models": ["SkyLock", "RS485 controllers"],
        "default_creds": {"admin": "admin"},
    },
    "schneider": {
        "name": "Schneider Electric ACL",
        "protocol": "CGI HTTP",
        "ports": [6400, 6401],
        "features": ["Lock/Unlock", "CCTV integración", "Eventos"],
        "models": ["ACL Controller", "Pelco Integration"],
        "default_creds": {"admin": "admin"},
    },
    "johnson": {
        "name": "Johnson Controls",
        "protocol": "P2000/CEM API",
        "ports": [6500, 6501],
        "features": ["Lock/Unlock", "P2000", "CEM", "Eventos"],
        "models": ["P2000", "CEM", "Access Manager"],
        "default_creds": {"admin": "admin"},
    },
    "stanley": {
        "name": "Stanley Access Control",
        "protocol": "REST API",
        "ports": [6600, 6601],
        "features": ["Abrir/Cerrar puerta", "Best Access", "Eventos"],
        "models": ["Best Access", "Stanley AC Controller"],
        "default_creds": {"admin": "admin"},
    },
    "bosch": {
        "name": "Bosch AMC2",
        "protocol": "AMC2 CGI",
        "ports": [6900, 6901],
        "features": ["Abrir/Cerrar puerta", "AMC2", "Alarmas", "Eventos"],
        "models": ["AMC2 4R", "AMC2 8R", "Access Control Module"],
        "default_creds": {"admin": "admin"},
    },
    "siemens": {
        "name": "Siemens SiPass",
        "protocol": "SiPass REST API",
        "ports": [68000, 68001],
        "features": ["Abrir/Cerrar puerta", "SiPass Integrated", "Eventos"],
        "models": ["SiPass Integrated", "SiPass IP"],
        "default_creds": {"admin": "admin"},
    },
    "cdvi": {
        "name": "CDVI AT200",
        "protocol": "AT200 REST API",
        "ports": [10629, 10630],
        "features": ["Lock/Unlock", "Badges", "Eventos"],
        "models": ["AT200", "AT200 Plus"],
        "default_creds": {"admin": "admin"},
    },
    "salto": {
        "name": "SALTO Systems",
        "protocol": "SALTO Virtual Network API",
        "ports": [4444, 4445],
        "features": ["Abrir/Cerrar puerta", "SVN (Virtual Network)", "Auditoría", "Usuarios", "Mobile Keys"],
        "models": ["SALTO Space", "XS4 One", "SALTO Blue"],
        "default_creds": {"admin": "admin"},
    },
    "nedap": {
        "name": "Nedap AEOS",
        "protocol": "AEOS REST API v2",
        "ports": [6000, 6001],
        "features": ["Lock/Unlock", "Cardholders", "Eventos", "CrossEntry", "UPEK", "QR"],
        "models": ["AEOS Controller", "CrossEntry", "UPEK"],
        "default_creds": {"admin": "admin"},
    },
    "2n": {
        "name": "2N Access Unit",
        "protocol": "CGI / REST API",
        "ports": [8080, 8081, 8091],
        "features": ["Relé (abrir puerta)", "Estado relé", "Eventos", "SIP intercom", "RFID", "PIN", "Huella"],
        "models": ["2N Access Unit", "2N Access Unit IP Style", "2N Helios IP"],
        "default_creds": {"admin": "2n"},
    },
    "kantech": {
        "name": "Kantech (Tyco/Johnson)",
        "protocol": "ioEdge API",
        "ports": [3456, 3457],
        "features": ["Lock/Unlock puerta", "ioEdge", "Badges", "Eventos"],
        "models": ["ioEdge", "Kantech KT-400", "Kantech KT-1"],
        "default_creds": {"admin": "admin"},
    },
    "wiegand": {
        "name": "Wiegand Genérico",
        "protocol": "Wiegand 26/34/58",
        "ports": ["N/A (RS485)"],
        "features": ["Lectura tarjetas RFID", "Relé", "1-4 puertas", "Requiere controlador TCP/IP intermedio"],
        "models": ["Controlador Wiegand 1/2/4 puertas", "Lectores RFID EM/Mifare/HID"],
    },
}

AC_DEFAULT_CREDS = {
    vendor: info["default_creds"]
    for vendor, info in ACCESS_CONTROL_INFO.items()
    if "default_creds" in info
}
