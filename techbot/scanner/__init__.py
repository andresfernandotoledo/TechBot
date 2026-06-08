import socket
import ipaddress
import struct
import os
import sys
import concurrent.futures
import subprocess
import time
import re

# ─── BASE DE DATOS DE PUERTOS ─────────────────────────────────
SERVICE_PORTS = {
    # ─── BÁSICOS ───────────────────────────────────────────────
    21: "FTP", 22: "SSH", 23: "Telnet", 25: "SMTP", 53: "DNS",
    80: "HTTP", 110: "POP3", 111: "RPC", 123: "NTP", 135: "MSRPC",
    139: "NetBIOS", 143: "IMAP", 161: "SNMP", 162: "SNMP Trap",
    389: "LDAP", 443: "HTTPS", 445: "SMB", 465: "SMTPS",
    500: "IPsec", 514: "Syslog", 554: "RTSP", 587: "SMTP Sub",
    631: "IPP", 636: "LDAPS", 993: "IMAPS", 995: "POP3S",
    # ─── BASES DE DATOS / STORAGE ─────────────────────────────
    1080: "SOCKS", 1194: "OpenVPN", 1433: "MSSQL", 1521: "Oracle",
    2049: "NFS", 3306: "MySQL", 5432: "PostgreSQL", 6379: "Redis",
    9042: "Cassandra", 9200: "Elasticsearch", 27017: "MongoDB",
    # ─── INFRAESTRUCTURA / CLOUD ──────────────────────────────
    2375: "Docker", 2376: "Docker TLS", 3389: "RDP", 5000: "Flask/API",
    5900: "VNC", 5985: "WinRM HTTP", 5986: "WinRM HTTPS",
    6443: "Kubernetes API", 8080: "HTTP Alt/Proxy", 8443: "HTTPS Alt",
    9000: "SonarQube/Portainer", 9090: "Prometheus", 10050: "Zabbix",
    # ─── INDUSTRIAL (SCADA / PLC) ────────────────────────────
    102: "Siemens S7", 502: "Modbus TCP", 2404: "IEC 60870-5-104",
    1883: "MQTT (IoT)", 8883: "MQTT SSL", 44818: "EtherNet/IP",
    47808: "BACnet/IP", 50000: "SAP/AS",
    # ─── CCTV / VIDEO ──────────────────────────────────────────
    3478: "STUN (VoIP/CCTV)", 3480: "Bosch CCTV", 8000: "Hikvision SDK",
    34567: "Hikvision/Dahua SDK", 37777: "Dahua SDK", 8899: "ONVIF",
    8200: "CCTV Stream", 8554: "RTSP Alt", 8888: "Dahua HTTP",
    # ─── CONTROL DE ACCESO ─────────────────────────────────────
    4370: "ZKTeco SDK", 5099: "Lenel/Paxton", 7000: "HID VertX",
    6000: "Nedap AEOS", 4445: "SALTO", 6200: "Assa Abloy",
}

# ─── CONSTANTES DE COMPATIBILIDAD ───────────────────────────
ONVIF_PORTS = [80, 8080, 8899]
CCTV_PORTS = [80, 443, 554, 8000, 8090, 8200, 8888, 8899, 37777, 3480, 7000,
              8443, 8080, 9393, 9505, 34567, 35555, 7547]
AC_PORTS = [80, 443, 8080, 8081, 8082, 4370, 5099, 5100, 8443, 3000]

# ─── FIRMAS DE SERVICIOS ──────────────────────────────────────
SERVICE_SIGNATURES = {
    "Cisco": ["cisco", "ios", "catalyst", "nexus", "rv320", "rv340"],
    "MikroTik": ["mikrotik", "routeros", "bandwidth test"],
    "Ubiquiti": ["ubnt", "ubiquiti", "unifi", "airmax", "edgemax"],
    "Fortinet": ["fortinet", "fortigate", "fortios"],
    "HP/Aruba": ["procurve", "aruba", "hewlett-packard"],
    "Dell": ["dell", "powerconnect", "idrac"],
    "VMware": ["vmware", "esxi", "vcenter"],
    "Siemens": ["siemens", "s7-", "simatic", "scalance"],
    "Schneider": ["schneider", "electric", "apc", "ups", "modicon"],
    "Hikvision": ["hikvision", "isapi", "ivms", "ds-2cd", "idvr"],
    "Dahua": ["dahua", "dhi-", "xvr", "nvr-", "ipc-"],
    "ZKTeco": ["zkteco", "zk-", "inbio", "iclock"],
    "Apache": ["apache", "httpd"],
    "Nginx": ["nginx"],
    "Microsoft": ["microsoft", "iis", "winrm", "msrpc"],
}

# ─── FUNCIONES CORE ───────────────────────────────────────────

def identify_vendor_and_service(banner, port):
    """Identificación universal de fabricante y servicio."""
    banner_lower = str(banner).lower()
    for vendor, keywords in SERVICE_SIGNATURES.items():
        for kw in keywords:
            if kw in banner_lower:
                return vendor
    special_ports = {502: "Industrial (Modbus)", 102: "Siemens SIMATIC", 1883: "IoT (MQTT)", 4370: "ZKTeco Biometric", 37777: "Dahua Device", 8000: "Hikvision Device"}
    return special_ports.get(port, None)

def scan_port(host, port, timeout=1.5):
    """Escanea un puerto TCP y recolecta banner."""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        result = sock.connect_ex((host, port))
        if result == 0:
            banner = ""
            try:
                if port in [80, 8080, 443, 8888]:
                    sock.send(b"GET / HTTP/1.1\r\nHost: " + host.encode() + b"\r\nConnection: close\r\n\r\n")
                banner = sock.recv(4096).decode("utf-8", errors="replace").strip()
            except: pass
            sock.close()
            vendor = identify_vendor_and_service(banner, port)
            service = SERVICE_PORTS.get(port, "Desconocido")
            return port, "open", service, vendor, banner, "tcp"
        sock.close()
        return port, "closed", "", None, "", "tcp"
    except: return port, "error", "", None, "", "tcp"


# ─── SONDAS UDP ──────────────────────────────────────────────

UDP_PROBES = {
    53: b"\x00\x01\x01\x00\x00\x01\x00\x00\x00\x00\x00\x00\x03www\x06google\x03com\x00\x00\x01\x00\x01",
    123: b"\x1b\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00",
    161: b"\x30\x26\x02\x01\x01\x04\x06\x70\x75\x62\x6c\x69\x63\xa0\x19\x02\x04\x00\x00\x00\x01\x02\x01\x00\x02\x01\x00\x30\x0b\x30\x09\x06\x05\x2b\x06\x01\x02\x01\x01\x05\x00",
    162: b"\x30\x26\x02\x01\x01\x04\x06\x70\x75\x62\x6c\x69\x63\xa0\x19\x02\x04\x00\x00\x00\x01\x02\x01\x00\x02\x01\x00\x30\x0b\x30\x09\x06\x05\x2b\x06\x01\x02\x01\x01\x05\x00",
    67: b"\x01\x01\x06\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00",
}

def scan_port_udp(host, port, timeout=1.5):
    """Escanea un puerto UDP enviando sonda específica si está disponible."""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.settimeout(timeout)
        probe = UDP_PROBES.get(port)
        if probe:
            sock.sendto(probe, (str(host), port))
        else:
            sock.sendto(b"\x00", (str(host), port))
        try:
            data, _ = sock.recvfrom(1024)
            sock.close()
            service = SERVICE_PORTS.get(port, "Desconocido")
            return port, "open", service, "", data[:200].decode("utf-8", errors="replace").strip(), "udp"
        except socket.timeout:
            sock.close()
            # Timeout sin respuesta → podría estar abierto pero sin respuesta
            return port, "open?", SERVICE_PORTS.get(port, "Desconocido"), "", "", "udp"
        except OSError:
            sock.close()
            return port, "closed", "", None, "", "udp"
    except: return port, "error", "", None, "", "udp"


def scan_ports(host, ports=None, timeout=1.5, max_threads=100, protocol="tcp"):
    """Escaneo masivo multihilo TCP o UDP."""
    if ports is None: ports = sorted(list(SERVICE_PORTS.keys()))
    scanner = scan_port if protocol == "tcp" else scan_port_udp
    results = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_threads) as executor:
        futures = {executor.submit(scanner, host, p, timeout): p for p in ports}
        for future in concurrent.futures.as_completed(futures):
            try:
                port, state, service, vendor, banner, proto = future.result()
                if state == "open" or state == "open?":
                    results.append({
                        "port": port, "state": state, "service": service,
                        "vendor": vendor or "Genérico",
                        "banner": banner[:200] if banner else "",
                        "protocol": proto,
                    })
            except: continue
    return sorted(results, key=lambda x: x["port"])

QUICK_SCAN_PORTS = [21, 22, 23, 25, 53, 80, 110, 123, 135, 139, 143, 161, 443, 445, 554, 631, 993, 995, 1433, 1521, 3306, 3389, 5432, 5900, 6379, 8080, 8443, 9090, 27017]

def quick_scan(host, timeout=1.5):
    """Escaneo rápido inteligente (solo puertos más comunes)."""
    return scan_ports(host, ports=QUICK_SCAN_PORTS, timeout=timeout)

PING_PORTS = [22, 80, 443, 8080, 8443, 3389, 8081, 9090]

def ping_host(host, timeout=2):
    """Ping por TCP connect (puertos comunes). Sin bins externos, funciona en todo SO."""
    for port in PING_PORTS:
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(timeout)
            start = time.time()
            ok = sock.connect_ex((str(host), port)) == 0
            end = time.time()
            sock.close()
            if ok:
                return {"alive": True, "host": str(host), "latency": round((end-start)*1000, 2), "ttl": -1, "port": port, "method": "tcp"}
        except:
            pass
    # Fallback ICMP si el binario está disponible
    is_win = os.name == "nt"
    ping_paths = ["ping.exe"] if is_win else ["/usr/bin/ping", "/bin/ping", "/system/bin/ping", "/data/data/com.termux/files/usr/bin/ping"]
    ping_bin = None
    for p in ping_paths:
        if is_win or os.path.exists(p):
            ping_bin = p
            break
    if ping_bin:
        try:
            param = "-n" if is_win else "-c"
            w_flag = "-w" if is_win else "-W"
            # Windows timeout en ms, Linux en segundos
            win_timeout = str(int(timeout * 1000))
            nix_timeout = str(timeout)
            cmd = [ping_bin, param, "1", w_flag, (win_timeout if is_win else nix_timeout), str(host)]
            if not is_win:
                cmd.insert(2, "-4")  # forzar IPv4 en Linux
            start = time.time()
            result = subprocess.run(cmd, capture_output=True, timeout=timeout+2)
            end = time.time()
            if result.returncode == 0:
                ttl = -1
                match = re.search(r"ttl=(\d+)", result.stdout.decode(), re.IGNORECASE)
                if match: ttl = int(match.group(1))
                return {"alive": True, "host": str(host), "latency": round((end-start)*1000, 2), "ttl": ttl, "port": None, "method": "icmp"}
        except:
            pass
    return {"alive": False, "host": str(host), "latency": 0, "ttl": -1, "port": None, "method": None}

def discover_hosts(subnet, timeout=1.5, max_threads=100):
    """Descubrimiento de hosts en red."""
    try: network = ipaddress.ip_network(subnet, strict=False)
    except: return []
    found = []
    ips = [str(ip) for ip in network.hosts()]
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_threads) as executor:
        futures = {executor.submit(ping_host, ip, timeout): ip for ip in ips}
        for future in concurrent.futures.as_completed(futures):
            res = future.result()
            if res["alive"]: found.append(res)
    return sorted(found, key=lambda x: [int(o) for o in x["host"].split(".")])

def os_detection(host, timeout=2):
    """Detección de S.O. (TTL + Banners)."""
    p = ping_host(host, timeout)
    if not p["alive"]: return "Inalcanzable"
    ttl = p["ttl"]
    method = p.get("method", "tcp")
    if ttl < 0:
        via = f"via TCP:{p.get('port','?')}" if method == "tcp" else "via ICMP"
        return f"Activo ({via}) — TTL no disponible"
    guess = "Desconocido"
    if 0 < ttl <= 64: guess = "Linux / IoT / Unix"
    elif 64 < ttl <= 128: guess = "Windows / macOS"
    elif 128 < ttl <= 255: guess = "Cisco / Router / Network"
    return f"{guess} (TTL={ttl})"

def traceroute(host, max_hops=15, timeout=1.5):
    """Traceroute."""
    results = []
    for ttl in range(1, max_hops + 1):
        try:
            param = "-n" if os.name == "nt" else "-c"
            ttl_f = "-i" if os.name == "nt" else "-t"
            cmd = ["ping", param, "1", ttl_f, str(ttl), "-W", "1000", str(host)]
            proc = subprocess.run(cmd, capture_output=True, timeout=timeout+1)
            ip = "*"
            m = re.search(r"(\d+\.\d+\.\d+\.\d+)", proc.stdout.decode())
            if m: ip = m.group(1)
            results.append({"hop": ttl, "ip": ip})
            if ip == str(host): break
        except: results.append({"hop": ttl, "ip": "*"})
    return results

# ─── FUNCIONES ESPECIALIZADAS PARA CCTV/AC ─────────────────────

def scan_cctv(host, timeout=2):
    """Escaneo específico de puertos CCTV."""
    ports = [80, 443, 554, 8000, 8090, 8200, 8888, 8899, 37777, 34567, 35555]
    results = scan_ports(host, ports, timeout)
    for r in results: r["device_type"] = r["vendor"]
    return results

def scan_access_control(host, timeout=2):
    """Escaneo específico de puertos Control de Acceso."""
    ports = [80, 443, 8080, 4370, 5099, 5100, 6000, 4445, 6200]
    results = scan_ports(host, ports, timeout)
    for r in results: r["device_type"] = r["vendor"]
    return results

def identify_device(host, timeout=3):
    """Identificación rápida por puerto y banner."""
    results = {}
    scan = quick_scan(host, timeout)
    for r in scan:
        if r["vendor"] != "Genérico":
            results[r["port"]] = r["vendor"]
    return results

def discover_cctv(subnet, timeout=2):
    """Descubre dispositivos CCTV en subred."""
    hosts = discover_hosts(subnet, timeout)
    found = []
    for h in hosts:
        res = scan_cctv(h["host"], timeout)
        if res:
            found.append({"ip": h["host"], "open_ports": [r["port"] for r in res], "device_type": list(set([r["vendor"] for r in res])), "services": res})
    return found

# ─── UTILIDADES REQUERIDAS POR APP.PY ──────────────────────────

def compare_port_scans(scan1, scan2):
    """Compara dos resultados de escaneo."""
    ports1 = {r["port"]: r for r in scan1}
    ports2 = {r["port"]: r for r in scan2}
    new = [ports2[p] for p in ports2 if p not in ports1]
    removed = [ports1[p] for p in ports1 if p not in ports2]
    return {"new_ports": new, "removed_ports": removed, "total_before": len(scan1), "total_after": len(scan2)}

def export_scan_results(results, filename="scan_result.txt"):
    """Exporta resultados a archivo."""
    with open(filename, "w") as f:
        f.write("Puerto\tServicio\tFabricante\tBanner\n")
        for r in results:
            f.write(f"{r['port']}\t{r['service']}\t{r['vendor']}\t{r['banner']}\n")
    return filename

def service_detection(host, port, timeout=3):
    """Alias para scan_port detallado."""
    p, s, svc, v, b = scan_port(host, port, timeout)
    return {"port": p, "service": svc, "vendor": v, "banner": b}
