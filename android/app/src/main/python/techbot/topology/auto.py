import ipaddress
import socket
import os
import re
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from techbot.snmp import snmp_get, snmp_walk

# Puertos comunes para detectar hosts activos
# Incluye Windows (SMB, RDP, NetBIOS), Linux (SSH), Mac (NetBIOS, VNC), web, CCTV, IoT
PING_PORTS = [
    22, 23, 80, 443, 3389, 8080, 8443, 9090, 8081,
    135, 139, 445, 548, 5900, 5901, 554, 161, 53,
    3000, 5000, 8000, 8888, 2049, 3306, 5432, 6379,
    11211, 27017, 5555, 4242, 5060, 1234, 2323, 7547,
]

TYPE_PORTS = {
    "router":   {22, 23, 80, 443, 161, 2323, 7547},
    "switch":   {22, 23, 80, 443, 161},
    "firewall": {22, 80, 443, 8443},
    "server":   {22, 80, 443, 3389, 8080, 3306, 5432, 6379, 27017},
    "pc":       {22, 3389, 445, 139, 135, 5900},
    "camera":   {80, 554, 8080, 443},
    "ap":       {22, 80, 443},
    "nvr":      {80, 554, 443, 8080},
    "printer":  {80, 443, 515, 631, 9100},
    "iot":      {80, 443, 554, 2323, 7547, 5555, 4242},
}

OID_SYSNAME = "1.3.6.1.2.1.1.5.0"
OID_SYSDESCR = "1.3.6.1.2.1.1.1.0"
OID_IFDESCR = "1.3.6.1.2.1.2.2.1.2"

# Múltiples OIDs de tabla ARP (distintos fabricantes/vendedores)
ARP_OIDS = [
    "1.3.6.1.2.1.4.22.1.2",  # ipNetToMediaPhysAddress (estándar)
    "1.3.6.1.2.1.3.1.1.1",    # atPhysAddress (MIB-II legacy)
    "1.3.6.1.2.1.4.35.1.4",   # ipNetToPhysicalPhysAddress (IPv6/IPv4)
    "1.3.6.1.4.1.9.9.23.1.2.1.1.4",  # ciscoIpNetToMediaEntry.cipNetToMediaPhys
    "1.3.6.1.4.1.1991.1.1.3.1.1.1.2",  # MikroTik ARP table
]


def _try_port(ip, port, timeout):
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(timeout)
        ok = s.connect_ex((ip, port)) == 0
        s.close()
        return ok
    except:
        return False


def _tcp_ping(ip, timeout=1):
    with ThreadPoolExecutor(max_workers=len(PING_PORTS)) as ex:
        futs = {ex.submit(_try_port, ip, p, timeout): p for p in PING_PORTS}
        for f in as_completed(futs):
            try:
                if f.result():
                    return True
            except:
                pass
    return False


def _scan_ports(ip, timeout=0.8):
    open_ports = set()
    with ThreadPoolExecutor(max_workers=len(PING_PORTS)) as ex:
        futs = {ex.submit(_try_port, ip, p, timeout): p for p in PING_PORTS}
        for f in as_completed(futs):
            port = futs[f]
            try:
                if f.result():
                    open_ports.add(port)
            except:
                pass
    return open_ports


def _detect_type_by_ports(ports):
    if not ports:
        return "unknown"
    best = "unknown"
    best_score = 0
    for dtype, dports in TYPE_PORTS.items():
        score = len(ports & dports)
        if score > best_score:
            best_score = score
            best = dtype
    return best


def _detect_type_by_sysdescr(descr):
    d = descr.lower()
    if any(x in d for x in ["camera", "video", "encoder", "decoder", "dvr", "nvr", "cctv"]):
        if "dvr" in d: return "dvr"
        if "nvr" in d: return "nvr"
        return "camera"
    if any(x in d for x in ["access point", "wap", "wireless ap", "ap-"]):
        return "ap"
    if any(x in d for x in ["firewall", "fortigate", "fortinet", "palo alto"]):
        return "firewall"
    if any(x in d for x in ["switch", "sg", "ws-c", "catalyst", "procurve", "smart switch", "vlan"]):
        return "switch"
    if any(x in d for x in ["router", "gateway", "cpe", "mikrotik", "rb", "home hub"]):
        return "router"
    if any(x in d for x in ["server", "proliant", "poweredge", "system x", "xserve"]):
        return "server"
    if any(x in d for x in ["printer", "laserjet", "officejet", "deskjet"]):
        return "printer"
    return "unknown"


def _detect_vendor_by_sysname(sysname):
    name = sysname.lower()
    if "cisco" in name: return "Cisco"
    if "mikrotik" in name or "mikro" in name: return "MikroTik"
    if "fortinet" in name or "fortigate" in name: return "Fortinet"
    if "ubiquiti" in name or "ubnt" in name: return "Ubiquiti"
    if "huawei" in name: return "Huawei"
    if "hikvision" in name: return "Hikvision"
    if "dahua" in name: return "Dahua"
    if "hp" in name or "procurve" in name or "aruba" in name: return "HP"
    if "dell" in name or "poweredge" in name: return "Dell"
    if "tp-link" in name or "tplink" in name: return "TP-Link"
    if "netgear" in name: return "Netgear"
    if "d-link" in name or "dlink" in name: return "D-Link"
    if "asus" in name: return "Asus"
    if "zyxel" in name: return "ZyXEL"
    if "linux" in name or "ubuntu" in name or "debian" in name: return "Linux"
    if "windows" in name or "microsoft" in name: return "Windows"
    if "apple" in name or "mac" in name: return "Apple"
    if "raspberry" in name or "rpi" in name: return "Raspberry Pi"
    return "Unknown"


def _read_local_arp_cache():
    """Lee la cache ARP local en las 4 plataformas.
    - Linux/Android: /proc/net/arp (file read, sin subprocess)
    - Windows/macOS: arp -a (subprocess fallback)."""
    ips = set()

    # Linux/Android: lectura directa de /proc/net/arp
    if os.path.exists("/proc/net/arp"):
        try:
            with open("/proc/net/arp") as f:
                next(f, None)
                for line in f:
                    parts = line.strip().split()
                    if len(parts) >= 4 and parts[0] != "IP" and parts[2] == "0x2":
                        try:
                            ipaddress.ip_address(parts[0])
                            ips.add(parts[0])
                        except:
                            pass
        except:
            pass
        if ips:
            return list(ips)

    # Fallback: arp -a (Windows/macOS/Linux)
    try:
        out = subprocess.getoutput("arp -a 2>/dev/null")
        # Formato Windows: 192.168.1.100 00-11-22-33-44-55 dynamic
        # Formato macOS/Linux: ? (192.168.1.100) at 00:11:22:33:44:55 on en0
        for m in re.finditer(r'(\d+\.\d+\.\d+\.\d+)', out):
            ip = m.group(1)
            try:
                ipaddress.ip_address(ip)
                ips.add(ip)
            except:
                pass
    except:
        pass

    return list(ips)


def _parse_arp_oids(arp, own_ip):
    """Extrae IPs vecinas de resultados SNMP ARP table."""
    found = []
    for oid, val in arp.items():
        parts = oid.split(".")
        if len(parts) >= 4:
            try:
                ipp = ".".join(parts[-4:])
                ipaddress.ip_address(ipp)
                if ipp != own_ip:
                    found.append(ipp)
            except:
                pass
    return found


def _scan_subnet(subnet, timeout=1, max_threads=100):
    try:
        net = ipaddress.ip_network(subnet, strict=False)
    except:
        return []
    if net.is_loopback:
        return []
    num_hosts = net.num_addresses
    if num_hosts > 1024:
        return []
    ips = [str(ip) for ip in net.hosts()]
    alive = []
    with ThreadPoolExecutor(max_workers=min(max_threads, len(ips))) as ex:
        fut = {ex.submit(_tcp_ping, ip, timeout): ip for ip in ips}
        for f in as_completed(fut):
            ip = fut[f]
            try:
                if f.result():
                    alive.append(ip)
            except:
                pass
    return sorted(alive, key=lambda x: [int(o) for o in x.split(".")])


def _get_hostname(ip):
    try:
        return socket.gethostbyaddr(ip)[0]
    except:
        return ip


def _subnet_from_ip(ip):
    try:
        ip_obj = ipaddress.ip_address(ip)
        if ip_obj.version == 4:
            parts = ip.split(".")
            return f"{parts[0]}.{parts[1]}.{parts[2]}.0/24"
    except:
        pass
    return None


def discover_topology(seed_ip, community="public", depth=2, max_devices=60):
    visited = set()
    devices = []
    edges = []
    queue = []
    subnet = _subnet_from_ip(seed_ip)

    # Paso 1: escanear toda la subred por TCP
    tcp_found = set()
    if subnet:
        scanned = _scan_subnet(subnet, timeout=1)
        for aip in scanned:
            tcp_found.add(aip)
            if aip not in visited:
                queue.append((aip, 0))

    # Paso 1b: cache ARP local (después del TCP scan, el kernel tiene ARP entries)
    local_arp = _read_local_arp_cache()
    for aip in local_arp:
        if aip not in visited and aip not in tcp_found:
            # Verificar que esté en la misma subred
            try:
                if subnet and ipaddress.ip_address(aip) in ipaddress.ip_network(subnet, strict=False):
                    queue.append((aip, 0))
            except:
                pass

    if not queue:
        queue.append((seed_ip, 0))

    # Paso 2: procesar cada host descubierto
    snmp_success_ips = []

    while queue and len(devices) < max_devices:
        ip, current_depth = queue.pop(0)
        if ip in visited or current_depth > depth:
            continue
        visited.add(ip)

        hostname = _get_hostname(ip)
        device = {
            "id": ip, "label": hostname, "ip": ip,
            "type": "unknown", "vendor": "", "model": "", "interfaces": [],
        }

        # Intentar SNMP
        snmp_ok = False
        try:
            sysname = snmp_get(ip, community, OID_SYSNAME)
            if sysname:
                snmp_ok = True
                snmp_success_ips.append(ip)
                device["label"] = str(sysname)
                device["vendor"] = _detect_vendor_by_sysname(str(sysname))
                try:
                    sysdescr = snmp_get(ip, community, OID_SYSDESCR)
                    if sysdescr:
                        descr = str(sysdescr)[:80]
                        device["model"] = descr
                        t = _detect_type_by_sysdescr(descr)
                        if t != "unknown":
                            device["type"] = t
                except:
                    pass

                # ARP table: probar múltiples OIDs
                if current_depth < depth:
                    for arp_oid in ARP_OIDS:
                        try:
                            arp = snmp_walk(ip, community, arp_oid)
                            if arp:
                                neighs = _parse_arp_oids(arp, ip)
                                for neigh_ip in neighs:
                                    if neigh_ip not in visited:
                                        if _try_port(neigh_ip, 80, 0.3) or _try_port(neigh_ip, 443, 0.3):
                                            queue.append((neigh_ip, current_depth + 1))
                                            if not any(e["source"] == ip and e["target"] == neigh_ip for e in edges):
                                                edges.append({"source": ip, "target": neigh_ip, "label": "ARP", "type": "ethernet"})
                        except:
                            pass

                # Interfaces SNMP
                try:
                    ifaces = snmp_walk(ip, community, OID_IFDESCR)
                    if ifaces:
                        device["interfaces"] = list(ifaces.values())[:10]
                except:
                    pass
        except:
            pass

        # Detectar tipo por puertos si SNMP no lo determinó
        if device["type"] == "unknown":
            open_ports = _scan_ports(ip, timeout=0.8)
            device["type"] = _detect_type_by_ports(open_ports)

        if snmp_ok:
            device["snmp"] = True

        devices.append(device)

    # Paso 3: conectar dispositivos sin edge al seed (topología estrella)
    for d in devices:
        if d["ip"] != seed_ip and not any(e["target"] == d["ip"] for e in edges):
            edges.append({"source": seed_ip, "target": d["ip"], "label": "link", "type": "ethernet"})

    return {"devices": devices, "edges": edges, "count": len(devices)}
