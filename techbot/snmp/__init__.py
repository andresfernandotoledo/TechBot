import socket
import struct
import re
import subprocess
import sys
import os


MIBS = {
    "sysDescr": "1.3.6.1.2.1.1.1.0",
    "sysObjectID": "1.3.6.1.2.1.1.2.0",
    "sysUpTime": "1.3.6.1.2.1.1.3.0",
    "sysContact": "1.3.6.1.2.1.1.4.0",
    "sysName": "1.3.6.1.2.1.1.5.0",
    "sysLocation": "1.3.6.1.2.1.1.6.0",
    "sysServices": "1.3.6.1.2.1.1.7.0",
    "ifNumber": "1.3.6.1.2.1.2.1.0",
    "ifDescr": "1.3.6.1.2.1.2.2.1.2",
    "ifType": "1.3.6.1.2.1.2.2.1.3",
    "ifMtu": "1.3.6.1.2.1.2.2.1.4",
    "ifSpeed": "1.3.6.1.2.1.2.2.1.5",
    "ifPhysAddress": "1.3.6.1.2.1.2.2.1.6",
    "ifAdminStatus": "1.3.6.1.2.1.2.2.1.7",
    "ifOperStatus": "1.3.6.1.2.1.2.2.1.8",
    "ifInOctets": "1.3.6.1.2.1.2.2.1.10",
    "ifOutOctets": "1.3.6.1.2.1.2.2.1.16",
    "ifInErrors": "1.3.6.1.2.1.2.2.1.14",
    "ifOutErrors": "1.3.6.1.2.1.2.2.1.20",
    "ipAdEntAddr": "1.3.6.1.2.1.4.20.1.1",
    "ipAdEntNetMask": "1.3.6.1.2.1.4.20.1.3",
    "ipRouteDest": "1.3.6.1.2.1.4.21.1.1",
    "ipRouteNextHop": "1.3.6.1.2.1.4.21.1.7",
    "ipRouteType": "1.3.6.1.2.1.4.21.1.8",
    "tcpConnState": "1.3.6.1.2.1.6.13.1.1",
    "tcpConnLocalPort": "1.3.6.1.2.1.6.13.1.3",
    "tcpConnRemAddress": "1.3.6.1.2.1.6.13.1.4",
    "tcpConnRemPort": "1.3.6.1.2.1.6.13.1.5",
    "udpLocalPort": "1.3.6.1.2.1.7.5.1.2",
    "snmpInPkts": "1.3.6.1.2.1.11.1.0",
    "snmpOutPkts": "1.3.6.1.2.1.11.2.0",
    "hrSystemUptime": "1.3.6.1.2.1.25.1.1.0",
    "hrSystemDate": "1.3.6.1.2.1.25.1.2.0",
    "hrMemorySize": "1.3.6.1.2.1.25.2.2.0",
    "hrStorageDescr": "1.3.6.1.2.1.25.2.3.1.3",
    "hrStorageSize": "1.3.6.1.2.1.25.2.3.1.5",
    "hrStorageUsed": "1.3.6.1.2.1.25.2.3.1.6",
    "hrProcessorLoad": "1.3.6.1.2.1.25.3.3.1.2",
    "dot1dBasePort": "1.3.6.1.2.1.17.1.4.1.1",
    "dot1dTpFdbAddress": "1.3.6.1.2.1.17.4.3.1.1",
    "dot1dTpFdbPort": "1.3.6.1.2.1.17.4.3.1.2",
    "entPhysicalDescr": "1.3.6.1.2.1.47.1.1.1.1.2",
    "entPhysicalVendorType": "1.3.6.1.2.1.47.1.1.1.1.3",
    "entPhysicalSerialNum": "1.3.6.1.2.1.47.1.1.1.1.11",
    "entPhysicalModelName": "1.3.6.1.2.1.47.1.1.1.1.13",
    "hrSWRunName": "1.3.6.1.2.1.25.4.2.1.2",
    "hrSWRunPath": "1.3.6.1.2.1.25.4.2.1.4",
    "hrSWRunPerfMem": "1.3.6.1.2.1.25.5.1.1.2",
    "bgpPeerState": "1.3.6.1.2.1.15.3.1.2",
    "bgpPeerRemoteAs": "1.3.6.1.2.1.15.3.1.9",
    "ospfNbrState": "1.3.6.1.2.1.14.10.1.6",
    "udpTable": "1.3.6.1.2.1.7.5.1",
    "tcpTable": "1.3.6.1.2.1.6.13.1",
    "sysORDescr": "1.3.6.1.2.1.1.9.1.3",
    "sysORUpTime": "1.3.6.1.2.1.1.9.1.4",
}

VENDOR_MIBS = {
    "cisco": "1.3.6.1.4.1.9",
    "mikrotik": "1.3.6.1.4.1.14988",
    "fortinet": "1.3.6.1.4.1.12356",
    "hp": "1.3.6.1.4.1.11",
    "dlink": "1.3.6.1.4.1.171",
    "foundry": "1.3.6.1.4.1.1991",
    "extremenetworks": "1.3.6.1.4.1.1916",
    "juniper": "1.3.6.1.4.1.2636",
    "3com": "1.3.6.1.4.1.43",
    "huawei": "1.3.6.1.4.1.2011",
    "zyxel": "1.3.6.1.4.1.890",
    "ubiquiti": "1.3.6.1.4.1.41112",
    "aruba": "1.3.6.1.4.1.14823",
    "paloalto": "1.3.6.1.4.1.25461",
    "checkpoint": "1.3.6.1.4.1.2620",
    "avaya": "1.3.6.1.4.1.6889",
    "brocade": "1.3.6.1.4.1.1588",
    "dell": "1.3.6.1.4.1.674",
    "f5": "1.3.6.1.4.1.3375",
    "vmware": "1.3.6.1.4.1.6876",
    # CCTV
    "hikvision": "1.3.6.1.4.1.42060",
    "dahua": "1.3.6.1.4.1.7012",
    "axis": "1.3.6.1.4.1.368",
    "bosch": "1.3.6.1.4.1.245",
    "vivotek": "1.3.6.1.4.1.122",
    "panasonic": "1.3.6.1.4.1.234",
    "samsung_hanwha": "1.3.6.1.4.1.283",
    "acti": "1.3.6.1.4.1.282",
    "mobotix": "1.3.6.1.4.1.242",
    "arecont": "1.3.6.1.4.1.14807",
    "geovision": "1.3.6.1.4.1.14143",
    # Access Control
    "zkteco": "1.3.6.1.4.1.38010",
    "hid_global": "1.3.6.1.4.1.2246",
    "assa_abloy": "1.3.6.1.4.1.41518",
    "lenel": "1.3.6.1.4.1.16024",
    "2n": "1.3.6.1.4.1.16684",
    "salto": "1.3.6.1.4.1.3606",
    # OTROS CCTV
    "pelco": "1.3.6.1.4.1.3150",
    "sony_cctv": "1.3.6.1.4.1.696",
    "jvc_cctv": "1.3.6.1.4.1.712",
    "tandberg": "1.3.6.1.4.1.226",
    "honeywell_video": "1.3.6.1.4.1.1369",
    "tiandy": "1.3.6.1.4.1.34577",
    "uniview": "1.3.6.1.4.1.35136",
    "cp_plus": "1.3.6.1.4.1.31103",
    "dali_cctv": "1.3.6.1.4.1.43584",
}


# Patrones de sysDescr para identificar dispositivos CCTV/AC
CCTV_AC_SNMP_PATTERNS = {
    "hikvision": ["hikvision", "ds-2", "i-series", "nvr", "dvr"],
    "dahua": ["dahua", "dhi-", "sd222", "sd492", "ipc-", "hfw", "hfw"],
    "axis": ["axis", "axis communications", "axis network camera", "axis video"],
    "bosch": ["bosch", "divar", "diagbox", "flexidome", "autodome"],
    "vivotek": ["vivotek", "network camera", "fd8", "ip8"],
    "panasonic": ["panasonic", "i-pro", "wv-", "network camera"],
    "samsung": ["samsung", "wiseview", "hanwha", "samsung techwin"],
    "acti": ["acti", "acti cam", "ac-"],
    "mobotix": ["mobotix", "mx-", "d24m"],
    "arecont": ["arecont", "arecont vision", "av"],
    "geovision": ["geovision", "gv-", "gv-bx"],
    "zkteco": ["zkteco", "zk", "uface", "iclock", "mb4", "ta", "inbio"],
    "hid": ["hid", "vertx", "hid reader", "hid global"],
    "lenel": ["lenel", "lencode", "onguard", "lenel ac"],
    "asssa_abloy": ["assa", "abloy", "aperio", "sherlock"],
    "2n": ["2n", "2n telecom", "2n helios", "2n access unit"],
    "salto": ["salto", "salto systems", "xs4"],
    "pelco": ["pelco", "dx-series", "sarix", "esprit"],
    "tiandy": ["tiandy", "tc-", "td-"],
    "uniview": ["uniview", "unv", "nvr3"],
    "honeywell_video": ["honeywell", "hrm", "hrdv", "maxpro"],
    "cp_plus": ["cp plus", "cp-plus", "cp_plus"],
}


def detect_device_type(host, community, version="2c"):
    """Detecta el tipo de dispositivo (CCTV, AC, network, etc.)."""
    sys_descr = snmp_get(host, community, "1.3.6.1.2.1.1.1.0", version)
    sys_obj = snmp_get(host, community, "1.3.6.1.2.1.1.2.0", version)
    descr = (sys_descr.get("value", "") + " " + sys_obj.get("value", "")).lower()

    for vendor, patterns in CCTV_AC_SNMP_PATTERNS.items():
        for p in patterns:
            if p in descr:
                return {"vendor": vendor, "type": "CCTV" if vendor in CCTV_AC_SNMP_PATTERNS and vendor not in ("zkteco","hid","lenel","2n","salto","assa_abloy") else "Access Control"}

    # Detectar por vendor OID
    vendor_oid = sys_obj.get("value", "")
    for vname, void in VENDOR_MIBS.items():
        if vendor_oid.startswith(void):
            return {"vendor": vname, "type": "Network"}

    return {"vendor": "desconocido", "type": "desconocido"}


def get_cctv_info(host, community, version="2c"):
    """Obtiene info específica de CCTV vía SNMP."""
    info = get_system_info(host, community, version)
    extras = {}

    # Intentar obtener canales de video (HP/Hikvision MIB)
    for oid_name in ["videoInputs", "videoOutputs", "motionDetect"]:
        for mib_name, mib_oid in {
            "videoInputs": "1.3.6.1.4.1.42060.1.1",
            "videoOutputs": "1.3.6.1.4.1.42060.1.2",
            "motionDetect": "1.3.6.1.4.1.42060.2.1",
        }.items():
            result = snmp_get(host, community, mib_oid + ".0", version)
            if "value" in result and result["value"].strip():
                extras[mib_name] = result["value"].strip()

    # Almacenamiento específico CCTV
    storage = get_storage(host, community, version)
    if isinstance(storage, list):
        extras["storage"] = storage

    info["cctv_extras"] = extras
    return info

IF_TYPES = {
    1: "other", 2: "regular1822", 3: "hdh1822", 4: "ddnX25",
    5: "rfc877x25", 6: "ethernetCsmacd", 7: "iso88023Csmacd",
    8: "iso88024TokenBus", 9: "iso88025TokenRing", 10: "iso88026Man",
    11: "starLan", 12: "proteon10Mbit", 13: "proteon80Mbit",
    14: "hyperchannel", 15: "fddi", 16: "lapb", 17: "sdlc",
    18: "ds1", 19: "e1", 20: "basicISDN", 21: "primaryISDN",
    22: "propPointToPointSerial", 23: "ppp", 24: "softwareLoopback",
    25: "eon", 26: "ethernet3Mbit", 27: "nsip", 28: "slip",
    29: "ultra", 30: "ds3", 31: "sip", 32: "frameRelay",
    33: "rs232", 34: "para", 35: "arcnet", 36: "arcnetPlus",
    37: "atm", 38: "miox25", 39: "sonet", 40: "x25ple",
    41: "iso88022llc", 42: "localTalk", 43: "smdsDxi",
    44: "frameRelayService", 45: "v35", 46: "hssi", 47: "g703at2mb",
    48: "g703at64k", 49: "propLogical", 50: "other",
    53: "propBWAp2mp", 54: "propBWAp2p", 55: "propVirtual",
    56: "tunnel", 57: "l2vlan", 61: "ieee80211", 62: "ieee80211b",
    71: "ieee80211a", 72: "ieee80211g", 117: "gigabitEthernet",
    131: "tunnel", 135: "l2vlan", 136: "bridge",
    161: "ieee80211n", 162: "ieee80211ac",
}

IF_STATUS = {1: "up", 2: "down", 3: "testing"}


def _run_snmpcmd(args):
    """Ejecuta un comando snmp del sistema."""
    try:
        result = subprocess.run(args, capture_output=True, timeout=15, text=True)
        return result.stdout
    except FileNotFoundError:
        return None
    except subprocess.TimeoutExpired:
        return None


def snmp_get(host, community, oid, version="2c", timeout=5):
    """SNMP GET - obtiene el valor de un OID."""
    out = _run_snmpcmd([
        "snmpget", "-v", version, "-c", community,
        "-t", str(timeout), "-O", "qv", host, oid
    ])
    if out is None:
        return {"error": "snmpget no instalado. Instalá snmp-mibs-downloader"}
    return {"host": host, "oid": oid, "value": out.strip()}


def snmp_get_next(host, community, oid, version="2c", timeout=5):
    """SNMP GETNEXT."""
    out = _run_snmpcmd([
        "snmpgetnext", "-v", version, "-c", community,
        "-t", str(timeout), "-O", "qv", host, oid
    ])
    if out is None:
        return {"error": "snmpget no instalado"}
    return {"host": host, "oid": oid, "value": out.strip()}


def snmp_walk(host, community, oid, version="2c", timeout=10):
    """SNMP WALK - camina un árbol OID."""
    out = _run_snmpcmd([
        "snmpwalk", "-v", version, "-c", community,
        "-t", str(timeout), "-O", "q", host, oid
    ])
    if out is None:
        return {"error": "snmpwalk no instalado. Instalá snmp-mibs-downloader"}
    results = {}
    for line in out.strip().split("\n"):
        parts = line.split(" = ", 1)
        if len(parts) == 2:
            key = parts[0].strip()
            val = parts[1].strip()
            # Resulta en 'key = val'
            if " = " in key:
                parts2 = key.split(" = ", 1)
                key = parts2[0].strip()
                val = parts2[1].strip()
            results[key] = val
    return results


def snmp_set(host, community, oid, value, value_type="s", version="2c", timeout=5):
    """SNMP SET - escribe un valor en un OID."""
    out = _run_snmpcmd([
        "snmpset", "-v", version, "-c", community,
        "-t", str(timeout), host, oid, value_type, str(value)
    ])
    if out is None:
        return {"error": "snmpset no instalado"}
    return {"host": host, "oid": oid, "value": value, "response": out.strip()}


def snmp_table(host, community, oid, version="2c", timeout=10):
    """SNMP TABLE - formatea una tabla SNMP."""
    out = _run_snmpcmd([
        "snmp-table", "-v", version, "-c", community,
        "-t", str(timeout), host, oid
    ])
    if out is None:
        return {"error": "snmp-table no disponible"}
    return {"table": out.strip()}


def get_system_info(host, community, version="2c"):
    """Obtiene información básica del sistema vía SNMP."""
    info = {}
    for name, oid in MIBS.items():
        if name in ("sysDescr", "sysName", "sysLocation", "sysContact",
                     "sysUpTime", "sysObjectID", "sysServices"):
            v = snmp_get(host, community, oid, version)
            if "value" in v:
                info[name] = v["value"]
    return info


def get_interfaces(host, community, version="2c"):
    """Obtiene todas las interfaces del dispositivo."""
    descrs = snmp_walk(host, community, MIBS["ifDescr"], version)
    speeds = snmp_walk(host, community, MIBS["ifSpeed"], version)
    status = snmp_walk(host, community, MIBS["ifOperStatus"], version)
    macs = snmp_walk(host, community, MIBS["ifPhysAddress"], version)

    interfaces = []
    for oid, descr in descrs.items():
        idx = oid.split(".")[-1]
        spd = speeds.get(f"{MIBS['ifSpeed']}.{idx}", "?")
        st = status.get(f"{MIBS['ifOperStatus']}.{idx}", "?")
        mac = macs.get(f"{MIBS['ifPhysAddress']}.{idx}", "?")
        st_name = IF_STATUS.get(int(st), st) if st.isdigit() else st
        interfaces.append({
            "index": idx,
            "description": descr,
            "speed": spd,
            "status": st_name,
            "mac": mac,
        })
    return interfaces


def get_mac_table(host, community, version="2c"):
    """Obtiene tabla de direcciones MAC (puentes/bridges)."""
    addrs = snmp_walk(host, community, MIBS["dot1dTpFdbAddress"], version)
    ports = snmp_walk(host, community, MIBS["dot1dTpFdbPort"], version)
    table = {}
    for oid, mac in addrs.items():
        idx = oid.split(".")[-1]
        port = ports.get(f"{MIBS['dot1dTpFdbPort']}.{idx}", "?")
        table[mac] = port
    return table


def get_routing_table(host, community, version="2c"):
    """Obtiene tabla de enrutamiento."""
    dests = snmp_walk(host, community, MIBS["ipRouteDest"], version)
    nexthops = snmp_walk(host, community, MIBS["ipRouteNextHop"], version)
    routes = []
    for oid, dest in dests.items():
        idx = oid.split(".")[-1]
        nh = nexthops.get(f"{MIBS['ipRouteNextHop']}.{idx}", "?")
        routes.append({"destination": dest, "next_hop": nh})
    return routes


def get_storage(host, community, version="2c"):
    """Obtiene información de almacenamiento."""
    descrs = snmp_walk(host, community, MIBS["hrStorageDescr"], version)
    sizes = snmp_walk(host, community, MIBS["hrStorageSize"], version)
    used = snmp_walk(host, community, MIBS["hrStorageUsed"], version)
    storages = []
    for oid, descr in descrs.items():
        idx = oid.split(".")[-1]
        sz = sizes.get(f"{MIBS['hrStorageSize']}.{idx}", "?")
        us = used.get(f"{MIBS['hrStorageUsed']}.{idx}", "?")
        storages.append({
            "description": descr,
            "size": sz,
            "used": us,
            "percent": round((int(us) / int(sz)) * 100, 1) if sz.isdigit() and us.isdigit() and int(sz) > 0 else "?"
        })
    return storages


def get_arp_table(host, community, version="2c"):
    """Obtiene tabla ARP."""
    out = _run_snmpcmd([
        "snmpwalk", "-v", version, "-c", community,
        "-t", "10", "-O", "q", host, "1.3.6.1.2.1.4.22.1.2"
    ])
    if out is None:
        return {"error": "snmpwalk no instalado"}
    entries = {}
    for line in out.strip().split("\n"):
        if " = " in line:
            parts = line.split(" = ", 1)
            key = parts[0].strip()
            val = parts[1].strip()
            entries[key] = val
    return entries


def get_process_list(host, community, version="2c"):
    """Obtiene lista de procesos en ejecución."""
    names = snmp_walk(host, community, MIBS["hrSWRunName"], version)
    mems = snmp_walk(host, community, MIBS["hrSWRunPerfMem"], version)
    processes = []
    for oid, name in names.items():
        idx = oid.split(".")[-1]
        mem = mems.get(f"{MIBS['hrSWRunPerfMem']}.{idx}", "?")
        processes.append({"name": name, "memory_kb": mem})
    return processes


def snmp_bulkwalk(host, community, oid, version="2c", timeout=15):
    """SNMP BULKWALK más rápido para grandes árboles."""
    out = _run_snmpcmd([
        "snmpbulkwalk", "-v", version, "-c", community,
        "-t", str(timeout), "-Cr", "50", "-O", "q", host, oid
    ])
    if out is None:
        return {"error": "snmpbulkwalk no disponible"}
    results = {}
    for line in out.strip().split("\n"):
        if " = " in line:
            key, val = line.split(" = ", 1)
            results[key.strip()] = val.strip()
    return results


def detect_vendor(host, community, version="2c"):
    """Detecta el fabricante del dispositivo por sysObjectID."""
    obj = snmp_get(host, community, MIBS["sysObjectID"], version)
    if "value" in obj:
        oid = obj["value"]
        for vendor, vendor_oid in VENDOR_MIBS.items():
            if oid.startswith(vendor_oid):
                return vendor
        return "desconocido"
    return "error"


def snmp_trap_listener(port=162, count=5, timeout=30):
    """Escucha traps SNMP (requiere permisos)."""
    import select
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.bind(("0.0.0.0", port))
        sock.settimeout(timeout)
        traps = []
        for _ in range(count):
            try:
                data, addr = sock.recvfrom(65535)
                traps.append({"from": addr[0], "port": addr[1], "size": len(data)})
            except socket.timeout:
                break
        sock.close()
        return traps
    except PermissionError:
        return {"error": "Permiso denegado para puerto %d" % port}
    except Exception as e:
        return {"error": str(e)}


def snmp_check(host, community, version="2c"):
    """Verifica si SNMP está accesible en un host."""
    result = snmp_get(host, community, "1.3.6.1.2.1.1.1.0", version)
    return "value" in result and result["value"].strip() != ""


def oid_lookup(oid_or_name):
    """Busca un OID por nombre o viceversa."""
    if oid_or_name.startswith("."):
        oid_or_name = oid_or_name[1:]
    for name, oid in MIBS.items():
        if oid_or_name.lower() == name.lower():
            return {"name": name, "oid": oid}
        if oid_or_name == oid:
            return {"name": name, "oid": oid}
    return {"name": "desconocido", "oid": oid_or_name}
