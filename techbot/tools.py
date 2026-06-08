import socket
import ssl
import struct
import time
import base64
import secrets
import urllib.request
import urllib.error
import json
from datetime import datetime


def dns_lookup(host, record_type="A"):
    """Resolución DNS usando socket.getaddrinfo / getnameinfo."""
    try:
        if record_type == "A":
            info = socket.getaddrinfo(host, None, socket.AF_INET, socket.SOCK_STREAM)
            ips = list(set(i[4][0] for i in info))
            return {"host": host, "type": "A", "records": ips, "count": len(ips)}
        elif record_type == "AAAA":
            info = socket.getaddrinfo(host, None, socket.AF_INET6, socket.SOCK_STREAM)
            ips = list(set(i[4][0] for i in info))
            return {"host": host, "type": "AAAA", "records": ips, "count": len(ips)}
        elif record_type == "PTR":
            ip = host
            try:
                name, _, _ = socket.gethostbyaddr(ip)
                return {"host": host, "type": "PTR", "records": [name], "count": 1}
            except socket.herror:
                return {"host": host, "type": "PTR", "records": [], "count": 0, "error": "No PTR record"}
        elif record_type == "ALL":
            info = socket.getaddrinfo(host, None, socket.AF_UNSPEC, socket.SOCK_STREAM)
            records = list(set(f"{i[4][0]} ({'IPv6' if i[0] == socket.AF_INET6 else 'IPv4'})" for i in info))
            return {"host": host, "type": "ALL", "records": records, "count": len(records)}
        else:
            info = socket.getaddrinfo(host, None, socket.AF_INET, socket.SOCK_STREAM)
            ips = list(set(i[4][0] for i in info))
            return {"host": host, "type": record_type, "records": ips, "count": len(ips)}
    except socket.gaierror as e:
        return {"host": host, "type": record_type, "records": [], "count": 0, "error": str(e)}


def reverse_dns(ip):
    """Resolución PTR inversa."""
    return dns_lookup(ip, "PTR")


def dns_mx(domain):
    """Resolución manual MX via DNS query UDP (sin dig)."""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.settimeout(3)
        tid = secrets.randbits(16)
        # DNS query: header(12 bytes) + question
        header = struct.pack(">HHHHHH", tid, 0x0100, 1, 0, 0, 0)
        labels = domain.strip(".").split(".")
        qname = b"".join(bytes([len(l)]) + l.encode() for l in labels) + b"\x00"
        qtype_mx = struct.pack(">HH", 15, 1)  # MX record, IN class
        query = header + qname + qtype_mx
        sock.sendto(query, ("8.8.8.8", 53))
        data, _ = sock.recvfrom(1024)
        sock.close()
        records = []
        offset = len(header) + len(qname) + 4  # skip question
        ancount = struct.unpack(">H", data[6:8])[0]
        for _ in range(ancount):
            if data[offset] & 0xC0: offset += 2
            else:
                while data[offset] != 0: offset += 1
                offset += 1
            rtype, rclass, ttl, rdlength = struct.unpack(">HHIH", data[offset:offset+10])
            offset += 10
            if rtype == 15:
                pref = struct.unpack(">H", data[offset:offset+2])[0]
                pos = offset + 2
                name_parts = []
                while data[pos] != 0:
                    if data[pos] & 0xC0:
                        name_parts.append(".")
                        break
                    l = data[pos]
                    name_parts.append(data[pos+1:pos+1+l].decode())
                    pos += l + 1
                records.append({"priority": pref, "exchange": ".".join(name_parts)})
            offset += rdlength
        records.sort(key=lambda r: r["priority"])
        return {"domain": domain, "type": "MX", "records": records, "count": len(records)}
    except Exception as e:
        return {"domain": domain, "type": "MX", "records": [], "count": 0, "error": str(e)}


def ssl_cert_check(host, port=443, timeout=5):
    """Verifica certificado SSL de un host:puerto."""
    try:
        ctx = ssl.create_default_context()
        ctx.check_hostname = True
        ctx.verify_mode = ssl.CERT_REQUIRED
        with socket.create_connection((host, port), timeout=timeout) as sock:
            with ctx.wrap_socket(sock, server_hostname=host) as ssock:
                cert = ssock.getpeercert()
                if not cert:
                    return {"host": host, "port": port, "error": "No certificate", "valid": False}
                issuer = dict(x[0] for x in cert.get("issuer", []))
                subject = dict(x[0] for x in cert.get("subject", []))
                not_before = cert.get("notBefore", "")
                not_after = cert.get("notAfter", "")
                cn = subject.get("commonName", host)
                sans = [x[1] for x in cert.get("subjectAltName", [])] if "subjectAltName" in cert else []
                now = datetime.utcnow()
                try:
                    from datetime import datetime as dt2
                    expires = dt2.strptime(not_after, "%b %d %H:%M:%S %Y %Z")
                    days_left = (expires - now).days
                except:
                    days_left = None
                return {
                    "host": host, "port": port, "valid": True,
                    "cn": cn, "alt_names": sans,
                    "issuer": issuer.get("organizationName", issuer.get("commonName", "?")),
                    "subject": subject.get("organizationName", ""),
                    "not_before": not_before,
                    "not_after": not_after,
                    "days_left": days_left,
                    "protocol": ssock.version(),
                    "cipher": ssock.cipher()[0],
                }
    except ssl.SSLCertVerificationError as e:
        return {"host": host, "port": port, "error": str(e), "valid": False}
    except Exception as e:
        return {"host": host, "port": port, "error": str(e), "valid": False}


def http_headers(url, timeout=5):
    """Obtiene headers HTTP de una URL."""
    if not url.startswith(("http://", "https://")):
        url = "https://" + url
    try:
        req = urllib.request.Request(url, method="HEAD")
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            headers = dict(resp.headers)
            return {
                "url": url,
                "status": resp.status,
                "reason": resp.reason,
                "headers": headers,
                "count": len(headers),
            }
    except urllib.error.HTTPError as e:
        return {"url": url, "status": e.code, "reason": str(e.reason), "headers": dict(e.headers), "error": None}
    except Exception as e:
        return {"url": url, "error": str(e)}


def wake_on_lan(mac, broadcast="255.255.255.255", port=9):
    """Envía magic packet Wake-on-LAN."""
    try:
        mac_clean = mac.replace(":", "").replace("-", "").replace(".", "")
        if len(mac_clean) != 12:
            return {"success": False, "error": "MAC inválida (formato: AA:BB:CC:DD:EE:FF)"}
        mac_bytes = bytes.fromhex(mac_clean)
        magic = b"\xff" * 6 + mac_bytes * 16
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        sock.sendto(magic, (broadcast, port))
        sock.close()
        return {"success": True, "mac": mac, "broadcast": broadcast, "port": port, "message": f"WOL enviado a {mac}"}
    except Exception as e:
        return {"success": False, "error": str(e)}


def generate_token(length=32, use_digits=True, use_symbols=True):
    """Genera token/password seguro."""
    alphabet = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"
    if use_digits: alphabet += "0123456789"
    if use_symbols: alphabet += "!@#$%^&*()-_=+[]{}|;:,.<>?/~"
    token = "".join(secrets.choice(alphabet) for _ in range(length))
    strength = "weak"
    if length >= 16 and use_digits and use_symbols: strength = "strong"
    elif length >= 8: strength = "medium"
    return {"token": token, "length": length, "strength": strength, "entropy_bits": len(token).bit_length() * length}


def local_ip():
    """Detecta la IP local y subred."""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.settimeout(1)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        parts = ip.split(".")
        subnet = f"{parts[0]}.{parts[1]}.{parts[2]}.0/24"
        return {"ip": ip, "subnet": subnet, "interface": ""}
    except:
        try:
            ip = socket.gethostbyname(socket.gethostname())
            if ip.startswith("127."):
                return {"ip": ip, "subnet": "unknown", "error": "No network"}
            parts = ip.split(".")
            subnet = f"{parts[0]}.{parts[1]}.{parts[2]}.0/24"
            return {"ip": ip, "subnet": subnet, "interface": ""}
        except:
            return {"ip": "unknown", "subnet": "unknown", "error": "No network detected"}
