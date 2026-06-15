import sys
import os
import json

# Compatibilidad Android (Chaquopy): detectar si estamos en APK
_ANDROID = hasattr(sys, 'getandroidapilevel') or 'ANDROID_ROOT' in os.environ
if _ANDROID:
    # En Chaquopy, la raíz del proyecto está donde está server.py
    _BASE = os.path.dirname(os.path.abspath(__file__))
    if _BASE not in sys.path:
        sys.path.insert(0, _BASE)
else:
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from flask import Flask, jsonify, request, render_template, session
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
    POE_PROFILES, NVR_CHANNEL_LIMITS,
)
from techbot.scripts import network_scripts, system_scripts, dhcp_scripts, dns_scripts, security_scripts
from techbot.apis.hikvision_api import HikvisionClient, HIKVISION_API
from techbot.apis.dahua_api import DahuaClient, DAHUA_API
from techbot.apis.zkteco_api import ZKTecoClient, ZKTECO_API
from techbot.access_control import (
    create_ac_client, ACCESS_CONTROL_INFO, EVENT_TYPES,
    CREDENTIAL_TYPES, DOOR_STATES
)
from techbot import tools as tech_tools
from techbot import wifi as wifi_tools
from techbot import dhcp as dhcp_tools
from techbot import bandwidth as bw_tools
from techbot.scanner import (
    scan_ports as scanner_scan_ports,
    scan_port as scanner_scan_port,
    quick_scan, discover_hosts, os_detection,
    traceroute, service_detection, compare_port_scans,
    export_scan_results, ping_host,
    scan_cctv, scan_access_control, discover_cctv,
    identify_device, CCTV_PORTS, AC_PORTS, ONVIF_PORTS,
)
from techbot.snmp import (
    snmp_get, snmp_walk, get_system_info,
    get_interfaces, get_mac_table, get_routing_table,
    get_storage, detect_vendor, get_arp_table,
    snmp_check, MIBS,
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
from techbot.ups import DIAGNOSTIC_PROCEDURE, estimate_battery_life
from techbot.zabbix import ZabbixAPI, get_notificaciones, format_notificaciones, ZABBIX_API_URL, ZABBIX_DEFAULT_USER, ZABBIX_DEFAULT_PASS
from techbot.monitor import start_monitor, stop_monitor, list_monitors
from techbot.topology import (
    list_topologies as topo_list,
    get_topology as topo_get,
    save_topology as topo_save,
    delete_topology as topo_del
)
from techbot.topology.auto import discover_topology as auto_discover_topology

# En Android (Chaquopy), Flask necesita rutas absolutas para templates/static
_templates = os.path.join(os.path.dirname(os.path.abspath(__file__)), "templates")
_static = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static")
if not os.path.isdir(_templates) and _ANDROID:
    # Fallback: buscar relativo al server.py
    _templates = os.path.join(os.path.dirname(os.path.dirname(__file__)), "webapp", "templates")
    _static = os.path.join(os.path.dirname(os.path.dirname(__file__)), "webapp", "static")

app = Flask(__name__,
            template_folder=_templates if os.path.isdir(_templates) else "templates",
            static_folder=_static if os.path.isdir(_static) else "static")
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "techbot-secret-key-change-in-prod")
app.config["SESSION_COOKIE_NAME"] = "techbot_session"

API_CLIENTS = {}
AC_CLIENTS = {}

# ─── RUTAS PRINCIPALES ────────────────────────────────────────

@app.route("/")
def index():
    return render_template("index.html")


# ─── PROTOCOLOS ───────────────────────────────────────────────

@app.route("/api/status")
def api_status():
    return jsonify({
        "status": "ok",
        "app": "TechBot",
        "version": "1.0",
        "android": _ANDROID,
        "api_routes": len([r for r in app.url_map.iter_rules() if r.rule.startswith('/api/')]),
    })


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
                    "poe_profiles": POE_PROFILES,
                    "nvr_channels": NVR_CHANNEL_LIMITS,
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
        elif calc == "vlsm":
            hosts = request.args.getlist("hosts_per_subnet")
            if not hosts and request.args.get("hosts_per_subnet"):
                hosts = request.args["hosts_per_subnet"].split(",")
            result = network_calc.vlsm(
                request.args["base_network"],
                [int(h.strip()) for h in hosts if h.strip()]
            )
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
        elif calc == "mw_to_dbm":
            result = network_calc.mw_to_dbm(float(request.args["mw"]))
        elif calc == "awg_to_mm2":
            result = conversions.awg_to_mm2(int(request.args["awg"]))
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
                nvr_channels=int(request.args["nvr_channels"]) if request.args.get("nvr_channels") else None,
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


@app.route("/api/diagnostics/<path:name>")
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


def _do_cctv_connect(data):
    vendor = data.get("vendor", "").lower()
    host = data.get("host", "")
    port = int(data.get("port", 80))
    user = data.get("user", "admin")
    password = data.get("password", "")
    ssl = data.get("ssl", False)
    session_id = f"{vendor}_{host}_{port}"

    if vendor == "hikvision":
        client = HikvisionClient(host, port, user, password, ssl)
    elif vendor == "dahua":
        client = DahuaClient(host, port, user, password, ssl)
    elif vendor == "zkteco":
        client = ZKTecoClient(host, port, user, password, ssl)
    else:
        return {"online": False, "error": "Vendor no soportado"}

    if client.is_online():
        API_CLIENTS[session_id] = client
        info = client.get_device_info()
        methods = [m for m in dir(client) if not m.startswith("_") and callable(getattr(client, m))]
        return {"online": True, "session": session_id, "info": info, "methods": methods}
    return {"online": False, "error": "No se pudo conectar"}


@app.route("/api/cctv/connect", methods=["POST"])
def api_cctv_connect():
    data = request.json or {}
    if request.args.get("async", "").lower() == "true" or data.get("async"):
        task_id = start_task(_do_cctv_connect, data)
        return jsonify({"task_id": task_id, "status": "running"})
    try:
        return jsonify(_do_cctv_connect(data))
    except Exception as e:
        return jsonify({"online": False, "error": str(e)})


def _do_cctv_command(data):
    session_id = data.get("session", "")
    method_name = data.get("method", "")
    if session_id not in API_CLIENTS:
        return {"error": "Sesión no encontrada. Conectá primero."}
    client = API_CLIENTS[session_id]
    method = getattr(client, method_name, None)
    if not method or not callable(method):
        return {"error": f"Método '{method_name}' no disponible"}
    result = method()
    if isinstance(result, bytes):
        return {"type": "binary", "size": len(result)}
    return {"result": result}


@app.route("/api/cctv/command", methods=["POST"])
def api_cctv_command():
    data = request.json or {}
    if request.args.get("async", "").lower() == "true" or data.get("async"):
        task_id = start_task(_do_cctv_command, data)
        return jsonify({"task_id": task_id, "status": "running"})
    try:
        return jsonify(_do_cctv_command(data))
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


def _do_ac_connect(data):
    vendor = data.get("vendor", "").lower()
    host = data.get("host", "").strip()
    try:
        port = int(data.get("port", 80))
    except (ValueError, TypeError):
        return {"online": False, "error": "Puerto inválido"}
    user = data.get("user", "admin")
    password = data.get("password", "")
    ssl = data.get("ssl", False)
    session_id = f"ac_{vendor}_{host}_{port}"

    if not host:
        return {"online": False, "error": "Host/IP requerido"}
    if not vendor:
        return {"online": False, "error": "Vendor requerido"}

    ac = create_ac_client(vendor, host, port, user, password, ssl)
    test = ac.test_connection()
    if isinstance(test, dict) and "error" in test:
        return {"online": False, "error": test["error"], "detail": test}
    AC_CLIENTS[session_id] = ac
    info = ac.get_info()
    methods = [m for m in dir(ac) if not m.startswith("_") and callable(getattr(ac, m))]
    return {
        "online": True,
        "session": session_id,
        "info": info,
        "methods": [m for m in methods if m not in ("get_info", "lock", "unlock", "test_connection")],
        "vendor_name": ACCESS_CONTROL_INFO.get(vendor, {}).get("name", vendor),
    }


@app.route("/api/access-control/connect", methods=["POST"])
def api_ac_connect():
    data = request.json or {}
    if request.args.get("async", "").lower() == "true" or data.get("async"):
        task_id = start_task(_do_ac_connect, data)
        return jsonify({"task_id": task_id, "status": "running"})
    try:
        return jsonify(_do_ac_connect(data))
    except ValueError as e:
        return jsonify({"online": False, "error": str(e)}), 400
    except Exception as e:
        return jsonify({"online": False, "error": f"Error al conectar: {e}"}), 500


def _do_ac_command(data):
    session_id = data.get("session", "")
    method_name = data.get("method", "")
    params = data.get("params", {})
    if not session_id:
        return {"error": "ID de sesión requerido"}
    if not method_name:
        return {"error": "Nombre del método requerido"}
    if session_id not in AC_CLIENTS:
        return {"error": "Sesión no encontrada. Conectá primero."}
    ac = AC_CLIENTS[session_id]
    method = getattr(ac, method_name, None)
    if not method or not callable(method):
        return {"error": f"Método '{method_name}' no disponible"}
    result = method(**params)
    return {"result": result}


@app.route("/api/access-control/command", methods=["POST"])
def api_ac_command():
    data = request.json or {}
    if request.args.get("async", "").lower() == "true" or data.get("async"):
        task_id = start_task(_do_ac_command, data)
        return jsonify({"task_id": task_id, "status": "running"})
    try:
        return jsonify(_do_ac_command(data))
    except ValueError as e:
        return jsonify({"error": f"Parámetro inválido: {e}"}), 400
    except Exception as e:
        return jsonify({"error": f"Error ejecutando: {e}"}), 500


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
    result = ping_host(host)
    os_info = os_detection(host)
    return {"host": host, "alive": result["alive"], "os": os_info, "latency": result.get("latency", 0), "ttl": result.get("ttl", -1)}

def _traceroute(host):
    hops = traceroute(host)
    return {"host": host, "hops": hops}

def _scan_ports(host, ports_str, protocol="tcp"):
    ports = None
    if ports_str:
        ports = [int(p.strip()) for p in ports_str.split(",") if p.strip().isdigit()]
    results = scanner_scan_ports(host, ports, protocol=protocol)
    os_info = os_detection(host)
    return {"host": host, "os": os_info, "ports": results, "count": len(results), "protocol": protocol}


def _scan_udp_ports(host, ports_str):
    return _scan_ports(host, ports_str, protocol="udp")

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
        return _async_or_run(_scanner_ping, host)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


def _scanner_ping(host):
    result = ping_host(host)
    os_info = os_detection(host)
    return {"host": host, "alive": result["alive"], "os": os_info, "latency": result.get("latency", 0), "ttl": result.get("ttl", -1)}


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


@app.route("/api/scanner/scan-ports-udp")
def api_scanner_scan_ports_udp():
    host = request.args.get("host", "")
    ports_str = request.args.get("ports", "")
    if not host:
        return jsonify({"error": "Host requerido"}), 400
    try:
        return _async_or_run(_scan_udp_ports, host, ports_str)
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


@app.route("/api/scanner/compare", methods=["POST"])
def api_scanner_compare():
    data = request.get_json()
    if not data or "scan1" not in data or "scan2" not in data:
        return jsonify({"error": "scan1 y scan2 requeridos"}), 400
    try:
        return jsonify(compare_port_scans(data["scan1"], data["scan2"]))
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/tools/http-title")
def api_tools_http_title():
    host = request.args.get("host", "")
    port = request.args.get("port", 80, type=int)
    if not host:
        return jsonify({"error": "Host requerido"}), 400
    try:
        _, _, _, _, banner, _ = scanner_scan_port(host, port, timeout=3)
        title = ""
        server = ""
        for line in banner.split("\n"):
            if line.lower().startswith("server:"):
                server = line.split(":", 1)[1].strip()
            elif "<title>" in line.lower():
                m = __import__("re").search(r"<title>(.*?)</title>", line, __import__("re").IGNORECASE)
                if m: title = m.group(1)
        return jsonify({"host": host, "port": port, "title": title, "server": server, "banner_preview": banner[:300]})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ─── TOOLS (DNS, SSL, WOL, HTTP, Token) ─────────────────────


@app.route("/api/tools/dns")
def api_tools_dns():
    host = request.args.get("host", "")
    rtype = request.args.get("type", "A")
    if not host:
        return jsonify({"error": "Host requerido"}), 400
    try:
        return jsonify(tech_tools.dns_lookup(host, rtype))
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/tools/dns/mx")
def api_tools_dns_mx():
    domain = request.args.get("domain", "")
    if not domain:
        return jsonify({"error": "Dominio requerido"}), 400
    try:
        return jsonify(tech_tools.dns_mx(domain))
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/tools/ssl")
def api_tools_ssl():
    host = request.args.get("host", "")
    port = request.args.get("port", 443, type=int)
    if not host:
        return jsonify({"error": "Host requerido"}), 400
    try:
        return jsonify(tech_tools.ssl_cert_check(host, port))
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/tools/http-headers")
def api_tools_http_headers():
    url = request.args.get("url", "")
    if not url:
        return jsonify({"error": "URL requerida"}), 400
    try:
        return jsonify(tech_tools.http_headers(url))
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/tools/wol", methods=["POST"])
def api_tools_wol():
    data = request.get_json()
    if not data or not data.get("mac"):
        return jsonify({"error": "MAC requerida"}), 400
    try:
        broadcast = data.get("broadcast", "255.255.255.255")
        port = data.get("port", 9)
        return jsonify(tech_tools.wake_on_lan(data["mac"], broadcast, port))
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/tools/token")
def api_tools_token():
    length = request.args.get("length", 32, type=int)
    use_digits = request.args.get("digits", "1") == "1"
    use_symbols = request.args.get("symbols", "1") == "1"
    try:
        return jsonify(tech_tools.generate_token(length, use_digits, use_symbols))
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/tools/local-ip")
def api_tools_local_ip():
    try:
        return jsonify(tech_tools.local_ip())
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/tools/whois")
def api_tools_whois():
    query = request.args.get("query", "")
    if not query:
        return jsonify({"error": "Dominio/IP requerido"}), 400
    try:
        return jsonify(tech_tools.whois_auto(query))
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/tools/ntp")
def api_tools_ntp():
    host = request.args.get("host", "pool.ntp.org")
    try:
        return jsonify(tech_tools.ntp_time(host))
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/tools/port-knock")
def api_tools_port_knock():
    host = request.args.get("host", "")
    ports_str = request.args.get("ports", "")
    delay = request.args.get("delay", 0.2, type=float)
    if not host or not ports_str:
        return jsonify({"error": "Host y puertos requeridos"}), 400
    ports = [int(p.strip()) for p in ports_str.split(",") if p.strip().isdigit()]
    try:
        return jsonify(tech_tools.port_knock(host, ports, delay))
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/tools/http-status")
def api_tools_http_status():
    url = request.args.get("url", "")
    follow = request.args.get("follow", "1") == "1"
    if not url:
        return jsonify({"error": "URL requerida"}), 400
    try:
        return jsonify(tech_tools.http_status(url, follow=follow))
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/tools/ping-latency")
def api_tools_ping_latency():
    host = request.args.get("host", "")
    if not host:
        return jsonify({"error": "Host requerido"}), 400
    try:
        return jsonify(tech_tools.ping_latency(host))
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/wifi/scan")
def api_wifi_scan():
    interface = request.args.get("interface", "")
    async_mode = request.args.get("async", "").lower() == "true"
    try:
        if async_mode:
            task_id = start_task(wifi_tools.scan_wifi, interface or None)
            return jsonify({"task_id": task_id, "status": "running"})
        return jsonify(wifi_tools.scan_wifi(interface or None))
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/wifi/interfaces")
def api_wifi_interfaces():
    try:
        return jsonify(wifi_tools.interface_info())
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/dhcp/discover")
def api_dhcp_discover():
    timeout = request.args.get("timeout", 3, type=int)
    try:
        return jsonify(dhcp_tools.discover_dhcp_servers(timeout))
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/bandwidth/poll")
def api_bw_poll():
    host = request.args.get("host", "")
    community = request.args.get("community", "public")
    ifindex = request.args.get("ifindex", "", type=int)
    name = request.args.get("name", f"if{ifindex}")
    if not host or not ifindex:
        return jsonify({"error": "host e ifindex requeridos"}), 400
    try:
        return jsonify(bw_tools.poll_interface(host, community, ifindex, name))
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/bandwidth/traffic")
def api_bw_traffic():
    host = request.args.get("host", "")
    ifindex = request.args.get("ifindex", "", type=int)
    if not host or not ifindex:
        return jsonify({"error": "host e ifindex requeridos"}), 400
    try:
        result = bw_tools.get_traffic(host, ifindex)
        if not result:
            return jsonify({"error": "Sin datos. Primero usá /api/bandwidth/poll"}), 404
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ─── SNMP ─────────────────────────────────────────────────────

@app.route("/api/snmp/info")
def api_snmp_info():
    return jsonify({
        "mibs": {k: v for k, v in list(MIBS.items())[:30]},
        "howto": "SNMP v1/v2c puro (sin binarios externos)",
        "functions": [
            "snmp_get(host, community, oid) - Obtener un valor",
            "snmp_walk(host, community, oid) - Caminar un árbol",
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
        return _async_or_run(_snmp_walk, host, community, oid)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


def _snmp_walk(host, community, oid):
    return snmp_walk(host, community, oid)


@app.route("/api/snmp/system")
def api_snmp_system():
    host = request.args.get("host", "")
    community = request.args.get("community", "public")
    if not host:
        return jsonify({"error": "Host requerido"}), 400
    try:
        return _async_or_run(_snmp_system, host, community)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


def _snmp_system(host, community):
    info = get_system_info(host, community)
    vendor = detect_vendor(host, community)
    info["vendor"] = vendor
    return info


@app.route("/api/snmp/interfaces")
def api_snmp_interfaces():
    host = request.args.get("host", "")
    community = request.args.get("community", "public")
    if not host:
        return jsonify({"error": "Host requerido"}), 400
    try:
        return _async_or_run(_snmp_interfaces, host, community)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


def _snmp_interfaces(host, community):
    ifaces = get_interfaces(host, community)
    return {"host": host, "interfaces": ifaces, "count": len(ifaces)}


@app.route("/api/snmp/check")
def api_snmp_check():
    host = request.args.get("host", "")
    community = request.args.get("community", "public")
    if not host:
        return jsonify({"error": "Host requerido"}), 400
    try:
        return _async_or_run(_snmp_check, host, community)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


def _snmp_check(host, community):
    accessible = snmp_check(host, community)
    return {"host": host, "community": community, "accessible": accessible}


@app.route("/api/snmp/detect-device")
def api_snmp_detect_device():
    host = request.args.get("host", "")
    community = request.args.get("community", "public")
    if not host:
        return jsonify({"error": "Host requerido"}), 400
    try:
        return _async_or_run(_snmp_detect_device, host, community)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


def _snmp_detect_device(host, community):
    device_type = detect_device_type(host, community)
    info = get_system_info(host, community)
    vendor = detect_vendor(host, community)
    return {"host": host, "device_type": device_type, "vendor": vendor, "system_info": info}


@app.route("/api/snmp/cctv-info")
def api_snmp_cctv_info():
    host = request.args.get("host", "")
    community = request.args.get("community", "public")
    if not host:
        return jsonify({"error": "Host requerido"}), 400
    try:
        return _async_or_run(_snmp_cctv_info, host, community)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


def _snmp_cctv_info(host, community):
    info = get_cctv_info(host, community)
    device_type = detect_device_type(host, community)
    return {"host": host, "device_type": device_type, "info": info}


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


# ─── TOPOLOGÍA ────────────────────────────────────────────────

@app.route("/api/topology/discover", methods=["POST"])
def api_topology_discover():
    data = request.get_json()
    seed = data.get("seed", "")
    community = data.get("community", "public")
    depth = data.get("depth", 2)
    if not seed:
        return jsonify({"error": "IP semilla requerida"}), 400
    return _async_or_run(auto_discover_topology, seed, community, depth)


@app.route("/api/topology", methods=["GET", "POST"])
def api_topology_list():
    if request.method == "POST":
        data = request.json or {}
        return jsonify(topo_save(data))
    return jsonify(topo_list())


@app.route("/api/topology/<topo_id>", methods=["GET", "DELETE"])
def api_topology_detail(topo_id):
    if request.method == "DELETE":
        return jsonify({"success": topo_del(topo_id)})
    topo = topo_get(topo_id)
    if topo:
        return jsonify(topo)
    return jsonify({"error": "Topología no encontrada"}), 404


# ─── SCRIPTS ──────────────────────────────────────────────────

def _list_script_funcs(mod):
    nombre = mod.__name__
    return sorted([n for n, o in vars(mod).items()
                   if not n.startswith("_") and getattr(o, '__module__', None) == nombre])


SCRIPTS_MODULES = {
    "network": network_scripts,
    "dhcp": dhcp_scripts,
    "dns": dns_scripts,
    "security": security_scripts,
    "system": system_scripts,
}


@app.route("/api/scripts")
def api_scripts():
    return jsonify({name: _list_script_funcs(mod) for name, mod in SCRIPTS_MODULES.items()})


@app.route("/api/scripts/<category>/<func_name>")
def api_script_source(category, func_name):
    import inspect
    mod = SCRIPTS_MODULES.get(category)
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
    mod = SCRIPTS_MODULES.get(category)
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
    is_async = request.args.get("async", "").lower() == "true"
    if request.is_json and not is_async:
        is_async = request.json.get("async", False) is True
    if is_async:
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
    custom_url = request.args.get("url", "").strip() or None
    try:
        if async_mode:
            task_id = start_task(run_speedtest, custom_url)
            return jsonify({"task_id": task_id, "status": "running"})
        result = run_speedtest(custom_url)
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ─── UPS ──────────────────────────────────────────────────────

# ─── MONITOR ──────────────────────────────────────────────────


@app.route("/api/monitor/start", methods=["POST"])
def api_monitor_start():
    data = request.get_json()
    subnet = data.get("subnet", "")
    interval = data.get("interval", 300)
    ntfy = data.get("ntfy_topic", "") or None
    if not subnet:
        return jsonify({"error": "Subred requerida"}), 400
    try:
        return jsonify(start_monitor(subnet, interval, ntfy))
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/monitor/stop", methods=["POST"])
def api_monitor_stop():
    data = request.get_json()
    subnet = data.get("subnet", "")
    if not subnet:
        return jsonify({"error": "Subred requerida"}), 400
    try:
        return jsonify(stop_monitor(subnet))
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/monitor/list")
def api_monitor_list():
    try:
        return jsonify(list_monitors())
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/ups/diagnostics")
def api_ups_diagnostics():
    return jsonify({"procedure": DIAGNOSTIC_PROCEDURE})


@app.route("/api/ups/battery-life")
def api_ups_battery_life():
    date = request.args.get("date", "")
    btype = request.args.get("type", "VRLA")
    if not date:
        return jsonify({"error": "Fecha de fabricacion requerida (YYYY-MM-DD)"}), 400
    try:
        result = estimate_battery_life(date, btype)
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ─── ZABBIX ────────────────────────────────────────────────────


def _zabbix_from_session():
    """Obtiene API URL y credenciales desde la sesion."""
    api_url = session.get("zabbix_api_url")
    user = session.get("zabbix_user")
    password = session.get("zabbix_pass")
    if not api_url:
        return None, "No hay sesion activa. Conectá primero."
    try:
        api = ZabbixAPI(api_url, user, password)
        return api, None
    except Exception as e:
        return None, str(e)


@app.route("/api/ups/zabbix/connect", methods=["POST"])
def api_ups_zabbix_connect():
    """Guarda credenciales en sesion y prueba conexion."""
    data = request.json or {}
    api_url = data.get("api_url", ZABBIX_API_URL)
    user = data.get("user", ZABBIX_DEFAULT_USER)
    password = data.get("password", ZABBIX_DEFAULT_PASS)
    try:
        api = ZabbixAPI(api_url, user, password)
        r = api.check_connection()
        if r.get("connected"):
            session["zabbix_api_url"] = api_url
            session["zabbix_user"] = user
            session["zabbix_pass"] = password
        return jsonify(r)
    except Exception as e:
        return jsonify({"connected": False, "error": str(e)})


@app.route("/api/ups/zabbix/status")
def api_ups_zabbix_status():
    api_url = session.get("zabbix_api_url")
    if not api_url:
        return jsonify({"connected": False})
    return jsonify({
        "connected": True,
        "api_url": api_url,
        "user": session.get("zabbix_user"),
    })


@app.route("/api/ups/zabbix/disconnect", methods=["POST"])
def api_ups_zabbix_disconnect():
    session.pop("zabbix_api_url", None)
    session.pop("zabbix_user", None)
    session.pop("zabbix_pass", None)
    return jsonify({"connected": False})


@app.route("/api/ups/zabbix/hosts")
def api_ups_zabbix_hosts():
    api, err = _zabbix_from_session()
    if err:
        return jsonify({"error": err}), 401
    try:
        hosts = api.get_hosts()
        ups_hosts = []
        for h in hosts:
            name = (h.get("name", "") + " " + h.get("host", "")).lower()
            templates = [t.get("name", "") for t in h.get("parentTemplates", [])]
            tnames = " ".join(templates).lower()
            if "ups" in name or "ups" in tnames:
                ups_hosts.append({
                    "hostid": h["hostid"],
                    "host": h["host"],
                    "name": h.get("name", ""),
                    "status": h.get("status"),
                    "templates": [t.get("name", "") for t in h.get("parentTemplates", [])],
                    "items": [{"name": i.get("name", ""), "key_": i.get("key_", ""), "lastvalue": i.get("lastvalue", "N/A"), "units": i.get("units", "")} for i in h.get("items", [])],
                })
        return jsonify({"hosts": ups_hosts, "total": len(ups_hosts)})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/ups/zabbix/alerts")
def api_ups_zabbix_alerts():
    api, err = _zabbix_from_session()
    if err:
        return jsonify({"error": err}), 401
    try:
        n = get_notificaciones(api, limit=20)
        if isinstance(n, dict) and "error" in n:
            return jsonify({"error": n["error"]}), 500
        return jsonify({"alerts": n, "total": len(n)})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ─── INICIO ───────────────────────────────────────────────────

if __name__ == "__main__":
    print("🌐 TechBot Web App corriendo en http://localhost:5000")
    app.run(host="0.0.0.0", port=5000, debug=True, threaded=True)
