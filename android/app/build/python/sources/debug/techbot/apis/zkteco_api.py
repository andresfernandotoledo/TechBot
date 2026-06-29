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


class ZKTecoClient:
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
        return {"error": last_error or "fallo en la solicitud"}

    def _parse_response(self, text):
        if isinstance(text, dict) and "error" in text:
            return text
        if not isinstance(text, str):
            return {"error": f"respuesta inesperada: {type(text).__name__}", "raw": str(text)}
        result = {}
        for line in text.split("\n"):
            line = line.strip()
            if "=" in line:
                key, val = line.split("=", 1)
                result[key.strip()] = val.strip()
        return result if result else {"raw": text}

    def _req_json(self, path):
        raw = self._request(path)
        if isinstance(raw, dict) and "error" in raw:
            return raw
        try:
            return json.loads(raw)
        except (json.JSONDecodeError, ValueError, TypeError):
            return {"raw": raw}

    def get_device_info(self):
        raw = self._request("/iclock/deviceinfo")
        return self._parse_response(raw)

    def sync_time(self):
        from datetime import datetime
        now = datetime.now().strftime("Y=%Y&M=%m&D=%d&H=%H&I=%M&S=%S")
        raw = self._request(f"/iclock/syncdatetime?{now}")
        if isinstance(raw, dict) and "error" in raw:
            return {"status": "error", "error": raw["error"]}
        return {"status": "ok", "response": raw}

    def get_records(self):
        raw = self._request("/iclock/getrequest")
        return self._parse_response(raw)

    def get_attendance_records(self):
        raw = self._request("/iclock/records")
        return self._parse_response(raw)

    def set_time(self, year, month, day, hour, minute, second):
        raw = self._request(
            f"/iclock/settime?Y={year}&M={month}&D={day}&H={hour}&m={minute}&S={second}"
        )
        if isinstance(raw, dict) and "error" in raw:
            return {"status": "error", "error": raw["error"]}
        return {"status": "ok", "response": raw}

    def send_command(self, command):
        raw = self._request(f"/iclock/devcmd?command={command}")
        if isinstance(raw, dict) and "error" in raw:
            return {"status": "error", "error": raw["error"]}
        return {"status": "ok", "response": raw}

    def get_operation_log(self):
        raw = self._request("/iclock/operlog")
        return self._parse_response(raw)

    def get_employees(self):
        return self._req_json("/personnel/api/employees")

    def get_transactions(self):
        return self._req_json("/personnel/api/transactions")

    def get_att_transactions_rest(self):
        return self._req_json("/device/rest/attTransactions")

    def is_online(self):
        try:
            result = self.get_device_info()
            if isinstance(result, dict) and "error" in result:
                return False
            return "DeviceName" in result or "raw" in result
        except Exception:
            return False

    def clear_attendance_cache(self):
        raw = self._request("/iclock/fmtcache")
        if isinstance(raw, dict) and "error" in raw:
            return {"status": "error", "error": raw["error"]}
        return {"status": "ok", "response": raw}


ZKTECO_API = {
    "Puertos": [80, 443, 4370, 8080],
    "Comandos SDK/SOAP": [
        ("/iclock/syncdatetime", "Sincronizar hora"),
        ("/iclock/getrequest", "Obtener datos de marcación"),
        ("/iclock/deviceinfo", "Info del dispositivo"),
        ("/iclock/cdata", "Subir datos de marcación"),
        ("/iclock/records", "Obtener registros"),
        ("/iclock/settime", "Configurar hora"),
        ("/iclock/devcmd", "Comando de dispositivo"),
        ("/iclock/operlog", "Log de operaciones"),
        ("/iclock/atcommand.axd", "Comando administrativo"),
        ("/iclock/devicecmd", "Comando desde servidor"),
        ("/personnel/api/employees", "API REST de empleados"),
        ("/personnel/api/transactions", "Transacciones API REST"),
        ("/device/rest/attTransactions", "Transacciones REST"),
    ],
    "Modelos comunes": [
        "uFace 302", "iClock 1600", "MB460", "K30", "TA500", "inBio460"
    ],
    "SDK": "ZKLib SDK (C++, Java, C#)",
    "Protocolos": ["TCP/IP", "RS232", "RS485", "USB"],
    "Puerto SDK": 4370,
}


list_commands = ZKTECO_API["Comandos SDK/SOAP"]
default_ports = ZKTECO_API["Puertos"]
default_creds = {"admin": "admin"}
