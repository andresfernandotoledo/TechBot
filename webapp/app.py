import sys
import os
import json

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from flask import Flask, jsonify, request, render_template
from techbot.protocols.protocols_db import list_protocols, get_protocol, search_protocols
from techbot.protocols.ports_db import COMMON_PORTS, get_port_service, search_ports
from techbot.console_commands import CONSOLE_COMMANDS, search_commands
from techbot.commands.cisco_commands import CISCO_COMMANDS
from techbot.commands.mikrotik_commands import MIKROTIK_COMMANDS
from techbot.commands.fortinet_commands import FORTINET_COMMANDS
from techbot.commands.linux_commands import LINUX_COMMANDS
from techbot.commands.windows_commands import WINDOWS_COMMANDS
from techbot.commands.cctv_commands import CCTV_COMMANDS
from techbot.diagnostics import DIAGNOSTIC_PROCEDURES
from techbot.diagnostics.cctv import (
    diagnose_camera, diagnose_hikvision_api, diagnose_dahua_api,
    diagnose_zkteco_api, diagnose_dvr_nvr, diagnose_nvr_storage,
    diagnose_full,
)
from techbot.calculators import network_calc, conversions, electrical_calc
from techbot.calculators.cctv_calc import (
    compute, calc_group, get_bitrate_kbps,
    BITRATE_TABLE, RESOLUTIONS, CODECS,
    SMART_CODECS, SCENE_FACTORS, RESOLUTION_INFO,
)
from techbot.scripts import network_scripts, system_scripts
from techbot.apis.hikvision_api import HikvisionClient, HIKVISION_API
from techbot.apis.dahua_api import DahuaClient, DAHUA_API
from techbot.apis.zkteco_api import ZKTecoClient, ZKTECO_API
from techbot.access_control import (
    create_ac_client, ACCESS_CONTROL_INFO, EVENT_TYPES,
    CREDENTIAL_TYPES, DOOR_STATES
)
from techbot.scanner import (
    scan_ports as scanner_scan_ports,
    quick_scan, discover_hosts, os_detection,
    traceroute, service_detection, compare_port_scans,
    export_scan_results, ping_host,
    scan_cctv, scan_access_control, discover_cctv,
    identify_device, CCTV_PORTS, AC_PORTS, ONVIF_PORTS,
)
from techbot.snmp import (
    snmp_get, snmp_walk, snmp_set, get_system_info,
    get_interfaces, get_mac_table, get_routing_table,
    get_storage, detect_vendor, get_arp_table,
    snmp_check, MIBS, VENDOR_MIBS,
    detect_device_type, get_cctv_info,
)
from techbot.ipam import (
    add_network, list_networks, get_network, delete_network, update_network,
    add_reservation, list_reservations, delete_reservation, search_reservations,
    get_available_ips, add_dhcp_scope, list_dhcp_scopes,
    add_dns_record, list_dns_records, delete_dns_record,
    add_vlan, list_vlans, delete_vlan,
    add_site, list_sites, get_stats,
    subnet_usage, find_free_network, suggest_ip
)
from techbot.mac_lookup import buscar_por_mac, buscar_por_fabricante, listar_fabricantes
from techbot.speedtest import run_speedtest, get_progress
from techbot.tasks import start_task, get_task, list_tasks
from techbot.ups import (
    NUTClient, UPSSNMPClient, ModbusUPSClient, PowerChuteClient,
    APCUPSDClient, DIAGNOSTIC_PROCEDURE, detect_ups,
    check_nut_available, UPS_MIB, BATTERY_STATUS_MAP,
    OUTPUT_SOURCE_MAP, TEST_RESULT_MAP, VENDOR_MIBS,
    get_apcaccess_status, get_pwrstat_status, estimate_battery_life,
)

app = Flask(__name__)

API_CLIENTS = {}
AC_CLIENTS = {}

# ─── RUTAS PRINCIPALES ────────────────────────────────────────

@app.route("/")
def index():
    return render_template("index.html")


# ─── PROTOCOLOS ───────────────────────────────────────────────

@app.route("/api/protocols")
def api_protocols():
    query = request.args.get("q")
    if query:
        results = search_protocols(query)
        return jsonify([{"name": n, **i} for n, i in results.items()])
    return jsonify(list_protocols())


@app.route("/api/protocols/<name>")
def api_protocol_detail(name):
    proto = get_protocol(name)
    if proto:
        return jsonify(proto)
    return jsonify({"error": "Protocolo no encontrado"}), 404


# ─── PUERTOS ──────────────────────────────────────────────────

@app.route("/api/ports")
def api_ports():
    query = request.args.get("q")
    if query:
        if query.isdigit():
            return jsonify({int(query): get_port_service(int(query))})
        results = search_ports(query)
        return jsonify(results)
    common = dict(sorted(COMMON_PORTS.items())[:50])
    for p in set(CCTV_PORTS + AC_PORTS):
        if p in COMMON_PORTS and p not in common:
            common[p] = COMMON_PORTS[p]
    return jsonify(dict(sorted(common.items())))


@app.route("/api/ports/<int:port>")
def api_port_detail(port):
    return jsonify({port: get_port_service(port)})


# ─── COMANDOS ─────────────────────────────────────────────────

def _cmds_to_objects(data):
    """Convierte tuplas (cmd, desc) a objetos {cmd, desc} para el frontend."""
    if isinstance(data, dict):
        return {k: _cmds_to_objects(v) for k, v in data.items()}
    if isinstance(data, list):
        return [{"cmd": c, "desc": d} if isinstance(c, str) and isinstance(d, str) else _cmds_to_objects(x) for c, d in data]
    return data


@app.route("/api/commands")
def api_commands():
    vendor = request.args.get("vendor", "").lower()
    query = request.args.get("q", "")
    vendors = {
        "cisco": CISCO_COMMANDS,
        "mikrotik": MIKROTIK_COMMANDS,
        "fortinet": FORTINET_COMMANDS,
        "linux": LINUX_COMMANDS,
        "windows": WINDOWS_COMMANDS,
        "cctv": CCTV_COMMANDS,
        "all": CONSOLE_COMMANDS,
    }
    if vendor and vendor in vendors:
        data = _cmds_to_objects(vendors[vendor])
        if query:
            results = {}
            for cat, subcats in data.items():
                if isinstance(subcats, dict):
                    for subcat, cmds in subcats.items():
                        for item in cmds:
                            if query.lower() in item["cmd"].lower() or query.lower() in item["desc"].lower():
                                if cat not in results:
                                    results[cat] = {}
                                if subcat not in results[cat]:
                                    results[cat][subcat] = []
                                results[cat][subcat].append(item)
                elif isinstance(subcats, list):
                    for item in subcats:
                        if query.lower() in item["cmd"].lower() or query.lower() in item["desc"].lower():
                            if cat not in results:
                                results[cat] = []
                            results[cat].append(item)
            return jsonify(results)
        return jsonify(data)
    return jsonify(list(vendors.keys()))


# ─── CALCULADORAS ─────────────────────────────────────────────

@app.route("/api/calculators")
def api_calculators():
    category = request.args.get("cat", "network")
    if category == "network":
        return jsonify({
            "subnet_calc": {"params": ["ip", "cidr"], "example": {"ip": "192.168.1.0", "cidr": 24}},
            "vlsm": {"params": ["base_network", "hosts_per_subnet[]"]},
            "bandwidth_calc": {"params": ["mbps", "duration_minutes"]},
            "transfer_time": {"params": ["file_size_mb", "speed_mbps"]},
            "cidr_to_mask": {"params": ["cidr"]},
            "mask_to_cidr": {"params": ["mask"]},
        })
    elif category == "conversions":
        return jsonify({
            "bytes_to_human": {"params": ["size_bytes"]},
            "celsius_to_fahrenheit": {"params": ["c"]},
            "dbm_to_mw": {"params": ["dbm"]},
            "mw_to_dbm": {"params": ["mw"]},
            "awg_to_mm2": {"params": ["awg"]},
        })
    elif category == "electrical":
        return jsonify({
            "ohms_law_v": {"params": ["i", "r"]},
            "voltage_divider": {"params": ["vin", "r1", "r2"]},
            "battery_capacity": {"params": ["load_w", "hours", "voltage"]},
            "solar_panel_required": {"params": ["load_kwh", "sun_hours"]},
        })
    elif category == "cctv":
        return jsonify({
            "cctv_calc": {
                "params": ["groups", "recording_hours", "motion_percent",
                           "retention_days", "total_storage_gb"],
                "options": {
                    "resolutions": RESOLUTIONS,
                    "codecs": CODECS,
                    "smart_codecs": list(SMART_CODECS.keys()),
                    "scenes": list(SCENE_FACTORS.keys()),
                    "res_info": {k: f"{v[0]}x{v[1]} ({v[2]:.1f}MP)" for k, v in RESOLUTION_INFO.items()},
                }
            },
        })
    return jsonify({"error": "Categoria no valida"}), 400


@app.route("/api/calculators/run")
def api_calculator_run():
    calc = request.args.get("calc", "")
    try:
        if calc == "subnet_calc":
            from techbot.calculators.network_calc import subnet_calc
            result = subnet_calc(request.args["ip"], int(request.args["cidr"]))
        elif calc == "bandwidth_calc":
            result = network_calc.bandwidth_calc(float(request.args["mbps"]), float(request.args["duration_minutes"]))
        elif calc == "transfer_time":
            result = network_calc.transfer_time(float(request.args["file_size_mb"]), float(request.args["speed_mbps"]))
        elif calc == "cidr_to_mask":
            result = network_calc.cidr_to_mask(int(request.args["cidr"]))
        elif calc == "mask_to_cidr":
            result = network_calc.mask_to_cidr(request.args["mask"])
        elif calc == "ohms_law_v":
            result = electrical_calc.ohms_law_v(float(request.args["i"]), float(request.args["r"]))
        elif calc == "voltage_divider":
            result = electrical_calc.voltage_divider(float(request.args["vin"]), float(request.args["r1"]), float(request.args["r2"]))
        elif calc == "bytes_to_human":
            result = conversions.bytes_to_human(float(request.args["size_bytes"]))
        elif calc == "celsius_to_fahrenheit":
            result = conversions.celsius_to_fahrenheit(float(request.args["c"]))
        elif calc == "dbm_to_mw":
            result = network_calc.decibels_to_mw(float(request.args["dbm"]))
        elif calc == "battery_capacity":
            result = electrical_calc.battery_capacity(float(request.args["load_w"]), float(request.args["hours"]), float(request.args["voltage"]))
        elif calc == "solar_panel_required":
            result = electrical_calc.solar_panel_required(float(request.args["load_kwh"]), float(request.args["sun_hours"]))
        elif calc == "cctv_calc":
            from techbot.calculators.cctv_calc import compute
            import json
            result = compute(
                groups=json.loads(request.args["groups"]),
                recording_hours=int(request.args.get("recording_hours", 24)),
                motion_percent=int(request.args.get("motion_percent", 100)),
                retention_days=int(request.args.get("retention_days", 30)),
                total_storage_gb=float(request.args.get("total_storage_gb", 2000)),
            )
        else:
            return jsonify({"error": f"Calculadora '{calc}' no encontrada"}), 400
        return jsonify({"result": str(result) if not isinstance(result, dict) else result})
    except Exception as e:
        return jsonify({"error": str(e)}), 400


# ─── DIAGNÓSTICO ──────────────────────────────────────────────

@app.route("/api/diagnostics")
def api_diagnostics():
    return jsonify(list(DIAGNOSTIC_PROCEDURES.keys()))


@app.route("/api/diagnostics/<name>")
def api_diagnostic_detail(name):
    if name == "cctv":
        return jsonify({
            "name": "Diagnóstico Automático CCTV",
            "endpoints": {
                "camera": "/api/diagnostics/cctv/camera/<host>",
                "hikvision": "/api/diagnostics/cctv/hikvision/<host>",
                "dahua": "/api/diagnostics/cctv/dahua/<host>",
                "zkteco": "/api/diagnostics/cctv/zkteco/<host>",
                "dvr_nvr": "/api/diagnostics/cctv/dvr-nvr/<host>",
                "nvr_storage": "/api/diagnostics/cctv/nvr-storage/<host>",
                "full": "/api/diagnostics/cctv/full/<host>",
            }
        })
    for key, val in DIAGNOSTIC_PROCEDURES.items():
        if key.lower().replace(" ", "_") == name.lower().replace(" ", "_"):
            return jsonify({"name": key, "content": val})
    return jsonify({"error": "Procedimiento no encontrado"}), 404


@app.route("/api/diagnostics/cctv/camera/<host>")
def api_diag_cctv_camera(host):
    timeout = int(request.args.get("timeout", 3))
    try:
        return _async_or_run(diagnose_camera, host, timeout)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/diagnostics/cctv/hikvision/<host>")
def api_diag_cctv_hik(host):
    port = int(request.args.get("port", 80))
    user = request.args.get("user", "admin")
    pw = request.args.get("password", "12345")
    timeout = int(request.args.get("timeout", 5))
    try:
        return _async_or_run(diagnose_hikvision_api, host, port, user, pw, timeout)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/diagnostics/cctv/dahua/<host>")
def api_diag_cctv_dahua(host):
    port = int(request.args.get("port", 80))
    user = request.args.get("user", "admin")
    pw = request.args.get("password", "admin")
    timeout = int(request.args.get("timeout", 5))
    try:
        return _async_or_run(diagnose_dahua_api, host, port, user, pw, timeout)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/diagnostics/cctv/zkteco/<host>")
def api_diag_cctv_zk(host):
    port = int(request.args.get("port", 80))
    user = request.args.get("user", "admin")
    pw = request.args.get("password", "admin")
    timeout = int(request.args.get("timeout", 5))
    try:
        return _async_or_run(diagnose_zkteco_api, host, port, user, pw, timeout)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/diagnostics/cctv/full/<host>")
def api_diag_cctv_full(host):
    timeout = int(request.args.get("timeout", 5))
    hik_p = int(request.args.get("hik_port", 80))
    dahua_p = int(request.args.get("dahua_port", 80))
    zk_p = int(request.args.get("zk_port", 80))
    try:
        return _async_or_run(
            diagnose_full, host, cctv_port=hik_p, ac_port=zk_p,
            timeout=timeout,
        )
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/diagnostics/cctv/dvr-nvr/<host>")
def api_diag_cctv_dvr_nvr(host):
    timeout = int(request.args.get("timeout", 3))
    try:
        return _async_or_run(diagnose_dvr_nvr, host, timeout)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/diagnostics/cctv/nvr-storage/<host>")
def api_diag_cctv_nvr_storage(host):
    port = int(request.args.get("port", 80))
    timeout = int(request.args.get("timeout", 5))
    try:
        return _async_or_run(diagnose_nvr_storage, host, port, timeout)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ─── APIs CCTV ────────────────────────────────────────────────

@app.route("/api/cctv")
def api_cctv():
    return jsonify({
        "hikvision": {
            "info": "Cliente ISAPI para cámaras y NVRs Hikvision",
            "ports": HIKVISION_API["Puertos"],
            "endpoints": [e[0] for e in HIKVISION_API["Comandos ISAPI"]],
            "default_creds": HIKVISION_API["Credenciales por defecto"],
        },
        "dahua": {
            "info": "Cliente CGI para cámaras y NVRs Dahua",
            "ports": DAHUA_API["Puertos"],
            "endpoints": [e[0] for e in DAHUA_API["Comandos CGI"]],
            "default_creds": DAHUA_API["Credenciales por defecto"],
        },
        "zkteco": {
            "info": "Cliente HTTP para dispositivos biométricos ZKTeco",
            "ports": ZKTECO_API["Puertos"],
            "endpoints": [e[0] for e in ZKTECO_API["Comandos SDK/SOAP"]],
        }
    })


@app.route("/api/cctv/connect", methods=["POST"])
def api_cctv_connect():
    data = request.json
    vendor = data.get("vendor", "").lower()
    host = data.get("host", "")
    port = int(data.get("port", 80))
    user = data.get("user", "admin")
    password = data.get("password", "")
    ssl = data.get("ssl", False)
    session_id = f"{vendor}_{host}_{port}"

    try:
        if vendor == "hikvision":
            client = HikvisionClient(host, port, user, password, ssl)
        elif vendor == "dahua":
            client = DahuaClient(host, port, user, password, ssl)
        elif vendor == "zkteco":
            client = ZKTecoClient(host, port, user, password, ssl)
        else:
            return jsonify({"error": "Vendor no soportado"}), 400

        if client.is_online():
            API_CLIENTS[session_id] = client
            info = client.get_device_info()
            methods = [m for m in dir(client) if not m.startswith("_") and callable(getattr(client, m))]
            return jsonify({"online": True, "session": session_id, "info": info, "methods": methods})
        else:
            return jsonify({"online": False, "error": "No se pudo conectar"})
    except Exception as e:
        return jsonify({"online": False, "error": str(e)})


@app.route("/api/cctv/command", methods=["POST"])
def api_cctv_command():
    data = request.json
    session_id = data.get("session", "")
    method_name = data.get("method", "")

    if session_id not in API_CLIENTS:
        return jsonify({"error": "Sesión no encontrada. Conectá primero."}), 400

    client = API_CLIENTS[session_id]
    method = getattr(client, method_name, None)
    if not method or not callable(method):
        return jsonify({"error": f"Método '{method_name}' no disponible"}), 400

    try:
        result = method()
        if isinstance(result, bytes):
            return jsonify({"type": "binary", "size": len(result)})
        return jsonify({"result": result})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ─── CONTROL DE ACCESO ────────────────────────────────────────

@app.route("/api/access-control")
def api_access_control():
    info = {}
    for vendor, data in ACCESS_CONTROL_INFO.items():
        info[vendor] = {
            "name": data["name"],
            "protocol": data["protocol"],
            "ports": data["ports"],
            "features": data["features"],
            "models": data["models"],
        }
    return jsonify({
        "vendors": info,
        "event_types": EVENT_TYPES,
        "credential_types": CREDENTIAL_TYPES,
        "door_states": DOOR_STATES,
    })


@app.route("/api/access-control/connect", methods=["POST"])
def api_ac_connect():
    data = request.json or {}
    vendor = data.get("vendor", "").lower()
    host = data.get("host", "").strip()
    try:
        port = int(data.get("port", 80))
    except (ValueError, TypeError):
        return jsonify({"online": False, "error": "Puerto inválido"}), 400
    user = data.get("user", "admin")
    password = data.get("password", "")
    ssl = data.get("ssl", False)
    session_id = f"ac_{vendor}_{host}_{port}"

    if not host:
        return jsonify({"online": False, "error": "Host/IP requerido"}), 400
    if not vendor:
        return jsonify({"online": False, "error": "Vendor requerido"}), 400

    try:
        ac = create_ac_client(vendor, host, port, user, password, ssl)
        test = ac.test_connection()
        if isinstance(test, dict) and "error" in test:
            return jsonify({"online": False, "error": test["error"], "detail": test}), 400
        AC_CLIENTS[session_id] = ac
        info = ac.get_info()
        methods = [m for m in dir(ac) if not m.startswith("_") and callable(getattr(ac, m))]
        return jsonify({
            "online": True,
            "session": session_id,
            "info": info,
            "methods": [m for m in methods if m not in ("get_info", "lock", "unlock", "test_connection")],
            "vendor_name": ACCESS_CONTROL_INFO.get(vendor, {}).get("name", vendor),
        })
    except ValueError as e:
        return jsonify({"online": False, "error": str(e)}), 400
    except Exception as e:
        return jsonify({"online": False, "error": f"Error al conectar: {e}"}), 500


@app.route("/api/access-control/command", methods=["POST"])
def api_ac_command():
    data = request.json or {}
    session_id = data.get("session", "")
    method_name = data.get("method", "")
    params = data.get("params", {})

    if not session_id:
        return jsonify({"error": "ID de sesión requerido"}), 400
    if not method_name:
        return jsonify({"error": "Nombre del método requerido"}), 400
    if session_id not in AC_CLIENTS:
        return jsonify({"error": "Sesión no encontrada. Conectá primero."}), 400

    ac = AC_CLIENTS[session_id]
    method = getattr(ac, method_name, None)
    if not method or not callable(method):
        return jsonify({"error": f"Método '{method_name}' no disponible"}), 400

    try:
        result = method(**params)
        return jsonify({"result": result})
    except ValueError as e:
        return jsonify({"error": f"Parámetro inválido: {e}"}), 400
    except Exception as e:
        return jsonify({"error": f"Error ejecutando {method_name}: {e}"}), 500


# ─── ESCÁNER DE RED ───────────────────────────────────────────

@app.route("/api/scanner/info")
def api_scanner_info():
    return jsonify({
        "functions": [
            "quick_scan(host) - Escanea puertos más comunes",
            "scan_ports(host, ports=None) - Escanea puertos específicos",
            "discover_hosts(subnet) - Descubre hosts activos por ping",
            "ping_host(host) - Ping a un host",
            "os_detection(host) - Detecta SO por TTL",
            "traceroute(host) - Traza ruta hasta el host",
            "service_detection(host, port) - Banner grabbing",
            "compare_port_scans(s1, s2) - Compara 2 escaneos",
        ],
        "common_ports": "21,22,23,25,53,80,110,443,445,3306,3389,8080,8443..."
    })


def _quick_scan(host):
    results = quick_scan(host)
    os_info = os_detection(host)
    return {"host": host, "os": os_info, "ports": results, "count": len(results)}

def _discover(subnet):
    hosts = discover_hosts(subnet)
    return {"subnet": subnet, "hosts": hosts, "count": len(hosts)}

def _scan_ping(host):
    alive = ping_host(host)
    os_info = os_detection(host)
    return {"host": host, "alive": alive, "os": os_info}

def _traceroute(host):
    hops = traceroute(host)
    return {"host": host, "hops": hops}

def _scan_ports(host, ports_str):
    ports = None
    if ports_str:
        ports = [int(p.strip()) for p in ports_str.split(",") if p.strip().isdigit()]
    results = scanner_scan_ports(host, ports)
    os_info = os_detection(host)
    return {"host": host, "os": os_info, "ports": results, "count": len(results)}

def _scan_cctv(host):
    results = scan_cctv(host)
    identity = identify_device(host)
    return {"host": host, "device_identity": identity, "ports": results, "count": len(results), "is_cctv": len(results) > 0}

def _scan_ac(host):
    results = scan_access_control(host)
    return {"host": host, "ports": results, "count": len(results), "is_access_control": any(r.get("is_access_control", False) for r in results)}

def _discover_cctv(subnet):
    devices = discover_cctv(subnet)
    return {"subnet": subnet, "devices": devices, "count": len(devices)}


@app.route("/api/scanner/quick-scan")
def api_scanner_quick():
    host = request.args.get("host", "")
    if not host:
        return jsonify({"error": "Host requerido"}), 400
    try:
        return _async_or_run(_quick_scan, host)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/scanner/discover")
def api_scanner_discover():
    subnet = request.args.get("subnet", "")
    if not subnet:
        return jsonify({"error": "Subred requerida (ej: 192.168.1.0/24)"}), 400
    try:
        return _async_or_run(_discover, subnet)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/scanner/ping")
def api_scanner_ping():
    host = request.args.get("host", "")
    if not host:
        return jsonify({"error": "Host requerido"}), 400
    try:
        alive = ping_host(host)
        os_info = os_detection(host)
        return jsonify({"host": host, "alive": alive, "os": os_info})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/scanner/traceroute")
def api_scanner_traceroute():
    host = request.args.get("host", "")
    if not host:
        return jsonify({"error": "Host requerido"}), 400
    try:
        return _async_or_run(_traceroute, host)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/scanner/scan-ports")
def api_scanner_scan_ports():
    host = request.args.get("host", "")
    ports_str = request.args.get("ports", "")
    if not host:
        return jsonify({"error": "Host requerido"}), 400
    try:
        return _async_or_run(_scan_ports, host, ports_str)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/scanner/scan-cctv")
def api_scanner_scan_cctv():
    host = request.args.get("host", "")
    if not host:
        return jsonify({"error": "Host requerido"}), 400
    try:
        return _async_or_run(_scan_cctv, host)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/scanner/scan-ac")
def api_scanner_scan_ac():
    host = request.args.get("host", "")
    if not host:
        return jsonify({"error": "Host requerido"}), 400
    try:
        return _async_or_run(_scan_ac, host)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/scanner/discover-cctv")
def api_scanner_discover_cctv():
    subnet = request.args.get("subnet", "")
    if not subnet:
        return jsonify({"error": "Subred requerida"}), 400
    try:
        return _async_or_run(_discover_cctv, subnet)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/scanner/ports-info")
def api_scanner_ports_info():
    return jsonify({
        "cctv_ports": sorted(CCTV_PORTS),
        "ac_ports": sorted(AC_PORTS),
        "onvif_ports": sorted(ONVIF_PORTS),
    })


# ─── SNMP ─────────────────────────────────────────────────────

@app.route("/api/snmp/info")
def api_snmp_info():
    return jsonify({
        "mibs": {k: v for k, v in list(MIBS.items())[:30]},
        "vendors": VENDOR_MIBS,
        "howto": "Requiere snmpget/snmpwalk instalados en el sistema",
        "functions": [
            "snmp_get(host, community, oid) - Obtener un valor",
            "snmp_walk(host, community, oid) - Caminar un árbol",
            "snmp_set(host, community, oid, value) - Escribir un valor",
            "get_system_info(host, community) - Info del sistema",
            "get_interfaces(host, community) - Interfaces de red",
            "get_mac_table(host, community) - Tabla MAC",
            "get_routing_table(host, community) - Tabla de rutas",
            "get_storage(host, community) - Almacenamiento",
            "detect_vendor(host, community) - Detectar fabricante",
        ]
    })


@app.route("/api/snmp/get")
def api_snmp_get():
    host = request.args.get("host", "")
    community = request.args.get("community", "public")
    oid = request.args.get("oid", "")
    if not host or not oid:
        return jsonify({"error": "Host y OID requeridos"}), 400
    try:
        result = snmp_get(host, community, oid)
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/snmp/walk")
def api_snmp_walk():
    host = request.args.get("host", "")
    community = request.args.get("community", "public")
    oid = request.args.get("oid", "1.3.6.1.2.1.1")
    if not host:
        return jsonify({"error": "Host requerido"}), 400
    try:
        result = snmp_walk(host, community, oid)
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/snmp/system")
def api_snmp_system():
    host = request.args.get("host", "")
    community = request.args.get("community", "public")
    if not host:
        return jsonify({"error": "Host requerido"}), 400
    try:
        info = get_system_info(host, community)
        vendor = detect_vendor(host, community)
        info["vendor"] = vendor
        return jsonify(info)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/snmp/interfaces")
def api_snmp_interfaces():
    host = request.args.get("host", "")
    community = request.args.get("community", "public")
    if not host:
        return jsonify({"error": "Host requerido"}), 400
    try:
        ifaces = get_interfaces(host, community)
        return jsonify({"host": host, "interfaces": ifaces, "count": len(ifaces)})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/snmp/check")
def api_snmp_check():
    host = request.args.get("host", "")
    community = request.args.get("community", "public")
    if not host:
        return jsonify({"error": "Host requerido"}), 400
    try:
        accessible = snmp_check(host, community)
        return jsonify({"host": host, "community": community, "accessible": accessible})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/snmp/detect-device")
def api_snmp_detect_device():
    host = request.args.get("host", "")
    community = request.args.get("community", "public")
    if not host:
        return jsonify({"error": "Host requerido"}), 400
    try:
        device_type = detect_device_type(host, community)
        info = get_system_info(host, community)
        vendor = detect_vendor(host, community)
        return jsonify({
            "host": host,
            "device_type": device_type,
            "vendor": vendor,
            "system_info": info,
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/snmp/cctv-info")
def api_snmp_cctv_info():
    host = request.args.get("host", "")
    community = request.args.get("community", "public")
    if not host:
        return jsonify({"error": "Host requerido"}), 400
    try:
        info = get_cctv_info(host, community)
        device_type = detect_device_type(host, community)
        return jsonify({
            "host": host,
            "device_type": device_type,
            "info": info,
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ─── IPAM ─────────────────────────────────────────────────────

def _ipam_error(fn, *args, **kwargs):
    """Ejecuta una función IPAM y captura excepciones."""
    try:
        return jsonify(fn(*args, **kwargs))
    except (ValueError, TypeError) as e:
        return jsonify({"error": f"Parámetro inválido: {e}"}), 400
    except IOError as e:
        return jsonify({"error": f"Error de E/S en DB: {e}"}), 500
    except Exception as e:
        return jsonify({"error": f"Error interno: {e}"}), 500


@app.route("/api/ipam/stats")
def api_ipam_stats():
    return _ipam_error(get_stats)


@app.route("/api/ipam/networks", methods=["GET", "POST"])
def api_ipam_networks():
    if request.method == "POST":
        data = request.json or {}
        return _ipam_error(add_network,
            data.get("network", ""),
            data.get("description", ""),
            data.get("site", "")
        )
    site = request.args.get("site")
    status = request.args.get("status")
    return _ipam_error(list_networks, site, status)


@app.route("/api/ipam/networks/<path:network_str>")
def api_ipam_network_detail(network_str):
    network_str = network_str.replace("_", "/")
    return _ipam_error(get_network, network_str)


@app.route("/api/ipam/reservations", methods=["GET", "POST", "DELETE"])
def api_ipam_reservations():
    if request.method == "POST":
        data = request.json or {}
        return _ipam_error(add_reservation,
            data.get("ip", ""), data.get("hostname", ""),
            data.get("mac", ""), data.get("description", ""),
            data.get("network", None)
        )
    elif request.method == "DELETE":
        data = request.json or {}
        return _ipam_error(delete_reservation, data.get("ip", ""))
    net = request.args.get("network")
    q = request.args.get("q")
    if q:
        return _ipam_error(search_reservations, q)
    return _ipam_error(list_reservations, net)


@app.route("/api/ipam/available")
def api_ipam_available():
    network = request.args.get("network", "")
    count = request.args.get("count", 10)
    if not network:
        return jsonify({"error": "Red requerida"}), 400
    result = get_available_ips(network, int(count))
    if isinstance(result, dict) and "error" in result:
        return jsonify(result), 400
    return jsonify({"network": network, "available": result})


@app.route("/api/ipam/dhcp", methods=["GET", "POST"])
def api_ipam_dhcp():
    if request.method == "POST":
        data = request.json or {}
        return _ipam_error(add_dhcp_scope,
            data.get("name", ""), data.get("network", ""),
            data.get("start_ip", ""), data.get("end_ip", ""),
            data.get("gateway", ""), data.get("dns_servers", [])
        )
    return _ipam_error(list_dhcp_scopes)


@app.route("/api/ipam/dns", methods=["GET", "POST", "DELETE"])
def api_ipam_dns():
    if request.method == "POST":
        data = request.json or {}
        return _ipam_error(add_dns_record,
            data.get("name", ""), data.get("type", "A"),
            data.get("value", ""), data.get("ttl", 3600)
        )
    elif request.method == "DELETE":
        data = request.json or {}
        return _ipam_error(delete_dns_record,
            data.get("name", ""), data.get("type", ""), data.get("value", "")
        )
    rtype = request.args.get("type")
    return _ipam_error(list_dns_records, rtype)


@app.route("/api/ipam/vlans", methods=["GET", "POST", "DELETE"])
def api_ipam_vlans():
    if request.method == "POST":
        data = request.json or {}
        return _ipam_error(add_vlan,
            data.get("vlan_id"), data.get("name", ""),
            data.get("network", ""), data.get("description", "")
        )
    elif request.method == "DELETE":
        data = request.json or {}
        return _ipam_error(delete_vlan, data.get("vlan_id"))
    return _ipam_error(list_vlans)


@app.route("/api/ipam/sites", methods=["GET", "POST"])
def api_ipam_sites():
    if request.method == "POST":
        data = request.json or {}
        return _ipam_error(add_site,
            data.get("name", ""), data.get("location", ""),
            data.get("description", "")
        )
    return _ipam_error(list_sites)


@app.route("/api/ipam/subnet-usage")
def api_ipam_subnet_usage():
    network = request.args.get("network", "")
    if not network:
        return jsonify({"error": "Red requerida"}), 400
    return _ipam_error(subnet_usage, network)


@app.route("/api/ipam/suggest")
def api_ipam_suggest():
    network = request.args.get("network", "")
    hostname = request.args.get("hostname", "")
    if not network:
        return jsonify({"error": "Red requerida"}), 400
    result = suggest_ip(network, hostname)
    if isinstance(result, dict) and "error" in result:
        return jsonify(result), 400
    return jsonify(result)


@app.route("/api/ipam/find-free")
def api_ipam_find_free():
    base = request.args.get("base", "")
    hosts = request.args.get("hosts", 50)
    count = request.args.get("count", 5)
    if not base:
        return jsonify({"error": "Red base requerida"}), 400
    result = find_free_network(base, int(hosts), int(count))
    if isinstance(result, dict) and "error" in result:
        return jsonify(result), 400
    return jsonify(result)


# ─── SCRIPTS ──────────────────────────────────────────────────

def _list_script_funcs(mod):
    nombre = mod.__name__
    return sorted([n for n, o in vars(mod).items()
                   if not n.startswith("_") and getattr(o, '__module__', None) == nombre])


@app.route("/api/scripts")
def api_scripts():
    return jsonify({
        "network": _list_script_funcs(network_scripts),
        "system": _list_script_funcs(system_scripts),
    })


@app.route("/api/scripts/<category>/<func_name>")
def api_script_source(category, func_name):
    import inspect
    mod = {"network": network_scripts, "system": system_scripts}.get(category)
    if not mod:
        return jsonify({"error": "Categoria no valida"}), 400
    fn = getattr(mod, func_name, None)
    if not fn or not callable(fn):
        return jsonify({"error": f"Función '{func_name}' no encontrada"}), 404
    try:
        source = inspect.getsource(fn)
        sig = str(inspect.signature(fn))
        return jsonify({"name": func_name, "signature": sig, "source": source})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/scripts/<category>/full")
def api_script_full(category):
    mod = {"network": network_scripts, "system": system_scripts}.get(category)
    if not mod:
        return jsonify({"error": "Categoria no valida"}), 400
    try:
        with open(mod.__file__) as f:
            return jsonify({"file": mod.__file__, "source": f.read()})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ─── MAC LOOKUP ────────────────────────────────────────────────

@app.route("/api/mac-lookup")
def api_mac_lookup():
    mac = request.args.get("mac", "").strip()
    fabricante = request.args.get("fabricante", "").strip()
    if mac:
        result = buscar_por_mac(mac)
        if "error" in result:
            return jsonify(result), 400
        return jsonify(result)
    if fabricante:
        results = buscar_por_fabricante(fabricante)
        return jsonify({"query": fabricante, "results": results, "count": len(results)})
    return jsonify({"fabricantes": listar_fabricantes()})


# ─── TAREAS EN SEGUNDO PLANO ────────────────────────────────────

def _async_or_run(func, *args, **kwargs):
    """Ejecuta una función en segundo plano si ?async=true, o directo si no."""
    if request.args.get("async", "").lower() == "true":
        task_id = start_task(func, *args, **kwargs)
        return jsonify({"task_id": task_id, "status": "running"})
    result = func(*args, **kwargs)
    return jsonify(result)


@app.route("/api/tasks")
def api_tasks_list():
    return jsonify(list_tasks())

@app.route("/api/task/<task_id>")
def api_task_status(task_id):
    return jsonify(get_task(task_id))


# ─── SPEEDTEST ──────────────────────────────────────────────────

@app.route("/api/speedtest", methods=["POST"])
def api_speedtest():
    async_mode = request.args.get("async", "").lower() == "true"
    try:
        if async_mode:
            task_id = start_task(run_speedtest)
            return jsonify({"task_id": task_id, "status": "running"})
        result = run_speedtest()
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ─── UPS ──────────────────────────────────────────────────────

@app.route("/api/ups/info")
def api_ups_info():
    return jsonify({
        "mib_oids": {k: v for k, v in list(UPS_MIB.items())[:15]},
        "vendor_oids": VENDOR_MIBS,
        "battery_status_map": {str(k): v for k, v in BATTERY_STATUS_MAP.items()},
        "output_source_map": {str(k): v for k, v in OUTPUT_SOURCE_MAP.items()},
        "test_result_map": {str(k): v for k, v in TEST_RESULT_MAP.items()},
    })


def _ups_snmp(host, community):
    cli = UPSSNMPClient(host, community)
    if not cli.check_access():
        raise RuntimeError("SNMP no accesible")
    result = cli.get_full_status()
    summary = cli.get_summary()
    return {"full": result, "summary": summary}

def _ups_detect(host, community):
    return detect_ups(host, community)

def _ups_nut(dest):
    ups_name = ""
    host = "localhost"
    if "@" in dest:
        ups_name, host = dest.split("@", 1)
    elif dest:
        ups_name = dest
    cli = NUTClient(ups_name, host)
    if not check_nut_available():
        raise RuntimeError("NUT (upsc) no instalado")
    if ups_name:
        return cli.get_summary()
    else:
        lista = cli.list_ups()
        return {"available_ups": lista, "disponibles": len(lista)}


@app.route("/api/ups/snmp-status")
def api_ups_snmp():
    host = request.args.get("host", "")
    community = request.args.get("community", "public")
    if not host:
        return jsonify({"error": "Host requerido"}), 400
    try:
        return _async_or_run(_ups_snmp, host, community)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/ups/detect")
def api_ups_detect():
    host = request.args.get("host", "")
    community = request.args.get("community", "public")
    if not host:
        return jsonify({"error": "Host requerido"}), 400
    try:
        return _async_or_run(_ups_detect, host, community)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/ups/nut-status")
def api_ups_nut():
    dest = request.args.get("ups", "")
    if not dest:
        return jsonify({"error": "UPS requerido (upsname@host o upsname)"}), 400
    try:
        return _async_or_run(_ups_nut, dest)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/ups/diagnostics")
def api_ups_diagnostics():
    return jsonify({"procedure": DIAGNOSTIC_PROCEDURE})


def _ups_apc(host):
    return get_apcaccess_status(host)

def _ups_pwrstat():
    return get_pwrstat_status()

def _ups_modbus(host, port):
    cli = ModbusUPSClient(host, port)
    if not cli.check_access():
        raise RuntimeError("Modbus TCP no accesible")
    return cli.get_status()

def _ups_powerchute(host, port, user, password, ssl):
    cli = PowerChuteClient(host, port, user, password, ssl)
    status = cli.get_status()
    battery = cli.get_battery()
    alarms = cli.get_alarms()
    return {"status": status, "battery": battery, "alarms": alarms}

def _ups_apcupsd(host, port):
    cli = APCUPSDClient(host, port)
    return cli.get_summary()


@app.route("/api/ups/apcaccess")
def api_ups_apc():
    host = request.args.get("host", "")
    try:
        return _async_or_run(_ups_apc, host)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/ups/pwrstat")
def api_ups_pwrstat():
    try:
        return _async_or_run(_ups_pwrstat)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/ups/modbus-status")
def api_ups_modbus():
    host = request.args.get("host", "")
    port = int(request.args.get("port", 502))
    if not host:
        return jsonify({"error": "Host requerido"}), 400
    try:
        return _async_or_run(_ups_modbus, host, port)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/ups/powerchute-status")
def api_ups_powerchute():
    host = request.args.get("host", "")
    port = int(request.args.get("port", 6547))
    user = request.args.get("user", "")
    password = request.args.get("password", "")
    ssl = request.args.get("ssl", "false").lower() == "true"
    if not host:
        return jsonify({"error": "Host requerido"}), 400
    try:
        return _async_or_run(_ups_powerchute, host, port, user, password, ssl)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/ups/apcupsd-status")
def api_ups_apcupsd():
    host = request.args.get("host", "localhost")
    port = int(request.args.get("port", 3551))
    try:
        return _async_or_run(_ups_apcupsd, host, port)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/ups/battery-life")
def api_ups_battery_life():
    date = request.args.get("date", "")
    btype = request.args.get("type", "VRLA")
    if not date:
        return jsonify({"error": "Fecha de fabricación requerida (YYYY-MM-DD)"}), 400
    try:
        result = estimate_battery_life(date, btype)
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ─── INICIO ───────────────────────────────────────────────────

if __name__ == "__main__":
    print("🌐 TechBot Web App corriendo en http://localhost:5000")
    app.run(host="0.0.0.0", port=5000, debug=True)
