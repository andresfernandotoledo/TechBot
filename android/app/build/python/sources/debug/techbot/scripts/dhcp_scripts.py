import socket
import struct
import subprocess
import ipaddress
import sys
import os


def dhcp_discover_simulate(interface="eth0"):
    """Simula un DHCP Discover y captura la oferta (requiere scapy o dhclient -v)"""

    # Simula un DHCP Discover usando dhclient. Ejecuta dhclient en modo verbose y busca ofertas (OFFER) y confirmaciones (ACK) en la salida.
    try:
        result = subprocess.getoutput(
            f"timeout 5 dhclient -v -1 {interface} 2>&1 | grep -i 'offer\\|ack'"
        )
        return result or "No se recibió oferta DHCP. ¿scapy disponible?"
    except Exception as e:
        return f"Error: {e}"


def dhcp_lease_info(interface="eth0"):
    """Muestra información de la concesión DHCP actual"""

    # Lee el archivo de leases DHCP para una interfaz. Busca en varias rutas típicas: /var/lib/dhcp/, /var/lib/NetworkManager/ y versiones dhcpcd.
    lease_files = []
    if sys.platform == "linux":
        lease_files = [
            f"/var/lib/dhcp/dhclient.{interface}.leases",
            "/var/lib/dhcp/dhclient.leases",
            f"/var/lib/NetworkManager/dhclient-{interface}.lease",
        ]
    elif sys.platform == "win32":
        return subprocess.getoutput("ipconfig /all | findstr /i DHCP")

    for lf in lease_files:
        if os.path.exists(lf):
            with open(lf) as f:
                return f.read()
    for lf in lease_files:
        alt = lf.replace("dhclient", "dhcpcd")
        if os.path.exists(alt):
            with open(alt) as f:
                return f.read()
    return "No se encontraron leases DHCP"


def dhcp_suggest_range(network, exclude_ips=None):
    """Sugiere un rango DHCP para una red dada"""

    # Sugiere un rango DHCP para una red. Excluye IPs específicas si se pasan, ajusta start/end basado en la cantidad de hosts totales.
    red = ipaddress.IPv4Network(network, strict=False)
    hosts = list(red.hosts())
    if not hosts:
        return {"error": "Red sin hosts disponibles"}

    exclude = exclude_ips or []
    exclude = [ipaddress.ip_address(ip) for ip in exclude if ip]

    start = hosts[0]
    end = hosts[-1]
    if len(hosts) > 100:
        start = hosts[10]
        end = hosts[-10]

    for h in hosts:
        if h not in exclude:
            start = h
            break
    for h in reversed(hosts):
        if h not in exclude and h != start:
            end = h
            break

    return {
        "network": network,
        "total_hosts": len(hosts),
        "dhcp_range_start": str(start),
        "dhcp_range_end": str(end),
        "available": len(hosts) - len([h for h in hosts if h in exclude]),
        "subnet_mask": str(red.netmask),
        "gateway_suggestion": str(hosts[0] if hosts[0] not in exclude else hosts[1]),
    }


def dhcp_check_server(server_ip, timeout=3):
    """Verifica si un servidor DHCP responde en el puerto 67"""

    # Verifica si un servidor DHCP responde en puerto UDP 67. Crea un socket UDP, conecta y si no hay excepción el puerto está accesible.
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.settimeout(timeout)
        sock.connect((server_ip, 67))
        sock.close()
        return {"server": server_ip, "port": 67, "reachable": True}
    except Exception as e:
        return {"server": server_ip, "port": 67, "reachable": False, "error": str(e)}


def dhcp_starvation_detect(arp_table_cmd="arp -a"):
    """Detecta posible ataque DHCP starvation revisando la tabla ARP"""

    # Detecta posible ataque DHCP starvation analizando la tabla ARP. Si una misma MAC tiene muchas IPs distintas, es sospechoso (más de 3 = alerta).
    output = subprocess.getoutput(arp_table_cmd)
    lines = output.strip().split("\n")
    entries = {}
    for line in lines:
        parts = line.split()
        if len(parts) >= 2:
            ip = parts[0].strip("()")
            mac = parts[1] if len(parts) >= 2 else ""
            if ip.count(".") == 3:
                if mac not in entries:
                    entries[mac] = []
                entries[mac].append(ip)

    suspicious = {mac: ips for mac, ips in entries.items() if len(ips) > 3}
    return {
        "total_arp_entries": len(lines),
        "unique_macs": len(entries),
        "suspicious_macs": len(suspicious),
        "details": suspicious,
    }


def dhcp_scope_calc(router_ip, mask, reserve_first=10, reserve_last=10):
    """Calcula el scope DHCP óptimo para una subred"""

    # Calcula scope DHCP óptimo. Toma IP del router y máscara, calcula la red, reserva las primeras N y últimas N IPs para infraestructura.
    red = ipaddress.IPv4Network(f"{router_ip}/{mask}", strict=False)
    hosts = list(red.hosts())
    if not hosts:
        return {"error": "Red sin hosts"}

    scope_start = hosts[reserve_first] if len(hosts) > reserve_first else hosts[0]
    scope_end = hosts[-(reserve_last + 1)] if len(hosts) > reserve_last else hosts[-1]
    total = int(scope_end) - int(scope_start) + 1

    return {
        "network": str(red),
        "netmask": str(red.netmask),
        "gateway": router_ip,
        "scope_start": str(scope_start),
        "scope_end": str(scope_end),
        "total_addresses": total,
        "reserved_beginning": reserve_first,
        "reserved_end": reserve_last,
        "broadcast": str(red.broadcast_address),
    }


def dhcp_ping_before_offer(host, timeout=2):
    """Simula la verificación Ping Before Offer que hacen algunos servidores DHCP"""

    # Simula ping before offer: verifica si una IP ya está respondiendo antes de asignarla. Si responde, está en uso.
    try:
        response = os.system(f"ping -c 1 -W {timeout} {host} >/dev/null 2>&1")
        return {"host": host, "in_use": response == 0, "available": response != 0}
    except Exception as e:
        return {"error": str(e)}


def dhcp_find_authoritative():
    """Busca servidores DHCP autoritativos en la red local via nmap o broadcast"""

    # Busca servidores DHCP autoritativos. Detecta la red local y sugiere nmap con script broadcast-dhcp-discover.
    try:
        local_ip = subprocess.getoutput(
            "ip route get 1 | awk '{print $7; exit}'"
        )
        subnet = subprocess.getoutput(
            f"ip route | grep {local_ip} | awk '{{print $1}}'"
        )
        if not subnet:
            subnet = subprocess.getoutput("ip -o -f inet addr show | awk '{print $4}'")
        if subnet:
            return {"suggestion": f"nmap --script broadcast-dhcp-discover -e {subnet}"}
        return {"suggestion": "nmap --script broadcast-dhcp-discover"}
    except Exception as e:
        return {"error": str(e)}


def dhcp_option_list(option_code):
    """Devuelve la descripción de una opción DHCP estándar"""

    # Devuelve descripción de opciones DHCP estándar (RFC 2132). Diccionario completo desde opción 1 hasta 212. Útil para configurar servidores DHCP.
    options = {
        1: "Subnet Mask", 2: "Time Offset", 3: "Router", 4: "Time Server",
        5: "Name Server", 6: "Domain Name Server", 7: "Log Server",
        8: "Cookie Server", 9: "LPR Server", 10: "Impress Server",
        11: "Resource Location Server", 12: "Host Name", 13: "Boot File Size",
        14: "Merit Dump File", 15: "Domain Name", 16: "Swap Server",
        17: "Root Path", 18: "Extensions Path", 19: "IP Forwarding",
        20: "Non-Local Source Routing", 21: "Policy Filter",
        22: "Maximum Datagram Reassembly", 23: "Default IP TTL",
        24: "Path MTU Aging Timeout", 25: "Path MTU Plateau Table",
        26: "Interface MTU", 27: "All Subnets are Local",
        28: "Broadcast Address", 29: "Perform Mask Discovery",
        30: "Mask Supplier", 31: "Perform Router Discovery",
        32: "Router Solicitation", 33: "Static Route",
        34: "Trailer Encapsulation", 35: "ARP Cache Timeout",
        36: "Ethernet Encapsulation", 37: "TCP Default TTL",
        38: "TCP Keepalive Interval", 39: "TCP Keepalive Garbage",
        40: "NIS Domain", 41: "NIS Servers", 42: "NTP Servers",
        43: "Vendor Specific Info", 44: "NetBIOS Name Server",
        45: "NetBIOS Datagram Distribution", 46: "NetBIOS Node Type",
        47: "NetBIOS Scope", 48: "X Window Font Server",
        49: "X Window Display Manager", 50: "Requested IP Address",
        51: "IP Address Lease Time", 52: "Option Overload",
        53: "DHCP Message Type", 54: "DHCP Server Identifier",
        55: "Parameter Request List", 56: "Message",
        57: "Maximum DHCP Message Size", 58: "Renewal (T1) Time",
        59: "Rebinding (T2) Time", 60: "Vendor Class Identifier",
        61: "Client Identifier", 66: "TFTP Server Name",
        67: "Boot File Name", 68: "Mobile IP Home Agent",
        69: "SMTP Server", 70: "POP3 Server", 71: "NNTP Server",
        72: "WWW Server", 73: "Finger Server", 74: "IRC Server",
        75: "StreetTalk Server", 76: "ST Directory Server",
        77: "User Class", 78: "Directory Agent", 79: "Service Location",
        80: "Naming Authority", 81: "Client FQDN", 82: "Relay Agent Info",
        83: "iSNS", 84: "Server/TFTP", 85: "NDS Servers",
        86: "NDS Tree Name", 87: "NDS Context", 88: "BCMCS Controller",
        89: "BCMCS Domain", 90: "Authentication", 91: "Client Last Transaction",
        92: "Associated IP", 93: "Client System", 94: "Client NDI",
        95: "LDAP", 96: "IEEE 1003.1", 97: "UUID/GUID",
        98: "User Auth", 99: "GEOCONF_CIVIC",
        100: "PCode", 101: "TCode", 108: "IPv6 Only Preferred",
        114: "CAPWAP AC", 118: "Subnet Selection",
        119: "Domain Search", 120: "SIP Servers",
        121: "Classless Static Route", 125: "Vendor-Identifying Options",
        138: "CAPWAP AC", 150: "TFTP Server Address",
        209: "Configuration File", 210: "Path Prefix",
        211: "Reboot Time", 212: "6LoWPAN",
    }
    result = options.get(option_code, "Opción desconocida")
    return {"option": option_code, "description": result}


def dhcp_release_renew(interface="eth0"):
    """Libera y renueva la concesión DHCP (requiere dhclient)"""

    # Libera y renueva concesión DHCP. En Linux dhclient -r libera, dhclient -v renueva. En Windows ipconfig /renew.
    if sys.platform != "linux":
        return subprocess.getoutput("ipconfig /renew")
    try:
        release = subprocess.getoutput(f"dhclient -r {interface} 2>&1")
        renew = subprocess.getoutput(f"dhclient -v {interface} 2>&1 | tail -5")
        return {"release": release or "OK", "renew": renew or "OK"}
    except Exception as e:
        return {"error": str(e)}


def dhcp_conflict_check(ip_address):
    """Verifica si una IP ya está en uso en la red (posible conflicto DHCP)"""

    # Verifica conflicto de IP: hace ping a la IP y revisa la tabla ARP. Si responde, hay un dispositivo usando esa IP (posible conflicto).
    try:
        response = os.system(f"ping -c 2 -W 1 {ip_address} >/dev/null 2>&1")
        arp = subprocess.getoutput(f"arp -a {ip_address} 2>/dev/null")
        return {
            "ip": ip_address,
            "responding": response == 0,
            "arp_entry": arp if "no entry" not in arp.lower() else None,
        }
    except Exception as e:
        return {"error": str(e)}


def dhcp_analyze_leases(lease_file=None):
    """Analiza archivo de leases DHCP y extrae info estructurada"""

    # Analiza archivo de leases DHCP con regex. Extrae IP, fechas start/end, MAC, hostname y estado (active/free) de cada lease.
    if not lease_file:
        candidates = [
            "/var/lib/dhcp/dhclient.leases",
            "/var/lib/NetworkManager/dhclient-*.lease",
        ]
        for c in candidates:
            import glob
            matches = glob.glob(c) if "*" in c else ([c] if os.path.exists(c) else [])
            if matches:
                lease_file = matches[0]
                break
    if not lease_file or not os.path.exists(lease_file):
        return {"error": "No se encontró archivo de leases"}

    with open(lease_file) as f:
        content = f.read()

    import re
    leases = []
    for block in content.split("lease {"):
        if not block.strip():
            continue
        ip_match = re.search(r"(\d+\.\d+\.\d+\.\d+)", block)
        start_match = re.search(r"starts \d+ (\d+/\d+/\d+ \d+:\d+:\d+)", block)
        end_match = re.search(r"ends \d+ (\d+/\d+/\d+ \d+:\d+:\d+)", block)
        mac_match = re.search(r"hardware ethernet ([0-9a-fA-F:]+)", block)
        host_match = re.search(r'option host-name "([^"]+)"', block)

        lease = {}
        if ip_match:
            lease["ip"] = ip_match.group(1)
        if start_match:
            lease["start"] = start_match.group(1)
        if end_match:
            lease["end"] = end_match.group(1)
        if mac_match:
            lease["mac"] = mac_match.group(1)
        if host_match:
            lease["hostname"] = host_match.group(1)
        if lease:
            binding = re.search(r"binding state (\w+)", block)
            lease["state"] = binding.group(1) if binding else "unknown"
            leases.append(lease)

    return {
        "file": lease_file,
        "total_leases": len(leases),
        "active": sum(1 for l in leases if l.get("state") == "active"),
        "free": sum(1 for l in leases if l.get("state") == "free"),
        "leases": leases,
    }


def dhcp_suggest_reservations(known_devices):
    """Sugiere reservaciones DHCP basadas en dispositivos conocidos"""

    # Sugiere reservaciones DHCP. Recibe lista de MAC y nombres, asigna IPs sugeridas comenzando desde 192.168.1.100.
    if isinstance(known_devices, str):
        lines = known_devices.strip().split("\n")
        known_devices = []
        for line in lines:
            parts = line.strip().split(",")
            if len(parts) >= 2:
                known_devices.append({"mac": parts[0].strip(), "name": parts[1].strip()})

    suggestions = []
    for i, dev in enumerate(known_devices):
        mac = dev.get("mac", "")
        name = dev.get("name", f"dispositivo_{i}")
        if ":" in mac and len(mac.replace(":", "")) == 12:
            oui = mac[:8].upper()
            suggestions.append({
                "mac": mac,
                "name": name,
                "suggested_ip": f"192.168.1.{100 + i}",
                "oui": oui,
            })
    return {
        "count": len(suggestions),
        "reservations": suggestions,
        "note": "Ajustar la red según corresponda",
    }


def dhcp_relay_check(server_ip):
    """Verifica conectividad con un relay DHCP"""

    # Verifica conectividad con relay DHCP. Envía un paquete DHCP Discover al puerto 67 y espera respuesta. Timeout de 3s.
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.settimeout(3)
        sock.connect((server_ip, 67))
        sock.sendto(b"\x01\x01\x06\x00", (server_ip, 67))
        data, addr = sock.recvfrom(1024)
        sock.close()
        return {"server": server_ip, "relay_reachable": True, "response_from": str(addr)}
    except socket.timeout:
        return {"server": server_ip, "relay_reachable": False, "note": "Timeout - sin respuesta"}
    except Exception as e:
        return {"server": server_ip, "relay_reachable": False, "error": str(e)}


def dhcp_exclude_range(network, exclude_start, exclude_end):
    """Calcula rango DHCP excluyendo un segmento de IPs"""

    # Calcula rango DHCP excluyendo un segmento. Divide la red en antes y después del rango excluido. Muestra hosts disponibles en cada segmento.
    try:
        red = ipaddress.IPv4Network(network, strict=False)
        start = ipaddress.IPv4Address(exclude_start)
        end = ipaddress.IPv4Address(exclude_end)

        if start < red.network_address or end > red.broadcast_address:
            return {"error": "Rango de exclusión fuera de la red"}

        hosts_antes = [h for h in red.hosts() if h < start]
        hosts_despues = [h for h in red.hosts() if h > end]

        return {
            "network": network,
            "excluded_range": f"{exclude_start} - {exclude_end}",
            "range_before": {"start": str(hosts_antes[0]) if hosts_antes else None, "end": str(hosts_antes[-1]) if hosts_antes else None},
            "range_after": {"start": str(hosts_despues[0]) if hosts_despues else None, "end": str(hosts_despues[-1]) if hosts_despues else None},
            "available_before": len(hosts_antes),
            "available_after": len(hosts_despues),
        }
    except ValueError as e:
        return {"error": str(e)}


def dhcp_multiple_scopes(networks):
    """Calcula scopes DHCP para múltiples redes/vlans"""

    # Calcula scopes DHCP para múltiples redes. Toma lista de redes separadas por coma y devuelve gateway, scope sugerido y broadcast.
    if isinstance(networks, str):
        networks = [n.strip() for n in networks.split(",")]
    results = {}
    for net in networks:
        try:
            red = ipaddress.IPv4Network(net, strict=False)
            hosts = list(red.hosts())
            results[net] = {
                "netmask": str(red.netmask),
                "total": len(hosts),
                "suggested_scope": f"{hosts[10] if len(hosts) > 10 else hosts[0]} - {hosts[-10] if len(hosts) > 10 else hosts[-1]}",
                "gateway": str(hosts[0]),
                "broadcast": str(red.broadcast_address),
            }
        except Exception as e:
            results[net] = {"error": str(e)}
    return results


def dhcp_failover_check(primary, secondary):
    """Verifica estado de failover DHCP entre dos servidores"""

    # Verifica failover entre servidores DHCP. Prueba conectividad al puerto 67 de primario y secundario. Indica si failover es posible.
    results = {}
    for name, ip in [("primary", primary), ("secondary", secondary)]:
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.settimeout(3)
            sock.connect((ip, 67))
            results[name] = {"ip": ip, "reachable": True}
            sock.close()
        except Exception as e:
            results[name] = {"ip": ip, "reachable": False, "error": str(e)}
    results["failover_possible"] = results.get("primary", {}).get("reachable") and results.get("secondary", {}).get("reachable")
    return results


def dhcp_option82_decode(hex_string):
    """Decodifica información de Option 82 (Relay Agent Info)"""

    # Decodifica Option 82 de DHCP (Relay Agent Info). Parsea subopciones 1 (circuit ID) y 2 (remote ID) de un string hexadecimal.
    try:
        if hex_string.startswith("0x"):
            hex_string = hex_string[2:]
        data = bytes.fromhex(hex_string)
        result = {"raw": hex_string, "decoded": {}}
        i = 0
        while i < len(data):
            if i + 1 < len(data):
                subopt = data[i]
                length = data[i + 1]
                if i + 2 + length <= len(data):
                    value = data[i + 2:i + 2 + length]
                    if subopt == 1:
                        result["decoded"]["circuit_id"] = value.hex()
                        try:
                            result["decoded"]["circuit_id_ascii"] = value.decode(errors="ignore")
                        except:
                            pass
                    elif subopt == 2:
                        result["decoded"]["remote_id"] = value.hex()
                        try:
                            result["decoded"]["remote_id_ascii"] = value.decode(errors="ignore")
                        except:
                            pass
                    i += 2 + length
                    continue
            break
        return result
    except Exception as e:
        return {"error": str(e), "hex": hex_string}


def dhcp_classless_static_route(network, gateway, metric=1):
    """Formatea una ruta estática para Option 121 (Classless Static Route)"""

    # Codifica ruta estática clase-less para Option 121. Convierte red+gateway a formato binario: prefijo + IP de red + IP de gateway.
    try:
        red = ipaddress.IPv4Network(network, strict=False)
        gw = ipaddress.IPv4Address(gateway)
        prefix = red.prefixlen
        net_bytes = red.network_address.packed
        gw_bytes = gw.packed
        route_bytes = bytes([prefix]) + net_bytes + gw_bytes
        return {
            "network": network,
            "gateway": gateway,
            "metric": metric,
            "encoded_hex": route_bytes.hex(),
            "encoded_length": len(route_bytes),
        }
    except Exception as e:
        return {"error": str(e)}


def dhcp_vendor_class(vendor_id):
    """Devuelve información sobre vendor class identifiers conocidos"""

    # Identifica el vendor class ID de DHCP. Busca en diccionario de clases conocidas: Windows, Android, Linux, Cisco, Hikvision, etc.
    vendors = {
        "MSFT 5.0": "Windows 2000",
        "docsis": "Cable Modem (DOCSIS)",
        "android-dhcp": "Android",
        "android-dhcp-": "Android",
        "dhcpcd": "dhcpcd client (Linux/BSD)",
        "udhcp": "BusyBox / Embedded Linux",
        "Cisco": "Cisco IP Phone / Router",
        "CISCO": "Cisco IP Phone / Router",
        "huawei": "Huawei",
        "Hikvision": "Hikvision CCTV",
        "Dahua": "Dahua CCTV",
        "TP-LINK": "TP-Link",
        "Samsung": "Samsung",
        "iPhone": "Apple iOS",
        "iPad": "Apple iOS",
        "Linux": "Linux kernel DHCP",
    }
    for key, desc in vendors.items():
        if vendor_id.startswith(key):
            return {"vendor_id": vendor_id, "match": key, "description": desc}
    return {"vendor_id": vendor_id, "match": None, "description": "Vendor desconocido"}


def dhcp_statistics(server_ip="8.8.8.8"):
    """Estadísticas básicas de conectividad y DHCP"""

    # Estadísticas de conectividad. Prueba reachabilidad a DNS (puerto 53) y DHCP (puerto 67). Muestra IP local y DNS configurados.
    stats = {"server": server_ip, "checks": {}}

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.settimeout(2)
    try:
        sock.connect((server_ip, 53))
        stats["checks"]["dns_reachable"] = True
    except:
        stats["checks"]["dns_reachable"] = False
    sock.close()

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.settimeout(2)
    try:
        sock.connect((server_ip, 67))
        stats["checks"]["dhcp_server_reachable"] = True
    except:
        stats["checks"]["dhcp_server_reachable"] = False
    sock.close()

    stats["local_ip"] = subprocess.getoutput("hostname -I 2>/dev/null | awk '{print $1}'")
    stats["dns_configured"] = subprocess.getoutput("grep nameserver /etc/resolv.conf 2>/dev/null | awk '{print $2}'")
    return stats
