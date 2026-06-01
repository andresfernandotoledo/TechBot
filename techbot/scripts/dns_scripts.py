import socket
import subprocess
import sys
import ipaddress
import struct


def dns_lookup(domain, server=None):
    """Resolución DNS directa (A record)"""

    # Resuelve un dominio a IP (registro A). Si se especifica servidor, usa dig @server. Si no, usa socket.gethostbyname().
    try:
        if server:
            old_res = socket.getaddrinfo
            result = subprocess.getoutput(
                f"dig @{server} {domain} +short 2>/dev/null || "
                f"nslookup {domain} {server} 2>/dev/null"
            )
            return result or "Sin respuesta"
        ip = socket.gethostbyname(domain)
        return ip
    except socket.gaierror:
        return None


def dns_reverse_lookup(ip):
    """Resolución DNS inversa (PTR record)"""

    # Resolución inversa (PTR). Dada una IP, devuelve el nombre de host. socket.gethostbyaddr() consulta el registro PTR.
    try:
        hostname = socket.gethostbyaddr(ip)[0]
        return hostname
    except socket.herror:
        return None


def dns_mx_records(domain):
    """Consulta registros MX de un dominio"""

    # Consulta registros MX de un dominio. Usa dig MX +short. Parsea la salida en formato prioridad + servidor. Intenta dns.resolver si falla.
    output = subprocess.getoutput(f"dig {domain} MX +short 2>/dev/null")
    if not output:
        try:
            import dns.resolver
            answers = dns.resolver.resolve(domain, "MX")
            return "\n".join([str(r) for r in answers])
        except ImportError:
            output = subprocess.getoutput(
                f"nslookup -type=MX {domain} 2>/dev/null | grep 'mail exchanger'"
            )
    records = []
    for line in output.strip().split("\n"):
        parts = line.strip().split()
        if parts:
            priority = parts[0] if parts[0].isdigit() else "?"
            mail_server = parts[-1] if len(parts) > 1 else line.strip()
            records.append({"priority": int(priority) if priority.isdigit() else 0, "server": mail_server})
    return records if records else output


def dns_ns_records(domain):
    """Consulta servidores NS de un dominio"""

    # Nameservers del dominio. dig NS +short devuelve los servidores de nombres autoritativos. Fallback: nslookup -type=NS.
    output = subprocess.getoutput(f"dig {domain} NS +short 2>/dev/null")
    if not output:
        output = subprocess.getoutput(f"nslookup -type=NS {domain} 2>/dev/null | grep 'nameserver'")
    return output.strip().split("\n") if output.strip() else []


def dns_txt_records(domain):
    """Consulta registros TXT de un dominio"""

    # Registros TXT del dominio. dig TXT +short. Incluye SPF, DKIM, verificaciones de dominio. Útil para diagnóstico de email.
    output = subprocess.getoutput(f"dig {domain} TXT +short 2>/dev/null")
    if not output:
        output = subprocess.getoutput(f"nslookup -type=TXT {domain} 2>/dev/null | grep 'text'")
    return output.strip().split("\n") if output.strip() else []


def dns_cname(domain):
    """Consulta registro CNAME de un dominio"""

    # Registro CNAME (alias canónico). dig CNAME +short. Muestra a qué dominio apunta el alias.
    output = subprocess.getoutput(f"dig {domain} CNAME +short 2>/dev/null")
    if not output:
        output = subprocess.getoutput(f"nslookup -type=CNAME {domain} 2>/dev/null")
    return output.strip() or None


def dns_aaaa_lookup(domain):
    """Resolución DNS IPv6 (AAAA record)"""

    # Resolución IPv6. dig AAAA +short devuelve direcciones IPv6 del dominio. Si no hay, devuelve None.
    try:
        output = subprocess.getoutput(f"dig {domain} AAAA +short 2>/dev/null")
        if not output:
            output = subprocess.getoutput(f"nslookup -type=AAAA {domain} 2>/dev/null | grep 'AAAA'")
        return output.strip().split("\n") if output.strip() else None
    except Exception:
        return None


def dns_srv_records(service, protocol, domain):
    """Consulta registros SRV ej: _sip._tcp.ejemplo.com"""

    # Registros SRV para servicios específicos. Formato: _service._protocol.dominio. Ej: _sip._tcp.ejemplo.com. Parsea prioridad, peso, puerto y target.
    query = f"_{service}._{protocol}.{domain}"
    output = subprocess.getoutput(f"dig {query} SRV +short 2>/dev/null")
    if not output:
        output = subprocess.getoutput(f"nslookup -type=SRV {query} 2>/dev/null")
    records = []
    for line in output.strip().split("\n"):
        parts = line.strip().split()
        if len(parts) >= 4:
            records.append({
                "priority": parts[0], "weight": parts[1],
                "port": parts[2], "target": parts[3],
            })
    return records if records else output


def dns_soa(domain):
    """Consulta registro SOA (Start of Authority)"""

    # Registro SOA (Start of Authority). Muestra servidor primario, email del admin, serial, refresh, retry, expire y TTL mínimo.
    output = subprocess.getoutput(f"dig {domain} SOA +short 2>/dev/null")
    if not output:
        output = subprocess.getoutput(f"nslookup -type=SOA {domain} 2>/dev/null | grep 'origin'")
    return output.strip() or None


def dns_chain_resolve(domain):
    """Resolución por cadena: desde root hasta el NS autoritativo"""

    # Resolución por cadena desde los root servers. dig +trace sigue la resolución desde la raíz hasta el NS autoritativo del dominio.
    output = subprocess.getoutput(f"dig +trace {domain} 2>/dev/null | head -60")
    if not output:
        output = subprocess.getoutput(f"dig {domain} +norecurse 2>/dev/null")
    return output if output else "No se pudo trazar la cadena DNS"


def dns_check_port(server="8.8.8.8", port=53):
    """Verifica si un servidor DNS responde en puerto UDP/TCP 53"""

    # Verifica si un servidor DNS responde en puerto 53 UDP y TCP. UDP para consultas normales, TCP para consultas grandes (AXFR, >512 bytes).
    udp_result = {"server": server, "port": port, "protocol": "UDP"}
    tcp_result = {"server": server, "port": port, "protocol": "TCP"}
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.settimeout(3)
        sock.connect((server, port))
        udp_result["reachable"] = True
        sock.close()
    except Exception as e:
        udp_result["reachable"] = False
        udp_result["error"] = str(e)
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(3)
        sock.connect((server, port))
        tcp_result["reachable"] = True
        sock.close()
    except Exception as e:
        tcp_result["reachable"] = False
        tcp_result["error"] = str(e)
    return {"udp": udp_result, "tcp": tcp_result}


def dns_batch_resolve(domains):
    """Resuelve múltiples dominios en lote"""

    # Resuelve múltiples dominios en lote. Acepta string separado por comas o lista. Devuelve dict {dominio: {ip, status}}.
    if isinstance(domains, str):
        domains = [d.strip() for d in domains.split(",")]
    results = {}
    for domain in domains:
        domain = domain.strip()
        if not domain:
            continue
        try:
            ip = socket.gethostbyname(domain)
            results[domain] = {"ip": ip, "status": "ok"}
        except socket.gaierror:
            results[domain] = {"ip": None, "status": "error"}
    return results


def dns_edns_check(domain):
    """Verifica si el servidor DNS soporta EDNS (Extension Mechanisms for DNS)"""

    # Verifica soporte de EDNS (Extension Mechanisms for DNS). EDNS permite consultas más grandes y DNSSEC. bool(output) indica soporte.
    output = subprocess.getoutput(f"dig +edns {domain} +short 2>/dev/null")
    edns = subprocess.getoutput(
        f"dig {domain} +dnssec +short 2>/dev/null"
    )
    return {
        "edns_support": bool(output),
        "dnssec_support": bool(edns),
        "note": "Usar 'dig +edns {domain}' y 'dig +dnssec {domain}' para detalles",
    }


def dns_cache_check(domain):
    """Verifica si hay caché DNS local para un dominio"""

    # Verifica si hay caché DNS local. En Linux dig +norecurse para ver respuesta en caché. En Windows ipconfig /displaydns.
    if sys.platform == "linux":
        result = subprocess.getoutput(
            f"dig {domain} +norecurse 2>/dev/null | grep -E 'ANSWER SECTION|AUTHORITY'"
        )
        return result or "No hay respuesta en caché local"
    elif sys.platform == "win32":
        result = subprocess.getoutput(f"ipconfig /displaydns | findstr {domain.split('.')[0]}")
        return result.strip() or "No se encontró en caché DNS"
    return subprocess.getoutput(f"nslookup {domain} 2>/dev/null")


def dns_flush_cache():
    """Limpia la caché DNS local"""

    # Limpia caché DNS. En Linux reinicia systemd-resolved o rndc flush. En Windows ipconfig /flushdns. En macOS dscacheutil -flushcache.
    if sys.platform == "linux":
        result = subprocess.getoutput(
            "systemctl restart systemd-resolved 2>/dev/null || "
            "rndc flush 2>/dev/null || "
            "dscacheutil -flushcache 2>/dev/null || "
            "echo 'No se pudo limpiar caché DNS'"
        )
    elif sys.platform == "win32":
        result = subprocess.getoutput("ipconfig /flushdns")
    else:
        result = subprocess.getoutput("dscacheutil -flushcache 2>/dev/null || echo 'No soportado'")
    return result.strip()


def dns_compare_resolvers(domain, resolvers=None):
    """Compara la respuesta de múltiples resolvers DNS"""

    # Compara la respuesta de múltiples resolvers para un mismo dominio. Por defecto: Google (8.8.8.8), Cloudflare (1.1.1.1), OpenDNS (208.67.222.222).
    if resolvers is None:
        resolvers = ["8.8.8.8", "1.1.1.1", "208.67.222.222"]
    if isinstance(resolvers, str):
        resolvers = [r.strip() for r in resolvers.split(",")]
    results = {}
    for resolver in resolvers:
        resolver = resolver.strip()
        try:
            ip = subprocess.getoutput(f"dig @{resolver} {domain} +short 2>/dev/null")
            results[resolver] = ip.strip() or "Sin respuesta"
        except Exception as e:
            results[resolver] = f"Error: {e}"
    return results


def dns_zone_transfer_check(domain, nameserver=None):
    """Verifica si un servidor DNS permite transferencia de zona (AXFR)"""

    # Verifica si un servidor permite transferencia de zona (AXFR). Si permite, cualquiera puede obtener todos los registros del dominio (vulnerabilidad).
    if not nameserver:
        ns = dns_ns_records(domain)
        if ns:
            nameserver = ns[0]
        else:
            return {"domain": domain, "error": "No se encontraron nameservers"}
    output = subprocess.getoutput(
        f"dig @{nameserver} {domain} AXFR +short 2>/dev/null"
    )
    if "Transfer failed" in output or "failed" in output.lower():
        return {"domain": domain, "nameserver": nameserver, "vulnerable": False, "result": output[:200]}
    if output.strip():
        return {"domain": domain, "nameserver": nameserver, "vulnerable": True, "result": output[:500]}
    return {"domain": domain, "nameserver": nameserver, "vulnerable": False, "result": "Transferencia denegada"}


def dns_spf_check(domain):
    """Consulta registro SPF (Sender Policy Framework)"""

    # Consulta registro SPF (Sender Policy Framework). Busca en registros TXT los que contienen 'v=spf1'. Indica qué servidores pueden enviar email por el dominio.
    records = dns_txt_records(domain)
    spf = [r for r in records if "v=spf1" in r]
    return {"domain": domain, "spf_records": spf if spf else None}


def dns_dkim_check(domain, selector="default"):
    """Consulta registro DKIM para un dominio"""

    # Consulta registro DKIM (DomainKeys Identified Mail). Busca _domainkey.dominio. selector por defecto 'default'. Firma digital de correos.
    query = f"{selector}._domainkey.{domain}"
    output = subprocess.getoutput(f"dig {query} TXT +short 2>/dev/null")
    if not output:
        output = subprocess.getoutput(f"nslookup -type=TXT {query} 2>/dev/null | grep 'text'")
    return {"selector": selector, "domain": domain, "dkim_record": output.strip() or None}


def dns_dmarc_check(domain):
    """Consulta registro DMARC"""

    # Consulta registro DMARC (Domain-based Message Authentication). Busca _dmarc.dominio. Política de qué hacer si SPF/DKIM fallan (reject/quarantine/none).
    query = f"_dmarc.{domain}"
    output = subprocess.getoutput(f"dig {query} TXT +short 2>/dev/null")
    if not output:
        output = subprocess.getoutput(f"nslookup -type=TXT {query} 2>/dev/null")
    return {"domain": domain, "dmarc_record": output.strip() or None}


def dns_email_auth_summary(domain):
    """Resumen de autenticación de email: SPF + DKIM + DMARC"""

    # Resumen de autenticación de email: SPF + DKIM + DMARC. Muestra si cada uno está configurado y su valor.
    spf = dns_spf_check(domain)
    dkim = dns_dkim_check(domain)
    dmarc = dns_dmarc_check(domain)
    return {
        "domain": domain,
        "spf": spf.get("spf_records"),
        "dkim": dkim.get("dkim_record"),
        "dmarc": dmarc.get("dmarc_record"),
        "has_spf": spf.get("spf_records") is not None,
        "has_dkim": dkim.get("dkim_record") is not None,
        "has_dmarc": dmarc.get("dmarc_record") is not None,
    }


def dns_blacklist_check(ip):
    """Verifica si una IP está en listas negras DNS (DNSBL)"""

    # Verifica si una IP está en listas negras DNS (DNSBL). Consulta Spamhaus, SpamCop, SORBS, Barracuda, PSBL. IP listada = posible fuente de spam.
    blacklists = [
        "zen.spamhaus.org",
        "bl.spamcop.net",
        "dnsbl.sorbs.net",
        "b.barracudacentral.org",
        "psbl.surriel.com",
    ]
    try:
        ip_parts = ip.split(".")
        reversed_ip = ".".join(reversed(ip_parts))
        results = {}
        for bl in blacklists:
            query = f"{reversed_ip}.{bl}"
            try:
                result = socket.gethostbyname(query)
                results[bl] = {"listed": True, "response": result}
            except socket.gaierror:
                results[bl] = {"listed": False, "response": None}
        listed_in = [bl for bl, r in results.items() if r["listed"]]
        return {"ip": ip, "blacklists_checked": len(blacklists), "listed_in": listed_in, "details": results}
    except Exception as e:
        return {"ip": ip, "error": str(e)}


def dns_resolver_performance(resolver="8.8.8.8", domain="google.com"):
    """Mide tiempo de respuesta de un resolver DNS"""

    # Mide tiempo de respuesta de un resolver DNS. Envía 3 consultas y calcula promedio, min y max en milisegundos.
    import time
    times = []
    for _ in range(3):
        start = time.time()
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.settimeout(3)
            query = b"\x00\x00\x00\x00\x00\x01\x00\x00\x00\x00\x00\x00" + b"\x06google\x03com\x00\x00\x01\x00\x01"
            sock.sendto(query, (resolver, 53))
            sock.recvfrom(512)
            elapsed = (time.time() - start) * 1000
            times.append(round(elapsed, 1))
        except:
            times.append(None)
        sock.close()
    valid = [t for t in times if t is not None]
    return {
        "resolver": resolver,
        "domain": domain,
        "times_ms": times,
        "avg_ms": round(sum(valid) / len(valid), 1) if valid else None,
        "min_ms": min(valid) if valid else None,
        "max_ms": max(valid) if valid else None,
    }


def dns_ptr_batch(ips):
    """Resolución inversa batch de múltiples IPs"""

    # Resolución inversa (PTR) en lote para múltiples IPs. Acepta string separado por comas o lista. Útil para auditorías de red.
    if isinstance(ips, str):
        ips = [ip.strip() for ip in ips.split(",")]
    results = {}
    for ip in ips:
        ip = ip.strip()
        if not ip:
            continue
        try:
            hostname = socket.gethostbyaddr(ip)[0]
            results[ip] = {"hostname": hostname, "status": "ok"}
        except socket.herror:
            results[ip] = {"hostname": None, "status": "not_found"}
        except Exception as e:
            results[ip] = {"hostname": None, "status": "error", "error": str(e)}
    return results


def dns_query_type(domain, record_type):
    """Consulta genérica: cualquier tipo de registro DNS"""

    # Consulta genérica de cualquier tipo de registro DNS. Tipos válidos: A, AAAA, MX, NS, CNAME, TXT, SOA, SRV, PTR, CAA, NAPTR.
    record_type = record_type.upper()
    valid_types = ["A", "AAAA", "MX", "NS", "CNAME", "TXT", "SOA", "SRV", "PTR", "CAA", "NAPTR"]
    if record_type not in valid_types:
        return {"error": f"Tipo inválido. Válidos: {', '.join(valid_types)}"}
    try:
        if record_type == "A":
            result = dns_lookup(domain)
        elif record_type == "AAAA":
            result = dns_aaaa_lookup(domain)
        elif record_type == "MX":
            result = dns_mx_records(domain)
        elif record_type == "NS":
            result = dns_ns_records(domain)
        elif record_type == "CNAME":
            result = dns_cname(domain)
        elif record_type == "TXT":
            result = dns_txt_records(domain)
        elif record_type == "SOA":
            result = dns_soa(domain)
        elif record_type == "PTR":
            result = dns_reverse_lookup(domain)
        else:
            output = subprocess.getoutput(f"dig {domain} {record_type} +short 2>/dev/null")
            result = output.strip().split("\n") if output.strip() else None
        return {"domain": domain, "type": record_type, "result": result}
    except Exception as e:
        return {"domain": domain, "type": record_type, "error": str(e)}


def dns_caa_records(domain):
    """Consulta registros CAA (Certificate Authority Authorization)"""

    # Registros CAA (Certificate Authority Authorization). Especifica qué CA pueden emitir certificados para el dominio. Parsea flags, tag y valor.
    output = subprocess.getoutput(f"dig {domain} CAA +short 2>/dev/null")
    if not output:
        output = subprocess.getoutput(f"nslookup -type=CAA {domain} 2>/dev/null")
    records = []
    for line in output.strip().split("\n"):
        parts = line.strip().split()
        if len(parts) >= 3:
            records.append({
                "flags": parts[0], "tag": parts[1].strip('"'),
                "value": parts[2].strip('"') if len(parts) > 2 else "",
            })
    return {"domain": domain, "caa_records": records if records else None}


def dns_naptr_records(domain):
    """Consulta registros NAPTR (ENUM, SIP routing)"""

    # Registros NAPTR (Name Authority Pointer). Usados en ENUM (telefonía) y SIP routing. Parsea orden, preferencia, flags, servicio, regex y reemplazo.
    output = subprocess.getoutput(f"dig {domain} NAPTR +short 2>/dev/null")
    if not output:
        return None
    records = []
    for line in output.strip().split("\n"):
        parts = line.strip().split()
        if len(parts) >= 5:
            records.append({
                "order": parts[0], "preference": parts[1],
                "flags": parts[2].strip('"'), "service": parts[3].strip('"'),
                "regexp": parts[4].strip('"'),
                "replacement": parts[5] if len(parts) > 5 else "",
            })
    return records if records else output


def dns_dnssec_validation(domain):
    """Verifica si un dominio tiene DNSSEC válido"""

    # Verifica DNSSEC en un dominio. Busca registros DNSSEC y verifica si la respuesta tiene el flag 'ad' (authentic data).
    try:
        output = subprocess.getoutput(f"dig {domain} +dnssec +cdflag +short 2>/dev/null")
        adflag = subprocess.getoutput(f"dig {domain} +dnssec 2>/dev/null | grep 'flags:' | head -1")
        has_ad = "ad" in adflag.lower() if adflag else False
        return {
            "domain": domain,
            "dnssec_records": output.strip().split("\n") if output.strip() else None,
            "authentic_data_flag": has_ad,
            "dnssec_enabled": bool(output.strip()) or has_ad,
        }
    except Exception as e:
        return {"domain": domain, "error": str(e)}


def dns_root_server_check():
    """Verifica accesibilidad a servidores root DNS"""

    # Verifica accesibilidad a servidores root DNS. Prueba A, B, C, D, E, F root servers enviando una consulta y esperando respuesta.
    roots = [
        "a.root-servers.net", "b.root-servers.net",
        "c.root-servers.net", "d.root-servers.net",
        "e.root-servers.net", "f.root-servers.net",
    ]
    results = {}
    for root in roots:
        try:
            ip = socket.gethostbyname(root)
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.settimeout(3)
            sock.connect((ip, 53))
            sock.sendto(b"\x00\x00\x00\x00\x00\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00", (ip, 53))
            sock.recvfrom(512)
            results[root] = {"ip": ip, "reachable": True}
            sock.close()
        except Exception as e:
            results[root] = {"ip": None, "reachable": False, "error": str(e)}
    return results


def dns_cache_size():
    """Muestra tamaño de la caché DNS local"""

    # Intenta determinar el tamaño de la caché DNS local. systemd-resolve --statistics o rndc status. En Windows cuenta líneas de ipconfig /displaydns.
    if sys.platform == "linux":
        result = subprocess.getoutput(
            "systemd-resolve --statistics 2>/dev/null || "
            "cat /proc/net/stat/dns_resolver 2>/dev/null || "
            "rndc status 2>/dev/null | grep -i cache || "
            "echo 'No disponible'"
        )
    elif sys.platform == "win32":
        result = subprocess.getoutput("ipconfig /displaydns | wc -l 2>/dev/null || echo 'No disponible'")
    else:
        result = "No soportado"
    return {"cache_info": result.strip()}


def dns_check_all_types(domain):
    """Consulta todos los tipos de registro DNS de una vez"""

    # Consulta todos los tipos de registro DNS de una vez. Prueba A, AAAA, MX, NS, TXT, CNAME, SOA, CAA y devuelve solo los que tienen datos.
    types = ["A", "AAAA", "MX", "NS", "TXT", "CNAME", "SOA", "CAA"]
    results = {}
    for t in types:
        try:
            r = dns_query_type(domain, t)
            if r.get("result"):
                results[t] = r["result"]
        except:
            pass
    return {"domain": domain, "records": results}
