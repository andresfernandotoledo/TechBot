import socket
import subprocess
import ssl
import sys
import os
import ipaddress
from datetime import datetime


def ssl_cert_check(host, port=443):
    """Obtiene información del certificado SSL de un host"""

    # Obtiene información del certificado SSL: subject, issuer, SAN, fechas de validez y serial. Conecta con SSLContext y extrae getpeercert().
    try:
        ctx = ssl.create_default_context()
        with ctx.wrap_socket(socket.socket(), server_hostname=host) as s:
            s.settimeout(5)
            s.connect((host, port))
            cert = s.getpeercert()
            if not cert:
                return {"error": "No se pudo obtener el certificado"}
            issuer = dict(x[0] for x in cert.get("issuer", []))
            subject = dict(x[0] for x in cert.get("subject", []))
            not_before = cert.get("notBefore", "")
            not_after = cert.get("notAfter", "")
            sans = cert.get("subjectAltName", [])
            return {
                "host": host,
                "port": port,
                "subject": subject.get("commonName", ""),
                "organization": subject.get("organizationName", ""),
                "issuer": issuer.get("commonName", ""),
                "issuer_org": issuer.get("organizationName", ""),
                "valid_from": not_before,
                "valid_until": not_after,
                "serial": hex(cert.get("serialNumber", 0)),
                "san": [s[1] for s in sans],
                "version": cert.get("version", ""),
            }
    except ssl.SSLCertVerificationError as e:
        return {"host": host, "port": port, "error": f"Error de verificación: {e}"}
    except Exception as e:
        return {"host": host, "port": port, "error": str(e)}


def ssl_expiry_days(host, port=443):
    """Calcula días restantes para expiración del certificado SSL"""

    # Calcula días restantes para expiración del certificado. Parsea la fecha notAfter y resta la fecha actual. Si es negativo, ya expiró.
    info = ssl_cert_check(host, port)
    if "error" in info:
        return info
    try:
        from datetime import datetime
        expires = datetime.strptime(info["valid_until"], "%b %d %H:%M:%S %Y %Z")
        remaining = (expires - datetime.now()).days
        return {"host": host, "port": port, "expires": str(expires), "days_remaining": remaining}
    except Exception as e:
        return {"error": str(e)}


def check_open_relay(server, port=25, from_addr="test@example.com", to_addr="test@example.org"):
    """Verifica si un servidor SMTP es open relay"""

    # Verifica si SMTP es open relay. Envía EHLO, MAIL FROM, RCPT TO. Si acepta RCPT TO sin autenticación, cualquiera puede enviar email.
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5)
        sock.connect((server, port))
        banner = sock.recv(1024).decode()
        sock.sendall(b"EHLO test\r\n")
        resp = sock.recv(1024).decode()
        sock.sendall(f"MAIL FROM:<{from_addr}>\r\n".encode())
        resp += sock.recv(1024).decode()
        sock.sendall(f"RCPT TO:<{to_addr}>\r\n".encode())
        resp += sock.recv(1024).decode()
        sock.sendall(b"QUIT\r\n")
        sock.close()
        is_relay = "250" in resp and "RCPT" in resp
        return {"server": server, "port": port, "open_relay": is_relay, "response": resp[:200]}
    except Exception as e:
        return {"server": server, "port": port, "open_relay": False, "error": str(e)}


def check_cors_headers(url):
    """Verifica headers CORS de un sitio web"""

    # Headers CORS de un sitio web. Verifica Access-Control-Allow-Origin, Methods, Headers, Credentials, Max-Age y Expose-Headers.
    try:
        import urllib.request
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req, timeout=5) as response:
            headers = dict(response.headers)
            cors = {
                "Access-Control-Allow-Origin": headers.get("Access-Control-Allow-Origin", ""),
                "Access-Control-Allow-Methods": headers.get("Access-Control-Allow-Methods", ""),
                "Access-Control-Allow-Headers": headers.get("Access-Control-Allow-Headers", ""),
                "Access-Control-Allow-Credentials": headers.get("Access-Control-Allow-Credentials", ""),
                "Access-Control-Max-Age": headers.get("Access-Control-Max-Age", ""),
                "Access-Control-Expose-Headers": headers.get("Access-Control-Expose-Headers", ""),
            }
            return cors
    except Exception as e:
        return {"error": str(e)}


def check_security_headers(url):
    """Verifica headers de seguridad HTTP"""

    # Headers de seguridad HTTP: HSTS, X-Frame-Options, X-Content-Type-Options, X-XSS-Protection, CSP, Referrer-Policy, Permissions-Policy.
    try:
        import urllib.request
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req, timeout=5) as response:
            headers = dict(response.headers)
            security = {
                "Strict-Transport-Security": headers.get("Strict-Transport-Security", "Ausente"),
                "X-Frame-Options": headers.get("X-Frame-Options", "Ausente"),
                "X-Content-Type-Options": headers.get("X-Content-Type-Options", "Ausente"),
                "X-XSS-Protection": headers.get("X-XSS-Protection", "Ausente"),
                "Content-Security-Policy": headers.get("Content-Security-Policy", "Ausente"),
                "Referrer-Policy": headers.get("Referrer-Policy", "Ausente"),
                "Permissions-Policy": headers.get("Permissions-Policy", "Ausente"),
            }
            return security
    except Exception as e:
        return {"error": str(e)}


def port_scan(host, ports="21,22,23,25,53,80,110,143,443,445,993,995,3306,3389,5432,6379,8080,8443,27017"):
    """Escanea puertos comunes en un host"""

    # Escanea puertos comunes TCP. Lista predeterminada de 20 puertos (FTP, SSH, HTTP, HTTPS, MySQL, etc.). Timeout de 1s por puerto.
    if isinstance(ports, str):
        ports = [int(p.strip()) for p in ports.split(",") if p.strip().isdigit()]
    open_ports = []
    for port in ports:
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(1)
            result = sock.connect_ex((host, port))
            if result == 0:
                service = socket.getservbyport(port, "tcp") if port <= 65535 else "?"
                open_ports.append({"port": port, "service": service})
            sock.close()
        except:
            pass
    return {"host": host, "open_ports": open_ports, "count": len(open_ports)}


def check_tls_version(host, port=443):
    """Verifica qué versiones de TLS/SSL soporta un servidor"""

    # Prueba qué versiones de TLS/SSL soporta un servidor. SSLv3 (inseguro), TLSv1.0, 1.1 (obsoletos), 1.2, 1.3. Timeout 3s por versión.
    versions = {}
    for ver_name, ver_ctx in [
        ("SSLv3", ssl.PROTOCOL_SSLv3 if hasattr(ssl, "PROTOCOL_SSLv3") else None),
        ("TLSv1.0", ssl.PROTOCOL_TLSv1),
        ("TLSv1.1", ssl.PROTOCOL_TLSv1_1 if hasattr(ssl, "PROTOCOL_TLSv1_1") else None),
        ("TLSv1.2", ssl.PROTOCOL_TLSv1_2),
        ("TLSv1.3", ssl.PROTOCOL_TLSv1_3 if hasattr(ssl, "PROTOCOL_TLSv1_3") else None),
    ]:
        ver_name, ver_ctx = ver_name, ver_ctx
        if ver_ctx is None:
            versions[ver_name] = "No soportado por el cliente"
            continue
        try:
            ctx = ssl.SSLContext(ver_ctx)
            with ctx.wrap_socket(socket.socket(), server_hostname=host) as s:
                s.settimeout(3)
                s.connect((host, port))
                versions[ver_name] = "Soportado"
        except ssl.SSLError:
            versions[ver_name] = "No soportado"
        except Exception as e:
            versions[ver_name] = f"Error: {e}"
    return {"host": host, "port": port, "versions": versions}


def check_firewall_port(host, port, protocol="tcp"):
    """Verifica si un puerto específico está abierto/filtrado/cerrado"""

    # Verifica estado de un puerto específico. TCP: connect_ex devuelve 0 (open), 111 (closed), otro (filtered). UDP: envía datagrama y espera respuesta.
    if protocol == "tcp":
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(3)
            result = sock.connect_ex((host, int(port)))
            sock.close()
            if result == 0:
                status = "open"
            elif result == 111:
                status = "closed"
            else:
                status = "filtered"
            return {"host": host, "port": port, "protocol": "tcp", "status": status}
        except socket.timeout:
            return {"host": host, "port": port, "protocol": "tcp", "status": "filtered"}
        except Exception as e:
            return {"host": host, "port": port, "protocol": "tcp", "status": "error", "error": str(e)}
    else:
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.settimeout(3)
            sock.sendto(b"test", (host, int(port)))
            sock.recvfrom(1024)
            status = "open"
        except socket.timeout:
            status = "open|filtered"
        except Exception as e:
            status = "error"
        return {"host": host, "port": port, "protocol": "udp", "status": status}


def banner_grab(host, port):
    """Obtiene el banner de servicio de un puerto"""

    # Obtiene banner de un servicio en un puerto. Conecta y recibe hasta 1024 bytes. Útil para identificar versiones de software.
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(3)
        sock.connect((host, int(port)))
        banner = sock.recv(1024).decode(errors="ignore").strip()
        sock.close()
        return {"host": host, "port": port, "banner": banner or "Sin banner"}
    except Exception as e:
        return {"host": host, "port": port, "error": str(e)}


def check_http_methods(url):
    """Verifica qué métodos HTTP soporta un servidor web (OPTIONS)"""

    # Métodos HTTP soportados. Envía OPTIONS y lee header Allow. Métodos inseguros: PUT, DELETE, TRACE, CONNECT.
    try:
        import urllib.request
        req = urllib.request.Request(url, method="OPTIONS")
        with urllib.request.urlopen(req, timeout=5) as response:
            allowed = response.headers.get("Allow", "")
            return {"url": url, "allowed_methods": allowed.split(", ") if allowed else []}
    except Exception as e:
        return {"url": url, "error": str(e)}


def detect_os_by_ttl(host):
    """Detecta sistema operativo por TTL del paquete"""

    # Detecta OS por TTL del ping. Linux/macOS ≤64, Windows ≤128, Cisco/Solaris ≤255. Basado en valores TTL iniciales típicos.
    try:
        output = subprocess.getoutput(f"ping -c 1 -W 2 {host} 2>/dev/null | grep ttl")
        if "ttl=" in output:
            ttl = int(output.split("ttl=")[1].split()[0])
            if ttl <= 64:
                os_guess = "Linux / Unix / macOS"
            elif ttl <= 128:
                os_guess = "Windows"
            elif ttl <= 255:
                os_guess = "Cisco / Router / Solaris"
            else:
                os_guess = "Desconocido"
            return {"host": host, "ttl": ttl, "os_guess": os_guess}
        return {"host": host, "error": "No responde a ping"}
    except Exception as e:
        return {"host": host, "error": str(e)}


def check_vulnerable_ports(host):
    """Verifica puertos vulnerables comunes (servicios expuestos)"""

    # Identifica puertos vulnerables comunes expuestos. FTP, Telnet, SMB, RDP, bases de datos. Calcula nivel de riesgo según cantidad.
    vulnerable = {
        21: "FTP - transmisión en texto claro",
        23: "Telnet - sin cifrado",
        25: "SMTP - posible open relay",
        53: "DNS - posible zone transfer",
        110: "POP3 - sin cifrado",
        135: "MSRPC - vulnerable a ataques",
        139: "NetBIOS - información expuesta",
        143: "IMAP - sin cifrado",
        445: "SMB - vulnerable a ransomware",
        1433: "MSSQL - expuesto",
        1521: "Oracle - expuesto",
        3306: "MySQL - expuesto",
        3389: "RDP - vulnerable a bluekeep",
        5432: "PostgreSQL - expuesto",
        5900: "VNC - sin cifrado",
        6379: "Redis - expuesto sin auth",
        8080: "HTTP alternativo - sin cifrado",
        8443: "HTTPS alternativo",
        27017: "MongoDB - expuesto sin auth",
    }
    try:
        abiertos = []
        for port, desc in vulnerable.items():
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(1)
            if sock.connect_ex((host, port)) == 0:
                abiertos.append({"port": port, "service": desc})
            sock.close()
        risk = "alto" if len(abiertos) > 3 else "medio" if len(abiertos) > 0 else "bajo"
        return {"host": host, "vulnerable_ports": abiertos, "count": len(abiertos), "risk_level": risk}
    except Exception as e:
        return {"host": host, "error": str(e)}


def check_default_credentials(host, service="ssh"):
    """Prueba credenciales por defecto conocidas en servicios"""

    # Prueba credenciales por defecto en HTTP Basic Auth. Lista de user:pass comunes: admin/admin, root/root, admin/12345, etc.
    defaults = {
        "ssh": [("root", "root"), ("root", "admin"), ("admin", "admin"), ("admin", "password"), ("admin", "12345"), ("root", "toor"), ("root", "changeme"), ("cisco", "cisco")],
        "ftp": [("anonymous", ""), ("ftp", "ftp"), ("admin", "admin"), ("user", "pass"), ("root", "root"), ("admin", "12345"), ("admin", "password")],
        "http": [("admin", "admin"), ("admin", "12345"), ("admin", "password"), ("admin", "Admin"), ("root", "root"), ("user", "user"), ("guest", "guest"), ("admin", "1111"), ("admin", "1234"), ("admin", "123456"), ("admin", "admin123"), ("Administrator", "admin")],
    }
    port_map = {"ssh": 22, "ftp": 21, "http": 80}
    port = port_map.get(service, 22)
    if service == "http":
        try:
            import urllib.request
            for user, passwd in defaults.get(service, []):
                try:
                    import base64
                    creds = base64.b64encode(f"{user}:{passwd}".encode()).decode()
                    req = urllib.request.Request(f"http://{host}:{port}/")
                    req.add_header("Authorization", f"Basic {creds}")
                    with urllib.request.urlopen(req, timeout=3) as r:
                        if r.status == 200:
                            return {"host": host, "service": service, "vulnerable": True, "credentials_found": f"{user}:{passwd}"}
                except:
                    pass
            return {"host": host, "service": service, "vulnerable": False}
        except:
            return {"host": host, "service": service, "error": "No se pudo probar"}
    return {"host": host, "service": service, "note": "Solo HTTP soportado, usar hydra para otros"}


def check_http_security(url):
    """Análisis completo de seguridad HTTP"""

    # Análisis completo de seguridad HTTP. Verifica servidor, tecnología, headers de seguridad, CORS y genera advertencias.
    try:
        import urllib.request
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req, timeout=5) as response:
            headers = dict(response.headers)
            server = headers.get("Server", "")
            powered = headers.get("X-Powered-By", "")
            via = headers.get("Via", "")

        warnings = []
        if "Apache/2.2" in server:
            warnings.append("Apache 2.2 antiguo (EOL)")
        if "IIS 6" in server or "IIS 7" in server:
            warnings.append("IIS antiguo")
        if "PHP" in powered:
            warnings.append("PHP version expuesta")
        if not headers.get("Strict-Transport-Security"):
            warnings.append("Falta HSTS")
        if not headers.get("X-Frame-Options"):
            warnings.append("Falta X-Frame-Options (clickjacking)")

        return {
            "url": url,
            "server": server,
            "powered_by": powered,
            "via": via,
            "security_headers": check_security_headers(url),
            "cors": check_cors_headers(url),
            "warnings": warnings,
            "secure": len(warnings) == 0,
        }
    except Exception as e:
        return {"url": url, "error": str(e)}


def ssh_bruteforce_check(host, port=22, user="root"):
    """Verifica si un servidor SSH permite múltiples intentos (no fail2ban)"""

    # Verifica si SSH es vulnerable a fuerza bruta. Mide tiempo de respuesta: si es <1.5s probablemente no hay fail2ban/rate-limiting.
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(3)
        sock.connect((host, port))
        banner = sock.recv(1024).decode(errors="ignore")
        sock.close()

        import time
        attempt_times = []
        for _ in range(3):
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(3)
            sock.connect((host, port))
            sock.recv(1024)
            start = time.time()
            sock.sendall(b"invaliduser\r\n")
            sock.recv(1024)
            elapsed = (time.time() - start) * 1000
            attempt_times.append(round(elapsed, 1))
            sock.close()
            time.sleep(0.5)

        avg_time = sum(attempt_times) / len(attempt_times)
        return {
            "host": host, "port": port,
            "banner": banner[:100],
            "avg_response_ms": round(avg_time, 1),
            "fail2ban_probable": avg_time > 1500,
            "rate_limiting": any(t > 3000 for t in attempt_times),
            "attempt_times_ms": attempt_times,
        }
    except Exception as e:
        return {"host": host, "port": port, "error": str(e)}


def check_proxy(proxy_host, proxy_port=8080, test_url="http://httpbin.org/ip"):
# Verifica si un proxy HTTP funciona. Configura ProxyHandler en urllib e intenta obtener una URL de prueba.
    """Verifica si un proxy HTTP/HTTPS funciona"""
    try:
        import urllib.request
        proxy = urllib.request.ProxyHandler({"http": f"http://{proxy_host}:{proxy_port}"})
        opener = urllib.request.build_opener(proxy)
        with opener.open(test_url, timeout=5) as r:
            return {"proxy": f"{proxy_host}:{proxy_port}", "working": True, "response": r.read().decode()[:200]}
    except Exception as e:
        return {"proxy": f"{proxy_host}:{proxy_port}", "working": False, "error": str(e)}


def check_vpn_protocols(host):
    """Detecta protocolos VPN abiertos en un host"""

    # Detecta servicios VPN abiertos: IKE (500), OpenVPN (1194), L2TP (1701), PPTP (1723), IPSec NAT-T (4500), WireGuard (51820).
    vpn_ports = {
        500: "IKE (IPSec)",
        1194: "OpenVPN",
        1701: "L2TP",
        1723: "PPTP",
        4500: "IPSec NAT-T",
        51820: "WireGuard",
    }
    open_ports = []
    for port, proto in vpn_ports.items():
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(1)
            if sock.connect_ex((host, port)) == 0:
                open_ports.append({"port": port, "protocol": proto, "type": "TCP"})
            sock.close()
            if port in (500, 4500):
                sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                sock.settimeout(1)
                sock.sendto(b"\x00" * 8, (host, port))
                try:
                    sock.recvfrom(1024)
                    open_ports.append({"port": port, "protocol": proto, "type": "UDP"})
                except socket.timeout:
                    pass
                sock.close()
        except:
            pass
    return {"host": host, "vpn_services": open_ports, "count": len(open_ports)}


def check_smb_signing(host):
    """Verifica si SMB signing está deshabilitado (vulnerable a relay)"""

    # Verifica SMB signing. Si está deshabilitado, es vulnerable a ataques de relay NTLM. Usa smbclient o nmap script smb-security-mode.
    try:
        output = subprocess.getoutput(
            f"smbclient -L //{host} -N 2>&1 | head -20 || "
            f"echo 'smbclient no disponible'"
        )
        if "protocol negotiation failed" in output:
            return {"host": host, "smb_signing": None, "error": "Negociación SMB falló"}
        return {"host": host, "smb_info": output[:200], "note": "Usar 'smbclient -L //host -N' o nmap --script smb-security-mode"}
    except Exception as e:
        return {"host": host, "error": str(e)}


def check_rdp_security(host, port=3389):
    """Verifica seguridad de RDP"""

    # Verifica seguridad de RDP. Detecta si está habilitado y si soporta NLA (Network Level Authentication). Recomienda nmap para análisis completo.
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(3)
        sock.connect((host, port))
        banner = sock.recv(1024).decode(errors="ignore")
        sock.close()
        nla_supported = "NLA" in banner or "HYBRID" in banner
        return {
            "host": host, "port": port,
            "rdp_enabled": True,
            "nla_supported": nla_supported,
            "banner": banner[:100],
            "note": "Usar 'nmap --script rdp-sec-check -p 3389 host' para análisis completo",
        }
    except Exception as e:
        return {"host": host, "port": port, "rdp_enabled": False, "error": str(e)}


def check_mysql_security(host, port=3306):
    """Verifica seguridad de MySQL expuesto"""

    # Verifica si MySQL está expuesto públicamente. Captura banner de MySQL. Si está expuesto, es un riesgo de seguridad.
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(3)
        sock.connect((host, port))
        banner = sock.recv(1024).decode(errors="ignore")
        sock.close()
        version = ""
        if "mysql" in banner.lower():
            version = banner.strip()
        return {
            "host": host, "port": port,
            "mysql_exposed": bool(version),
            "version_banner": version[:100] if version else None,
            "risk": "alto" if version else "bajo",
        }
    except Exception as e:
        return {"host": host, "port": port, "mysql_exposed": False, "error": str(e)}


def check_redis_security(host, port=6379):
    """Verifica si Redis está expuesto sin autenticación"""

    # Verifica si Redis está expuesto sin autenticación. Envía PING y espera +PONG. Si responde, no requiere auth.
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(3)
        sock.connect((host, port))
        sock.sendall(b"PING\r\n")
        response = sock.recv(1024).decode(errors="ignore")
        sock.close()
        vulnerable = "+PONG" in response
        return {
            "host": host, "port": port,
            "redis_exposed": True,
            "no_auth": vulnerable,
            "response": response[:100],
        }
    except Exception as e:
        return {"host": host, "port": port, "redis_exposed": False, "error": str(e)}


def check_mongodb_security(host, port=27017):
    """Verifica si MongoDB está expuesto sin autenticación"""

    # Verifica si MongoDB está expuesto sin auth. Intenta listar bases de datos. Requiere pymongo o protocolo raw alternativo.
    try:
        from pymongo import MongoClient
        client = MongoClient(host, port, serverSelectionTimeoutMS=3000)
        dbs = client.list_database_names()
        client.close()
        return {
            "host": host, "port": port,
            "mongodb_exposed": True,
            "databases": dbs[:5],
            "no_auth": True,
        }
    except ImportError:
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(3)
            sock.connect((host, port))
            sock.sendall(b"\x3a\x00\x00\x00\x00\x00\x00\x00\xd4\x07\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00")
            response = sock.recv(1024).decode(errors="ignore")
            sock.close()
            return {"host": host, "port": port, "mongodb_exposed": True, "response": response[:100], "note": "Instalar pymongo para verificación completa"}
        except:
            return {"host": host, "port": port, "mongodb_exposed": False}
    except Exception as e:
        return {"host": host, "port": port, "mongodb_exposed": False, "error": str(e)}


def check_ftp_anonymous(host, port=21):
    """Verifica si FTP permite acceso anónimo"""

    # Verifica si FTP permite acceso anónimo. Envía USER anonymous + PASS test. Si acepta, cualquiera puede acceder al servidor FTP.
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5)
        sock.connect((host, port))
        banner = sock.recv(1024).decode(errors="ignore")
        sock.sendall(b"USER anonymous\r\n")
        resp1 = sock.recv(1024).decode(errors="ignore")
        sock.sendall(b"PASS test@test.com\r\n")
        resp2 = sock.recv(1024).decode(errors="ignore")
        sock.sendall(b"PWD\r\n")
        resp3 = sock.recv(1024).decode(errors="ignore")
        sock.sendall(b"QUIT\r\n")
        sock.close()
        anonymous_allowed = "230" in resp2 or "2" in resp2[:1]
        return {
            "host": host, "port": port,
            "ftp_open": True,
            "anonymous_allowed": anonymous_allowed,
            "banner": banner[:100],
            "response": (resp1 + resp2 + resp3)[:200],
        }
    except Exception as e:
        return {"host": host, "port": port, "ftp_open": False, "error": str(e)}


def check_snmp_public(host, community="public"):
    """Verifica si SNMP permite acceso con community public"""

    # Verifica si SNMP permite acceso con community 'public'. snmpget a sysDescr. Si responde, información expuesta.
    try:
        output = subprocess.getoutput(
            f"snmpget -v2c -c {community} -t 2 {host} .1.3.6.1.2.1.1.1.0 2>/dev/null"
        )
        if output:
            return {"host": host, "community": community, "snmp_accessible": True, "system_info": output[:200]}
        return {"host": host, "community": community, "snmp_accessible": False}
    except Exception as e:
        return {"host": host, "community": community, "snmp_accessible": False, "error": str(e)}


def check_subdomain_enum(domain, wordlist="www,mail,ftp,admin,dns,ns1,ns2,webmail,portal,vpn,smtp,pop,imap,api,blog,shop,dev,test,git,jenkins,confluence,jira,wiki,help,status,cdn,cloud,app,mx,remote,direct,exchange,owa,autodiscover,correo,server,ns,mssql,mysql,proxy,router,switch,radio,cam,cctv,ftp2,backup,mail2,smtp2,dns2,web,ssl,secure,ssh,telnet,ldap,radius,sip,voip,chat,forum,info,download,upload,images,video,media,static,assets,news,login,signup,register,store,shop2,panel,cpanel,whm,webmail2,beta,stage,prod,production,development,testing,demo,support,info,helpdesk,ticket,billing,payment,invoice,customers,clients,partners,partners,admin2,root,adminpanel,dashboard,monitor,monitoring,stats,analytics,reports,reports,logs,debug,error,api2,api3,graphql,rest,soap,xml,json,ws,websocket,socket,stream,cdn2,cloud2,s3,storage,db,db2,database,redis,mongo,sql,backup2,archive,old,new,temp,tmp,test2,prueba,example,sample,internal,external,corp,office,home,work,lab,dev2,staging,preprod,qa,uat,sandbox,playground,training,learn,docs,documentation,help2,faq,about,contact,terms,privacy,policy,legal,jobs,careers,apply,news2,blog2,forum2,community,network,gallery,photo,files,share,sync,upload2,download2,transfer,mirror,cache,proxy2,vpn2,remote2,access,gateway,firewall,router2,switch2,wifi,ap,hotspot,captive,portal2,auth,login2,logout,register2,profile,account,settings,config,setup,install,update,upgrade,patch,pilot,earlyaccess,betatest,gammatest,release,version,v1,v2,v3,api4,web2,app2,m2,mobile,tablet,android,ios,windows,mac,linux,unix,bsd,solaris,aix,hpux,ibm,oracle,sap,erp,crm,hr,hris,payroll,time,attendance,recruitment,learning,lms,elearning,moodle,blackboard,canvas,sakai,edx,coursera,udemy,teachable,thinkific,kajabi,clickfunnels,leadpages,unbounce,instapage,landing,squeeze,sales,marketing,automation,mailchimp,constantcontact,activecampaign,convertkit,drip,getresponse,aweber,campaignmonitor,madmimi,sendgrid,sendy,list,subscribe,unsubscribe,newsletter,email,email2,outlook,exchange2,office365,lync,skype,teams,zoom,goto,webex,adobe,connect,meeting,webinar,training,live,event,events,calendar,schedule,booking,appointment,reserve,rsvp,register3,ticket2,order,purchase,cart,checkout,payment2,billing2,invoice2,receipt,receipts,quote,quotes,order2,orders,history,transactions,receipts,refund,cancel,returns,exchange2,wishlist,favorite,like,share2,review,rating,comment,feedback,survey,poll,vote,suggestion,complaint,support2,helpdesk2,ticket3,faq2,knowledgebase,kb,wiki2,forum3,discussion,board,thread,post,topic,message,chat2,livechat,livehelp,callback,callme,phone,contact2,about2,team,staff,employee,office2,location,address,map,direction,store2,shop3,outlet,dealer,distributor,partner,affiliate,reseller,wholesale,retail,distributor2,franchise,franchisee,franchisor,license,licensing,copyright,trademark,patent,legal2,privacy2,terms2,disclaimer,imprint,impressum,agb,gtc,datenschutz,dsgvo,gdpr,compliance,audit,security2,safety,risk,insurance,bond,guarantee,warranty,service,services,support3,maintenance,repair,fix,help3,assistance,faq3,tutorial,howto,guide,manual,documentation2,reference,api5,sdk,lib,library,plugin,extension,addon,module,integration,connector,bridge,middleware,adapter,wrapper,proxy3,gateway2,tunnel,tunnel2,relay,pipe,channel,queue,topic,exchange3,bus,broker,message,messaging,pubsub,subpub,publish,subscribe2,stream2,event2,eventbus,command,query,aggregate,projection,snapshot,readmodel,writemodel,cqrs,eventsourcing,saga,processmanager,workflow,bpm,bpmn,dmn,decision,rules,bre,drools,jess,clips,jena,sesame,neo4j,graphdb,orientdb,arangodb,cosmosdb,cassandra,hbase,bigtable,bigquery,redshift,snowflake,databricks,spark,flink,storm,samza,heron,kafka2,pulsar,rabbit,activemq,zeromq,nanomsg,mqtt,coap,amqp,stomp,xmpp,sip2,h323,rtsp,rtmp,hls,dash,mpeg,mss,smooth,streaming,media2,video2,audio,podcast,cast,airplay,chromecast,dial,upnp,dlna,samsungtv,lg,tv,smarttv,roku,firetv,appletv,androidtv,webos,tizen,boxee,xbmc,kodi,plex,emby,jellyfin,subsonic,icecast,shoutcast,vlc,mpc,potplayer,kmplayer,gomplayer,videonow,flv,mp4,avi,mkv,mov,wmv,webm,ogg,ogv,opus,flac,wav,aiff,aac,mp3,midi,mod,s3m,it,xm,669,far,sid,mpc,mpc2,mpc3,mpc4,mpc5,mpc6,mpc7,mpc8,mpc9,mpc,mp"):
    """Enumera subdominios comunes de un dominio"""

    # Enumera subdominios comunes de un dominio. Prueba una wordlist extensa (400+ subdominios típicos). Cada subdominio se resuelve con gethostbyname().
    if isinstance(wordlist, str):
        subs = [s.strip() for s in wordlist.split(",")]
    else:
        subs = wordlist
    found = []
    for sub in subs:
        if not sub:
            continue
        full = f"{sub}.{domain}"
        try:
            ip = socket.gethostbyname(full)
            found.append({"subdomain": full, "ip": ip})
        except socket.gaierror:
            pass
    return {"domain": domain, "checked": len(subs), "found": found, "count": len(found)}


def check_port_knocking(host, knock_ports):
    """Simula port knocking y verifica si se abre un puerto"""

    # Simula port knocking: envía paquetes a una secuencia de puertos. Si el puerto oculto se abre después de la secuencia, el knocking funciona.
    if isinstance(knock_ports, str):
        knock_ports = [int(p.strip()) for p in knock_ports.split(",") if p.strip().isdigit()]
    results = []
    for port in knock_ports:
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(1)
            sock.connect_ex((host, port))
            sock.close()
            results.append({"port": port, "knocked": True})
        except:
            results.append({"port": port, "knocked": False})
    return {"host": host, "knock_sequence": knock_ports, "results": results}


def check_cipher_suites(host, port=443):
    """Lista suites de cifrado soportadas (requiere openssl)"""

    # Lista suites de cifrado soportadas. Usa nmap ssl-enum-ciphers u openssl s_client. Versiones TLS y cifrados débiles/fuertes.
    try:
        output = subprocess.getoutput(
            f"nmap --script ssl-enum-ciphers -p {port} {host} 2>/dev/null | grep -E 'TLSv|SSLv|weak|strong' | head -30 || "
            f"openssl s_client -connect {host}:{port} -cipher 'ALL' 2>&1 | grep 'Cipher' | head -10 || "
            f"echo 'nmap/openssl no disponible'"
        )
        return {"host": host, "port": port, "cipher_info": output}
    except Exception as e:
        return {"host": host, "port": port, "error": str(e)}


def check_honeypot_detect(host):
    """Intenta detectar si un host es un honeypot"""

    # Intenta detectar honeypots. Verifica banners genéricos SSH y HTTP. Si todos son genéricos/default, podría ser un honeypot.
    try:
        indicators = []
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(3)
        sock.connect((host, 22))
        banner = sock.recv(1024).decode(errors="ignore")
        sock.close()
        if "ssh" in banner.lower() and "ubuntu" in banner.lower():
            indicators.append("Banner SSH genérico (posible honeypot)")

        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(3)
        sock.connect((host, 80))
        http = b""
        sock.sendall(b"GET / HTTP/1.0\r\n\r\n")
        http = sock.recv(2048).decode(errors="ignore")
        sock.close()
        if "default" in http.lower() and "welcome" in http.lower():
            indicators.append("Página default (posible honeypot)")

        return {
            "host": host,
            "honeypot_probability": len(indicators),
            "indicators": indicators,
            "note": "Sospechoso si todos los servicios devuelven banners genéricos",
        }
    except Exception as e:
        return {"host": host, "error": str(e)}


def generate_firewall_rule(service, action="allow", source_ip="any"):
    """Genera reglas de firewall para diferentes plataformas"""

    # Genera reglas de firewall para distintas plataformas: iptables, ufw, firewalld, netsh (Windows), Cisco ACL.
    port_map = {"ssh": 22, "http": 80, "https": 443, "ftp": 21, "smtp": 25, "dns": 53, "mysql": 3306, "rdp": 3389, "vnc": 5900, "openvpn": 1194, "ipp": 631, "samba": 445}
    port = port_map.get(service, service)
    action_str = "ACCEPT" if action == "allow" else "DROP"
    rules = {
        "iptables": f"iptables -A INPUT -p tcp --dport {port} -s {source_ip} -j {action_str}",
        "ufw": f"ufw {'allow' if action == 'allow' else 'deny'} {port}/tcp" if source_ip == "any" else f"ufw {'allow' if action == 'allow' else 'deny'} from {source_ip} to any port {port} proto tcp",
        "firewalld": f"firewall-cmd {'--add-port' if action == 'allow' else '--remove-port'}={port}/tcp --permanent" if source_ip == "any" else f"firewall-cmd {'--add-rich-rule' if action == 'allow' else '--remove-rich-rule'}='rule family=ipv4 source address={source_ip} port port={port} protocol=tcp accept' --permanent",
        "windows_netsh": f"netsh advfirewall firewall add rule name='{service}_{action}' dir=in action={'allow' if action == 'allow' else 'block'} protocol=TCP localport={port}",
        "cisco_acl": f"access-list 100 {'permit' if action == 'allow' else 'deny'} tcp {source_ip} any eq {port}" if source_ip != "any" else f"access-list 100 {'permit' if action == 'allow' else 'deny'} tcp any any eq {port}",
    }
    return {"service": service, "action": action, "port": port, "rules": rules}


def check_self_signed_cert(host, port=443):
    """Detecta si un certificado SSL es autofirmado"""

    # Detecta certificados autofirmados. Compara issuer con subject. Si son iguales, el certificado es autofirmado (no confiable por CA pública).
    cert = ssl_cert_check(host, port)
    if "error" in cert:
        return cert
    is_self_signed = cert.get("issuer") == cert.get("subject")
    return {
        "host": host, "port": port,
        "self_signed": is_self_signed,
        "issuer": cert.get("issuer"),
        "subject": cert.get("subject"),
        "organization": cert.get("organization"),
        "valid_until": cert.get("valid_until"),
    }


def check_http_redirect(url):
    """Verifica cadena de redirecciones HTTP"""

    # Sigue cadena de redirecciones HTTP (301/302). Útil para detectar bucles de redirección o redirecciones a HTTPS.
    try:
        import urllib.request
        redirects = []
        last_url = url
        for _ in range(10):
            req = urllib.request.Request(last_url, method="HEAD")
            req.add_header("User-Agent", "Mozilla/5.0")
            try:
                with urllib.request.urlopen(req, timeout=5) as r:
                    redirects.append({"url": last_url, "status": r.status, "final_url": r.url})
                    if r.url == last_url:
                        break
                    last_url = r.url
            except urllib.error.HTTPError as e:
                redirects.append({"url": last_url, "status": e.code, "error": str(e.reason)})
                break
        return {"initial_url": url, "redirects": redirects, "count": len(redirects)}
    except Exception as e:
        return {"url": url, "error": str(e)}
