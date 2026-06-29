import socket
import struct
import random
import time
import os


def discover_dhcp_servers(timeout=3):
    """Envía DHCPDISCOVER broadcast y colecciona ofertas de servidores DHCP.
    En Android/Linux sin root: bindea a puerto alto (>1024) y escucha."""
    servers = {}
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

        # Intentar bind a puerto 68 (requiere root), fallback a 6768 (no root)
        bind_port = 68
        try:
            sock.bind(("0.0.0.0", bind_port))
        except PermissionError:
            bind_port = 6768
            try:
                sock.bind(("0.0.0.0", bind_port))
            except OSError:
                sock.close()
                # Último intento: bind efímero
                sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
                sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                sock.bind(("0.0.0.0", 0))
                bind_port = sock.getsockname()[1]

        sock.settimeout(timeout)

        # DHCPDISCOVER packet
        xid = random.randint(0, 0xFFFFFFFF)
        chaddr = bytes([random.randint(0, 255) for _ in range(6)])
        # BOOTP header
        bootp = struct.pack("!BBBBLHHH", 1, 1, 6, 0, xid, 0, 0, 0)
        bootp += b"\x00" * 16 + b"\x00" * 16 + b"\x00" * 64 + chaddr + b"\x00" * 10 + b"\x00" * 64 + b"\x00" * 128
        # DHCP options
        options = b"\x63\x82\x53\x63"  # magic cookie
        options += struct.pack(">BB", 53, 1)  # DHCPDISCOVER
        options += struct.pack(">BB", 55, 2) + struct.pack(">BB", 1, 3)  # param list: subnet, router
        options += struct.pack(">BB", 255, 0)  # end
        packet = bootp + options

        sock.sendto(packet, ("255.255.255.255", 67))

        start = time.time()
        while time.time() - start < timeout:
            try:
                data, addr = sock.recvfrom(1024)
                if len(data) < 240:
                    continue
                # Parse DHCP options
                msg_type = None
                server_id = None
                subnet_mask = None
                lease_time = None
                router = None
                dns_servers = None
                domain = None
                pos = 240
                while pos < len(data):
                    if data[pos] == 255:
                        break
                    if data[pos] == 0:
                        pos += 1
                        continue
                    opt_len = data[pos + 1]
                    if data[pos] == 53 and opt_len >= 1:
                        msg_type = data[pos + 2]
                    elif data[pos] == 54 and opt_len >= 4:
                        server_id = socket.inet_ntoa(data[pos + 2:pos + 6])
                    elif data[pos] == 1 and opt_len >= 4:
                        subnet_mask = socket.inet_ntoa(data[pos + 2:pos + 6])
                    elif data[pos] == 51 and opt_len >= 4:
                        lease_time = struct.unpack("!I", data[pos + 2:pos + 6])[0]
                    elif data[pos] == 3 and opt_len >= 4:
                        router = socket.inet_ntoa(data[pos + 2:pos + 6])
                    elif data[pos] == 6:
                        dns_list = []
                        for i in range(0, opt_len, 4):
                            if i + 4 <= opt_len:
                                dns_list.append(socket.inet_ntoa(data[pos + 2 + i:pos + 6 + i]))
                        dns_servers = dns_list
                    elif data[pos] == 15:
                        domain = data[pos + 2:pos + 2 + opt_len].decode("utf-8", errors="replace")
                    pos += opt_len + 2

                if msg_type == 2:  # DHCPOFFER
                    yiaddr = socket.inet_ntoa(data[16:20])
                    if server_id and server_id not in servers:
                        servers[server_id] = {
                            "server_id": server_id,
                            "offered_ip": yiaddr,
                            "subnet_mask": subnet_mask,
                            "lease_time_s": lease_time,
                            "router": router,
                            "dns_servers": dns_servers,
                            "domain": domain,
                            "mac": ":".join(f"{b:02x}" for b in data[28:34]),
                        }
            except socket.timeout:
                break
            except Exception:
                continue
        sock.close()
    except PermissionError:
        return {"error": "Permiso denegado. En Termux/Linux sin root usá: pkg install termux-api o ejecutá como root", "servers": [], "count": 0}
    except OSError as e:
        return {"error": f"Error de red: {e}", "servers": [], "count": 0}
    except Exception as e:
        return {"error": str(e), "servers": [], "count": 0}

    return {"servers": list(servers.values()), "count": len(servers)}


def dhcp_release(interface=None):
    """Libera y renueva DHCP (requiere dhclient en el sistema)."""
    return {"error": "Requiere dhclient (root/sudo). Usá DHCP Discover para ver ofertas sin root."}
