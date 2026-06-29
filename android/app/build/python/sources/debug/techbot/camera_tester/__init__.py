# Probador de Cámaras IP - Pure Python
# Descubre, testea y configura cámaras IP, convertidores coaxial→RJ45

import socket
import ipaddress
import concurrent.futures
import time
import struct

CCTV_PORTS = [80, 443, 554, 8000, 8090, 8888, 8899, 37777, 34567, 35555, 8200, 9393, 9505, 7547, 8080, 8443]

# ─── DETECCIÓN MASIVA DE CÁMARAS ──────────────────────────────

def _tcp_port(host, port, timeout=1.5):
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(timeout)
        if s.connect_ex((str(host), port)) == 0:
            banner = b""
            try:
                if port in (80, 8080, 443, 8888):
                    s.send(f"GET / HTTP/1.0\r\nHost: {host}\r\n\r\n".encode())
                    banner = s.recv(4096)
            except: pass
            s.close()
            brand = _detect_brand(banner, port)
            return {"port": port, "open": True, "banner": banner[:200].decode("utf-8","replace").strip(), "brand": brand}
        s.close()
    except: pass
    return {"port": port, "open": False, "banner": "", "brand": None}

def _detect_brand(banner, port):
    b = banner.lower()
    if b"hikvision" in b or b"isapi" in b: return "Hikvision"
    if b"dahua" in b or b"dhi-" in b or b"xvr" in b: return "Dahua"
    if b"zkteco" in b or b"zk-" in b: return "ZKTeco"
    if b"axis" in b: return "Axis"
    if b"bosch" in b or b"divar" in b: return "Bosch"
    if b"panasonic" in b: return "Panasonic"
    if b"samsung" in b or b"hanwha" in b: return "Hanwha"
    if b"vivotek" in b: return "Vivotek"
    if b"geovision" in b: return "GeoVision"
    if b"d-link" in b or b"dlink" in b: return "D-Link"
    if b"tp-link" in b or b"tplink" in b: return "TP-Link"
    if b"ubiquiti" in b or b"unifi" in b: return "Ubiquiti"
    if b"reolink" in b: return "Reolink"
    if b"amcrest" in b: return "Amcrest"
    if b"foscam" in b: return "Foscam"
    if b"wanscam" in b: return "Wanscam"
    if b"tenvis" in b: return "Tenvis"
    if b"lhasa" in b: return "Lhasa"
    if port == 554: return "RTSP"
    if port == 8899: return "ONVIF"
    if port == 37777: return "Dahua SDK"
    if port == 34567: return "Hikvision SDK"
    return None

def detect_cameras(subnet, timeout=1.5, max_workers=100):
    """Escanea una subred buscando cámaras IP. Devuelve lista de dicts."""
    try:
        network = ipaddress.ip_network(subnet, strict=False)
    except:
        return {"error": f"Subred inválida: {subnet}"}
    ips = [str(ip) for ip in network.hosts()]
    found = []

    def _check_ip(ip):
        results = []
        with concurrent.futures.ThreadPoolExecutor(max_workers=len(CCTV_PORTS)) as pool:
            futures = {pool.submit(_tcp_port, ip, p, timeout): p for p in CCTV_PORTS}
            for f in concurrent.futures.as_completed(futures):
                r = f.result()
                if r["open"]:
                    results.append(r)
        if results:
            brands = list(set(r["brand"] for r in results if r["brand"]))
            return {"ip": ip, "ports": results, "brand": brands[0] if brands else "Desconocida", "count": len(results)}
        return None

    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as pool:
        futures = {pool.submit(_check_ip, ip): ip for ip in ips}
        for f in concurrent.futures.as_completed(futures):
            r = f.result()
            if r:
                found.append(r)
    return sorted(found, key=lambda x: [int(o) for o in x["ip"].split(".")])


# ─── TEST COMPLETO DE CÁMARA ─────────────────────────────────

def test_camera(host, timeout=2):
    """Prueba completa de una cámara IP."""
    result = {"host": host, "alive": False, "ports": [], "http": None, "rtsp": None, "onvif": None, "brand": None}

    # Ping TCP
    for p in [80, 443, 554]:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(timeout)
        try:
            if s.connect_ex((host, p)) == 0:
                result["alive"] = True
                result["latency"] = "vivo"
                s.close()
                break
        except: pass
        s.close()

    # Escaneo de puertos CCTV
    result["ports"] = [r for r in [_tcp_port(host, p, timeout) for p in CCTV_PORTS] if r["open"]]

    # HTTP probe
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(timeout)
        s.connect((host, 80))
        s.send(f"GET / HTTP/1.0\r\nHost: {host}\r\n\r\n".encode())
        resp = s.recv(4096).decode("utf-8","replace")
        s.close()
        result["http"] = resp[:300]
        brand = _detect_brand(resp.encode(), 80)
        if brand: result["brand"] = brand
    except: pass

    # RTSP probe
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(timeout)
        s.connect((host, 554))
        s.send(b"OPTIONS rtsp://" + host.encode() + b"/ RTSP/1.0\r\nCSeq: 1\r\n\r\n")
        resp = s.recv(4096).decode("utf-8","replace")
        s.close()
        result["rtsp"] = resp[:200]
    except: pass

    # ONVIF probe (WS-Discovery simplificado)
    try:
        msg = b'<?xml version="1.0"?><s:Envelope xmlns:s="http://www.w3.org/2003/05/soap-envelope" xmlns:a="http://schemas.xmlsoap.org/ws/2004/08/addressing"><s:Header><a:Action s:mustUnderstand="1">http://schemas.xmlsoap.org/ws/2005/04/discovery/Probe</a:Action><a:MessageID>uuid:1</a:MessageID><a:To s:mustUnderstand="1">urn:schemas-xmlsoap-org:ws:2005:04:discovery</a:To></s:Header><s:Body><Probe xmlns="http://schemas.xmlsoap.org/ws/2005/04/discovery"><Types>dn:NetworkVideoTransmitter</Types></Probe></s:Body></s:Envelope>'
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.settimeout(timeout)
        s.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        s.sendto(msg, ("239.255.255.250", 3702))
        try:
            data, _ = s.recvfrom(4096)
            result["onvif"] = "Detectado" if b"ProbeMatches" in data else "Sin respuesta"
        except socket.timeout:
            result["onvif"] = "No responde"
        s.close()
    except: pass

    if not result["brand"] and result["ports"]:
        brands = [p["brand"] for p in result["ports"] if p["brand"]]
        if brands: result["brand"] = brands[0]

    return result


# ─── RTSP URLS ────────────────────────────────────────────────

RTSP_PATTERNS = {
    "Hikvision": [
        "rtsp://{user}:{pwd}@{ip}:554/Streaming/Channels/101",
        "rtsp://{user}:{pwd}@{ip}:554/Streaming/Channels/102",
        "rtsp://{user}:{pwd}@{ip}:554/Streaming/Channels/201",
        "rtsp://{user}:{pwd}@{ip}:554/h264/ch1/main/av_stream",
        "rtsp://{user}:{pwd}@{ip}:554/h264/ch1/sub/av_stream",
    ],
    "Dahua": [
        "rtsp://{user}:{pwd}@{ip}:554/cam/realmonitor?channel=1&subtype=0",
        "rtsp://{user}:{pwd}@{ip}:554/cam/realmonitor?channel=1&subtype=1",
        "rtsp://{user}:{pwd}@{ip}:554/cam/realmonitor?channel=2&subtype=0",
    ],
    "Axis": [
        "rtsp://{user}:{pwd}@{ip}:554/axis-media/media.amp",
        "rtsp://{user}:{pwd}@{ip}:554/onvif/media",
    ],
    "Bosch": [
        "rtsp://{user}:{pwd}@{ip}:554/rtsp_tunnel",
        "rtsp://{user}:{pwd}@{ip}:554/",
    ],
    "Generic": [
        "rtsp://{user}:{pwd}@{ip}:554/live",
        "rtsp://{user}:{pwd}@{ip}:554/stream1",
        "rtsp://{user}:{pwd}@{ip}:554/video1",
        "rtsp://{user}:{pwd}@{ip}:554/h264",
        "rtsp://{user}:{pwd}@{ip}:554/mpeg4",
        "rtsp://{user}:{pwd}@{ip}:554/live/ch0",
        "rtsp://{user}:{pwd}@{ip}:554/ch1/main",
    ],
    "Panasonic": [
        "rtsp://{user}:{pwd}@{ip}:554/MediaInput/h264",
        "rtsp://{user}:{pwd}@{ip}:554/MediaInput/mpeg4",
    ],
    "Samsung/Hanwha": [
        "rtsp://{user}:{pwd}@{ip}:554/onvif/profile1/media",
        "rtsp://{user}:{pwd}@{ip}:554/onvif/profile2/media",
    ],
    "Vivotek": [
        "rtsp://{user}:{pwd}@{ip}:554/live.sdp",
        "rtsp://{user}:{pwd}@{ip}:554/rtsp.sdp",
    ],
    "Ubiquiti": [
        "rtsp://{user}:{pwd}@{ip}:554/video",
        "rtsp://{user}:{pwd}@{ip}:7447/video",
    ],
    "Reolink": [
        "rtsp://{user}:{pwd}@{ip}:554/h264Preview_01_main",
        "rtsp://{user}:{pwd}@{ip}:554/h264Preview_01_sub",
    ],
    "Amcrest": [
        "rtsp://{user}:{pwd}@{ip}:554/cam/realmonitor?channel=1&subtype=0",
        "rtsp://{user}:{pwd}@{ip}:554/cam/realmonitor?channel=1&subtype=1",
    ],
    "Foscam": [
        "rtsp://{user}:{pwd}@{ip}:554/videoMain",
        "rtsp://{user}:{pwd}@{ip}:554/videoSub",
    ],
    "TP-Link": [
        "rtsp://{user}:{pwd}@{ip}:554/stream1",
        "rtsp://{user}:{pwd}@{ip}:554/stream2",
    ],
    "Converter (Coax→IP)": [
        "rtsp://{user}:{pwd}@{ip}:554/live/ch0",
        "rtsp://{user}:{pwd}@{ip}:554/live/ch1_0",
        "rtsp://{user}:{pwd}@{ip}:554/live/ch1_1",
        "rtsp://{user}:{pwd}@{ip}:554/avstream/channel/1/stream/0",
        "rtsp://{user}:{pwd}@{ip}:554/avstream/channel/1/stream/1",
    ],
    "Uniview": [
        "rtsp://{user}:{pwd}@{ip}:554/unicast/c1/s0/live",
        "rtsp://{user}:{pwd}@{ip}:554/unicast/c1/s1/live",
        "rtsp://{user}:{pwd}@{ip}:554/media/video1",
    ],
    "Honeywell": [
        "rtsp://{user}:{pwd}@{ip}:554/streaming/channels/1",
        "rtsp://{user}:{pwd}@{ip}:554/streaming/channels/2",
    ],
    "Grandstream": [
        "rtsp://{user}:{pwd}@{ip}:554/live/ch00_0",
        "rtsp://{user}:{pwd}@{ip}:554/live/ch00_1",
        "rtsp://{user}:{pwd}@{ip}:554/play/ch00_0",
    ],
    "ACTi": [
        "rtsp://{user}:{pwd}@{ip}:554/stream1",
        "rtsp://{user}:{pwd}@{ip}:554/stream2",
        "rtsp://{user}:{pwd}@{ip}:554/rtspstream",
    ],
    "D-Link": [
        "rtsp://{user}:{pwd}@{ip}:554/live1.sdp",
        "rtsp://{user}:{pwd}@{ip}:554/live2.sdp",
        "rtsp://{user}:{pwd}@{ip}:554/mpeg4/media.amp",
    ],
    "Geovision": [
        "rtsp://{user}:{pwd}@{ip}:554/live.sdp",
        "rtsp://{user}:{pwd}@{ip}:554/rtsp/1",
        "rtsp://{user}:{pwd}@{ip}:554/rtsp/2",
    ],
    "Lorex": [
        "rtsp://{user}:{pwd}@{ip}:554/cam/realmonitor?channel=1&subtype=0",
        "rtsp://{user}:{pwd}@{ip}:554/cam/realmonitor?channel=1&subtype=1",
    ],
    "Wanscam": [
        "rtsp://{user}:{pwd}@{ip}:554/onvif1",
        "rtsp://{user}:{pwd}@{ip}:554/onvif2",
        "rtsp://{user}:{pwd}@{ip}:554/h264",
    ],
    "SV3C": [
        "rtsp://{user}:{pwd}@{ip}:554/stream0",
        "rtsp://{user}:{pwd}@{ip}:554/stream1",
    ],
    "Zmodo": [
        "rtsp://{user}:{pwd}@{ip}:5554/stream",
        "rtsp://{user}:{pwd}@{ip}:554/live/ch00_0",
    ],
    "Milesight": [
        "rtsp://{user}:{pwd}@{ip}:554/live/channel_0",
        "rtsp://{user}:{pwd}@{ip}:554/live/channel_1",
        "rtsp://{user}:{pwd}@{ip}:554/streaming/channel_0",
    ],
}

def rtsp_urls(brand="Generic", ip="192.168.1.100", user="admin", password="admin"):
    """Genera URLs RTSP probables para una marca/IP."""
    brand = brand.title()
    patterns = RTSP_PATTERNS.get(brand, RTSP_PATTERNS["Generic"])
    return [p.format(ip=ip, user=user, pwd=password) for p in patterns]




# ─── CONVERTIDORES COAXIAL→RJ45 ─────────────────────────────

CONVERTER_INFO = {
    "Dahua HVR": {
        "desc": "Convertidor HVR (Híbrido DVR) — canales BNC + IP. Requiere configuración de canal como 'IP' o 'Coax'.",
        "models": ["HVR1008", "HVR1016", "HVR1604", "HVR3204"],
        "config": "Configurar cada canal como IPC (IP Camera) en lugar de BNC. Asignar IP del conversor/encoder.",
    },
    "Dahua HCVR": {
        "desc": "Convertidor HCVR (Híbrido Coax) — compatible con cámaras HDCVI analógicas + IP. Conversión por canal.",
        "models": ["HCVR4104", "HCVR4108", "HCVR5116"],
        "config": "Menú → Cámara → Tipo → IPC. Ingresar IP, puerto, usuario y contraseña de la cámara.",
    },
    "Hikvision DVR Encoder": {
        "desc": "DVR Híbrido que convierte señal analógica a IP. Cada canal BNC puede configurarse como entrada IP.",
        "models": ["DS-7204HGHI", "DS-7208HGHI", "DS-7216HGHI"],
        "config": "Configuración → Cámara → Tipo → IP. Ingresar IP, protocolo (ONVIF/RTSP), usuario y contraseña.",
    },
    "Dahua Coax→IP Converter (EoC)": {
        "desc": "Convertidor de señal coaxial a Ethernet vía EoC (Ethernet over Coax). Transforma cualquier cámara analógica en IP.",
        "models": ["DHI-EOC101", "DHI-EOC104"],
        "config": "Conectar el conversor al coaxial y al switch PoE. Acceder por navegador a la IP por defecto (192.168.1.xxx). Configurar resolución, FPS y compresión.",
    },
    "Hikvision Coax→IP Converter": {
        "desc": "Módulo encoder coaxial→IP. Recibe video analógico BNC y lo digitaliza a RTSP/ONVIF.",
        "models": ["DS-6704HCI", "DS-6708HCI"],
        "config": "Asignar IP vía SADP (Hikvision tool). Configurar streaming: resolución, bitrate, GOP.",
    },
    "Genérico Coax→IP (Encoder)": {
        "desc": "Encoder de video analógico a IP. Usado para digitalizar cámaras CCTV antiguas.",
        "models": ["Encoder 1ch", "Encoder 4ch", "Encoder 8ch"],
        "config": "Conectar señal BNC al encoder. Conectar Ethernet al switch. Acceder vía navegador. Configurar IP, RTSP, ONVIF. Cada canal genera un stream RTSP independiente.",
    },
}

COAX_PINOUTS = {
    "BNC (hembra) a RJ45": {
        "desc": "Para convertir señal de cámara analógica (BNC) a RJ45 usando un balun o adaptador pasivo.",
        "wiring": "Par 1 (pin 1-2): Video + \nPar 2 (pin 3-6): Video - \nPar 3 (pin 4-5): Alimentación + (si aplica)\nPar 4 (pin 7-8): Alimentación - (si aplica)\nNOTA: Usar balun BNC→RJ45. No conectar coaxial directamente al RJ45.",
    },
    "RJ45 PoE (Cámaras IP)": {
        "desc": "Pinout estándar T568B para cámaras IP con PoE.",
        "wiring": "Pin 1: Blanco/Naranja (TX+)\nPin 2: Naranja (TX-)\nPin 3: Blanco/Verde (RX+)\nPin 4: Azul (PoE+)\nPin 5: Blanco/Azul (PoE+)\nPin 6: Verde (RX-)\nPin 7: Blanco/Marrón (PoE-)\nPin 8: Marrón (PoE-)",
    },
    "Siamese (BNC + Alimentación) a RJ45": {
        "desc": "Cable siamés con BNC para video y par de alimentación. Convertir a RJ45 requiere balun + fuente.",
        "wiring": "BNC: al balun → RJ45 pares 1/2\nAlimentación: al conector DC del balun activo o inyector\nNOTA: No conectar 12V directamente al RJ45 (daña el switch).",
    },
}

# ─── CREDENCIALES POR DEFECTO ──────────────────────────────────

DEFAULT_CREDS = {
    "Hikvision": {"user": "admin", "password": "12345"},
    "Dahua": {"user": "admin", "password": "admin"},
    "Axis": {"user": "root", "password": "pass"},
    "Bosch": {"user": "admin", "password": "admin"},
    "Panasonic": {"user": "admin", "password": "12345"},
    "Samsung/Hanwha": {"user": "admin", "password": "4321"},
    "Vivotek": {"user": "admin", "password": "admin"},
    "Ubiquiti": {"user": "ubnt", "password": "ubnt"},
    "Reolink": {"user": "admin", "password": ""},
    "Amcrest": {"user": "admin", "password": "admin"},
    "Foscam": {"user": "admin", "password": ""},
    "TP-Link": {"user": "admin", "password": "admin"},
    "D-Link": {"user": "admin", "password": ""},
    "ZKTeco": {"user": "admin", "password": "123456"},
    "Uniview": {"user": "admin", "password": "123456"},
    "Honeywell": {"user": "admin", "password": "12345"},
    "Grandstream": {"user": "admin", "password": "admin"},
    "ACTi": {"user": "admin", "password": "admin"},
    "Geovision": {"user": "admin", "password": "admin"},
    "Lorex": {"user": "admin", "password": "admin"},
    "Wanscam": {"user": "admin", "password": "123456"},
    "SV3C": {"user": "admin", "password": "admin"},
    "Zmodo": {"user": "admin", "password": ""},
    "Milesight": {"user": "admin", "password": "admin"},
}

DEFAULT_IPS = {
    "Hikvision": "192.0.0.64",
    "Dahua": "192.168.1.108",
    "Axis": "192.168.0.90",
    "Bosch": "192.168.178.178",
    "Panasonic": "192.168.1.253",
    "Vivotek": "192.168.0.20",
    "TP-Link": "192.168.1.100",
    "D-Link": "192.168.0.20",
    "Ubiquiti": "192.168.1.20",
    "Reolink": "192.168.1.10",
    "Foscam": "192.168.1.10",
    "Uniview": "192.168.1.200",
    "Honeywell": "192.168.1.168",
    "Grandstream": "192.168.1.168",
    "ACTi": "192.168.0.100",
    "Geovision": "192.168.0.10",
    "Lorex": "192.168.1.108",
    "Wanscam": "192.168.1.200",
    "SV3C": "192.168.1.10",
    "Zmodo": "10.1.0.100",
    "Milesight": "192.168.1.88",
}

# ─── RESET PROCEDURES ─────────────────────────────────────────

RESET_PROCEDURES = {
    "Hikvision": [
        "1. Encender la cámara",
        "2. Presionar y mantener el botón RESET (dentro de la tarjeta SD o en el cable) por 10 segundos",
        "3. Soltar. La cámara reinicia con IP 192.0.0.64 y credenciales admin/12345",
        "Alternativa: Usar SADP Tool (Windows) → seleccionar cámara → botón 'Forgot Password' → reset",
        "Alternativa 2: Contactar a soporte Hikvision con código QR de la cámara",
    ],
    "Dahua": [
        "1. Presionar botón RESET por 10-15 segundos (varía según modelo)",
        "2. La cámara emite un beep y reinicia",
        "3. IP por defecto: 192.168.1.108, usuario: admin, contraseña: admin",
        "Alternativa: Usar ConfigTool (Dahua) → buscar dispositivo → hacer click derecho → Reset",
        "Para XVR/NVR: Usar menú local → Sistema → Mantenimiento → Restaurar",
    ],
    "Hikvision DVR/NVR": [
        "1. Encender el DVR/NVR con monitor y mouse conectados",
        "2. Ir a Configuración → Sistema → Mantenimiento → Restaurar valores predeterminados",
        "3. Elegir 'Restaurar valores predeterminados' (no formatear disco)",
        "Alternativa: Mantener presionado botón RESET en placa por 10 segundos",
    ],
    "Dahua XVR/NVR": [
        "1. Menú → Sistema → Mantenimiento → Restaurar configuración de fábrica",
        "2. Ingresar contraseña actual (por defecto: admin)",
        "3. Confirmar. El equipo reinicia.",
        "Alternativa: Botón RESET en placa (abrir equipo, presionar 10s)",
    ],
    "Axis": [
        "1. Presionar botón de control (junto a conector de red) por 15-30 segundos",
        "2. Soltar cuando el LED parpadee en amarillo",
        "3. La cámara reinicia con IP DHCP (o 192.168.0.90 si no hay DHCP)",
        "Usuario: root, Contraseña: pass",
    ],
    "TP-Link": [
        "1. Mantener botón RESET por 5-10 segundos",
        "2. Soltar cuando el LED parpadee rápido",
        "3. IP por defecto: 192.168.1.100 (o DHCP)",
    ],
    "Reolink": [
        "1. Mantener botón RESET por 5 segundos",
        "2. La cámara emite un sonido y reinicia",
        "3. Usar app Reolink o cliente Windows para reconfigurar",
    ],
    "Uniview": [
        "1. Presionar botón RESET por 10 segundos (debajo de la tapa de la SD)",
        "2. Soltar. La cámara reinicia con IP 192.168.1.200 y credenciales admin/123456",
        "Alternativa: Usar Uniview Toolbox (Windows) para reset por software",
    ],
    "Grandstream": [
        "1. Presionar botón RESET (cerca del conector Ethernet) por 7 segundos",
        "2. Soltar cuando el LED parpadee rápido",
        "3. IP por defecto: 192.168.1.168, usuario: admin, contraseña: admin",
    ],
    "ACTi": [
        "1. Con cámara encendida, presionar botón RESET por 10 segundos",
        "2. La cámara reinicia con IP 192.168.0.100 y credenciales admin/admin",
        "Alternativa: Usar ACTi Utility (Windows) para reset por red",
    ],
    "Geovision": [
        "1. Presionar botón RESET en el cable (si tiene) o en la placa",
        "2. Mantener 10-15 segundos hasta que el LED parpadee",
        "3. IP por defecto: DHCP (o 192.168.0.10 si no hay DHCP)",
        "Alternativa: Usar GV-IP Device Utility para reset",
    ],
    "Lorex": [
        "1. Presionar botón RESET por 10-15 segundos",
        "2. La cámara emite un beep y reinicia",
        "3. IP por defecto: DHCP (o 192.168.1.108 si no hay DHCP)",
        "Credenciales por defecto: admin/admin",
        "Nota: Lorex es rebranding de Dahua. Aplica mismo procedimiento.",
    ],
    "D-Link": [
        "1. Presionar botón RESET en el costado por 10 segundos",
        "2. Soltar cuando el LED parpadee en rojo",
        "3. IP por defecto: 192.168.0.20 (o DHCP)",
        "Usuario: admin, contraseña: vacía",
    ],
    "Wanscam": [
        "1. Presionar botón RESET (en el cable o detrás) por 10 segundos",
        "2. Soltar y esperar reinicio",
        "3. IP por defecto: 192.168.1.200, admin/123456",
        "Alternativa: Usar app 'Wanscam HD' o 'IP Camera Tool'",
    ],
    "Honeywell": [
        "1. Presionar botón RESET por 10 segundos",
        "2. Soltar. La cámara reinicia con valores de fábrica",
        "3. IP por defecto: DHCP (192.168.1.168 si no hay DHCP)",
        "Usuario: admin, contraseña: 12345",
    ],
    "SV3C": [
        "1. Mantener botón RESET por 5-8 segundos",
        "2. La cámara emite un mensaje de voz 'Reset OK'",
        "3. IP por defecto: 192.168.1.10, admin/admin",
    ],
}


# ─── GUÍA DE CONFIGURACIÓN DE CONVERTIDORES ──────────────────

CONVERTER_GUIDE_STEPS = """
# Guía: Configurar convertidor Coaxial → RJ45

## Material necesario:
- Convertidor/Encoder coaxial→IP
- Cable coaxial de la cámara analógica
- Cable Ethernet (RJ45) al switch
- Fuente de alimentación para el convertidor (12V DC normalmente)
- Laptop con navegador web

## Pasos:

### 1. Conexión física
- Conectar cable coaxial de la cámara al puerto BNC del convertidor
- Conectar cable Ethernet del convertidor al switch PoE (o router)
- Conectar alimentación 12V al convertidor
- Verificar LEDs: Power (verde), Link (verde/parpadeo)

### 2. Descubrir IP del convertidor
- Por defecto, el convertidor toma IP por DHCP
- Usar la herramienta de detección del fabricante (SADP para Hikvision, ConfigTool para Dahua)
- O escanear la subred con esta misma herramienta (pestaña "Detectar")

### 3. Acceder vía navegador
- Abrir http://<IP_DEL_CONVERTIDOR>
- Credenciales por defecto: admin/admin o admin/12345
- Cambiar contraseña

### 4. Configurar streaming
- Ir a Configuración → Video/Stream
- Configurar:
  - Resolución: D1 (704x576) o CIF (352x288) según calidad deseada
  - Compresión: H.264 (recomendado) o MJPEG
  - Bitrate: 1024-4096 Kbps según ancho de banda
  - FPS: 25 (PAL) o 30 (NTSC)

### 5. Verificar RTSP
- URL típica: rtsp://admin:admin@<IP>:554/live/ch0
- Probar con VLC o con el probador RTSP de esta herramienta

### 6. Integrar con NVR
- En el NVR: agregar cámara IP
- Ingresar IP, puerto (554), usuario y contraseña del convertidor
- Verificar que el stream se visualice

## Notas importantes:
- El estándar de video analógico puede ser: PAL-N, PAL-B, NTSC (configurar según región)
- Algunos encoders requieren configuración de "Modo de canal": IPC (cámara IP) vs Coax (analógico)
- Si no hay video, verificar: voltaje de alimentación, conexión BNC, tipo de señal (CVBS/HDCVI/AHD/TVI)
"""


# ─── WORKFLOW: CÁMARA ANALÓGICA → CONVERTIDOR → PoE → IP ────

CAMERA_WORKFLOW = {
    "title": "Convertir cámara analógica (BNC) a IP mediante convertidor Coax→RJ45",
    "overview": "Cámara CCTV analógica → cable coaxial → convertidor Coax→RJ45 → cable Ethernet → Switch PoE → NVR/Red",
    "diagram": [
        "📷 Cámara Analógica (BNC)",
        "       ↓",
        "   Cable Coaxial (RG-59/RG-6)",
        "       ↓",
        "🔄 Convertidor Coax→RJ45 (Encoder)",
        "       ↓",
        "   Cable Ethernet (RJ45) ← PoE del switch alimenta el convertidor",
        "       ↓",
        "🔌 Switch PoE",
        "       ↓",
        "💾 NVR / Software de gestión / VLC",
    ],
    "steps": [
        {
            "step": 1,
            "name": "Resetear el convertidor (opcional pero recomendado)",
            "icon": "🔁",
            "detail": "Si el convertidor ya tuvo configuración previa, hacé factory reset. Mantené el botón RESET por 10-15s (varía por modelo). Esto asegura IP por DHCP y credenciales de fábrica.",
            "action": "Ir a pestaña Reset → elegir marca → seguir pasos",
            "action_tab": "reset",
        },
        {
            "step": 2,
            "name": "Conectar cámara analógica al convertidor",
            "icon": "🔌",
            "detail": "Conectá el cable coaxial BNC de la cámara al puerto BNC del convertidor. Verificá que el conector esté bien enroscado. Si la cámara tiene alimentación separada (12V DC), conectala también.",
            "action": "Ver pestaña Pinout → BNC→RJ45 para referencia de cableado",
            "action_tab": "pinout",
        },
        {
            "step": 3,
            "name": "Conectar convertidor al switch PoE",
            "icon": "🔗",
            "detail": "Conectá un cable Ethernet (RJ45) del convertidor al switch PoE. El switch PoE alimenta el convertidor a través del mismo cable Ethernet (PoE 802.3af/at). No necesita fuente externa si el convertidor es PoE-compatible.\n\n⚠️ Si el convertidor NO es PoE, conectá su fuente de alimentación 12V DC antes de enchufar el Ethernet.",
            "action": "Esperá 30-60s a que el convertidor arranque. El LED de Power/Link debe encenderse.",
            "action_tab": None,
        },
        {
            "step": 4,
            "name": "Descubrir IP del convertidor en la red",
            "icon": "🔍",
            "detail": "Usá la pestaña Detectar para escanear la subred. El convertidor aparecerá con los puertos 80 (HTTP) y 554 (RTSP) abiertos. Su marca suele detectarse automáticamente.\n\nIPs típicas: 192.168.1.108 (Dahua), 192.0.0.64 (Hikvision), DHCP si está disponible.",
            "action": "Ir a pestaña Detectar → ingresar subred → escanear",
            "action_tab": "detect",
        },
        {
            "step": 5,
            "name": "Probar conexión al convertidor",
            "icon": "🔌",
            "detail": "Una vez encontrada la IP, usá la pestaña Probar para verificar que el convertidor responda. La prueba muestra: ping, HTTP (acceso web), RTSP (stream de video), ONVIF (compatibilidad).",
            "action": "Ir a pestaña Probar → ingresar IP del convertidor",
            "action_tab": "probe",
        },
        {
            "step": 6,
            "name": "Generar y verificar URL RTSP",
            "icon": "📹",
            "detail": "Usá la pestaña RTSP para generar las URLs de streaming. Seleccioná la marca del convertidor, ingresá la IP, usuario y contraseña. Probá las URLs en VLC o en el NVR.\n\nURL típica para convertidores: rtsp://admin:admin@192.168.1.108:554/live/ch0",
            "action": "Ir a pestaña RTSP → seleccionar marca → generar URLs",
            "action_tab": "rtsp",
        },
        {
            "step": 7,
            "name": "Configurar streaming desde el navegador",
            "icon": "⚙️",
            "detail": "Abrí http://IP_DEL_CONVERTIDOR en el navegador. Ingresá con admin/admin (o credenciales por defecto). Configurá:\n- Resolución: D1 (704×576) o CIF según calidad\n- Compresión: H.264\n- Bitrate: 1024-4096 Kbps\n- FPS: 25 (PAL) / 30 (NTSC)\n- Usuario y contraseña para RTSP\n\n📌 Guardar cambios y reiniciar el convertidor.",
            "action": "Abrir navegador → http://IP → configurar",
            "action_tab": None,
        },
        {
            "step": 8,
            "name": "Agregar al NVR o visor",
            "icon": "💾",
            "detail": "En el NVR (Hikvision, Dahua, etc.):\n1. Agregar cámara IP\n2. Ingresar IP del convertidor\n3. Protocolo: ONVIF o RTSP\n4. Puerto: 554 (RTSP) o 80 (HTTP para ONVIF)\n5. Usuario y contraseña configurados en paso 7\n6. Ruta del stream: /live/ch0 o /avstream/channel/1/stream/0\n\nVerificar que el video se visualice correctamente.",
            "action": "Ir al menú del NVR → Agregar cámara → configurar",
            "action_tab": None,
        },
    ],
    "tips": [
        "💡 Si el convertidor no aparece en la red, probá con un cable Ethernet directo a la PC (sin switch) y asignale una IP manual en el mismo rango que la IP por defecto del convertidor.",
        "💡 Los LED del convertidor indican: Power (verde fijo = alimentación OK), Link (verde/parpadeo = actividad de red), Video (parpadeo = detecta señal de cámara).",
        "💡 Si no hay video, verificá: tipo de señal (la cámara debe ser CVBS, no HDCVI/AHD/TVI a menos que el convertidor lo soporte), voltaje de alimentación, integridad del cable coaxial.",
        "💡 El estándar de video debe coincidir: PAL-N para Argentina, NTSC para América del Norte. Configurable en la mayoría de los convertidores.",
        "💡 Algunos convertidores tienen un jumper o switch para elegir entre 12V externo y PoE. Verificá la posición correcta.",
        "💡 Si el switch PoE no entrega energía (el convertidor no enciende), probá con un inyector PoE intermedio o fuente 12V.",
    ],
}


# ─── API PÚBLICA ────────────────────────────────────────────

# ─── ACCIONES SOBRE CÁMARAS (PTZ, REBOOT, CONFIG) ───────────

def _http_request(host, port, path, user="admin", password="", ssl=False, method="GET", body=None, timeout=5):
    """Helper: hace request HTTP y devuelve (status, body, headers)."""
    import http.client
    try:
        if ssl:
            conn = http.client.HTTPSConnection(host, port, timeout=timeout)
        else:
            conn = http.client.HTTPConnection(host, port, timeout=timeout)
        auth = ""
        if user:
            import base64
            auth = "Basic " + base64.b64encode(f"{user}:{password}".encode()).decode()
        headers = {"Authorization": auth, "Connection": "close"}
        if body:
            headers["Content-Type"] = "application/xml"
        conn.request(method, path, body=body, headers=headers)
        resp = conn.getresponse()
        data = resp.read()
        conn.close()
        return resp.status, data, dict(resp.getheaders())
    except Exception as e:
        return 0, str(e).encode(), {}


def onvif_ptz(host, port=80, user="admin", password="admin", command="right", timeout=5):
    """Controla PTZ vía ONVIF. Comandos: left, right, up, down, zoom_in, zoom_out, stop."""
    soap_template = """<?xml version="1.0" encoding="utf-8"?>
<s:Envelope xmlns:s="http://www.w3.org/2003/05/soap-envelope"
            xmlns:tds="http://www.onvif.org/ver10/device/wsdl"
            xmlns:tev="http://www.onvif.org/ver10/events/wsdl"
            xmlns:trt="http://www.onvif.org/ver10/media/wsdl"
            xmlns:tptz="http://www.onvif.org/ver20/ptz/wsdl"
            xmlns:tt="http://www.onvif.org/ver10/schema">
  <s:Body>
    {body}
  </s:Body>
</s:Envelope>"""

    # GetProfiles para obtener token
    prof_body = """<trt:GetProfiles/>"""
    xml = soap_template.replace("{body}", prof_body)
    status, data, _ = _http_request(host, port, "/onvif/media_service", user, password, method="POST", body=xml, timeout=timeout)
    if status != 200:
        return {"error": f"Error ONVIF GetProfiles: status {status}", "raw": data[:200].decode("utf-8","replace")}

    import xml.parsers.expat
    token = None
    # Parse simple para encontrar el primer token
    try:
        text = data.decode("utf-8","replace")
        import re
        m = re.search(r'<tt:Token>([^<]+)</tt:Token>', text)
        if m: token = m.group(1)
    except: pass

    if not token:
        return {"error": "No se encontró token ONVIF", "raw": data[:300]}

    # Map commands to ONVIF RelativeMove
    cmd_map = {
        "left":   (-0.3, 0, 0),
        "right":  (0.3, 0, 0),
        "up":     (0, 0.3, 0),
        "down":   (0, -0.3, 0),
        "zoom_in": (0, 0, 0.3),
        "zoom_out": (0, 0, -0.3),
    }

    if command == "stop":
        move_body = f"""<tptz:Stop>
  <tptz:ProfileToken>{token}</tptz:ProfileToken>
</tptz:Stop>"""
    elif command in cmd_map:
        x, y, z = cmd_map[command]
        move_body = f"""<tptz:RelativeMove>
  <tptz:ProfileToken>{token}</tptz:ProfileToken>
  <tptz:Translation>
    <tt:PanTilt x="{x}" y="{y}" space="http://www.onvif.org/ver10/tptz/PanTiltSpaces/TranslationGenericSpace"/>
    <tt:Zoom x="{z}" space="http://www.onvif.org/ver10/tptz/ZoomSpaces/TranslationGenericSpace"/>
  </tptz:Translation>
</tptz:RelativeMove>"""
    else:
        return {"error": f"Comando desconocido: {command}"}

    xml = soap_template.replace("{body}", move_body)
    status, data, _ = _http_request(host, port, "/onvif/ptz_service", user, password, method="POST", body=xml, timeout=timeout)
    return {"status": status, "command": command, "token": token, "ok": status == 200}


def camera_reboot(host, port=80, user="admin", password="admin", brand="Hikvision", timeout=5):
    """Reinicia cámara vía HTTP API."""
    brand_lower = brand.lower()
    try:
        if "hikvision" in brand_lower:
            status, data, _ = _http_request(host, port, "/ISAPI/System/reboot", user, password, method="PUT", body="<?xml version=\"1.0\" encoding=\"UTF-8\"?><Reboot><status>0</status></Reboot>", timeout=timeout)
            return {"ok": status == 200, "status": status, "method": "ISAPI"}
        elif "dahua" in brand_lower:
            import urllib.parse
            path = f"/cgi-bin/reboot.cgi?action=reboot&user={user}&pwd={password}"
            status, data, _ = _http_request(host, port, path, timeout=timeout)
            return {"ok": status == 200, "status": status, "method": "CGI"}
        else:
            # ONVIF Reboot (SystemReboot)
            soap = """<?xml version="1.0" encoding="utf-8"?>
<s:Envelope xmlns:s="http://www.w3.org/2003/05/soap-envelope"
            xmlns:tds="http://www.onvif.org/ver10/device/wsdl">
  <s:Body>
    <tds:SystemReboot/>
  </s:Body>
</s:Envelope>"""
            status, data, _ = _http_request(host, port, "/onvif/device_service", user, password, method="POST", body=soap, timeout=timeout)
            return {"ok": status == 200, "status": status, "method": "ONVIF"}
    except Exception as e:
        return {"error": str(e)}


def camera_factory_reset(host, port=80, user="admin", password="admin", brand="Hikvision", timeout=8):
    """Restablece la cámara a valores de fábrica vía HTTP API."""
    brand_lower = brand.lower()
    try:
        if "hikvision" in brand_lower:
            status, data, _ = _http_request(host, port, "/ISAPI/System/factoryReset", user, password, method="PUT", timeout=timeout)
            if status == 200:
                return {"ok": True, "method": "ISAPI", "message": "Restablecimiento iniciado"}
            status2, data2, _ = _http_request(host, port, "/ISAPI/System/restoreFactory", user, password, method="PUT", timeout=timeout)
            return {"ok": status2 == 200, "status": status2, "method": "ISAPI", "message": "Restablecimiento iniciado" if status2 == 200 else f"Error HTTP {status2}"}
        elif "dahua" in brand_lower:
            path = f"/cgi-bin/magicBox.cgi?action=factoryReset&user={user}&pwd={password}"
            status, data, _ = _http_request(host, port, path, timeout=timeout)
            return {"ok": status == 200, "status": status, "method": "CGI", "message": "Restablecimiento iniciado" if status == 200 else f"Error HTTP {status}"}
        elif "axis" in brand_lower:
            status, data, _ = _http_request(host, port, "/axis-cgi/factorydefault.cgi", user, password, timeout=timeout)
            return {"ok": status == 200, "status": status, "method": "CGI", "message": "Restablecimiento iniciado" if status == 200 else f"Error HTTP {status}"}
        else:
            # ONVIF FactoryReset
            soap = """<?xml version="1.0" encoding="utf-8"?>
<s:Envelope xmlns:s="http://www.w3.org/2003/05/soap-envelope"
            xmlns:tds="http://www.onvif.org/ver10/device/wsdl">
  <s:Body>
    <tds:SystemReboot/>
  </s:Body>
</s:Envelope>"""
            status, data, _ = _http_request(host, port, "/onvif/device_service", user, password, method="POST", body=soap, timeout=timeout)
            return {"ok": False, "note": "ONVIF no tiene factoryReset estándar, se intentó reboot", "status": status, "method": "ONVIF"}
    except Exception as e:
        return {"error": str(e)}


def camera_info_via_http(host, port=80, user="admin", password="admin", brand="Hikvision", timeout=5):
    """Obtiene info detallada de la cámara vía HTTP API."""
    brand_lower = brand.lower()
    try:
        if "hikvision" in brand_lower:
            status, data, _ = _http_request(host, port, "/ISAPI/System/deviceInfo", user, password, timeout=timeout)
            if status == 200:
                import re
                text = data.decode("utf-8","replace")
                info = {}
                for tag in ["deviceName", "deviceID", "model", "serialNumber", "firmwareVersion", "firmwareReleasedDate", "deviceType", "macAddress"]:
                    m = re.search(f'<{tag}>(.*?)</{tag}>', text)
                    if m: info[tag] = m.group(1)
                return info
        elif "dahua" in brand_lower:
            status, data, _ = _http_request(host, port, f"/cgi-bin/global.cgi?action=getCurrentUser&user={user}&pwd={password}", timeout=timeout)
            status2, data2, _ = _http_request(host, port, f"/cgi-bin/magicBox.cgi?action=getHardwareVersion&user={user}&pwd={password}", timeout=timeout)
            info = {"raw_dahua": data[:200].decode("utf-8","replace")}
            if status2 == 200: info["hardware"] = data2.decode("utf-8","replace").strip()
            return info
        elif "axis" in brand_lower:
            resp = _http_request(host, port, "/axis-cgi/prodinfo.cgi", timeout=timeout)
            return {"raw": resp[1][:300].decode("utf-8","replace")}
    except: pass
    return {}


def onvif_get_profiles(host, port=80, user="admin", password="admin", timeout=5):
    """Obtiene perfiles ONVIF y devuelve el primer token."""
    soap = """<?xml version="1.0" encoding="utf-8"?>
<s:Envelope xmlns:s="http://www.w3.org/2003/05/soap-envelope"
            xmlns:trt="http://www.onvif.org/ver10/media/wsdl">
  <s:Body><trt:GetProfiles/></s:Body>
</s:Envelope>"""
    status, data, _ = _http_request(host, port, "/onvif/media_service", user, password, method="POST", body=soap, timeout=timeout)
    if status != 200:
        return None, data[:200].decode("utf-8","replace")
    import re
    text = data.decode("utf-8","replace")
    tokens = re.findall(r'<tt:Token>([^<]+)</tt:Token>', text)
    return tokens[0] if tokens else None, text


def onvif_ptz_presets(host, port=80, user="admin", password="admin", action="list", preset_name="", timeout=5):
    """Gestiona presets PTZ vía ONVIF.
    action: 'list' (lista), 'goto' (ir a), 'set' (guardar posición actual), 'remove' (eliminar)
    preset_name: nombre del preset (para set). Para goto usa el token del primer preset."""
    token, raw = onvif_get_profiles(host, port, user, password, timeout)
    if not token:
        return {"error": "No se pudo obtener token ONVIF", "raw": raw[:200]}

    soap_body = ""
    soap_target = "/onvif/ptz_service"

    if action == "list":
        soap_body = f"""<tptz:GetPresets>
  <tptz:ProfileToken>{token}</tptz:ProfileToken>
</tptz:GetPresets>"""
        status, data, _ = _http_request(host, port, soap_target, user, password, method="POST",
            body=soap_header("tptz", soap_body), timeout=timeout)
        if status != 200:
            return {"error": f"Error GetPresets: {status}", "raw": data[:200].decode("utf-8","replace")}
        import re
        text = data.decode("utf-8","replace")
        presets = []
        for m in re.finditer(r'<tt:Preset(?:[^>]*)>.*?</tt:Preset>', text, re.DOTALL):
            p = m.group()
            pt = re.search(r'<tt:Token>([^<]+)</tt:Token>', p)
            pn = re.search(r'<tt:Name>([^<]*)</tt:Name>', p)
            presets.append({"token": pt.group(1) if pt else "", "name": pn.group(1) if pn else ""})
        return {"ok": True, "action": "list", "presets": presets, "count": len(presets)}

    elif action == "goto":
        soap_body = f"""<tptz:GotoPreset>
  <tptz:ProfileToken>{token}</tptz:ProfileToken>
  <tptz:PresetToken>{preset_name}</tptz:PresetToken>
</tptz:GotoPreset>"""
        status, data, _ = _http_request(host, port, soap_target, user, password, method="POST",
            body=soap_header("tptz", soap_body), timeout=timeout)
        return {"ok": status == 200, "action": "goto", "preset": preset_name, "status": status}

    elif action == "set":
        soap_body = f"""<tptz:SetPreset>
  <tptz:ProfileToken>{token}</tptz:ProfileToken>
  <tptz:PresetName>{preset_name}</tptz:PresetName>
</tptz:SetPreset>"""
        status, data, _ = _http_request(host, port, soap_target, user, password, method="POST",
            body=soap_header("tptz", soap_body), timeout=timeout)
        return {"ok": status == 200, "action": "set", "preset": preset_name, "status": status}

    elif action == "remove":
        soap_body = f"""<tptz:RemovePreset>
  <tptz:ProfileToken>{token}</tptz:ProfileToken>
  <tptz:PresetToken>{preset_name}</tptz:PresetToken>
</tptz:RemovePreset>"""
        status, data, _ = _http_request(host, port, soap_target, user, password, method="POST",
            body=soap_header("tptz", soap_body), timeout=timeout)
        return {"ok": status == 200, "action": "remove", "preset": preset_name, "status": status}

    return {"error": f"Acción desconocida: {action}"}


def soap_header(ns, body):
    """Envuelve body en SOAP envelope con namespace."""
    return f"""<?xml version="1.0" encoding="utf-8"?>
<s:Envelope xmlns:s="http://www.w3.org/2003/05/soap-envelope"
            xmlns:tds="http://www.onvif.org/ver10/device/wsdl"
            xmlns:trt="http://www.onvif.org/ver10/media/wsdl"
            xmlns:tptz="http://www.onvif.org/ver20/ptz/wsdl"
            xmlns:tev="http://www.onvif.org/ver10/events/wsdl"
            xmlns:tt="http://www.onvif.org/ver10/schema">
  <s:Body>
    {body}
  </s:Body>
</s:Envelope>"""


def camera_set_ip(host, port=80, user="admin", password="admin", brand="Hikvision",
                  new_ip="192.168.1.100", subnet_mask="255.255.255.0", gateway="192.168.1.1", timeout=5):
    """Cambia la IP de la cámara vía HTTP API."""
    brand_lower = brand.lower()
    try:
        if "hikvision" in brand_lower:
            xml = f"""<?xml version="1.0" encoding="UTF-8"?>
<NetworkInterface>
  <id>1</id>
  <IPAddress>
    <ipVersion>IPv4</ipVersion>
    <AddressingType>static</AddressingType>
    <IPAddress>{new_ip}</IPAddress>
    <SubnetMask>{subnet_mask}</SubnetMask>
    <DefaultGateway>
      <IPv4Address>{gateway}</IPv4Address>
    </DefaultGateway>
  </IPAddress>
</NetworkInterface>"""
            status, data, _ = _http_request(host, port, "/ISAPI/System/Network/interfaces/1/IPAddress", user, password,
                                           method="PUT", body=xml, timeout=timeout)
            if status in (200, 201):
                return {"ok": True, "method": "ISAPI", "ip": new_ip, "message": f"IP cambiada a {new_ip}"}
            # Intentar vía NetworkManagement
            xml2 = f"""<?xml version="1.0" encoding="UTF-8"?>
<IPAddress>
  <ipVersion>IPv4</ipVersion>
  <AddressingType>static</AddressingType>
  <IPAddress>{new_ip}</IPAddress>
  <SubnetMask>{subnet_mask}</SubnetMask>
  <DefaultGateway>{gateway}</DefaultGateway>
</IPAddress>"""
            status2, data2, _ = _http_request(host, port, "/ISAPI/System/Network/interfaces/1/ipAddress", user, password,
                                              method="PUT", body=xml2, timeout=timeout)
            return {"ok": status2 in (200, 201), "method": "ISAPI", "ip": new_ip,
                    "message": f"IP cambiada a {new_ip}" if status2 in (200,201) else f"Error HTTP {status}/{status2}"}
        elif "dahua" in brand_lower:
            path = f"/cgi-bin/netCfg.cgi?action=setIP&user={user}&pwd={password}&ip={new_ip}&mask={subnet_mask}&gateway={gateway}"
            status, data, _ = _http_request(host, port, path, timeout=timeout)
            return {"ok": status == 200, "method": "CGI", "ip": new_ip,
                    "message": f"IP cambiada a {new_ip}" if status == 200 else f"Error HTTP {status}"}
        elif "axis" in brand_lower:
            path = f"/axis-cgi/param.cgi?action=update&Network.BootProto=static&Network.IPAddress={new_ip}&Network.SubnetMask={subnet_mask}&Network.DefaultRouter={gateway}&user={user}&pwd={password}"
            status, data, _ = _http_request(host, port, path, timeout=timeout)
            return {"ok": status == 200, "method": "CGI", "ip": new_ip,
                    "message": f"IP cambiada a {new_ip}" if status == 200 else f"Error HTTP {status}"}
        else:
            return {"error": f"Marca {brand} no soportada para cambio de IP"}
    except Exception as e:
        return {"error": str(e)}


def camera_set_password(host, port=80, user="admin", password="admin", brand="Hikvision",
                        new_user="admin", new_password="admin123", timeout=5):
    """Cambia la contraseña de admin vía HTTP API."""
    brand_lower = brand.lower()
    try:
        if "hikvision" in brand_lower:
            import hashlib, random, string
            # Hikvision requiere primer login con contraseña actual, luego cambiar
            # Método: ISAPI System/User/Password
            xml = f"""<?xml version="1.0" encoding="UTF-8"?>
<User>
  <userName>{new_user}</userName>
  <password>{new_password}</password>
  <userLevel>Administrator</userLevel>
</User>"""
            status, data, _ = _http_request(host, port, "/ISAPI/Security/users/1", user, password,
                                           method="PUT", body=xml, timeout=timeout)
            if status in (200, 201):
                return {"ok": True, "method": "ISAPI", "user": new_user, "message": "Contraseña cambiada"}
            status2, data2, _ = _http_request(host, port, "/ISAPI/System/IO/user/1/password", user, password,
                                              method="PUT", body=xml, timeout=timeout)
            return {"ok": status2 in (200, 201), "method": "ISAPI",
                    "message": "Contraseña cambiada" if status2 in (200,201) else f"Error HTTP {status}/{status2}"}
        elif "dahua" in brand_lower:
            path = f"/cgi-bin/userManager.cgi?action=modifyUser&user={user}&pwd={password}&username={new_user}&newPassword={new_password}"
            status, data, _ = _http_request(host, port, path, timeout=timeout)
            return {"ok": status == 200, "method": "CGI",
                    "message": "Contraseña cambiada" if status == 200 else f"Error HTTP {status}"}
        else:
            # ONVIF SetUser
            import base64
            pass_b64 = base64.b64encode(new_password.encode()).decode()
            soap = soap_header("tds", f"""<tds:SetUser>
  <tds:User>
    <tt:Username>{new_user}</tt:Username>
    <tt:Password>{new_password}</tt:Password>
    <tt:UserLevel>Administrator</tt:UserLevel>
  </tds:User>
</tds:SetUser>""")
            status, data, _ = _http_request(host, port, "/onvif/device_service", user, password,
                                            method="POST", body=soap, timeout=timeout)
            return {"ok": status == 200, "method": "ONVIF",
                    "message": "Contraseña cambiada" if status == 200 else f"Error HTTP {status}"}
    except Exception as e:
        return {"error": str(e)}


def camera_set_datetime(host, port=80, user="admin", password="admin", brand="Hikvision",
                        datetime=None, ntp_server="", timeout=5):
    """Configura fecha/hora o NTP en la cámara vía HTTP API."""
    import time
    if datetime is None:
        datetime = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    brand_lower = brand.lower()
    try:
        if "hikvision" in brand_lower:
            if ntp_server:
                xml = f"""<?xml version="1.0" encoding="UTF-8"?>
<NTP>
  <enabled>true</enabled>
  <NTPPort>123</NTPPort>
  <NTPServer>{ntp_server}</NTPServer>
  <timeSyncMode>NTP</timeSyncMode>
</NTP>"""
                status, data, _ = _http_request(host, port, "/ISAPI/System/time/ntpServers/1", user, password,
                                                method="PUT", body=xml, timeout=timeout)
            else:
                xml = f"""<?xml version="1.0" encoding="UTF-8"?>
<Time>
  <timeMode>manual</timeMode>
  <localTime>{datetime}</localTime>
</Time>"""
                status, data, _ = _http_request(host, port, "/ISAPI/System/time", user, password,
                                                method="PUT", body=xml, timeout=timeout)
            return {"ok": status in (200, 201), "method": "ISAPI",
                    "message": f"Hora configurada" if status in (200,201) else f"Error HTTP {status}"}
        elif "dahua" in brand_lower:
            if ntp_server:
                path = f"/cgi-bin/ntp.cgi?action=setConfig&user={user}&pwd={password}&Enable=1&Server={ntp_server}&Port=123"
            else:
                path = f"/cgi-bin/global.cgi?action=setTime&user={user}&pwd={password}&time={datetime}"
            status, data, _ = _http_request(host, port, path, timeout=timeout)
            return {"ok": status == 200, "method": "CGI",
                    "message": f"Hora configurada" if status == 200 else f"Error HTTP {status}"}
        elif "axis" in brand_lower:
            path = f"/axis-cgi/param.cgi?action=update&System.Date.Time={datetime}&user={user}&pwd={password}"
            status, data, _ = _http_request(host, port, path, timeout=timeout)
            return {"ok": status == 200, "method": "CGI",
                    "message": f"Hora configurada" if status == 200 else f"Error HTTP {status}"}
        else:
            # ONVIF SetSystemDateAndTime
            import time
            utc = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
            soap = soap_header("tds", f"""<tds:SetSystemDateAndTime>
  <tds:DateTimeType>Manual</tds:DateTimeType>
  <tds:DaylightSavings>false</tds:DaylightSavings>
  <tds:UTCDateTime>
    <tt:Time>
      <tt:Hour>{time.strftime('%H', time.gmtime())}</tt:Hour>
      <tt:Minute>{time.strftime('%M', time.gmtime())}</tt:Minute>
      <tt:Second>{time.strftime('%S', time.gmtime())}</tt:Second>
    </tt:Time>
    <tt:Date>
      <tt:Year>{time.strftime('%Y', time.gmtime())}</tt:Year>
      <tt:Month>{time.strftime('%m', time.gmtime())}</tt:Month>
      <tt:Day>{time.strftime('%d', time.gmtime())}</tt:Day>
    </tt:Date>
  </tds:UTCDateTime>
</tds:SetSystemDateAndTime>""")
            status, data, _ = _http_request(host, port, "/onvif/device_service", user, password,
                                            method="POST", body=soap, timeout=timeout)
            return {"ok": status == 200, "method": "ONVIF",
                    "message": f"Hora configurada" if status == 200 else f"Error HTTP {status}"}
    except Exception as e:
        return {"error": str(e)}


def camera_set_dhcp(host, port=80, user="admin", password="admin", brand="Hikvision",
                    enabled=True, timeout=5):
    """Activa/desactiva DHCP en la cámara vía HTTP API."""
    brand_lower = brand.lower()
    try:
        if "hikvision" in brand_lower:
            mode = "DHCP" if enabled else "static"
            xml = f"""<?xml version="1.0" encoding="UTF-8"?>
<IPAddress>
  <ipVersion>IPv4</ipVersion>
  <AddressingType>{mode}</AddressingType>
</IPAddress>"""
            status, data, _ = _http_request(host, port, "/ISAPI/System/Network/interfaces/1/ipAddress", user, password,
                                           method="PUT", body=xml, timeout=timeout)
            return {"ok": status in (200, 201), "method": "ISAPI", "dhcp": enabled,
                    "message": f"DHCP {'activado' if enabled else 'desactivado'}" if status in (200,201) else f"Error HTTP {status}"}
        elif "dahua" in brand_lower:
            mode = "1" if enabled else "0"
            path = f"/cgi-bin/netCfg.cgi?action=setIP&user={user}&pwd={password}&dhcp={mode}"
            status, data, _ = _http_request(host, port, path, timeout=timeout)
            return {"ok": status == 200, "method": "CGI", "dhcp": enabled,
                    "message": f"DHCP {'activado' if enabled else 'desactivado'}" if status == 200 else f"Error HTTP {status}"}
        else:
            return {"error": f"Marca {brand} no soportada para DHCP"}
    except Exception as e:
        return {"error": str(e)}


def camera_snapshot(host, port=80, user="admin", password="admin", brand="Hikvision", timeout=5):
    """Obtiene un snapshot JPEG de la cámara vía HTTP API.
    Devuelve bytes de la imagen o None."""
    brand_lower = brand.lower()
    try:
        paths = []
        if "hikvision" in brand_lower:
            paths = ["/ISAPI/Streaming/channels/101/picture",
                      "/ISAPI/Streaming/channels/102/picture",
                      "/onvif/snapshot"]
        elif "dahua" in brand_lower:
            paths = [f"/cgi-bin/snapshot.cgi?channel=1&user={user}&pwd={password}",
                      f"/cgi-bin/imagesCatch?channel=1&user={user}&pwd={password}"]
        elif "axis" in brand_lower:
            paths = ["/axis-cgi/jpg/image.cgi"]
        elif "ubiquiti" in brand_lower:
            paths = ["/snap.jpeg", "/snapshot.cgi"]
        else:
            paths = ["/onvif/snapshot", "/snapshot.jpeg", "/snap.jpg", "/image/jpeg"]

        for path in paths:
            try:
                if brand_lower == "dahua" and "snapshot.cgi" in path:
                    # Dahua necesita user/pwd en URL
                    status, data, _ = _http_request(host, port, path, timeout=timeout)
                else:
                    status, data, _ = _http_request(host, port, path, user, password, timeout=timeout)
                if status == 200 and len(data) > 1000 and data[:4] in (b'\xff\xd8\xff\xe0', b'\xff\xd8\xff\xdb', b'\xff\xd8\xff\xe1'):
                    return data
            except: pass
    except: pass
    return None


def default_creds_for(brand):
    """Devuelve credenciales por defecto para una marca."""
    return DEFAULT_CREDS.get(brand, {"user": "admin", "password": ""})


def default_ip_for(brand):
    """Devuelve IP por defecto para una marca."""
    return DEFAULT_IPS.get(brand, "DHCP")


def api_info():
    """Información del módulo probador."""
    return {
        "brands": list(RTSP_PATTERNS.keys()),
        "converters": list(CONVERTER_INFO.keys()),
        "default_creds": {k: v for k, v in DEFAULT_CREDS.items()},
        "default_ips": DEFAULT_IPS,
        "reset_procedures": list(RESET_PROCEDURES.keys()),
    }

def converter_details(name):
    """Devuelve información detallada de un convertidor."""
    return CONVERTER_INFO.get(name, {"error": "Convertidor no encontrado"})

def pinout_info(name):
    """Devuelve información de cableado."""
    return COAX_PINOUTS.get(name, {"error": "Pinout no encontrado"})

def reset_procedure(brand):
    """Devuelve procedimiento de reset para una marca."""
    return RESET_PROCEDURES.get(brand, {"error": "Marca no encontrada"})
