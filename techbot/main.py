#!/usr/bin/env python3
import os
import json
import sys
import inspect
from datetime import datetime

# Asegura que el directorio raíz del proyecto esté en sys.path
_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)


BANNER = """
╔══════════════════════════════════════════════╗
║           TECHBOT - Asistente Técnico        ║
║     Redes · Sistemas · Seguridad · CCTV      ║
╚══════════════════════════════════════════════╝
"""


def clear():
    os.system("cls" if os.name == "nt" else "clear")


def pausa():
    input("\n  Presiona Enter para volver...")


def cabecera(titulo):
    print(f"\n{'='*56}")
    print(f"  {titulo}")
    print(f"{'='*56}")


def _contar(data):
    if isinstance(data, dict):
        return sum(_contar(v) for v in data.values())
    if isinstance(data, list):
        return len(data)
    return 0


def _mostrar_comandos(data):
    if isinstance(data, dict):
        for subcat, cmds in data.items():
            print(f"\n    ── {subcat} ──")
            for cmd, desc in cmds:
                print(f"    {cmd:<45} {desc}")
    elif isinstance(data, list):
        for cmd, desc in data:
            print(f"    {cmd:<45} {desc}")


def buscar_en(data, q):
    encontrados = 0
    if isinstance(data, dict):
        for cat, cmds in data.items():
            buscar_en(cmds, q)
        return
    if isinstance(data, list):
        for cmd, desc in data:
            if q in cmd.lower() or q in desc.lower():
                print(f"    {cmd:<45} {desc}")
                encontrados += 1
    if encontrados == 0:
        print("    Sin resultados")


# ─── MENÚ PRINCIPAL ───────────────────────────────────────────

def _cargar_conteos():
    from techbot.console_commands import CONSOLE_COMMANDS
    from techbot.commands.cisco_commands import CISCO_COMMANDS
    from techbot.commands.mikrotik_commands import MIKROTIK_COMMANDS
    from techbot.commands.fortinet_commands import FORTINET_COMMANDS
    from techbot.commands.linux_commands import LINUX_COMMANDS
    from techbot.commands.windows_commands import WINDOWS_COMMANDS
    return {
        "B": ("Comandos Cisco", _contar(CISCO_COMMANDS)),
        "C": ("Comandos MikroTik", _contar(MIKROTIK_COMMANDS)),
        "D": ("Comandos Fortinet", _contar(FORTINET_COMMANDS)),
        "E": ("Comandos Linux", _contar(LINUX_COMMANDS)),
        "F": ("Comandos Windows", _contar(WINDOWS_COMMANDS)),
        "2": ("Comandos de Consola", _contar(CONSOLE_COMMANDS)),
    }


def menu_principal():
    clear()
    print(BANNER)
    print(f"  Fecha: {datetime.now().strftime('%d/%m/%Y %H:%M')}")
    print(f"{'─'*56}")
    print(f"  [1]  Scripts Python")
    print(f"  [2]  Comandos de Consola (473)")
    print(f"  [3]  Calculadoras Técnicas")
    print(f"  [4]  Protocolos de Red")
    print(f"  [5]  Puertos Comunes (600+)")
    print(f"  [6]  Escáner de Red")
    print(f"  [7]  SNMP")
    print(f"  [8]  IPAM")
    print(f"  [9]  APIs CCTV")
    print(f"  [A]  Control de Acceso")
    print(f"  [B]  Comandos Cisco (151)")
    print(f"  [C]  Comandos MikroTik (122)")
    print(f"  [D]  Comandos Fortinet (125)")
    print(f"  [E]  Comandos Linux (397)")
    print(f"  [F]  Comandos Windows (265)")
    print(f"  [G]  Diagnóstico")
    print(f"  [H]  UPS - Monitoreo y Gestión")
    print(f"  {'─'*56}")
    print(f"  Total: ~1533 comandos  |  [0] Salir")
    print(f"{'─'*56}")
    return input("  Opción: ").strip().upper()


# ─── SCRIPTS PYTHON EJECUTABLES ──────────────────────────────

SCRIPTS_MENU = [
    ("1", "Red"),
    ("2", "Sistema"),
    ("0", "Volver"),
]


def _menu_ver_script(titulo, ruta_archivo, modulo):
    import linecache
    mod = __import__(f"techbot.scripts.{modulo}", fromlist=["*"])
    nombre_mod = f"techbot.scripts.{modulo}"
    funciones = sorted([n for n, o in vars(mod).items()
                        if not n.startswith("_") and getattr(o, '__module__', None) == nombre_mod])
    with open(ruta_archivo) as f:
        codigo_completo = f.read()
    while True:
        clear()
        cabecera(f"SCRIPTS - {titulo}")
        print(f"  Total: {len(funciones)} funciones  |  Archivo: {ruta_archivo.split('/')[-1]}")
        print(f"{'─'*56}")
        for i, fn in enumerate(funciones, 1):
            sig = ""
            try:
                sig = str(inspect.signature(getattr(mod, fn)))
            except:
                pass
            print(f"  [{i:>2}] {fn}{sig}")
        print(f"  [a] Ver archivo completo")
        print(f"  [v] Volver")
        opc = input("\n  Opción: ").strip()
        if opc == "v":
            break
        if opc == "a":
            print(f"\n{'='*56}")
            print(f"  COMPLETO: {ruta_archivo.split('/')[-1]}")
            print(f"{'='*56}")
            for i, line in enumerate(codigo_completo.split("\n"), 1):
                print(f"  {i:>4} {line}")
            print(f"{'─'*56}")
            print(f"  Total: {len(codigo_completo.split(chr(10)))} líneas")
            pausa()
            continue
        if opc.isdigit():
            idx = int(opc) - 1
            if 0 <= idx < len(funciones):
                fn_name = funciones[idx]
                fn = getattr(mod, fn_name)
                try:
                    src = inspect.getsource(fn)
                    print(f"\n{'='*56}")
                    print(f"  def {fn_name}{inspect.signature(fn)}")
                    print(f"{'='*56}")
                    for i, line in enumerate(src.split("\n"), 1):
                        print(f"  {i:>4} {line}")
                    print(f"{'─'*56}")
                    print(f"  {len(src.split(chr(10)))} líneas")
                except Exception as e:
                    print(f"  Error al obtener código: {e}")
                pausa()


def menu_scripts():
    import techbot.scripts.network_scripts
    import techbot.scripts.system_scripts
    net_path = techbot.scripts.network_scripts.__file__
    sys_path = techbot.scripts.system_scripts.__file__
    while True:
        clear()
        cabecera("SCRIPTS PYTHON")
        print("  [1] Scripts de Red")
        print("  [2] Scripts de Sistema")
        print("  [0] Volver")
        opc = input("  Opción: ").strip()
        if opc == "0":
            break
        if opc == "1":
            _menu_ver_script("RED", net_path, "network_scripts")
        elif opc == "2":
            _menu_ver_script("SISTEMA", sys_path, "system_scripts")


# ─── COMANDOS DE CONSOLA ──────────────────────────────────────

def menu_comandos():
    from techbot.console_commands import CONSOLE_COMMANDS
    while True:
        clear()
        cabecera("COMANDOS DE CONSOLA (473)")
        categorias = list(CONSOLE_COMMANDS.keys())
        for i, c in enumerate(categorias, 1):
            total = _contar(CONSOLE_COMMANDS[c])
            print(f"  [{i}] {c} ({total})")
        print(f"  [b] Buscar")
        print(f"  [v] Volver")
        opc = input("\n  Opción: ").strip()
        if opc == "v":
            break
        if opc == "b":
            q = input("  Buscar: ").strip().lower()
            encontrados = 0
            for cat, data in CONSOLE_COMMANDS.items():
                if isinstance(data, dict):
                    for subcat, cmds in data.items():
                        for cmd, desc in cmds:
                            if q in cmd.lower() or q in desc.lower():
                                print(f"  [{cat}/{subcat}] {cmd:<45} {desc}")
                                encontrados += 1
                elif isinstance(data, list):
                    for cmd, desc in data:
                        if q in cmd.lower() or q in desc.lower():
                            print(f"  [{cat}] {cmd:<45} {desc}")
                            encontrados += 1
            print(f"  ({encontrados} resultados)")
            pausa()
            continue
        if opc.isdigit():
            idx = int(opc) - 1
            if 0 <= idx < len(categorias):
                cat = categorias[idx]
                print(f"\n  {cat} ({_contar(CONSOLE_COMMANDS[cat])} comandos):")
                _mostrar_comandos(CONSOLE_COMMANDS[cat])
                pausa()


# ─── CALCULADORAS ─────────────────────────────────────────────

def menu_calculadoras():
    from techbot.calculators.network_calc import subnet_calc, cidr_to_mask, mask_to_cidr, bandwidth_calc, transfer_time
    from techbot.calculators.conversions import bytes_to_human, celsius_to_fahrenheit, dbm_to_mw
    from techbot.calculators.electrical_calc import ohms_law_v, voltage_divider, battery_capacity, solar_panel_required
    while True:
        clear()
        cabecera("CALCULADORAS TÉCNICAS")
        print("""
  [1] Calculadora de Subred     subnet_calc(ip, cidr)
  [2] CIDR a Máscara            cidr_to_mask(cidr)
  [3] Máscara a CIDR            mask_to_cidr(mask)
  [4] Ancho de Banda            bandwidth_calc(mbps, min)
  [5] Tiempo Transferencia      transfer_time(archivo_mb, vel_mbps)
  [6] Bytes a formato legible   bytes_to_human(bytes)
  [7] Celsius a Fahrenheit      celsius_to_fahrenheit(c)
  [8] dBm a mW                  dbm_to_mw(dbm)
  [9] Ley de Ohm (V=I*R)        ohms_law_v(i, r)
  [A] Divisor de Voltaje       voltage_divider(vin, r1, r2)
  [B] Capacidad de Batería     battery_capacity(w, h, v)
  [C] Paneles Solares          solar_panel_required(kwh, sol_h)
  [0] Volver
        """)
        opc = input("  Opción: ").strip().upper()
        if opc == "0":
            break
        try:
            if opc == "1":
                ip = input("  IP: ")
                c = int(input("  CIDR: "))
                r = subnet_calc(ip, c)
                print(f"\n  Red: {r['network']}/{r['cidr']}")
                print(f"  Máscara: {r['netmask']}")
                print(f"  Broadcast: {r['broadcast']}")
                print(f"  Hosts: {r['usable_hosts']}")
                print(f"  Rango: {r['first_ip']} - {r['last_ip']}")
            elif opc == "2":
                print(f"  Máscara: {cidr_to_mask(int(input('CIDR: ')))}")
            elif opc == "3":
                print(f"  CIDR: /{mask_to_cidr(input('Máscara: '))}")
            elif opc == "4":
                r = bandwidth_calc(float(input("Mbps: ")), float(input("Minutos: ")))
                print(f"  Datos: {bytes_to_human(r['bytes'])}")
            elif opc == "5":
                r = transfer_time(float(input("Tamaño (MB): ")), float(input("Velocidad (Mbps): ")))
                print(f"  Tiempo: {r['seconds']:.1f}s ({r['minutes']:.1f} min)")
            elif opc == "6":
                print(f"  {bytes_to_human(float(input('Bytes: ')))}")
            elif opc == "7":
                print(f"  {celsius_to_fahrenheit(float(input('°C: '))):.1f} °F")
            elif opc == "8":
                print(f"  {dbm_to_mw(float(input('dBm: '))):.2f} mW")
            elif opc == "9":
                print(f"  Voltaje: {ohms_law_v(float(input('Corriente (A): ')), float(input('Resistencia (Ω): ')))} V")
            elif opc == "A":
                r = voltage_divider(float(input("Vin: ")), float(input("R1 (Ω): ")), float(input("R2 (Ω): ")))
                print(f"  Vout: {r} V")
            elif opc == "B":
                r = battery_capacity(float(input("Carga (W): ")), float(input("Horas: ")), float(input("Voltaje: ")))
                print(f"  Capacidad: {r['ah']:.1f} Ah (con DoD 80%: {r['ah_adjusted']:.1f} Ah)")
            elif opc == "C":
                print(f"  Paneles necesarios: {solar_panel_required(float(input('Consumo (kWh/día): ')), float(input('Horas sol: ')))}")
        except Exception as e:
            print(f"  Error: {e}")
        pausa()


# ─── PROTOCOLOS ───────────────────────────────────────────────

def menu_protocolos():
    from techbot.protocols.protocols_db import list_protocols, get_protocol, search_protocols
    while True:
        clear()
        cabecera("PROTOCOLOS DE RED")
        print("\n  Protocolos disponibles:")
        for p in list_protocols():
            print(f"    - {p}")
        q = input("\n  Buscar protocolo (Enter para volver): ").strip()
        if not q:
            break
        p = get_protocol(q)
        if p:
            print(f"\n  {p['name']}")
            print(f"  Puerto: {p['port']}")
            print(f"  Transporte: {p['transport']}")
            print(f"  Capa OSI: {p['layer']}")
            print(f"  {p['description']}")
        else:
            r = search_protocols(q)
            if r:
                print(f"\n  Resultados ({len(r)}):")
                for n, i in r.items():
                    print(f"    {n:<15} {i['name']}")
            else:
                print("  No encontrado.")
        pausa()


# ─── PUERTOS ──────────────────────────────────────────────────

def menu_puertos():
    from techbot.protocols.ports_db import COMMON_PORTS, get_port_service, search_ports
    while True:
        clear()
        cabecera("PUERTOS COMUNES (600+)")
        print("\n  Ejemplos:")
        for p in [20, 21, 22, 23, 25, 53, 67, 80, 110, 123, 143, 161, 443, 445, 554, 3389, 8080, 8443]:
            print(f"    {p:<5} {COMMON_PORTS[p]}")
        q = input("\n  Buscar puerto (número o servicio, Enter=volver): ").strip()
        if not q:
            break
        try:
            print(f"  Puerto {q}: {get_port_service(int(q))}")
        except ValueError:
            r = search_ports(q)
            if r:
                print(f"  ({len(r)} resultados)")
                for p, s in sorted(r.items())[:30]:
                    print(f"    {p:>5}: {s}")
                if len(r) > 30:
                    print(f"  ... y {len(r)-30} más")
            else:
                print("  No encontrado.")
        pausa()


# ─── ESCÁNER DE RED ──────────────────────────────────────────

def menu_escaner():
    from techbot.scanner import quick_scan, discover_hosts, ping_host, os_detection, traceroute, scan_cctv, scan_access_control
    while True:
        clear()
        cabecera("ESCÁNER DE RED")
        print("""
  [1] Ping + Detección de SO      ping_host() + os_detection()
  [2] Escaneo Rápido (60 puertos) quick_scan()
  [3] Escaneo CCTV (18 puertos)   scan_cctv()
  [4] Escaneo Ctrl.Acceso (10 p.) scan_access_control()
  [5] Descubrir Hosts en subred   discover_hosts()
  [6] Traceroute                  traceroute()
  [0] Volver
        """)
        opc = input("  Opción: ").strip()
        if opc == "0":
            break
        host = input("  Host/IP: ").strip()
        if not host:
            continue
        try:
            if opc == "1":
                vivo = ping_host(host)
                so = os_detection(host) if vivo else "N/A"
                print(f"\n  Host: {host}")
                print(f"  Responde: {'✅ SÍ' if vivo else '❌ NO'}")
                print(f"  SO detectado: {so}")
            elif opc == "2":
                r = quick_scan(host)
                so = os_detection(host)
                print(f"\n  Host: {host}  |  SO: {so}")
                print(f"  Puertos abiertos: {len(r)}")
                for p in r:
                    print(f"    {p['port']:<5} {p['service']}")
            elif opc == "3":
                r = scan_cctv(host)
                print(f"\n  📷 Dispositivo CCTV: {host}")
                print(f"  Puertos CCTV encontrados: {len(r)}")
                for p in r:
                    print(f"    {p['port']:<5} {p['service']:<20} {p.get('device_type','')}")
                    if p.get("banner_preview"):
                        print(f"          Banner: {p['banner_preview'][:60]}")
            elif opc == "4":
                r = scan_access_control(host)
                print(f"\n  🚪 Control de Acceso: {host}")
                print(f"  Puertos encontrados: {len(r)}")
                for p in r:
                    print(f"    {p['port']:<5} {p['service']:<20} {'✅ AC' if p.get('is_access_control') else ''}")
            elif opc == "5":
                r = discover_hosts(host)
                print(f"\n  Hosts activos en {host}: {len(r)}")
                for h in r:
                    print(f"    {h}")
            elif opc == "6":
                r = traceroute(host)
                print(f"\n  Traceroute a {host}:")
                for h in r:
                    print(f"    {h['hop']:>2}. {h['ip']}")
        except Exception as e:
            print(f"  Error: {e}")
        pausa()


# ─── SNMP ─────────────────────────────────────────────────────

def menu_snmp():
    from techbot.snmp import snmp_get, snmp_walk, get_system_info, detect_vendor, snmp_check, get_interfaces, detect_device_type
    while True:
        clear()
        cabecera("SNMP")
        host = input("  Host (Enter para volver): ").strip()
        if not host:
            break
        comm = input("  Community [public]: ").strip() or "public"
        try:
            print("\n  Verificando acceso SNMP...")
            if not snmp_check(host, comm):
                print("  ❌ No se puede acceder por SNMP")
                pausa()
                continue
            vend = detect_vendor(host, comm)
            tipo = detect_device_type(host, comm)
            print(f"  Fabricante: {vend}")
            print(f"  Tipo: {tipo['type']} ({tipo['vendor']})")
            print("\n  [1] Info del sistema")
            print("  [2] Interfaces")
            print("  [3] Walk completo")
            opc = input("  Opción: ").strip()
            if opc == "1":
                info = get_system_info(host, comm)
                for k, v in info.items():
                    print(f"    {k}: {v}")
            elif opc == "2":
                ifaces = get_interfaces(host, comm)
                for i in ifaces:
                    print(f"    {i['index']:>2}. {i['description']:<25} {i['status']:<5} {i['speed']}")
            elif opc == "3":
                oid = input("  OID inicial [1.3.6.1.2.1.1]: ").strip() or "1.3.6.1.2.1.1"
                r = snmp_walk(host, comm, oid)
                for k, v in list(r.items())[:40]:
                    print(f"    {k} = {v}")
                if len(r) > 40:
                    print(f"  ... y {len(r)-40} más")
        except Exception as e:
            print(f"  Error: {e}")
        pausa()


# ─── IPAM ─────────────────────────────────────────────────────

def menu_ipam():
    from techbot.ipam import add_network, list_networks, get_network, add_reservation, list_reservations, get_available_ips, get_stats, add_vlan, list_vlans
    while True:
        clear()
        cabecera("IPAM - GESTIÓN DE IPs")
        stats = get_stats()
        print(f"\n  📊 Estadísticas:")
        print(f"     Redes: {stats['networks']}  |  Reservas: {stats['reservations']}")
        print(f"     DHCP: {stats['dhcp_scopes']}  |  DNS: {stats['dns_records']}  |  VLANs: {stats['vlans']}")
        print(f"     Uso: {stats['usage_percent']}% ({stats['used_ips']}/{stats['total_capacity']} IPs)")
        print("""
  [1] Listar redes
  [2] Agregar red
  [3] Ver detalle de red
  [4] Listar reservaciones
  [5] Agregar reservación
  [6] Ver IPs disponibles
  [7] Listar VLANs
  [8] Agregar VLAN
  [0] Volver
        """)
        opc = input("  Opción: ").strip()
        if opc == "0":
            break
        try:
            if opc == "1":
                for n in list_networks():
                    print(f"    {n['network']:<20} {n.get('description',''):<25} {n['used_hosts']}/{n['total_hosts']} usado")
            elif opc == "2":
                r = add_network(input("Red (CIDR): "), input("Descripción: "), input("Sitio: "))
                print(f"  {'✅' if r.get('success') else '❌'} {r.get('network', r.get('error',''))}")
            elif opc == "3":
                net = get_network(input("Red: "))
                if "error" in net:
                    print(f"  ❌ {net['error']}")
                else:
                    print(f"  {net['network']} - {net.get('description','')}")
                    print(f"  Gateway: {net.get('gateway','-')}  Sitio: {net.get('site','-')}")
                    print(f"  Uso: {net['used_hosts']}/{net['total_hosts']}")
                    if net.get("reservations"):
                        for r in net["reservations"]:
                            print(f"    {r['ip']:<16} {r['hostname']:<20} {r.get('mac','')}")
            elif opc == "4":
                for r in list_reservations(network_str=input("Red (opcional): ") or None):
                    print(f"    {r['ip']:<16} {r['hostname']:<20} {r.get('mac','')}")
            elif opc == "5":
                r = add_reservation(input("IP: "), input("Hostname: "), input("MAC: "), input("Descripción: "))
                print(f"  {'✅' if r.get('success') else '❌'} {r.get('reservation', r.get('error',''))}")
            elif opc == "6":
                for ip in get_available_ips(input("Red: "), count=20):
                    print(f"    {ip}")
            elif opc == "7":
                for v in list_vlans():
                    print(f"    VLAN {v['vlan_id']:<5} {v['name']:<20} {v.get('network','')}")
            elif opc == "8":
                r = add_vlan(int(input("VLAN ID: ")), input("Nombre: "), input("Red: "), input("Descripción: "))
                msg = r.get("vlan", {}).get("vlan_id", r.get("error", ""))
                print(f"  {'✅' if r.get('success') else '❌'} VLAN {msg}")
        except Exception as e:
            print(f"  Error: {e}")
        pausa()


# ─── APIs CCTV ────────────────────────────────────────────────

def _mostrar_api_info(nombre, data):
    print(f"\n  📡 {nombre}")
    for k, v in data.items():
        if k in ("Puertos",):
            print(f"  Puertos: {v}")
        elif isinstance(v, list) and v and isinstance(v[0], (list, tuple)):
            print(f"  {k} ({len(v)} endpoints):")
            for ruta, desc in v:
                print(f"    {ruta:<55} {desc}")
        elif isinstance(v, list):
            print(f"  {k}: {', '.join(str(x) for x in v)}")
        elif isinstance(v, dict):
            print(f"  {k}: {v}")


def menu_apis_cctv():
    from techbot.apis.hikvision_api import HIKVISION_API, HikvisionClient
    from techbot.apis.dahua_api import DAHUA_API, DahuaClient
    from techbot.apis.zkteco_api import ZKTECO_API, ZKTecoClient
    while True:
        clear()
        cabecera("APIs CCTV")
        print("""
  [1] Hikvision (ISAPI)
  [2] Dahua (CGI)
  [3] ZKTeco (SDK/SOAP/REST)
  [0] Volver
        """)
        opc = input("  Opción: ").strip()
        if opc == "0":
            break
        data = {"1": (HIKVISION_API, HikvisionClient, "HIKVISION"),
                "2": (DAHUA_API, DahuaClient, "DAHUA"),
                "3": (ZKTECO_API, ZKTecoClient, "ZKTECO")}.get(opc)
        if not data:
            continue
        api_data, Cliente, nombre = data
        _mostrar_api_info(nombre, api_data)
        if input("\n  ¿Conectar a dispositivo real? (s/N): ").strip().lower() == "s":
            try:
                host = input("  IP: ")
                puerto = int(input("  Puerto [80]: ") or 80)
                user = input("  Usuario [admin]: ") or "admin"
                pw = input("  Password: ")
                cli = Cliente(host, puerto, user, pw)
                if cli.is_online():
                    print("  ✅ Conectado")
                    info = cli.get_device_info() if nombre != "DAHUA" else cli.get_system_info()
                    if isinstance(info, dict):
                        for k, v in info.items():
                            print(f"    {k}: {v}")
                else:
                    print("  ❌ No se pudo conectar")
            except Exception as e:
                print(f"  Error: {e}")
        pausa()


# ─── CONTROL DE ACCESO ────────────────────────────────────────

def menu_ctrl_acceso():
    from techbot.access_control import create_ac_client, ACCESS_CONTROL_INFO
    while True:
        clear()
        cabecera("CONTROL DE ACCESO")
        print("""
  [1] Hikvision Access Control
  [2] Dahua Access Control
  [3] ZKTeco Access Control
  [0] Volver
        """)
        opc = input("  Opción: ").strip()
        if opc == "0":
            break
        vendor_map = {"1": "hikvision", "2": "dahua", "3": "zkteco"}
        vendor = vendor_map.get(opc)
        if not vendor:
            continue
        info = ACCESS_CONTROL_INFO.get(vendor, {})
        print(f"\n  {info.get('name', vendor)}")
        print(f"  Protocolo: {info.get('protocol', '-')}")
        print(f"  Puertos: {info.get('ports', [])}")
        print(f"  Funciones: {', '.join(info.get('features', []))}")
        if input("\n  ¿Conectar a dispositivo? (s/N): ").strip().lower() == "s":
            host = input("  IP: ")
            puerto = int(input("  Puerto [80]: ") or 80)
            user = input("  Usuario [admin]: ") or "admin"
            pw = input("  Password: ")
            try:
                ac = create_ac_client(vendor, host, puerto, user, pw)
                if ac.connected:
                    print("  ✅ Conectado")
                    while True:
                        print("\n  Opciones:")
                        print("  [1] Abrir puerta")
                        print("  [2] Cerrar puerta")
                        print("  [3] Mantener puerta")
                        print("  [4] Estado de puerta")
                        print("  [5] Listar usuarios")
                        print("  [6] Eventos")
                        print("  [0] Desconectar")
                        c = input("  Opción: ").strip()
                        if c == "0":
                            break
                        acc = {"1": "open_door", "2": "close_door", "3": "hold_door",
                               "4": "get_door_status", "5": "list_users", "6": "get_events"}
                        if c in acc:
                            try:
                                fn = getattr(ac, acc[c])
                                res = fn(seconds=int(input("Segundos: ") or 5)) if c == "3" else fn()
                                print(json.dumps(res, indent=4))
                            except Exception as e:
                                print(f"  Error: {e}")
                else:
                    print("  ❌ No se pudo conectar")
            except Exception as e:
                print(f"  Error: {e}")
        pausa()


# ─── COMANDOS POR FABRICANTE ─────────────────────────────────

def menu_comandos_fabricante(titulo, total, modulo, attr):
    try:
        m = __import__(f"techbot.commands.{modulo}", fromlist=[attr])
        data = getattr(m, attr)
    except ImportError:
        print(f"  Módulo {modulo} no disponible")
        pausa()
        return

    while True:
        clear()
        cabecera(f"{titulo} ({total})")
        categorias = list(data.keys())
        for i, c in enumerate(categorias, 1):
            cmds = data[c]
            t = _contar(cmds)
            print(f"  [{i}] {c} ({t})")
        print(f"  [b] Buscar en todos")
        print(f"  [v] Volver")
        opc = input("\n  Opción: ").strip()
        if opc == "v":
            break
        if opc == "b":
            q = input("  Buscar: ").strip().lower()
            enc = 0
            for cat, cmds in data.items():
                if isinstance(cmds, dict):
                    for sub, items in cmds.items():
                        for cmd, desc in items:
                            if q in cmd.lower() or q in desc.lower():
                                print(f"  [{sub}] {cmd:<45} {desc}")
                                enc += 1
                elif isinstance(cmds, list):
                    for cmd, desc in cmds:
                        if q in cmd.lower() or q in desc.lower():
                            print(f"  {cmd:<45} {desc}")
                            enc += 1
            print(f"  ({enc} resultados)")
            pausa()
            continue
        if opc.isdigit():
            idx = int(opc) - 1
            if 0 <= idx < len(categorias):
                cat = categorias[idx]
                print(f"\n  {cat} ({_contar(data[cat])} comandos):")
                _mostrar_comandos(data[cat])
                pausa()


# ─── DIAGNÓSTICO ──────────────────────────────────────────────

def menu_diagnostico():
    from techbot.diagnostics.procedures import DIAGNOSTIC_PROCEDURES
    while True:
        clear()
        cabecera("PROCEDIMIENTOS DE DIAGNÓSTICO")
        procs = list(DIAGNOSTIC_PROCEDURES.keys())
        for i, p in enumerate(procs, 1):
            print(f"  [{i}] {p}")
        print(f"  [v] Volver")
        opc = input("\n  Opción: ").strip()
        if opc == "v":
            break
        if opc.isdigit():
            idx = int(opc) - 1
            if 0 <= idx < len(procs):
                key = procs[idx]
                print(f"\n{'='*56}")
                print(f"  {key}")
                print(f"{'='*56}")
                print(DIAGNOSTIC_PROCEDURES[key])
                pausa()


# ─── UPS ──────────────────────────────────────────────────────

def menu_ups():
    from techbot.ups import NUTClient, UPSSNMPClient, DIAGNOSTIC_PROCEDURE, detect_ups, check_nut_available
    while True:
        clear()
        cabecera("UPS - MONITOREO Y GESTIÓN")
        print("""
  [1] Estado via SNMP (UPS-MIB)
  [2] Estado via NUT (Network UPS Tools)
  [3] Detectar UPS en un host
  [4] Diagnóstico y resolución de problemas
  [0] Volver
        """)
        opc = input("  Opción: ").strip()
        if opc == "0":
            break
        if opc == "1":
            host = input("  Host: ").strip()
            if not host:
                continue
            comm = input("  Community [public]: ").strip() or "public"
            try:
                cli = UPSSNMPClient(host, comm)
                if not cli.check_access():
                    print("  ❌ SNMP no accesible")
                else:
                    r = cli.get_summary()
                    for k, v in r.items():
                        print(f"    {k}: {v}")
            except Exception as e:
                print(f"  Error: {e}")
            pausa()
        elif opc == "2":
            if not check_nut_available():
                print("  ❌ NUT (upsc) no está instalado en este sistema")
                print("     Instalá: sudo apt install nut-client (Linux)")
                pausa()
                continue
            dest = input("  UPS@host [localhost]: ").strip()
            ups_name = ""
            host = "localhost"
            if "@" in dest:
                ups_name, host = dest.split("@", 1)
            elif dest:
                ups_name = dest
            try:
                cli = NUTClient(ups_name, host)
                if not cli.is_available():
                    print("  ❌ NUT no está disponible")
                elif ups_name:
                    r = cli.get_summary()
                    for k, v in r.items():
                        print(f"    {k}: {v}")
                else:
                    lista = cli.list_ups()
                    if lista:
                        print(f"\n  UPS disponibles: {', '.join(lista)}")
                        print("  Usá: UPS@host (ej: APC@192.168.1.50)")
                    else:
                        print("  No se encontraron UPS. Verificá NUT.")
            except Exception as e:
                print(f"  Error: {e}")
            pausa()
        elif opc == "3":
            host = input("  Host: ").strip()
            if not host:
                continue
            comm = input("  Community [public]: ").strip() or "public"
            try:
                r = detect_ups(host, comm)
                for k, v in r.items():
                    print(f"    {k}: {v}")
            except Exception as e:
                print(f"  Error: {e}")
            pausa()
        elif opc == "4":
            print(DIAGNOSTIC_PROCEDURE)
            pausa()


# ─── MAIN ─────────────────────────────────────────────────────

def main():
    accion = {
        "1": menu_scripts,
        "2": menu_comandos,
        "3": menu_calculadoras,
        "4": menu_protocolos,
        "5": menu_puertos,
        "6": menu_escaner,
        "7": menu_snmp,
        "8": menu_ipam,
        "9": menu_apis_cctv,
        "A": menu_ctrl_acceso,
        "B": lambda: menu_comandos_fabricante("COMANDOS CISCO IOS", 151, "cisco_commands", "CISCO_COMMANDS"),
        "C": lambda: menu_comandos_fabricante("COMANDOS MIKROTIK RouterOS", 122, "mikrotik_commands", "MIKROTIK_COMMANDS"),
        "D": lambda: menu_comandos_fabricante("COMANDOS FORTINET FortiOS", 125, "fortinet_commands", "FORTINET_COMMANDS"),
        "E": lambda: menu_comandos_fabricante("COMANDOS LINUX", 397, "linux_commands", "LINUX_COMMANDS"),
        "F": lambda: menu_comandos_fabricante("COMANDOS WINDOWS", 265, "windows_commands", "WINDOWS_COMMANDS"),
        "G": menu_diagnostico,
        "H": menu_ups,
    }
    while True:
        opc = menu_principal()
        if opc == "0":
            clear()
            print("\n  ¡Hasta luego!\n")
            break
        fn = accion.get(opc)
        if fn:
            fn()
        else:
            print("\n  Opción no válida")
            pausa()


if __name__ == "__main__":
    main()
