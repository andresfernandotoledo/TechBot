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


def whois_lookup(query, server="whois.iana.org", port=43, timeout=10):
    """Consulta WHOIS directa via TCP."""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        sock.connect((server, port))
        sock.sendall((query + "\r\n").encode())
        data = b""
        while True:
            chunk = sock.recv(4096)
            if not chunk: break
            data += chunk
        sock.close()
        text = data.decode("utf-8", errors="replace")
        lines = [l.strip() for l in text.split("\n") if l.strip()]
        return {"query": query, "server": server, "raw": "\n".join(lines[:60]), "lines": len(lines)}
    except Exception as e:
        return {"query": query, "server": server, "error": str(e)}


def whois_auto(domain):
    """WHOIS con redirección automática (IANA → whois del registro)."""
    result = whois_lookup(domain)
    if "error" in result:
        return result
    # Buscar whois server en la respuesta
    for line in result.get("raw", "").split("\n"):
        if "whois." in line.lower() and "server" in line.lower():
            parts = line.split(":")
            if len(parts) >= 2:
                srv = parts[-1].strip()
                if srv and srv != result["server"]:
                    return whois_lookup(domain, server=srv)
    return result


def ntp_time(host="pool.ntp.org", timeout=3):
    """Obtiene hora de un servidor NTP vía UDP."""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.settimeout(timeout)
        # NTP request: LI=0, VN=4, Mode=3
        pkt = b"\x1b" + 47 * b"\x00"
        sock.sendto(pkt, (host, 123))
        data, _ = sock.recvfrom(1024)
        sock.close()
        if len(data) < 48:
            return {"host": host, "error": "Respuesta corta"}
        import struct
        t = struct.unpack("!12I", data)[10]
        from datetime import datetime, timezone
        ntp_epoch = datetime(1900, 1, 1, tzinfo=timezone.utc)
        ts = ntp_epoch.timestamp() + t
        now = datetime.now(timezone.utc).timestamp()
        offset = round(ts - now, 3)
        return {
            "host": host,
            "ntp_time": datetime.fromtimestamp(ts, timezone.utc).isoformat(),
            "local_time": datetime.now().isoformat(),
            "offset_seconds": offset,
            "stratum": data[47],
        }
    except Exception as e:
        return {"host": host, "error": str(e)}


def port_knock(host, ports, delay=0.2, timeout=2):
    """Port knocking: envía TCP SYN a una secuencia de puertos."""
    results = []
    for port in ports:
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(timeout)
            sock.connect((host, port))
            sock.close()
            results.append({"port": port, "status": "open"})
        except (socket.timeout, ConnectionRefusedError, OSError):
            results.append({"port": port, "status": "sent"})
        time.sleep(delay)
    return {"host": host, "sequence": ports, "results": results, "count": len(results)}


def http_status(url, timeout=5, follow=True):
    """Verifica estado HTTP de una URL."""
    if not url.startswith(("http://", "https://")):
        url = "https://" + url
    try:
        req = urllib.request.Request(url, method="HEAD")
        if not follow:
            class NoRedirect(urllib.request.HTTPRedirectHandler):
                def redirect_request(self, req, fp, code, msg, headers, newurl):
                    return None
            opener = urllib.request.build_opener(NoRedirect)
            resp = opener.open(req, timeout=timeout)
        else:
            resp = urllib.request.urlopen(req, timeout=timeout)
        return {
            "url": url,
            "status": resp.status,
            "reason": resp.reason,
            "redirected": resp.url != url,
            "final_url": resp.url,
        }
    except urllib.error.HTTPError as e:
        return {"url": url, "status": e.code, "reason": str(e.reason), "redirected": False, "final_url": url}
    except Exception as e:
        return {"url": url, "error": str(e)}


def ping_latency(host, count=4, timeout=3):
    """Mide latencia TCP connect a varios puertos (simula ping)."""
    ports = [80, 443, 22, 8080]
    results = []
    for port in ports:
        try:
            start = time.time()
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(timeout)
            sock.connect((host, port))
            elapsed = round((time.time() - start) * 1000, 1)
            sock.close()
            results.append({"port": port, "latency_ms": elapsed, "status": "ok"})
        except:
            pass
    if not results:
        return {"host": host, "error": "Sin respuesta en puertos comunes", "latency_ms": None}
    avg = round(sum(r["latency_ms"] for r in results) / len(results), 1)
    return {"host": host, "results": results, "latency_ms": avg, "min_ms": min(r["latency_ms"] for r in results), "max_ms": max(r["latency_ms"] for r in results)}
