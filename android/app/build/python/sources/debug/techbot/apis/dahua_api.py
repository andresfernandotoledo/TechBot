import urllib.request
import urllib.error
import base64
import json
import time
import socket


def _validar_host(host):
    if not host or not isinstance(host, str):
        raise ValueError("Host debe ser una cadena no vacía")
    return host.strip()


def _validar_puerto(port):
    p = int(port)
    if p < 1 or p > 65535:
        raise ValueError(f"Puerto inválido: {port}")
    return p


class DahuaClient:
    def __init__(self, host, port=80, username="admin", password="admin",
                 use_ssl=False, timeout=10, max_retries=2):
        self.host = _validar_host(host)
        self.port = _validar_puerto(port)
        self.username = str(username) if username else "admin"
        self.password = str(password) if password else "admin"
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
                    return resp.read().decode()
            except urllib.error.HTTPError as e:
                return e.read().decode() if e.fp else str(e)
            except urllib.error.URLError as e:
                last_error = f"error de conexión: {e.reason}"
            except socket.timeout:
                last_error = "timeout de conexión"
            except OSError as e:
                last_error = f"error de red: {e.strerror or e}"
            if attempt < self.max_retries:
                time.sleep(1 * (attempt + 1))
        return f"error: {last_error}"

    def _parse_cgi(self, text):
        if isinstance(text, dict) and "error" in text:
            return text
        result = {}
        if isinstance(text, str) and text.startswith("error"):
            return {"error": text}
        if not isinstance(text, str):
            return {"error": f"respuesta inesperada: {type(text).__name__}"}
        for line in text.split("\n"):
            line = line.strip()
            if "=" in line:
                key, val = line.split("=", 1)
                result[key.strip()] = val.strip()
        return result

    def _req(self, path):
        raw = self._request(path)
        return self._parse_cgi(raw)

    def get_system_info(self):
        return self._req("/cgi-bin/magicBox.cgi?action=getSystemInfo")

    def get_device_type(self):
        return self._req("/cgi-bin/param.cgi?command=getDeviceType")

    def get_network_config(self):
        return self._req("/cgi-bin/configManager.cgi?action=getConfig&name=Network")

    def get_snapshot(self, channel=1):
        raw = self._request(f"/cgi-bin/snapshot.cgi?channel={channel}")
        if isinstance(raw, str) and raw.startswith("error"):
            return None
        return raw

    def ptz_command(self, channel=1, command="Up", action="start"):
        raw = self._request(
            f"/cgi-bin/ptz.cgi?action={action}&code={command}&channel={channel}"
        )
        if isinstance(raw, str) and raw.startswith("error"):
            return {"status": "error", "error": raw}
        return {"status": "ok", "response": raw}

    def ptz_move(self, channel=1, direction="up"):
        cmd_map = {
            "up": "Up", "down": "Down", "left": "Left", "right": "Right",
            "zoomin": "ZoomIn", "zoomout": "ZoomOut",
        }
        cmd = cmd_map.get(direction.lower(), direction)
        return self.ptz_command(channel, cmd, "start")

    def ptz_stop(self, channel=1, direction="up"):
        cmd_map = {
            "up": "Up", "down": "Down", "left": "Left", "right": "Right",
        }
        cmd = cmd_map.get(direction.lower(), direction)
        return self.ptz_command(channel, cmd, "stop")

    def start_record(self, channel=1):
        raw = self._request(f"/cgi-bin/record.cgi?action=start&channel={channel}")
        if isinstance(raw, str) and raw.startswith("error"):
            return {"status": "error", "error": raw}
        return {"status": "ok", "response": raw}

    def stop_record(self, channel=1):
        raw = self._request(f"/cgi-bin/record.cgi?action=stop&channel={channel}")
        if isinstance(raw, str) and raw.startswith("error"):
            return {"status": "error", "error": raw}
        return {"status": "ok", "response": raw}

    def get_alarm_status(self):
        return self._req("/cgi-bin/alarm.cgi?action=getStatus")

    def get_storage_info(self):
        return self._req("/cgi-bin/storageManager.cgi?action=query&type=hddInfo")

    def open_door(self):
        raw = self._request("/cgi-bin/accessControl.cgi?action=openDoor")
        if isinstance(raw, str) and raw.startswith("error"):
            return {"status": "error", "error": raw}
        return {"status": "ok", "response": raw}

    def get_logs(self, count=50):
        return self._req(f"/cgi-bin/log.cgi?action=query&count={count}")

    def get_accounts(self):
        return self._req("/cgi-bin/accountManager.cgi?action=query")

    def get_thermal_info(self):
        return self._req("/cgi-bin/thermalManager.cgi?action=getInfo")

    def query_recordings(self, channel=1):
        return self._req(
            f"/cgi-bin/recordManager.cgi?action=query&channel={channel}&type=byTime"
        )

    def is_online(self):
        try:
            result = self.get_system_info()
            if isinstance(result, dict) and "error" in result:
                return False
            return "sn" in result
        except Exception:
            return False

    def reboot(self):
        raw = self._request("/cgi-bin/magicBox.cgi?action=reboot")
        if isinstance(raw, str) and raw.startswith("error"):
            return {"status": "error", "error": raw}
        return {"status": "ok", "response": raw}


DAHUA_API = {
    "Puertos": [80, 443, 554, 37777, 8200],
    "Comandos CGI": [
        ("/cgi-bin/magicBox.cgi?action=getSystemInfo", "Info del sistema"),
        ("/cgi-bin/param.cgi?command=getDeviceType", "Tipo de dispositivo"),
        ("/cgi-bin/configManager.cgi?action=getConfig&name=Network", "Config red"),
        ("/cgi-bin/snapshot.cgi?channel=1", "Captura de imagen"),
        ("/cgi-bin/record.cgi?action=start&channel=1", "Iniciar grabación"),
        ("/cgi-bin/ptz.cgi?action=start&code=Up&channel=1", "Control PTZ"),
        ("/cgi-bin/eventManager.cgi?action=attach&codes=[VideoMotion]", "Detección movimiento"),
        ("/cgi-bin/alarm.cgi?action=getStatus", "Estado de alarmas"),
        ("/cgi-bin/storageManager.cgi?action=query&type=hddInfo", "Info HDD"),
        ("/cgi-bin/accessControl.cgi?action=openDoor", "Abrir puerta"),
        ("/cgi-bin/accountManager.cgi?action=query", "Gestión de cuentas"),
        ("/cgi-bin/log.cgi?action=query&count=50", "Logs del sistema"),
    ],
    "Modelos comunes": [
        "DHI-NVR5xxx", "DHI-NVR4xxx", "SD22204", "SD49225", "IPC-HFWxxxx"
    ],
    "Credenciales por defecto": {"admin": "admin"},
}


list_commands = DAHUA_API["Comandos CGI"]
default_ports = DAHUA_API["Puertos"]
default_creds = DAHUA_API["Credenciales por defecto"]
