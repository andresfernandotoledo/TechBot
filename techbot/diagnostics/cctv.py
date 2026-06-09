import socket
import urllib.request
import urllib.error
import time
import json


def _ping(host, timeout=3):
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(timeout)
        for port in [80, 443, 22, 8080, 554, 8000]:
            try:
                if s.connect_ex((host, port)) == 0:
                    s.close()
                    return True
            except:
                pass
        s.close()
        return False
    except:
        return False


def _scan_port(host, port, timeout=2):
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(timeout)
        result = s.connect_ex((host, port))
        s.close()
        return result == 0
    except (socket.gaierror, OSError):
        return False


def _grab_banner(host, port, timeout=3):
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(timeout)
        s.connect((host, port))
        if port == 80:
            s.send(b"GET / HTTP/1.0\r\nHost: %s\r\n\r\n" % host.encode())
        elif port == 554:
            s.send(b"OPTIONS RTSP/1.0\r\nCSeq: 1\r\n\r\n")
        data = s.recv(1024)
        s.close()
        return data.decode("utf-8", errors="replace")[:200]
    except Exception:
        return ""


def _check_http(host, port=80, timeout=5):
    proto = "https" if port == 443 else "http"
    url = f"{proto}://{host}:{port}/"
    try:
        req = urllib.request.Request(url, method="GET")
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            body = resp.read().decode("utf-8", errors="replace")[:500]
            return {
                "status": resp.status,
                "server": resp.headers.get("Server", ""),
                "body_preview": body[:100],
            }
    except urllib.error.HTTPError as e:
        return {"status": e.code, "error": str(e)}
    except urllib.error.URLError as e:
        return {"status": 0, "error": str(e.reason)}
    except Exception as e:
        return {"status": 0, "error": str(e)}


def _check_rtsp(host, port=554, timeout=3):
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(timeout)
        s.connect((host, port))
        s.send(b"OPTIONS RTSP/1.0\r\nCSeq: 1\r\n\r\n")
        resp = s.recv(1024).decode("utf-8", errors="replace")[:200]
        s.close()
        if "RTSP" in resp or "200 OK" in resp:
            return {"available": True, "response": resp[:100]}
        return {"available": False, "response": resp[:100]}
    except Exception as e:
        return {"available": False, "error": str(e)}


def diagnose_camera(host, timeout=3):
    result = {
        "host": host,
        "ping": False,
        "puertos_abiertos": [],
        "http": None,
        "rtsp": None,
        "posible_fabricante": None,
        "errores": [],
    }
    try:
        result["ping"] = _ping(host, timeout)
    except Exception as e:
        result["errores"].append(f"ping: {e}")

    puertos_cctv = [80, 443, 554, 8000, 8080, 8443, 8899, 37777, 34567, 35555, 9393, 9505, 7547, 3480, 7000, 8200, 8888]
    abiertos = []
    for p in puertos_cctv:
        try:
            if _scan_port(host, p, timeout=min(2, timeout)):
                abiertos.append(p)
        except Exception:
            pass
    result["puertos_abiertos"] = abiertos

    vendor_signatures = {
        "Hikvision": [80, 443, 8000, 8200, 34567],
        "Dahua": [80, 443, 37777, 35555, 8888],
        "AXIS": [80, 443, 554],
        "Bosch": [80, 443, 3480],
        "Vivotek": [80, 443, 9393],
        "Verint": [80, 443, 9505],
        "ONVIF": [80, 443, 8899],
    }
    for vendor, ports in vendor_signatures.items():
        if all(p in abiertos for p in ports):
            result["posible_fabricante"] = vendor
            break
    if not result.get("posible_fabricante") and abiertos:
        if 80 in abiertos or 443 in abiertos:
            result["posible_fabricante"] = "Cámara IP genérica"
        elif 554 in abiertos:
            result["posible_fabricante"] = "Streamer RTSP"

    if 80 in abiertos or 443 in abiertos:
        try:
            p = 443 if 443 in abiertos else 80
            result["http"] = _check_http(host, p, timeout)
            if result["http"] and result["http"].get("server"):
                server = result["http"]["server"].lower()
                if not result.get("posible_fabricante") or result["posible_fabricante"] == "Cámara IP genérica":
                    if "hikvision" in server:
                        result["posible_fabricante"] = "Hikvision"
                    elif "dahua" in server or "dvr" in server or "xvr" in server:
                        result["posible_fabricante"] = "Dahua"
                    elif "axis" in server:
                        result["posible_fabricante"] = "AXIS"
                    elif "bosch" in server:
                        result["posible_fabricante"] = "Bosch"
                    elif "vivotek" in server:
                        result["posible_fabricante"] = "Vivotek"
        except Exception as e:
            result["errores"].append(f"http: {e}")

    if 554 in abiertos:
        try:
            result["rtsp"] = _check_rtsp(host, 554, timeout)
        except Exception as e:
            result["errores"].append(f"rtsp: {e}")

    return result


def diagnose_hikvision_api(host, port=80, username="admin", password="12345", timeout=5):
    from techbot.apis.hikvision_api import HikvisionClient
    result = {"host": host, "port": port, "conectado": False}
    try:
        cli = HikvisionClient(host, port, username, password, timeout=timeout, max_retries=1)
        if not cli.is_online():
            result["error"] = "No se pudo conectar"
            return result
        result["conectado"] = True
        result["info"] = cli.get_device_info()
        try:
            result["storage"] = cli.get_storage_status()
        except Exception:
            result["storage"] = "no accesible"
        return result
    except ValueError as e:
        result["error"] = f"validación: {e}"
    except Exception as e:
        result["error"] = str(e)
    return result


def diagnose_dahua_api(host, port=80, username="admin", password="admin", timeout=5):
    from techbot.apis.dahua_api import DahuaClient
    result = {"host": host, "port": port, "conectado": False}
    try:
        cli = DahuaClient(host, port, username, password, timeout=timeout, max_retries=1)
        if not cli.is_online():
            result["error"] = "No se pudo conectar"
            return result
        result["conectado"] = True
        result["info"] = cli.get_system_info()
        try:
            result["storage"] = cli.get_storage_info()
        except Exception:
            result["storage"] = "no accesible"
        return result
    except ValueError as e:
        result["error"] = f"validación: {e}"
    except Exception as e:
        result["error"] = str(e)
    return result


def diagnose_zkteco_api(host, port=80, username="admin", password="admin", timeout=5):
    from techbot.apis.zkteco_api import ZKTecoClient
    result = {"host": host, "port": port, "conectado": False}
    try:
        cli = ZKTecoClient(host, port, username, password, timeout=timeout, max_retries=1)
        if not cli.is_online():
            result["error"] = "No se pudo conectar"
            return result
        result["conectado"] = True
        result["info"] = cli.get_device_info()
        return result
    except ValueError as e:
        result["error"] = f"validación: {e}"
    except Exception as e:
        result["error"] = str(e)
    return result


def diagnose_dvr_nvr(host, timeout=3):
    result = {
        "host": host,
        "ping": False,
        "puertos_abiertos": [],
        "es_dvr_nvr": False,
        "posible_fabricante": None,
        "interfaz_web": None,
        "servicios_cctv": {},
        "onvif": None,
        "p2p": None,
        "errores": [],
    }
    try:
        result["ping"] = _ping(host, timeout)
    except Exception as e:
        result["errores"].append(f"ping: {e}")

    puertos_dvr_nvr = [80, 443, 554, 8000, 8200, 8888, 8899, 37777, 34567,
                       35555, 8443, 8090, 9393, 9505, 7000, 3480]
    abiertos = []
    for p in puertos_dvr_nvr:
        try:
            if _scan_port(host, p, timeout=min(2, timeout)):
                abiertos.append(p)
        except Exception:
            pass
    result["puertos_abiertos"] = abiertos

    if not abiertos:
        return result

    result["es_dvr_nvr"] = True
    servicios = {
        80: "HTTP (Web)",
        443: "HTTPS (Web Seguro)",
        554: "RTSP (Streaming)",
        8000: "Hikvision SDK",
        8200: "Dahua Streaming",
        8888: "Dahua HTTP",
        8899: "ONVIF",
        37777: "Dahua SDK",
        34567: "Hikvision SDK/Debug",
        35555: "Dahua Debug/Config",
        8443: "HTTPS Alterno",
        8090: "CCTV HTTP",
        9393: "VIVOTEK",
        9505: "Verint",
        7000: "HID VertX (AC)",
        3480: "Bosch CCTV",
    }
    for p in abiertos:
        if p in servicios:
            result["servicios_cctv"][p] = servicios[p]

    vendor_sig_dvr_nvr = {
        "Hikvision DVR/NVR": [8000, 34567],
        "Dahua DVR/NVR": [37777, 35555],
        "Hikvision/Dahua (Web)": [80, 443],
    }
    for vendor, ports in vendor_sig_dvr_nvr.items():
        if all(p in abiertos for p in ports):
            result["posible_fabricante"] = vendor
            break
    if not result.get("posible_fabricante") and 80 in abiertos:
        try:
            http = _check_http(host, 80, timeout)
            if http and http.get("server"):
                srv = http["server"].lower()
                if "hikvision" in srv or "dvr" in srv:
                    result["posible_fabricante"] = "Hikvision DVR/NVR"
                elif "dahua" in srv or "xvr" in srv:
                    result["posible_fabricante"] = "Dahua DVR/NVR"
        except Exception:
            pass

    if 80 in abiertos or 443 in abiertos:
        try:
            p = 443 if 443 in abiertos else 80
            result["interfaz_web"] = _check_http(host, p, timeout)
        except Exception as e:
            result["errores"].append(f"web: {e}")

    if 554 in abiertos:
        try:
            result["onvif"] = _check_rtsp(host, 554, timeout)
        except Exception as e:
            result["errores"].append(f"rtsp: {e}")

    if 8899 in abiertos:
        try:
            result["onvif"] = _check_http(host, 8899, timeout)
        except Exception as e:
            result["errores"].append(f"onvif: {e}")

    return result


def diagnose_nvr_storage(host, port=80, timeout=5):
    result = {"host": host, "port": port, "almacenamiento": None}
    try:
        from techbot.apis.hikvision_api import HikvisionClient
        cli = HikvisionClient(host, port, timeout=timeout, max_retries=1)
        if cli.is_online():
            result["storage_api"] = cli.get_storage_status()
            result["metodo"] = "Hikvision ISAPI"
    except Exception:
        pass
    if not result.get("storage_api"):
        try:
            from techbot.apis.dahua_api import DahuaClient
            cli = DahuaClient(host, port, timeout=timeout, max_retries=1)
            if cli.is_online():
                result["storage_api"] = cli.get_storage_info()
                result["metodo"] = "Dahua CGI"
        except Exception:
            pass
    if not result.get("storage_api"):
        result["error"] = "No se pudo consultar almacenamiento"
    return result


def diagnose_full(host, cctv_port=80, ac_port=80,
                  hik_user="admin", hik_pass="12345",
                  dahua_user="admin", dahua_pass="admin",
                  zk_user="admin", zk_pass="admin",
                  timeout=5):
    result = {
        "host": host,
        "red": None,
        "hikvision": None,
        "dahua": None,
        "zkteco": None,
        "diagnostico_completo": False,
    }
    result["red"] = diagnose_camera(host, timeout)
    ports_open = result["red"].get("puertos_abiertos", [])
    if 80 in ports_open or 8000 in ports_open or 34567 in ports_open:
        p = 8000 if 8000 in ports_open else (34567 if 34567 in ports_open else cctv_port)
        result["hikvision"] = diagnose_hikvision_api(host, p, hik_user, hik_pass, timeout)
    if 80 in ports_open or 37777 in ports_open or 8888 in ports_open:
        p = 8888 if 8888 in ports_open else (37777 if 37777 in ports_open else cctv_port)
        result["dahua"] = diagnose_dahua_api(host, p, dahua_user, dahua_pass, timeout)
    if 80 in ports_open or 4370 in ports_open or 8080 in ports_open:
        p = 8080 if 8080 in ports_open else (4370 if 4370 in ports_open else ac_port)
        result["zkteco"] = diagnose_zkteco_api(host, p, zk_user, zk_pass, timeout)
    result["diagnostico_completo"] = True
    return result
