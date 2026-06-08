import socket
from techbot.snmp import snmp_walk


def discover_topology(seed_ip, community="public", depth=2, max_devices=20):
    """Descubre topología de red vía SNMP ARP + sysName."""
    visited = set()
    devices = []
    edges = []
    queue = [(seed_ip, 0)]

    OID_ARP_TABLE = "1.3.6.1.2.1.4.22.1.2"
    OID_SYSNAME = "1.3.6.1.2.1.1.5.0"
    OID_IFDESCR = "1.3.6.1.2.1.2.2.1.2"
    OID_LLDP_REMOTE = "1.0.8802.1.1.2.1.4.1.1.4"

    while queue and len(devices) < max_devices:
        ip, current_depth = queue.pop(0)
        if ip in visited or current_depth > depth:
            continue
        visited.add(ip)

        try:
            hostname = socket.gethostbyaddr(ip)[0]
        except:
            hostname = ip

        device = {"id": ip, "label": hostname, "ip": ip, "type": "unknown", "interfaces": []}
        devices.append(device)

        # Get sysName via SNMP
        try:
            sysname = snmp_walk(ip, community, OID_SYSNAME)
            if sysname and sysname[0].get("value"):
                device["label"] = sysname[0]["value"]
                device["vendor"] = _detect_vendor_by_sysname(sysname[0]["value"])
        except:
            pass

        # Get interfaces
        try:
            ifaces = snmp_walk(ip, community, OID_IFDESCR)
            device["interfaces"] = [i.get("value", f"eth{n}") for n, i in enumerate(ifaces[:10])]
        except:
            pass

        # Get ARP table
        try:
            arp = snmp_walk(ip, community, OID_ARP_TABLE)
            arp_ips = set()
            for entry in arp:
                val = entry.get("value", "")
                if val and val != ip and "." in val:
                    arp_ips.add(val)
            for neighbor_ip in arp_ips:
                if neighbor_ip not in visited:
                    queue.append((neighbor_ip, current_depth + 1))
                edges.append({
                    "source": ip,
                    "target": neighbor_ip,
                    "label": "ARP",
                    "type": "ethernet",
                })
        except:
            pass

        # Get LLDP neighbors
        try:
            lldp = snmp_walk(ip, community, OID_LLDP_REMOTE)
            for entry in lldp:
                val = entry.get("value", "")
                if val and "." in val and val not in visited:
                    queue.append((val, current_depth + 1))
                    edges.append({
                        "source": ip,
                        "target": val,
                        "label": "LLDP",
                        "type": "fiber",
                    })
        except:
            pass

    return {"devices": devices, "edges": edges, "count": len(devices)}


def _detect_vendor_by_sysname(sysname):
    name = sysname.lower()
    if "cisco" in name: return "Cisco"
    if "mikrotik" in name: return "MikroTik"
    if "fortinet" in name or "fortigate" in name: return "Fortinet"
    if "ubuntu" in name or "debian" in name or "centos" in name: return "Linux"
    if "windows" in name: return "Windows"
    if "hikvision" in name: return "Hikvision"
    if "dahua" in name: return "Dahua"
    return "Unknown"
