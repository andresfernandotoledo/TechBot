import ipaddress
import json
import os
import re
import fcntl
import time
from datetime import datetime


IPAM_DB_FILE = os.path.join(os.path.dirname(__file__), "ipam_db.json")


EMPTY_DB = {
    "networks": [],
    "reservations": [],
    "dhcp_scopes": [],
    "dns_records": [],
    "vlans": [],
    "sites": [],
    "metadata": {
        "created": datetime.now().isoformat(),
        "version": "1.0",
    }
}


def _validar_str(val, campo, max_len=255, requerido=False):
    if not isinstance(val, str):
        return {"error": f"{campo} debe ser texto"}
    val = val.strip()
    if requerido and not val:
        return {"error": f"{campo} es requerido"}
    if len(val) > max_len:
        return {"error": f"{campo} demasiado largo (máx {max_len} caracteres)"}
    return None


def _validar_ip(ip_str):
    try:
        return ipaddress.ip_address(ip_str)
    except ValueError:
        return None


def _validar_red(red_str):
    try:
        return ipaddress.IPv4Network(red_str, strict=False)
    except ValueError:
        return None


def _lock_db(archivo, modo="r"):
    try:
        fcntl.flock(archivo, fcntl.LOCK_EX if modo == "w" else fcntl.LOCK_SH)
    except (IOError, AttributeError):
        pass


def _unlock_db(archivo):
    try:
        fcntl.flock(archivo, fcntl.LOCK_UN)
    except (IOError, AttributeError):
        pass


def _load_db():
    """Carga la base de datos IPAM con lock compartido."""
    if os.path.exists(IPAM_DB_FILE):
        try:
            with open(IPAM_DB_FILE, "r") as f:
                _lock_db(f, "r")
                data = json.load(f)
                _unlock_db(f)
                return data
        except (json.JSONDecodeError, IOError):
            return dict(EMPTY_DB)
    return dict(EMPTY_DB)


def _save_db(db):
    """Guarda la base de datos IPAM con lock exclusivo."""
    with open(IPAM_DB_FILE, "w") as f:
        _lock_db(f, "w")
        json.dump(db, f, indent=2)
        _unlock_db(f)
    return True


def _find_network_in_db(network_str, db):
    """Busca una red en la DB."""
    for i, net in enumerate(db["networks"]):
        if net["network"] == network_str:
            return i, net
    return None, None


# ─── REDES ────────────────────────────────────────────────────

def add_network(network_str, description="", site=""):
    """Agrega una red al IPAM."""
    err = _validar_str(description, "Descripción", max_len=200)
    if err:
        return err
    err = _validar_str(site, "Sitio", max_len=100)
    if err:
        return err
    try:
        net = ipaddress.IPv4Network(network_str, strict=False)
    except ValueError as e:
        return {"error": f"Red inválida: {e}"}

    db = _load_db()
    idx, existing = _find_network_in_db(str(net.network_address) + "/" + str(net.prefixlen), db)
    if existing:
        return {"error": "La red ya existe", "network": existing}

    entry = {
        "network": str(net.network_address) + "/" + str(net.prefixlen),
        "cidr": net.prefixlen,
        "netmask": str(net.netmask),
        "broadcast": str(net.broadcast_address),
        "gateway": "",
        "description": description,
        "site": site,
        "first_ip": str(net.network_address + 1) if net.num_addresses > 2 else "",
        "last_ip": str(net.broadcast_address - 1) if net.num_addresses > 2 else "",
        "total_hosts": net.num_addresses - 2,
        "used_hosts": 0,
        "status": "active",
        "vlan_id": None,
        "created": datetime.now().isoformat(),
    }
    db["networks"].append(entry)
    _save_db(db)
    return {"success": True, "network": entry}


def list_networks(site=None, status=None):
    """Lista todas las redes."""
    db = _load_db()
    nets = db["networks"]
    if site:
        nets = [n for n in nets if n.get("site", "").lower() == site.lower()]
    if status:
        nets = [n for n in nets if n.get("status", "").lower() == status.lower()]
    for net in nets:
        try:
            net_obj = ipaddress.ip_network(net["network"])
            used = 0
            for r in db["reservations"]:
                try:
                    if ipaddress.ip_address(r["ip"]) in net_obj:
                        used += 1
                except (ValueError, KeyError):
                    continue
            net["used_hosts"] = used
        except (ValueError, KeyError):
            net["used_hosts"] = 0
    return nets


def get_network(network_str):
    """Obtiene detalle de una red."""
    db = _load_db()
    idx, net = _find_network_in_db(network_str, db)
    if net:
        net["used_hosts"] = len([r for r in db["reservations"] if ipaddress.ip_address(r["ip"]) in ipaddress.ip_network(net["network"])])
        net["reservations"] = [r for r in db["reservations"] if ipaddress.ip_address(r["ip"]) in ipaddress.ip_network(net["network"])]
        return net
    return {"error": "Red no encontrada"}


def delete_network(network_str):
    """Elimina una red."""
    db = _load_db()
    idx, net = _find_network_in_db(network_str, db)
    if net:
        db["networks"].pop(idx)
        _save_db(db)
        return {"success": True}
    return {"error": "Red no encontrada"}


def update_network(network_str, updates):
    """Actualiza campos de una red."""
    db = _load_db()
    idx, net = _find_network_in_db(network_str, db)
    if net:
        for key, val in updates.items():
            if key in ("description", "gateway", "site", "status", "vlan_id"):
                net[key] = val
        db["networks"][idx] = net
        _save_db(db)
        return {"success": True, "network": net}
    return {"error": "Red no encontrada"}


# ─── RESERVACIONES IP ─────────────────────────────────────────

def add_reservation(ip, hostname, mac="", description="", network_str=None):
    """Agrega una reservación IP."""
    ip_obj = _validar_ip(ip)
    if not ip_obj:
        return {"error": f"IP inválida: {ip}"}
    err = _validar_str(hostname, "Hostname", max_len=100, requerido=True)
    if err:
        return err
    err = _validar_str(description, "Descripción", max_len=200)
    if err:
        return err
    if mac:
        mac = mac.upper().strip()
        if not re.match(r"^([0-9A-F]{2}[:-]){5}([0-9A-F]{2})$", mac):
            return {"error": f"MAC inválida: {mac}. Usar formato AA:BB:CC:DD:EE:FF"}

    db = _load_db()
    existing = [r for r in db["reservations"] if r["ip"] == ip]
    if existing:
        return {"error": "IP ya reservada", "reservation": existing[0]}

    if network_str:
        net = _validar_red(network_str)
        if not net:
            return {"error": f"Red inválida: {network_str}"}
        if ip_obj not in net:
            return {"error": f"IP {ip} no está en la red {network_str}"}

    entry = {
        "ip": ip,
        "hostname": hostname,
        "mac": mac if mac else "",
        "description": description,
        "created": datetime.now().isoformat(),
        "updated": datetime.now().isoformat(),
    }
    db["reservations"].append(entry)
    _save_db(db)
    return {"success": True, "reservation": entry}


def list_reservations(network_str=None):
    """Lista reservaciones."""
    db = _load_db()
    reservations = db["reservations"]
    if network_str:
        try:
            net = ipaddress.IPv4Network(network_str, strict=False)
            reservations = [r for r in reservations if ipaddress.ip_address(r["ip"]) in net]
        except ValueError:
            return {"error": "Red inválida"}
    return reservations


def delete_reservation(ip):
    """Elimina una reservación."""
    db = _load_db()
    before = len(db["reservations"])
    db["reservations"] = [r for r in db["reservations"] if r["ip"] != ip]
    if len(db["reservations"]) < before:
        _save_db(db)
        return {"success": True}
    return {"error": "Reservación no encontrada"}


def search_reservations(query):
    """Busca reservaciones por IP, hostname o MAC."""
    db = _load_db()
    q = query.lower()
    results = []
    for r in db["reservations"]:
        if (q in r["ip"].lower() or q in r["hostname"].lower() or q in r.get("mac", "").lower()):
            results.append(r)
    return results


def get_available_ips(network_str, count=10):
    """Obtiene IPs disponibles en una red."""
    try:
        net = ipaddress.IPv4Network(network_str, strict=False)
    except ValueError as e:
        return {"error": str(e)}

    db = _load_db()
    reserved_ips = {r["ip"] for r in db["reservations"]}
    available = []
    for ip in net.hosts():
        if str(ip) not in reserved_ips:
            available.append(str(ip))
            if len(available) >= count:
                break
    return available


# ─── DHCP SCOPES ──────────────────────────────────────────────

def add_dhcp_scope(name, network_str, start_ip, end_ip, gateway="", dns_servers=None, lease_time="1d"):
    """Agrega un scope DHCP."""
    err = _validar_str(name, "Nombre", max_len=100, requerido=True)
    if err:
        return err
    net = _validar_red(network_str)
    if not net:
        return {"error": f"Red inválida: {network_str}"}
    start = _validar_ip(start_ip)
    if not start:
        return {"error": f"IP inicio inválida: {start_ip}"}
    end = _validar_ip(end_ip)
    if not end:
        return {"error": f"IP fin inválida: {end_ip}"}
    if int(start) >= int(end):
        return {"error": f"Rango inválido: {start_ip} > {end_ip}"}
    if start not in net or end not in net:
        return {"error": f"Rango {start_ip}-{end_ip} fuera de la red {network_str}"}
    if gateway:
        gw = _validar_ip(gateway)
        if not gw:
            return {"error": f"Gateway inválida: {gateway}"}
    if not re.match(r"^\d+[dhms]?$", lease_time.lower().strip()):
        return {"error": f"Tiempo de concesión inválido: {lease_time}. Usar ej: 1d, 12h, 3600"}

    db = _load_db()
    scope = {
        "name": name.strip(),
        "network": network_str,
        "range": {"start": str(start), "end": str(end)},
        "gateway": gateway if gateway else "",
        "dns_servers": dns_servers or [],
        "lease_time": lease_time.strip(),
        "options": {},
        "active_leases": 0,
        "status": "active",
        "created": datetime.now().isoformat(),
    }
    db["dhcp_scopes"].append(scope)
    _save_db(db)
    return {"success": True, "scope": scope}


def list_dhcp_scopes():
    """Lista scopes DHCP."""
    db = _load_db()
    return db["dhcp_scopes"]


# ─── DNS RECORDS ──────────────────────────────────────────────

def add_dns_record(name, record_type, value, ttl=3600):
    """Agrega un registro DNS."""
    err = _validar_str(name, "Nombre DNS", max_len=255, requerido=True)
    if err:
        return err
    err = _validar_str(value, "Valor DNS", max_len=255, requerido=True)
    if err:
        return err
    record_type = record_type.upper()
    valid_types = ["A", "AAAA", "CNAME", "MX", "TXT", "NS", "SRV", "PTR"]
    if record_type not in valid_types:
        return {"error": f"Tipo inválido. Válidos: {valid_types}"}
    try:
        ttl = int(ttl)
        if ttl < 0 or ttl > 86400:
            return {"error": f"TTL inválido: {ttl}. Debe estar entre 0 y 86400"}
    except (ValueError, TypeError):
        return {"error": f"TTL debe ser numérico"}

    if record_type == "A":
        if not _validar_ip(value):
            return {"error": f"Valor inválido para registro A: {value}. Debe ser una IPv4"}
    elif record_type == "AAAA":
        try:
            ipaddress.IPv6Address(value)
        except ValueError:
            return {"error": f"Valor inválido para registro AAAA: {value}. Debe ser una IPv6"}

    db = _load_db()
    entry = {
        "name": name.strip(),
        "type": record_type,
        "value": value.strip(),
        "ttl": ttl,
        "created": datetime.now().isoformat(),
    }
    db["dns_records"].append(entry)
    _save_db(db)
    return {"success": True, "record": entry}


def list_dns_records(record_type=None):
    """Lista registros DNS."""
    db = _load_db()
    records = db["dns_records"]
    if record_type:
        records = [r for r in records if r["type"].upper() == record_type.upper()]
    return records


def delete_dns_record(name, record_type, value):
    """Elimina un registro DNS."""
    db = _load_db()
    before = len(db["dns_records"])
    db["dns_records"] = [r for r in db["dns_records"]
                          if not (r["name"] == name and r["type"] == record_type and r["value"] == value)]
    if len(db["dns_records"]) < before:
        _save_db(db)
        return {"success": True}
    return {"error": "Registro no encontrado"}


# ─── VLANs ────────────────────────────────────────────────────

def add_vlan(vlan_id, name, network_str="", description=""):
    """Agrega una VLAN."""
    err = _validar_str(name, "Nombre VLAN", max_len=100, requerido=True)
    if err:
        return err
    err = _validar_str(description, "Descripción", max_len=200)
    if err:
        return err
    try:
        vlan_id = int(vlan_id)
        if vlan_id < 1 or vlan_id > 4094:
            return {"error": f"VLAN ID inválido: {vlan_id}. Debe estar entre 1 y 4094"}
    except (ValueError, TypeError):
        return {"error": f"VLAN ID debe ser numérico"}
    if network_str and not _validar_red(network_str):
        return {"error": f"Red inválida: {network_str}"}

    db = _load_db()
    existing = [v for v in db["vlans"] if v["vlan_id"] == vlan_id]
    if existing:
        return {"error": f"VLAN {vlan_id} ya existe", "vlan": existing[0]}

    entry = {
        "vlan_id": vlan_id,
        "name": name.strip(),
        "network": network_str,
        "description": description,
        "created": datetime.now().isoformat(),
    }
    db["vlans"].append(entry)
    _save_db(db)
    return {"success": True, "vlan": entry}


def list_vlans():
    """Lista VLANs."""
    db = _load_db()
    return db["vlans"]


def delete_vlan(vlan_id):
    """Elimina una VLAN."""
    db = _load_db()
    before = len(db["vlans"])
    db["vlans"] = [v for v in db["vlans"] if v["vlan_id"] != vlan_id]
    if len(db["vlans"]) < before:
        _save_db(db)
        return {"success": True}
    return {"error": "VLAN no encontrada"}


# ─── SITIOS ───────────────────────────────────────────────────

def add_site(name, location="", description=""):
    """Agrega un sitio."""
    err = _validar_str(name, "Nombre del sitio", max_len=100, requerido=True)
    if err:
        return err
    err = _validar_str(location, "Ubicación", max_len=200)
    if err:
        return err
    err = _validar_str(description, "Descripción", max_len=200)
    if err:
        return err
    db = _load_db()
    existing = [s for s in db["sites"] if s["name"].lower() == name.strip().lower()]
    if existing:
        return {"error": f"El sitio '{name}' ya existe", "site": existing[0]}
    entry = {
        "name": name.strip(),
        "location": location.strip(),
        "description": description.strip(),
        "created": datetime.now().isoformat(),
    }
    db["sites"].append(entry)
    _save_db(db)
    return {"success": True, "site": entry}


def list_sites():
    """Lista sitios."""
    db = _load_db()
    return db["sites"]


# ─── ESTADÍSTICAS ─────────────────────────────────────────────

def get_stats():
    """Obtiene estadísticas del IPAM."""
    db = _load_db()
    total_ips = sum(
        ipaddress.IPv4Network(n["network"], strict=False).num_addresses - 2
        for n in db["networks"]
    )
    used_ips = len(db["reservations"])
    return {
        "networks": len(db["networks"]),
        "reservations": len(db["reservations"]),
        "dhcp_scopes": len(db["dhcp_scopes"]),
        "dns_records": len(db["dns_records"]),
        "vlans": len(db["vlans"]),
        "sites": len(db["sites"]),
        "total_capacity": total_ips,
        "used_ips": used_ips,
        "usage_percent": round(used_ips / total_ips * 100, 1) if total_ips > 0 else 0,
    }


# ─── FUNCIONES DE CÁLCULO ─────────────────────────────────────

def subnet_usage(network_str):
    """Calcula el uso de una subred."""
    try:
        net = ipaddress.IPv4Network(network_str, strict=False)
    except ValueError as e:
        return {"error": str(e)}

    db = _load_db()
    reservations = [r for r in db["reservations"] if ipaddress.ip_address(r["ip"]) in net]
    total = net.num_addresses - 2
    used = len(reservations)
    return {
        "network": network_str,
        "total_hosts": total,
        "used": used,
        "available": total - used,
        "percent": round(used / total * 100, 1) if total > 0 else 0,
        "reservations": reservations,
    }


def find_free_network(base_network, required_hosts, count=5):
    """Encuentra redes libres dentro de una red base."""
    try:
        base = ipaddress.IPv4Network(base_network, strict=False)
    except ValueError as e:
        return {"error": str(e)}

    bits_needed = (required_hosts + 2).bit_length()
    new_prefix = 32 - bits_needed
    if new_prefix <= base.prefixlen:
        return {"error": f"No hay suficiente espacio. Máscara /{base.prefixlen} es muy pequeña"}

    db = _load_db()
    existing = {n["network"] for n in db["networks"]}

    available = []
    for subnet in base.subnets(new_prefix=new_prefix):
        if str(subnet) not in existing:
            available.append(str(subnet))
            if len(available) >= count:
                break
    return {"available": available, "prefix": new_prefix, "usable_hosts": subnet.num_addresses - 2}


def ip_range_to_cidr(start_ip, end_ip):
    """Convierte un rango de IPs a lista de CIDRs."""
    try:
        start_obj = ipaddress.IPv4Address(start_ip)
        end_obj = ipaddress.IPv4Address(end_ip)
    except ValueError as e:
        return {"error": str(e)}
    start = int(start_obj)
    end = int(end_obj)
    if start > end:
        return {"error": f"IP inicio {start_ip} es mayor que IP fin {end_ip}"}
    results = []
    while start <= end:
        max_size = 32
        while max_size > 0:
            mask = (1 << (32 - max_size)) - 1
            network_start = start & ~mask
            if network_start != start:
                break
            if network_start + (1 << (32 - max_size)) - 1 > end:
                break
            max_size -= 1
        max_size += 1
        cidr = f"{ipaddress.IPv4Address(start)}/{max_size}"
        results.append(cidr)
        start += 1 << (32 - max_size)
    return results


def suggest_ip(network_str, hostname=""):
    """Sugiere la próxima IP libre en una red."""
    available = get_available_ips(network_str, 5)
    if isinstance(available, dict) and "error" in available:
        return available
    if isinstance(available, list) and available:
        result = available[0]
        if hostname:
            res = add_reservation(result, hostname, description="Asignación automática")
            if "error" in res:
                return {"error": f"IP sugerida {result} pero no se pudo reservar: {res['error']}",
                        "suggested_ip": result, "available": available}
        return {"suggested_ip": result, "available": available}
    return {"error": f"No hay IPs disponibles en {network_str}"}
