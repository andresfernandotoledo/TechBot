import socket
import ipaddress
import subprocess
import os
import struct
import sys
from datetime import datetime


def scan_ports(host, start_port=1, end_port=1024):
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
    red = ipaddress.ip_network(subnet, strict=False)
    activos = []
    for ip in red.hosts():
        ip_str = str(ip)
        response = os.system(f"ping -c 1 -W 1 {ip_str} > /dev/null 2>&1")
        if response == 0:
            activos.append(ip_str)
    return activos

def dns_lookup(domain):
    try:
        return socket.gethostbyname(domain)
    except socket.gaierror:
        return None

def reverse_dns(ip):
    try:
        return socket.gethostbyaddr(ip)[0]
    except socket.herror:
        return None

def ip_to_binary(ip):
    partes = ip.split('.')
    return '.'.join(format(int(p), '08b') for p in partes)

def subnet_info(ip, mask):
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
    resultado = []
    for ttl in range(1, 30):
        cmd = f"ping -c 1 -t {ttl} -W 1 {host} 2>&1"
        salida = subprocess.getoutput(cmd)
        resultado.append(f"{ttl}: {salida.split(chr(10))[0]}")
    return resultado

def calculate_subnets(base_network, num_subnets):
    red = ipaddress.IPv4Network(base_network, strict=False)
    bits_needed = (num_subnets - 1).bit_length()
    new_prefix = red.prefixlen + bits_needed
    subnets = list(red.subnets(new_prefix=new_prefix))
    return subnets[:num_subnets]

def validate_ip(ip):
    try:
        ipaddress.ip_address(ip)
        return True
    except ValueError:
        return False

def get_default_gateway():
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
    try:
        return subprocess.getoutput(f"whois {domain} 2>/dev/null")
    except:
        return "whois no disponible"

def check_http_headers(url):
    try:
        import urllib.request
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req, timeout=5) as response:
            return dict(response.headers)
    except:
        return {}

def ssl_cert_info(host, port=443):
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
    return int(mac.replace(":", ""), 16)

def ip_to_decimal(ip):
    packed = socket.inet_aton(ip)
    return struct.unpack("!I", packed)[0]

def decimal_to_ip(decimal):
    return socket.inet_ntoa(struct.pack("!I", decimal))

def dhcp_range(network):
    red = ipaddress.IPv4Network(network, strict=False)
    hosts = list(red.hosts())
    return {
        "start": str(hosts[100]) if len(hosts) > 100 else str(hosts[0]),
        "end": str(hosts[-50]) if len(hosts) > 50 else str(hosts[-1])
    }

def get_public_ip():
    try:
        import urllib.request
        with urllib.request.urlopen("https://api.ipify.org", timeout=5) as r:
            return r.read().decode()
    except:
        return None
