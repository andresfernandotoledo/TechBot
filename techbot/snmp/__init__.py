# techbot/snmp/__init__.py
# Pure-Python SNMP v1/v2c implementation with subprocess fallback

import socket
import time
import threading

from .ber import *

_SNMP_PORT = 161
_DEFAULT_TIMEOUT = 3


class SNMPError(Exception):
    pass


# ─── Backward-compatible public API ─────────────────────────
# Callers use: snmp_get(host, community, oid)
#              snmp_walk(host, community, oid)

def snmp_get(host, community, oid, version=2, port=161, timeout=_DEFAULT_TIMEOUT):
    result = _pure_get(host, oid, community, version, port, timeout)
    return _format_value(result) if result is not None else None


def snmp_walk(host, community, oid, version=2, port=161, timeout=_DEFAULT_TIMEOUT):
    results = _pure_walk(host, oid, community, version, port, timeout)
    # Return dict of {oid_str: formatted_value}
    d = {}
    for o, v in results:
        d[o] = _format_value(v)
    return d


def snmp_check(host, community="public", timeout=2):
    try:
        val = snmp_get(host, community, "1.3.6.1.2.1.1.1.0", timeout=timeout)
        return val is not None
    except:
        return False


def _extract_field_index(oid_str, base_oid):
    """Extrae (campo, índice) de un OID tipo .1.3.6.1.2.1.2.2.1.<campo>.<índice>."""
    suffix = oid_str.replace(base_oid.rstrip("."), "").strip(".")
    parts = suffix.split(".") if suffix else []
    if len(parts) >= 2:
        try:
            return int(parts[0]), int(parts[-1])
        except ValueError:
            pass
    elif len(parts) == 1 and parts[0].isdigit():
        return int(parts[0]), 0
    return None, None


def get_interfaces(host, community="public", timeout=3):
    oid_iface = "1.3.6.1.2.1.2.2.1"
    walk_raw = _pure_walk(host, oid_iface, community, port=161, timeout=timeout)
    ifaces = {}
    for oid_str, raw_val in walk_raw:
        field, idx = _extract_field_index(oid_str, oid_iface)
        if field is None:
            continue
        if idx not in ifaces:
            ifaces[idx] = {"index": idx, "description": "", "type": "", "mtu": 0, "speed": 0, "mac": "", "admin": "down", "oper": "down", "in_octets": 0, "out_octets": 0}

        v = _format_value(raw_val)
        if field == 1:
            ifaces[idx]["description"] = str(v) if v else ""
        elif field == 2:
            ifaces[idx]["type"] = int(v) if isinstance(v, (int, float)) else 0
        elif field == 3:
            ifaces[idx]["mtu"] = int(v) if isinstance(v, (int, float)) else 0
        elif field == 4:
            ifaces[idx]["speed"] = int(v) if isinstance(v, (int, float)) else 0
        elif field == 5:
            ifaces[idx]["mac"] = str(v) if v else ""
        elif field == 6:
            ifaces[idx]["admin"] = "up" if v == 1 else "down"
        elif field == 7:
            ifaces[idx]["oper"] = "up" if v == 1 else "down"
        elif field == 10:
            ifaces[idx]["in_octets"] = int(v) if isinstance(v, (int, float)) else 0
        elif field == 16:
            ifaces[idx]["out_octets"] = int(v) if isinstance(v, (int, float)) else 0

    result = []
    for idx in sorted(ifaces.keys()):
        iface = ifaces[idx]
        iface["status"] = "UP" if iface.get("oper") == "up" and iface.get("admin") == "up" else "DOWN"
        result.append(iface)
    return result


def get_system_info(host, community="public", timeout=3):
    oids = {
        "sysDescr": "1.3.6.1.2.1.1.1.0",
        "sysObjectID": "1.3.6.1.2.1.1.2.0",
        "sysName": "1.3.6.1.2.1.1.5.0",
        "sysLocation": "1.3.6.1.2.1.1.6.0",
        "sysContact": "1.3.6.1.2.1.1.4.0",
        "sysUpTime": "1.3.6.1.2.1.1.3.0",
        "sysServices": "1.3.6.1.2.1.1.7.0",
    }
    info = {}
    for name, oid in oids.items():
        try:
            val = _pure_get(host, oid, community, port=161, timeout=timeout)
            if val is not None:
                _, raw = val
                fv = _format_value(raw)
                if name == "sysUpTime" and isinstance(fv, (int, float)):
                    # Timeticks (hundredths of seconds)
                    total_secs = fv / 100
                    days, rem = divmod(total_secs, 86400)
                    hours, rem = divmod(rem, 3600)
                    mins, secs = divmod(rem, 60)
                    info[name] = f"{int(days)}d {int(hours):02d}:{int(mins):02d}:{int(secs):02d}"
                else:
                    info[name] = str(fv) if fv is not None else ""
        except:
            info[name] = ""
    return info


def detect_vendor(host, community="public", timeout=3):
    try:
        sysdescr = _pure_get(host, "1.3.6.1.2.1.1.1.0", community, timeout=timeout)
        if sysdescr:
            _, raw = sysdescr
            descr = str(_format_value(raw)).lower()
            if "cisco" in descr: return "Cisco"
            if "mikrotik" in descr: return "MikroTik"
            if "fortinet" in descr or "fortigate" in descr: return "Fortinet"
            if "junos" in descr or "juniper" in descr: return "Juniper"
            if "huawei" in descr: return "Huawei"
            if "hp " in descr or "procurve" in descr or "aruba" in descr: return "HP/Aruba"
            if "dell" in descr: return "Dell"
            if "linux" in descr or "ubuntu" in descr or "debian" in descr: return "Linux"
            if "unix" in descr: return "Unix"
            if "windows" in descr: return "Windows"
            if "ubiquiti" in descr or "unifi" in descr or "airmax" in descr: return "Ubiquiti"
            if "dlink" in descr or "d-link" in descr: return "D-Link"
            if "tplink" in descr or "tp-link" in descr: return "TP-Link"
            if "hikvision" in descr: return "Hikvision"
            if "dahua" in descr: return "Dahua"
            if "grandstream" in descr: return "Grandstream"
            return "Unknown"
    except:
        pass
    return "Unknown"


def detect_device_type(host, community="public", timeout=3):
    info = get_system_info(host, community, timeout)
    descr = info.get("sysDescr", "").lower()
    services = info.get("sysServices", "")

    if "router" in descr: return {"type": "Router", "vendor": detect_vendor(host, community)}
    if "switch" in descr: return {"type": "Switch", "vendor": detect_vendor(host, community)}
    if "access point" in descr or "ap-" in descr: return {"type": "Access Point", "vendor": detect_vendor(host, community)}
    if "firewall" in descr: return {"type": "Firewall", "vendor": detect_vendor(host, community)}
    if "camera" in descr or "ipc" in descr: return {"type": "Camera", "vendor": detect_vendor(host, community)}
    if "printer" in descr: return {"type": "Printer", "vendor": detect_vendor(host, community)}
    if "server" in descr: return {"type": "Server", "vendor": detect_vendor(host, community)}
    if "phone" in descr and "voip" in descr: return {"type": "VoIP Phone", "vendor": detect_vendor(host, community)}
    # services: bitmask
    try:
        svc = int(str(services))
        if svc & 4: return {"type": "Router/Switch", "vendor": detect_vendor(host, community)}
    except:
        pass
    return {"type": "Unknown", "vendor": detect_vendor(host, community)}


# ─── Pure-Python SNMP core (private) ────────────────────────

def _pure_get(host, oid, community, version=1, port=161, timeout=_DEFAULT_TIMEOUT):
    """Returns (oid_str, raw_value_bytes) or None."""
    try:
        req = _build_get_request(oid, community, version, request_id=_request_id())
        resp = _udp_send_recv(host, port, req, timeout)
        return _parse_response(resp)
    except:
        return None


def _pure_getnext(host, oid, community, version=1, port=161, timeout=_DEFAULT_TIMEOUT):
    """Returns (next_oid_str, raw_value_bytes) or None."""
    try:
        req = _build_getnext_request(oid, community, version, request_id=_request_id())
        resp = _udp_send_recv(host, port, req, timeout)
        return _parse_response(resp)
    except:
        return None


def _pure_walk(host, base_oid, community, version=1, port=161, timeout=_DEFAULT_TIMEOUT):
    """Returns [(oid_str, raw_value_bytes), ...]."""
    results = []
    oid = base_oid.rstrip(".")
    base = base_oid.rstrip(".")
    max_iters = 500
    for _ in range(max_iters):
        try:
            oid_val = _pure_getnext(host, oid, community, version, port, timeout)
        except:
            break
        if oid_val is None:
            break
        next_oid, value = oid_val
        if not next_oid.startswith(base):
            break
        if len(results) > 0 and next_oid == results[-1][0]:
            break
        results.append((next_oid, value))
        oid = next_oid
        time.sleep(0.05)
    return results


# ─── Low-level helpers ──────────────────────────────────────

_request_counter = 0
_rid_lock = threading.Lock()


def _request_id():
    global _request_counter
    with _rid_lock:
        _request_counter = (_request_counter + 1) & 0x7FFFFFFF
        return _request_counter


def _udp_send_recv(host, port, data, timeout):
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.settimeout(timeout)
    try:
        sock.sendto(data, (host, port))
        resp, _ = sock.recvfrom(65535)
        return resp
    except socket.timeout:
        raise SNMPError(f"Timeout contacting {host}:{port}")
    except OSError as e:
        raise SNMPError(f"Network error: {e}")
    finally:
        sock.close()


# ─── Build SNMP messages ────────────────────────────────────

def _build_get_request(oid, community, version, request_id):
    pdu = _build_pdu(
        ASN1_CONTEXT | 0x00,
        request_id, 0, 0,
        encode_sequence(encode_varbind(oid, encode_null()))
    )
    ver = encode_int(version)
    comm = encode_octet_string(community.encode())
    return encode_sequence(ver + comm + pdu)


def _build_getnext_request(oid, community, version, request_id):
    pdu = _build_pdu(
        ASN1_CONTEXT | 0x01,
        request_id, 0, 0,
        encode_sequence(encode_varbind(oid, encode_null()))
    )
    ver = encode_int(version)
    comm = encode_octet_string(community.encode())
    return encode_sequence(ver + comm + pdu)


def _build_pdu(pdu_type, request_id, error_status, error_index, body):
    return encode_constructed(
        pdu_type,
        encode_int(request_id) +
        encode_int(error_status) +
        encode_int(error_index) +
        body
    )


# ─── Parse SNMP responses ───────────────────────────────────

def _parse_response(data):
    """Parse SNMP response bytes → (oid_str, (value_tag, value_bytes))."""
    try:
        # Outer SEQUENCE { version INTEGER, community OCTET STRING, ... PDU }
        (outer_tag, msg_bytes), _ = decode_tlv(data)
        if outer_tag != ASN1_SEQUENCE:
            raise SNMPError(f"Expected SEQUENCE, got tag 0x{outer_tag:02x}")
        ver, rest = decode_int(msg_bytes)
        comm, rest = skip_octet_string(rest)
        # rest = PDU (context-specific tag)
        (pdu_tag, pdu_bytes), _ = decode_tlv(rest)
        rid, rest2 = decode_int(pdu_bytes)
        err, rest3 = decode_int(rest2)
        if err != 0:
            raise SNMPError(f"SNMP error status: {err}")
        ei, rest4 = decode_int(rest3)
        # rest4 = SEQUENCE of varbinds
        vb_seq, vb_rest = unwrap_sequence(rest4)
        vb_inner, _ = unwrap_sequence(vb_seq)
        oid_str, rest7 = decode_oid(vb_inner)
        value_tlv, _ = decode_tlv(rest7)
        return (oid_str, value_tlv)
    except SNMPError:
        raise
    except Exception as e:
        raise SNMPError(f"Parse error: {e}")


# ─── Value formatting ───────────────────────────────────────

def _format_value(tlv_data):
    """Given (tag, value) tuple from decode_tlv, return formatted Python value."""
    if tlv_data is None:
        return None
    tag, raw = tlv_data
    if tag == ASN1_INTEGER:
        return int.from_bytes(raw, 'big', signed=True)
    elif tag == ASN1_OCTET_STRING:
        try:
            return raw.decode('utf-8', errors='replace')
        except:
            return raw.hex()
    elif tag == ASN1_OBJECT_ID:
        try:
            oid, _ = decode_oid(encode_tlv(tag, raw))
            return oid
        except:
            return raw.hex()
    elif tag == ASN1_NULL:
        return None
    elif tag == ASN1_BOOLEAN:
        return len(raw) > 0 and raw[0] != 0
    elif tag & 0xC0 == 0x40:  # APPLICATION class (Counter, Gauge, TimeTicks, etc.)
        try:
            return int.from_bytes(raw, 'big')
        except:
            return raw.hex()
    else:
        try:
            return int.from_bytes(raw, 'big')
        except:
            return raw.hex()


# ─── Additional API functions (webapp compat) ───────────────

MIBS = {
    "sysDescr": "1.3.6.1.2.1.1.1.0",
    "sysObjectID": "1.3.6.1.2.1.1.2.0",
    "sysUpTime": "1.3.6.1.2.1.1.3.0",
    "sysName": "1.3.6.1.2.1.1.5.0",
    "ifDescr": "1.3.6.1.2.1.2.2.1.2",
    "ifType": "1.3.6.1.2.1.2.2.1.3",
    "ifMtu": "1.3.6.1.2.1.2.2.1.4",
    "ifSpeed": "1.3.6.1.2.1.2.2.1.5",
    "ifPhysAddress": "1.3.6.1.2.1.2.2.1.6",
    "ifAdminStatus": "1.3.6.1.2.1.2.2.1.7",
    "ifOperStatus": "1.3.6.1.2.1.2.2.1.8",
    "ifInOctets": "1.3.6.1.2.1.2.2.1.10",
    "ifOutOctets": "1.3.6.1.2.1.2.2.1.16",
    "ipNetToMediaPhysAddress": "1.3.6.1.2.1.4.22.1.2",
    "ipNetToMediaNetAddress": "1.3.6.1.2.1.4.22.1.3",
    "dot1dTpFdbAddress": "1.3.6.1.2.1.17.4.3.1.1",
    "dot1dTpFdbPort": "1.3.6.1.2.1.17.4.3.1.2",
    "hrStorageDescr": "1.3.6.1.2.1.25.2.3.1.3",
    "hrStorageSize": "1.3.6.1.2.1.25.2.3.1.5",
    "hrStorageUsed": "1.3.6.1.2.1.25.2.3.1.6",
}

def get_mac_table(host, community="public", timeout=5):
    """Obtiene tabla MAC (bridge MIB)."""
    oid_mac = "1.3.6.1.2.1.17.4.3.1.1"
    oid_port = "1.3.6.1.2.1.17.4.3.1.2"
    macs = _pure_walk(host, oid_mac, community, timeout=timeout)
    ports = _pure_walk(host, oid_port, community, timeout=timeout)
    if not macs:
        return []
    # Build MAC -> port mapping
    mac_port = {}
    for o, v in ports:
        parts = o.split(".")
        idx = parts[-1] if parts else ""
        mac_port[idx] = _format_value(v)
    result = []
    for o, v in macs:
        fv = _format_value(v)
        idx = o.split(".")[-1]
        port = mac_port.get(idx, "?")
        result.append({"mac": str(fv) if fv else "", "port": int(port) if isinstance(port, (int, float)) else str(port), "vlan": 1})
    return result


def get_routing_table(host, community="public", timeout=5):
    """Obtiene tabla de enrutamiento (IP Route Table)."""
    oid_dest = "1.3.6.1.2.1.4.21.1.1"
    oid_nexthop = "1.3.6.1.2.1.4.21.1.7"
    oid_iface = "1.3.6.1.2.1.4.21.1.2"
    oid_metric = "1.3.6.1.2.1.4.21.1.4"
    dests = _pure_walk(host, oid_dest, community, timeout=timeout)
    if not dests:
        return []
    nexthops = {o: _format_value(v) for o, v in _pure_walk(host, oid_nexthop, community, timeout=timeout)}
    ifaces = {o: _format_value(v) for o, v in _pure_walk(host, oid_iface, community, timeout=timeout)}
    metrics = {o: _format_value(v) for o, v in _pure_walk(host, oid_metric, community, timeout=timeout)}
    result = []
    for o, v in dests:
        dest = _format_value(v)
        nh = nexthops.get(o, "0.0.0.0")
        ifc = ifaces.get(o, 0)
        met = metrics.get(o, 0)
        result.append({"destination": str(dest), "nexthop": str(nh), "ifIndex": int(ifc) if isinstance(ifc, (int, float)) else 0, "metric": int(met) if isinstance(met, (int, float)) else 0})
    return result


def get_storage(host, community="public", timeout=5):
    """Obtiene información de almacenamiento (Host Resources MIB)."""
    oid_descr = "1.3.6.1.2.1.25.2.3.1.3"
    oid_size = "1.3.6.1.2.1.25.2.3.1.5"
    oid_used = "1.3.6.1.2.1.25.2.3.1.6"
    descrs = _pure_walk(host, oid_descr, community, timeout=timeout)
    if not descrs:
        return []
    sizes = {o: _format_value(v) for o, v in _pure_walk(host, oid_size, community, timeout=timeout)}
    useds = {o: _format_value(v) for o, v in _pure_walk(host, oid_used, community, timeout=timeout)}
    result = []
    for o, v in descrs:
        descr = _format_value(v)
        sz = sizes.get(o, 0)
        us = useds.get(o, 0)
        if sz and int(sz) > 0:
            pct = round(int(us) / int(sz) * 100, 1) if int(sz) > 0 else 0
        else:
            pct = 0
        result.append({"description": str(descr), "size": int(sz) if isinstance(sz, (int, float)) else 0, "used": int(us) if isinstance(us, (int, float)) else 0, "percent": pct})
    return result


def get_arp_table(host, community="public", timeout=5):
    """Obtiene tabla ARP (ipNetToMedia)."""
    oid_mac = "1.3.6.1.2.1.4.22.1.2"
    oid_ip = "1.3.6.1.2.1.4.22.1.3"
    macs = _pure_walk(host, oid_mac, community, timeout=timeout)
    ips = {o: _format_value(v) for o, v in _pure_walk(host, oid_ip, community, timeout=timeout)}
    result = []
    for o, v in macs:
        mac = _format_value(v)
        ip = ips.get(o, "?")
        result.append({"ip": str(ip), "mac": str(mac) if mac else ""})
    return result


def get_cctv_info(host, community="public", timeout=5):
    """Intenta obtener info de cámaras CCTV vía SNMP."""
    sysdescr = _pure_get(host, "1.3.6.1.2.1.1.1.0", community, timeout=timeout)
    if not sysdescr:
        return {}
    _, raw = sysdescr
    descr = str(_format_value(raw)).lower()
    if "hikvision" in descr:
        return {"vendor": "Hikvision", "type": "Camera", "channels": "N/A"}
    if "dahua" in descr:
        return {"vendor": "Dahua", "type": "Camera", "channels": "N/A"}
    return {"vendor": detect_vendor(host, community), "type": "Unknown"}
