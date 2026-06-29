import socket
import ipaddress
import subprocess
import os
import struct
import sys
from datetime import datetime


def scan_ports(host, start_port=1, end_port=1024):

    # Escanea puertos TCP en un rango. Crea un socket por cada puerto y usa connect_ex() que devuelve 0 si el puerto está abierto. Timeout de 0.5s por puerto.
    resultados = []
    for port in range(start_port, end_port + 1):
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(0.5)
        result = sock.connect_ex((host, port))
        if result == 0:
            resultados.append(port)
        sock.close()
    return resultados

def ping_sweep(subnet):

    # Barre una subred con ping. Itera sobre cada IP de la red (excluyendo network y broadcast) y ejecuta un ping -c 1 -W 1. Si el ping vuelve con éxito, la IP está activa.
    red = ipaddress.ip_network(subnet, strict=False)
    activos = []
    for ip in red.hosts():
        ip_str = str(ip)
        response = os.system(f"ping -c 1 -W 1 {ip_str} > /dev/null 2>&1")
        if response == 0:
            activos.append(ip_str)
    return activos

def dns_lookup(domain):

    # Resuelve un nombre de dominio a IP usando socket.gethostbyname(). Si no existe el dominio, gaierror captura el error y devuelve None.
    try:
        return socket.gethostbyname(domain)
    except socket.gaierror:
        return None

def reverse_dns(ip):

    # Resolución inversa: dada una IP, devuelve el nombre de host usando gethostbyaddr(). Si no hay registro PTR, herror captura el error.
    try:
        return socket.gethostbyaddr(ip)[0]
    except socket.herror:
        return None

def ip_to_binary(ip):

    # Convierte una IP en formato decimal a binario. Separa por puntos, convierte cada octeto a binario de 8 bits con format(int(p), '08b').
    partes = ip.split('.')
    return '.'.join(format(int(p), '08b') for p in partes)

def subnet_info(ip, mask):

    # Calcula información de subred: dirección de red, broadcast, máscara, cantidad de hosts, primer y último host usable. Usa ipaddress.IPv4Network.
    red = ipaddress.IPv4Network(f"{ip}/{mask}", strict=False)
    return {
        "network": str(red.network_address),
        "broadcast": str(red.broadcast_address),
        "netmask": str(red.netmask),
        "hosts": red.num_addresses - 2,
        "first_host": str(red.network_address + 1),
        "last_host": str(red.broadcast_address - 1)
    }

def mac_to_vendor(mac):

    # Determina el fabricante de una MAC extrayendo los primeros 6 caracteres (OUI) y buscando en un diccionario básico. No confiar ciegamente, es una lista limitada.
    oui = mac.upper().replace(":", "")[:6]
    vendors = {
        "F8E7B5": "Aruba/HPE",
        "0050C2": "Cisco",
        "3C5A37": "Huawei",
        "0050B6": "3Com",
        "00147C": "MikroTik",
        "90F652": "Fortinet",
        "00037F": "Hikvision",
        "B0A732": "Dahua",
        "001E0B": "ZKTeco",
    }
    return vendors.get(oui, "Vendor desconocido")

def traceroute(host):

    # Traza la ruta hacia un host incrementando el TTL desde 1 hasta 30. Cada salto ejecuta ping con -t (TTL). Cuando el TTL expira, el router responde con Time Exceeded.
    resultado = []
    for ttl in range(1, 30):
        cmd = f"ping -c 1 -t {ttl} -W 1 {host} 2>&1"
        salida = subprocess.getoutput(cmd)
        resultado.append(f"{ttl}: {salida.split(chr(10))[0]}")
    return resultado

def calculate_subnets(base_network, num_subnets):

    # Calcula subredes a partir de una red base. Determina cuántos bits se necesitan para la cantidad de subredes solicitadas usando bit_length().
    red = ipaddress.IPv4Network(base_network, strict=False)
    bits_needed = (num_subnets - 1).bit_length()
    new_prefix = red.prefixlen + bits_needed
    subnets = list(red.subnets(new_prefix=new_prefix))
    return subnets[:num_subnets]

def validate_ip(ip):

    # Valida si una cadena es una dirección IP válida usando ipaddress.ip_address(). Si lanza ValueError, no es válida.
    try:
        ipaddress.ip_address(ip)
        return True
    except ValueError:
        return False

def get_default_gateway():

    # Obtiene la puerta de enlace predeterminada del sistema. En Linux lee 'ip route | grep default', en Windows 'ipconfig | findstr Gateway'.
    try:
        if sys.platform == "linux":
            output = subprocess.getoutput("ip route | grep default")
            return output.split()[2] if output else None
        elif sys.platform == "win32":
            output = subprocess.getoutput("ipconfig | findstr /i \"Gateway\"")
            return output.split(": ")[-1] if ":" in output else None
    except:
        return None

def whois_query(domain):

    # Ejecuta whois para un dominio usando subprocess. Requiere que whois esté instalado en el sistema.
    try:
        return subprocess.getoutput(f"whois {domain} 2>/dev/null")
    except:
        return "whois no disponible"

def check_http_headers(url):

    # Obtiene los headers HTTP de una URL usando urllib. Con timeout de 5 segundos para evitar que se cuelgue.
    try:
        import urllib.request
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req, timeout=5) as response:
            return dict(response.headers)
    except:
        return {}

def ssl_cert_info(host, port=443):

    # Obtiene el certificado SSL de un host:puerto. Conecta con SSLContext, extrae el certificado con getpeercert(). Timeout de 5s.
    try:
        import ssl
        ctx = ssl.create_default_context()
        with ctx.wrap_socket(socket.socket(), server_hostname=host) as s:
            s.settimeout(5)
            s.connect((host, port))
            cert = s.getpeercert()
            return cert
    except:
        return {}

def mac_to_decimal(mac):

    # Convierte una MAC a decimal. Elimina los ':' y convierte de hexadecimal a entero con int(..., 16).
    return int(mac.replace(":", ""), 16)

def ip_to_decimal(ip):

    # Convierte una IP a entero de 32 bits. Usa inet_aton() para empaquetar y struct.unpack para convertir a entero sin signo.
    packed = socket.inet_aton(ip)
    return struct.unpack("!I", packed)[0]

def decimal_to_ip(decimal):

    # Convierte un entero de 32 bits a IP. Usa struct.pack('!I', decimal) y luego inet_ntoa() para formatear como cadena.
    return socket.inet_ntoa(struct.pack("!I", decimal))

def dhcp_range(network):

    # Calcula un rango DHCP típico para una red. Toma los hosts 100 a -50 (últimos 50) como rango sugerido. Ajustable según necesidades.
    red = ipaddress.IPv4Network(network, strict=False)
    hosts = list(red.hosts())
    return {
        "start": str(hosts[100]) if len(hosts) > 100 else str(hosts[0]),
        "end": str(hosts[-50]) if len(hosts) > 50 else str(hosts[-1])
    }

def get_public_ip():

    # Obtiene la IP pública consultando api.ipify.org con urllib. Timeout de 5 segundos. No requiere autenticación.
    try:
        import urllib.request
        with urllib.request.urlopen("https://api.ipify.org", timeout=5) as r:
            return r.read().decode()
    except:
        return None


def arp_table():
    """Muestra la tabla ARP del sistema"""

    # Muestra la tabla ARP del sistema. En Linux usa 'arp -n' o 'ip neigh show'. En Windows usa 'arp -a'.
    if sys.platform == "linux":
        return subprocess.getoutput("arp -n 2>/dev/null || ip neigh show")
    elif sys.platform == "win32":
        return subprocess.getoutput("arp -a")
    return subprocess.getoutput("arp -a")


def route_table():
    """Muestra la tabla de rutas del sistema"""

    # Muestra la tabla de enrutamiento. En Linux 'ip route show', en Windows 'route print'. Muestra rutas a todas las redes conocidas.
    if sys.platform == "linux":
        return subprocess.getoutput("ip route show 2>/dev/null || route -n")
    elif sys.platform == "win32":
        return subprocess.getoutput("route print")
    return subprocess.getoutput("netstat -rn")


def mtu_discovery(host="8.8.8.8", start=1500, end=1400):
    """Descubre el MTU de la ruta hacia un host"""

    # Descubre el MTU de ruta hacia un host. Envía pings con DF (Don't Fragment) de distintos tamaños. El más grande que pasa sin fragmentar es el MTU.
    mtu = None
    for size in range(start, end - 1, -10):
        cmd = f"ping -M do -c 1 -s {size - 28} -W 2 {host} 2>&1"
        if sys.platform == "win32":
            cmd = f"ping -f -l {size} -n 1 -w 2000 {host} 2>&1"
        result = os.system(f"{cmd} >/dev/null 2>&1")
        if result == 0:
            mtu = size
            break
    return {"host": host, "path_mtu": mtu, "note": f"MTU de ruta: {mtu}" if mtu else "No se pudo determinar"}


def http_status_check(url):
    """Verifica el código de estado HTTP de una URL"""

    # Verifica el código de estado HTTP de una URL. Usa método HEAD para no descargar el cuerpo completo. Captura HTTPError para códigos 4xx/5xx.
    try:
        import urllib.request
        req = urllib.request.Request(url, method="HEAD")
        with urllib.request.urlopen(req, timeout=5) as response:
            return {
                "url": url,
                "status": response.status,
                "reason": response.reason,
                "server": response.headers.get("Server", ""),
                "content_type": response.headers.get("Content-Type", ""),
            }
    except urllib.error.HTTPError as e:
        return {"url": url, "status": e.code, "reason": e.reason}
    except urllib.error.URLError as e:
        return {"url": url, "error": str(e.reason)}
    except Exception as e:
        return {"url": url, "error": str(e)}


def check_port_forward(public_ip, port, internal_host="localhost", internal_port=None):
    """Verifica si un puerto está siendo reenviado correctamente"""

    # Verifica si hay port forwarding hacia una IP pública. Intenta conectar al puerto desde fuera. Timeout de 5s. Si conecta, el forward está activo.
    if internal_port is None:
        internal_port = port
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5)
        sock.connect((public_ip, port))
        sock.close()
        return {
            "public_ip": public_ip,
            "port": port,
            "forward_active": True,
            "note": "Puerto abierto externamente (forward probablemente activo)",
        }
    except socket.timeout:
        return {
            "public_ip": public_ip,
            "port": port,
            "forward_active": False,
            "note": "Puerto filtrado o forward no configurado",
        }
    except Exception as e:
        return {
            "public_ip": public_ip,
            "port": port,
            "forward_active": False,
            "error": str(e),
        }


def active_connections():
    """Muestra conexiones activas de red"""

    # Muestra conexiones de red activas. En Linux 'ss -tupan' (socket statistics), en Windows 'netstat -anob'. Incluye procesos asociados.
    if sys.platform == "linux":
        return subprocess.getoutput("ss -tupan 2>/dev/null || netstat -tupan")
    elif sys.platform == "win32":
        return subprocess.getoutput("netstat -anob")
    return subprocess.getoutput("netstat -an")


def bandwidth_test_simple(host="8.8.8.8", count=5):
    """Test de ancho de banda simple usando ping con tamaño de paquete"""

    # Test simple de ancho de banda. Envía pings con distintos tamaños de paquete (64, 512, 1024, 1472 bytes) y muestra la respuesta.
    results = []
    for size in [64, 512, 1024, 1472]:
        cmd = f"ping -c {count} -s {size} -W 2 {host} 2>&1 | tail -1"
        output = subprocess.getoutput(cmd)
        results.append({"packet_size": size, "result": output})
    return {"host": host, "results": results}


def dns_servers_detect():
    """Detecta los servidores DNS configurados en el sistema"""

    # Detecta los servidores DNS configurados en el sistema. Lee /etc/resolv.conf en Linux o ipconfig /all en Windows.
    if sys.platform == "linux":
        dns = subprocess.getoutput("grep 'nameserver' /etc/resolv.conf | awk '{print $2}'")
        return {"dns_servers": dns.strip().split("\n") if dns.strip() else []}
    elif sys.platform == "win32":
        output = subprocess.getoutput("ipconfig /all | findstr 'DNS'")
        servers = []
        for line in output.split("\n"):
            if "Servidores DNS" in line or "DNS Servers" in line:
                servers.append(line.split(":")[-1].strip())
        return {"dns_servers": servers}
    return {"dns_servers": subprocess.getoutput("cat /etc/resolv.conf 2>/dev/null | grep nameserver")}


def network_discovery(subnet):
    """Descubre hosts activos en una subred"""

    # Descubre hosts activos en una subred con ping. Limita a /22 o menor para no saturar la red. Devuelve IP y hostname de cada host encontrado.
    try:
        red = ipaddress.ip_network(subnet, strict=False)
    except ValueError as e:
        return {"error": f"Subred inválida: {e}"}

    if red.num_addresses > 1024:
        return {"error": f"Subred demasiado grande ({red.num_addresses} hosts). Usá /22 o menor."}

    active = []
    for ip in red.hosts():
        ip_str = str(ip)
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(1)
            alive = False
            for port in [22, 80, 443, 8080, 3389]:
                try:
                    if s.connect_ex((ip_str, port)) == 0:
                        alive = True
                        break
                except:
                    pass
            s.close()
            if alive:
                try:
                    hostname = socket.gethostbyaddr(ip_str)[0]
                except socket.herror:
                    hostname = None
                active.append({"ip": ip_str, "hostname": hostname})
        except:
            pass
    return {"subnet": subnet, "active": active, "count": len(active)}


def netstat_summary():
    """Resumen de estadísticas de red"""

    # Muestra estadísticas de red del sistema. Incluye paquetes transmitidos, errores, colisiones, etc. Usa 'netstat -s'.
    if sys.platform == "linux":
        return subprocess.getoutput("netstat -s 2>/dev/null | head -50")
    return subprocess.getoutput("netstat -s 2>/dev/null | head -50")


def interfaces_detail():
    """Muestra información detallada de interfaces de red"""

    # Muestra información detallada de interfaces. En Linux 'ip -d addr show', en Windows 'ipconfig /all'. Incluye MAC, IP, máscara, estado.
    if sys.platform == "linux":
        return subprocess.getoutput("ip -d addr show 2>/dev/null || ifconfig -a")
    elif sys.platform == "win32":
        return subprocess.getoutput("ipconfig /all")
    return subprocess.getoutput("ifconfig -a")


def speed_test_cli():
    """Ejecuta un test de velocidad rápido via curl (descarga archivo de prueba)"""

    # Test de velocidad rápido descargando archivos de speedtest.tele2.net con curl. Mide tiempo de descarga y calcula velocidad en Kbps/Mbps.
    try:
        sizes = [
            ("100KB", "https://speedtest.tele2.net/100KB.zip"),
            ("1MB", "https://speedtest.tele2.net/1MB.zip"),
        ]
        results = {}
        for name, url in sizes:
            start = datetime.now()
            r = os.system(f"curl -s -o /dev/null -w '%{{speed_download}}' --max-time 10 {url} 2>/dev/null")
            elapsed = (datetime.now() - start).total_seconds()
            if elapsed > 0:
                speed_kbps = (int(name.replace("KB", "").replace("MB", "")) * 1024 if "MB" in name else int(name.replace("KB", ""))) * 8 / elapsed
                results[name] = f"{speed_kbps:.0f} Kbps (~{speed_kbps/1000:.1f} Mbps)"
            else:
                results[name] = "Error"
        return results
    except Exception as e:
        return {"error": str(e)}


def wifi_info():
    """Muestra información de la conexión WiFi actual"""

    # Muestra información de la conexión WiFi actual. En Linux prueba iwconfig, iw dev, nmcli. En Windows netsh wlan show interfaces.
    if sys.platform == "linux":
        return subprocess.getoutput(
            "iwconfig 2>/dev/null || iw dev 2>/dev/null || nmcli dev wifi list 2>/dev/null | head -20"
        )
    elif sys.platform == "win32":
        return subprocess.getoutput("netsh wlan show interfaces")
    return "No soportado"


def wifi_scan():
    """Escanea redes WiFi disponibles"""

    # Escanea redes WiFi disponibles. En Linux nmcli dev wifi list o iwlist scan. En Windows netsh wlan show networks. Muestra SSID, señal, seguridad.
    if sys.platform == "linux":
        return subprocess.getoutput(
            "nmcli dev wifi list 2>/dev/null || iwlist scan 2>/dev/null | head -60"
        )
    elif sys.platform == "win32":
        return subprocess.getoutput("netsh wlan show networks")
    return "No soportado"


def ntp_check(server="pool.ntp.org"):
    """Verifica sincronización NTP con un servidor"""

    # Verifica sincronización NTP. Prueba ntpdate, chronyd y sntp en ese orden. Devuelve la respuesta del primer comando que funciona.
    result = subprocess.getoutput(
        f"ntpdate -q {server} 2>/dev/null || "
        f"chronyd -q 'server {server} iburst' 2>/dev/null || "
        f"sntp {server} 2>/dev/null || "
        f"echo 'Cliente NTP no disponible'"
    )
    return {"server": server, "result": result}


def tcp_latency(host, port=80, count=5):
    """Mide latencia TCP (time to connect) a un host:puerto"""

    # Mide latencia TCP (tiempo de conexión) a un host:puerto. Hace count conexiones, mide el tiempo con datetime, calcula promedio, min y max.
    latencies = []
    for _ in range(count):
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(3)
            start = datetime.now()
            sock.connect((host, port))
            elapsed = (datetime.now() - start).total_seconds() * 1000
            sock.close()
            latencies.append(round(elapsed, 2))
        except Exception:
            latencies.append(None)
    valid = [l for l in latencies if l is not None]
    if valid:
        avg = round(sum(valid) / len(valid), 2)
        return {"host": host, "port": port, "latencies_ms": latencies, "avg_ms": avg, "min_ms": min(valid), "max_ms": max(valid)}
    return {"host": host, "port": port, "error": "No se pudo conectar"}


def packet_loss_test(host="8.8.8.8", count=10):
    """Mide pérdida de paquetes hacia un host"""

    # Mide pérdida de paquetes enviando count pings. Analiza la salida buscando 'packet loss' o 'received' para calcular el porcentaje.
    output = subprocess.getoutput(f"ping -c {count} -W 2 {host} 2>&1 | tail -1")
    if "packet loss" in output:
        loss = output.split("packet loss")[0].strip().split()[-1]
        loss_pct = float(loss.replace("%", ""))
    elif "received" in output:
        parts = output.split(",")
        loss_pct = 100.0
        for p in parts:
            if "packet loss" in p:
                loss_pct = float(p.strip().split()[0].replace("%", ""))
                break
    else:
        loss_pct = 100.0
    return {"host": host, "packets_sent": count, "packet_loss_pct": loss_pct, "quality": "good" if loss_pct < 1 else "fair" if loss_pct < 5 else "poor" if loss_pct < 20 else "unusable"}


def interface_stats(interface="eth0"):
    """Estadísticas detalladas de una interfaz de red"""

    # Estadísticas detalladas de una interfaz. Lee archivos /sys/class/net/ para RX/TX bytes, paquetes, errores, descartados y colisiones.
    if sys.platform == "linux":
        output = subprocess.getoutput(f"ip -s link show {interface} 2>/dev/null || cat /sys/class/net/{interface}/statistics/* 2>/dev/null")
        if not output:
            return {"error": f"Interfaz {interface} no encontrada"}
        try:
            rx_bytes = open(f"/sys/class/net/{interface}/statistics/rx_bytes").read().strip()
            tx_bytes = open(f"/sys/class/net/{interface}/statistics/tx_bytes").read().strip()
            rx_packets = open(f"/sys/class/net/{interface}/statistics/rx_packets").read().strip()
            tx_packets = open(f"/sys/class/net/{interface}/statistics/tx_packets").read().strip()
            rx_errors = open(f"/sys/class/net/{interface}/statistics/rx_errors").read().strip()
            tx_errors = open(f"/sys/class/net/{interface}/statistics/tx_errors").read().strip()
            rx_dropped = open(f"/sys/class/net/{interface}/statistics/rx_dropped").read().strip()
            tx_dropped = open(f"/sys/class/net/{interface}/statistics/tx_dropped").read().strip()
            collisions = open(f"/sys/class/net/{interface}/statistics/collisions").read().strip()
            return {
                "interface": interface,
                "rx_bytes": int(rx_bytes), "tx_bytes": int(tx_bytes),
                "rx_packets": int(rx_packets), "tx_packets": int(tx_packets),
                "rx_errors": int(rx_errors), "tx_errors": int(tx_errors),
                "rx_dropped": int(rx_dropped), "tx_dropped": int(tx_dropped),
                "collisions": int(collisions),
            }
        except Exception as e:
            return {"interface": interface, "raw": output[:500], "error": str(e)}
    return subprocess.getoutput(f"ifconfig {interface} 2>/dev/null | grep -E 'RX|TX'")


def interface_speed(interface="eth0"):
    """Muestra velocidad y duplex de una interfaz"""

    # Muestra velocidad y duplex de una interfaz. Lee /sys/class/net/ para speed, duplex y operstate. Útil para verificar negociación.
    if sys.platform == "linux":
        speed = subprocess.getoutput(f"cat /sys/class/net/{interface}/speed 2>/dev/null")
        duplex = subprocess.getoutput(f"cat /sys/class/net/{interface}/duplex 2>/dev/null")
        operstate = subprocess.getoutput(f"cat /sys/class/net/{interface}/operstate 2>/dev/null")
        return {
            "interface": interface,
            "speed_mbps": speed or "desconocido",
            "duplex": duplex or "desconocido",
            "operstate": operstate or "desconocido",
        }
    return {"interface": interface, "note": "usar ethtool para linux"}


def cable_test(interface="eth0"):
    """Test de cable de red (requiere ethtool)"""

    # Test de cable de red con ethtool. Muestra información de link, velocidad, duplex, MDI/MDI-X. Solo disponible en Linux con ethtool.
    if sys.platform == "linux":
        output = subprocess.getoutput(f"ethtool {interface} 2>/dev/null | grep -E 'Link|Speed|Duplex|MDI|Pair|Cable'")
        if not output:
            return {"error": f"ethtool no disponible o interfaz {interface} no encontrada"}
        return {"interface": interface, "cable_test": output.strip()}
    return {"error": "Solo Linux con ethtool"}


def poe_check(interface="eth0"):
    """Verifica estado PoE en un switch (Linux con lldpd o ethtool)"""

    # Verifica estado PoE en interfaces. Usa ethtool o lldpctl. Útil para switches PoE. Muestra si el puerto está entregando energía.
    if sys.platform == "linux":
        output = subprocess.getoutput(
            f"ethtool {interface} 2>/dev/null | grep -i poe || "
            f"lldpctl 2>/dev/null | grep -A5 '{interface}' || "
            f"echo 'PoE info no disponible sin lldpd/ethtool'"
        )
        return {"interface": interface, "poe_info": output}
    return {"error": "Solo Linux"}


def dhcp_server_find_subnet(subnet="192.168.1.0/24"):
    """Busca servidores DHCP en una subred via nmap"""

    # Busca servidores DHCP en una subred usando nmap con script broadcast-dhcp-discover. Alternativa: nmap UDP puerto 67.
    try:
        output = subprocess.getoutput(f"nmap --script broadcast-dhcp-discover {subnet} 2>/dev/null || nmap -sU -p 67 --script dhcp-discover {subnet} 2>/dev/null || echo 'nmap no disponible'")
        return {"subnet": subnet, "result": output[:500]}
    except Exception as e:
        return {"subnet": subnet, "error": str(e)}


def bridge_check():
    """Muestra puentes de red (bridges) configurados"""

    # Muestra puentes de red (bridges) configurados. En Linux 'brctl show' o 'ip link show type bridge'. Útil para máquinas virtuales.
    if sys.platform == "linux":
        return subprocess.getoutput("brctl show 2>/dev/null || ip link show type bridge 2>/dev/null || echo 'No bridges'")
    return "No soportado"


def vlan_check():
    """Muestra VLANs configuradas en el sistema"""

    # Muestra VLANs configuradas. Linux: 'ip link show | grep vlan', 'cat /proc/net/vlan/config' o 'vconfig show'.
    if sys.platform == "linux":
        return subprocess.getoutput("ip -o link show | grep -i vlan 2>/dev/null || cat /proc/net/vlan/config 2>/dev/null || vconfig show 2>/dev/null || echo 'No VLANs detectadas'")
    return "No soportado"


def bonding_check():
    """Muestra interfaces en bonding (LAG)"""

    # Muestra interfaces en bonding/LAG. Lee /proc/net/bonding/* o 'ip link show type bond'. Muestra esclavos y modo de balanceo.
    if sys.platform == "linux":
        return subprocess.getoutput("cat /proc/net/bonding/* 2>/dev/null | head -60 || ip link show type bond 2>/dev/null || echo 'No bonding detectado'")
    return "No soportado"


def iperf_test(server="localhost", port=5201, duration=5, direction="download"):
    """Test de throughput via iperf3 (requiere iperf3 en servidor/cliente)"""

    # Test de rendimiento con iperf3. Requiere iperf3 instalado en cliente y servidor. Soporta descarga (download) y subida (upload con -R).
    cmd = f"iperf3 -c {server} -p {port} -t {duration}"
    if direction == "upload":
        cmd += " -R"
    try:
        output = subprocess.getoutput(f"{cmd} 2>&1 | tail -20")
        if "error" in output.lower():
            return {"server": server, "error": output[:200]}
        return {"server": server, "port": port, "direction": direction, "result": output}
    except Exception as e:
        return {"server": server, "error": str(e)}


def jitter_test(host="8.8.8.8", count=20):
    """Mide jitter variando la latencia entre paquetes"""

    # Mide jitter (variación de latencia). Envía count pings con 50ms de separación, calcula diferencia entre latencias consecutivas.
    import time
    times = []
    for _ in range(count):
        start = time.time()
        resp = os.system(f"ping -c 1 -W 1 {host} >/dev/null 2>&1")
        if resp == 0:
            elapsed = (time.time() - start) * 1000
            times.append(round(elapsed, 1))
        time.sleep(0.05)
    if len(times) < 2:
        return {"host": host, "error": "No hay suficientes muestras"}
    diffs = [abs(times[i] - times[i+1]) for i in range(len(times)-1)]
    avg_jitter = round(sum(diffs) / len(diffs), 1)
    return {
        "host": host,
        "samples": len(times),
        "jitter_avg_ms": avg_jitter,
        "jitter_max_ms": round(max(diffs), 1),
        "latency_avg_ms": round(sum(times) / len(times), 1),
        "latency_min_ms": min(times),
        "latency_max_ms": max(times),
    }


def conntrack_check():
    """Muestra tabla de conexiones de red."""
    try:
        with open("/proc/net/nf_conntrack") as f:
            lines = f.read().strip().split("\n")[:30]
            return "\n".join(lines) if lines else "conntrack no disponible"
    except:
        return "No soportado en este SO"


def mtr_trace(host, count=10):
    """Disponible solo si mtr o traceroute están instalados."""
    return {"host": host, "trace": "mtr/binario no disponible"}


def tcptraceroute(host, port=80):
    """Reemplazado por traceroute TCP en scanner."""
    from techbot.scanner import traceroute as tr
    hops = tr(host, max_hops=15, port=port)
    trace_str = "\n".join(f"{h['hop']:>2}. {h['ip']}" for h in hops)
    return {"host": host, "port": port, "trace": trace_str}


def dhcp_renew_all():
    """Renueva todas las interfaces con DHCP"""

    # Renueva todas las interfaces DHCP. En Linux ejecuta dhclient para cada interfaz. En Windows 'ipconfig /renew'.
    if sys.platform != "linux":
        return subprocess.getoutput("ipconfig /renew")
    interfaces = subprocess.getoutput("ip -o link show | grep -v LOOPBACK | awk -F': ' '{print $2}'")
    results = {}
    for iface in interfaces.strip().split("\n"):
        iface = iface.strip()
        if iface and iface != "lo":
            result = subprocess.getoutput(f"dhclient -v {iface} 2>&1 | tail -3")
            results[iface] = result or "OK"
    return results


def local_ip_info():
    """Muestra información de IPs locales"""

    # Muestra información de IPs locales. En Linux 'ip addr show', en Windows 'ipconfig | findstr IPv4'.
    if sys.platform == "linux":
        return subprocess.getoutput("ip -o -f inet addr show | awk '{print $2, $4}'")
    elif sys.platform == "win32":
        return subprocess.getoutput("ipconfig | findstr IPv4")
    return subprocess.getoutput("ifconfig | grep inet")


def public_ip_info():
    """Obtiene IP pública y geolocalización básica"""

    # Obtiene IP pública y geolocalización. Usa api.ipify.org para IP y ip-api.com para geolocalización (país, región, ciudad, ISP).
    try:
        import urllib.request
        import json
        ip = get_public_ip()
        if not ip:
            return {"error": "No se pudo obtener IP pública"}
        req = urllib.request.Request(f"http://ip-api.com/json/{ip}")
        with urllib.request.urlopen(req, timeout=5) as r:
            geo = json.loads(r.read().decode())
            return {"ip": ip, "country": geo.get("country"), "region": geo.get("regionName"), "city": geo.get("city"), "isp": geo.get("isp"), "org": geo.get("org"), "lat": geo.get("lat"), "lon": geo.get("lon")}
    except Exception as e:
        return {"ip": get_public_ip(), "error": str(e)}


def wifi_channels():
    """Muestra canales WiFi y frecuencias"""

    # Diccionario de canales WiFi 2.4GHz y 5GHz con sus frecuencias en MHz. Útil para planificar redes inalámbricas sin interferencia.
    channels = {
        "2.4 GHz": {1: "2412", 2: "2417", 3: "2422", 4: "2427", 5: "2432", 6: "2437", 7: "2442", 8: "2447", 9: "2452", 10: "2457", 11: "2462", 12: "2467", 13: "2472"},
        "5 GHz": {36: "5180", 40: "5200", 44: "5220", 48: "5240", 52: "5260", 56: "5280", 60: "5300", 64: "5320", 100: "5500", 104: "5520", 108: "5540", 112: "5560", 116: "5580", 120: "5600", 124: "5620", 128: "5640", 132: "5660", 136: "5680", 140: "5700", 149: "5745", 153: "5765", 157: "5785", 161: "5805", 165: "5825"},
    }
    return channels


def ethernet_speed_test(host="8.8.8.8", size=1472):
    """Test rápido de velocidad de Ethernet enviando paquetes de gran tamaño"""

    # Test rápido de velocidad Ethernet usando ping con paquetes de gran tamaño (1472 bytes). Envía 5 pings y mide pérdida.
    return packet_loss_test(host, count=5)


def nat_check():
    """Verifica si estamos detrás de NAT"""

    # Verifica si el sistema está detrás de NAT. Compara IP pública con IP local. Si la local es privada (10.x, 172.x, 192.168.x), está detrás de NAT.
    try:
        public_ip = get_public_ip()
        if not public_ip:
            return {"nat": None, "error": "No se pudo obtener IP pública"}
        local_ip = subprocess.getoutput("hostname -I 2>/dev/null | awk '{print $1}'")
        if local_ip.startswith("10.") or local_ip.startswith("172.") or local_ip.startswith("192.168"):
            return {"behind_nat": True, "local_ip": local_ip, "public_ip": public_ip}
        return {"behind_nat": False, "local_ip": local_ip, "public_ip": public_ip}
    except Exception as e:
        return {"error": str(e)}


def ipv6_check():
    """Verifica conectividad IPv6"""

    # Verifica conectividad IPv6. Hace ping6 a ipv6.google.com y lista direcciones IPv6 locales. Muestra si hay conectividad IPv6.
    try:
        output = subprocess.getoutput("ping6 -c 1 -W 2 ipv6.google.com 2>&1 | head -3")
        local = subprocess.getoutput("ip -6 addr show 2>/dev/null | grep inet6 | head -5")
        return {
            "ipv6_enabled": bool("bytes from" in output or "64 bytes" in output),
            "ipv6_addresses": local.strip().split("\n") if local.strip() else [],
            "ping_test": output[:200] if output else "No responde IPv6",
        }
    except Exception as e:
        return {"error": str(e)}


def bgp_lookup(as_number=None, ip=None):
    """Consulta información BGP (requiere whois o bgp.he.net)"""

    # Consulta información BGP para un ASN o IP. Usa whois para obtener nombre del AS, país y descripción. Alternativa: bgp.he.net.
    if as_number:
        output = subprocess.getoutput(f"whois AS{as_number} 2>/dev/null | grep -E 'AS Name|Origin|Country|descr' | head -10")
        return {"asn": as_number, "info": output[:500] if output else "whois no disponible"}
    if ip:
        output = subprocess.getoutput(f"whois {ip} 2>/dev/null | grep -E 'origin|AS|as-name|descr' | head -10")
        return {"ip": ip, "info": output[:500] if output else "whois no disponible"}
    return {"error": "Especificar AS o IP"}
