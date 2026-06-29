import urllib.request
import urllib.error
import base64
import json
import time
import socket
import xml.etree.ElementTree as ET


def _validar_host(host):
    if not host or not isinstance(host, str):
        raise ValueError("Host debe ser una cadena no vacía")
    return host.strip()


def _validar_puerto(port):
    p = int(port)
    if p < 1 or p > 65535:
        raise ValueError(f"Puerto inválido: {port}")
    return p


class HikvisionClient:
    def __init__(self, host, port=80, username="admin", password="12345",
                 use_ssl=False, timeout=10, max_retries=2):
        self.host = _validar_host(host)
        self.port = _validar_puerto(port)
        self.username = str(username) if username else "admin"
        self.password = str(password) if password else "12345"
        self.timeout = max(timeout, 3)
        self.max_retries = max(0, max_retries)
        self.proto = "https" if use_ssl else "http"
        self.base_url = f"{self.proto}://{self.host}:{self.port}"
        self.auth_header = self._make_auth()

    def _make_auth(self):
        credentials = f"{self.username}:{self.password}"
        encoded = base64.b64encode(credentials.encode()).decode()
        return f"Basic {encoded}"

    def _request(self, path, method="GET", data=None):
        url = f"{self.base_url}{path}"
        last_error = None
        for attempt in range(self.max_retries + 1):
            try:
                req = urllib.request.Request(url, method=method, data=data)
                req.add_header("Authorization", self.auth_header)
                with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                    return resp.read()
            except urllib.error.HTTPError as e:
                body = e.read()
                return body if body else b""
            except urllib.error.URLError as e:
                last_error = f"error de conexión: {e.reason}"
            except socket.timeout:
                last_error = "timeout de conexión"
            except OSError as e:
                last_error = f"error de red: {e.strerror or e}"
            if attempt < self.max_retries:
                time.sleep(1 * (attempt + 1))
        return {"error": last_error or "fallo en la solicitud"}

    def _parse_xml(self, raw):
        if isinstance(raw, dict) and "error" in raw:
            return raw
        try:
            root = ET.fromstring(raw)
            return {child.tag.split("}")[-1]: child.text for child in root}
        except (ET.ParseError, TypeError):
            return {"raw": raw.decode() if isinstance(raw, bytes) else str(raw)}

    def get_device_info(self):
        return self._parse_xml(self._request("/ISAPI/System/deviceInfo"))

    def get_channel_status(self, channel=1):
        return self._parse_xml(self._request(f"/ISAPI/Streaming/channels/{channel}"))

    def get_storage_status(self):
        return self._parse_xml(self._request("/ISAPI/System/Storage/status"))

    def get_network_config(self, interface=1):
        return self._parse_xml(self._request(f"/ISAPI/System/Network/interfaces/{interface}"))

    def get_device_time(self):
        return self._parse_xml(self._request("/ISAPI/System/time"))

    def ptz_control(self, channel=1, command="Up", action="start"):
        cmd_map = {
            "up": "Up", "down": "Down", "left": "Left", "right": "Right",
            "zoomin": "ZoomIn", "zoomout": "ZoomOut", "focusnear": "FocusNear",
            "focusfar": "FocusFar", "irisleave": "IrisLeave", "irisclose": "IrisClose",
        }
        cmd = cmd_map.get(command.lower(), command)
        raw = self._request(
            f"/ISAPI/PTZCtrl/channels/{channel}/{action}?command={cmd}"
        )
        if isinstance(raw, dict) and "error" in raw:
            return {"status": "error", "error": raw["error"]}
        return {"status": "ok", "response": raw}

    def ptz_move(self, channel=1, command="up"):
        return self.ptz_control(channel, command, "start")

    def ptz_stop(self, channel=1, command="up"):
        return self.ptz_control(channel, command, "stop")

    def get_alarm_status(self):
        return self._parse_xml(self._request("/ISAPI/Event/triggers"))

    def get_io_inputs(self, io=1):
        return self._parse_xml(self._request(f"/ISAPI/System/IO/inputs/{io}"))

    def get_io_outputs(self, io=1):
        return self._parse_xml(self._request(f"/ISAPI/System/IO/outputs/{io}"))

    def is_online(self):
        try:
            result = self.get_device_info()
            if isinstance(result, dict) and "error" in result:
                return False
            return "deviceName" in result or "raw" in result
        except Exception:
            return False

    def get_snapshot(self, channel=1):
        raw = self._request(f"/ISAPI/Streaming/channels/{channel}/picture")
        if isinstance(raw, dict) and "error" in raw:
            return None
        return raw

    def reboot(self):
        raw = self._request("/ISAPI/System/reboot", method="PUT")
        if isinstance(raw, dict) and "error" in raw:
            return {"status": "error", "error": raw["error"]}
        return {"status": "ok", "response": raw}


HIKVISION_API = {
    "Puertos": [80, 443, 554, 8000, 8200],
    "Comandos ISAPI": [
        ("/ISAPI/System/deviceInfo", "Info del dispositivo"),
        ("/ISAPI/Security/UserCheck", "Autenticación de usuario"),
        ("/ISAPI/Streaming/channels/1", "Estado del canal 1"),
        ("/ISAPI/Event/triggers", "Eventos/detección"),
        ("/ISAPI/System/Storage/status", "Estado de almacenamiento"),
        ("/ISAPI/System/Network/interfaces/1", "Configuración de red"),
        ("/ISAPI/System/time", "Hora del dispositivo"),
        ("/ISAPI/PTZCtrl/channels/1", "Control PTZ"),
        ("/ISAPI/Event/notification/alertStream", "Alertas en tiempo real"),
        ("/ISAPI/Intelligent/FDLib", "Detección facial"),
        ("/ISAPI/AccessControl/UserRecord", "Control de acceso"),
        ("/ISAPI/System/IO/outputs/1", "Salidas de relé"),
        ("/ISAPI/Streaming/channels/1/picture", "Capturar snapshot"),
    ],
    "Modelos comunes": [
        "DS-2CD2xxx", "DS-2CD3xxx", "DS-7608NI", "DS-7716NI", "iDS-2CD7xxx"
    ],
    "Credenciales por defecto": {"admin": "12345"},
}


list_commands = HIKVISION_API["Comandos ISAPI"]
default_ports = HIKVISION_API["Puertos"]
default_creds = HIKVISION_API["Credenciales por defecto"]
