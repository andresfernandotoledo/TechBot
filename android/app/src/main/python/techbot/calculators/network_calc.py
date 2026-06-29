import ipaddress
import math


def subnet_calc(ip, cidr):
    """Calcula todos los parámetros de una subred IPv4."""
    try:
        red = ipaddress.IPv4Network(f"{ip}/{cidr}", strict=False)
    except ValueError as e:
        raise ValueError(f"IP o CIDR inválido: {e}")
    usable = red.num_addresses - 2 if red.num_addresses > 2 else 0
    return {
        "network":      str(red.network_address),
        "broadcast":    str(red.broadcast_address),
        "netmask":      str(red.netmask),
        "wildcard":     str(red.hostmask),
        "cidr":         red.prefixlen,
        "usable_hosts": usable,
        "first_ip":     str(red.network_address + 1) if usable > 0 else "N/A",
        "last_ip":      str(red.broadcast_address - 1) if usable > 0 else "N/A",
        "total_ips":    red.num_addresses,
        "ip_class":     _ip_class(str(red.network_address)),
        "is_private":   red.is_private,
        "is_loopback":  red.is_loopback,
    }


def _ip_class(ip):
    first = int(ip.split(".")[0])
    if first < 128:   return "A"
    if first < 192:   return "B"
    if first < 224:   return "C"
    if first < 240:   return "D (Multicast)"
    return "E (Reservado)"


def vlsm(base_network, hosts_per_subnet):
    """
    Calcula subredes VLSM a partir de una red base y lista de hosts requeridos.
    Ordena de mayor a menor automáticamente.
    """
    try:
        red = ipaddress.IPv4Network(base_network, strict=False)
    except ValueError as e:
        raise ValueError(f"Red base inválida: {e}")

    subnets         = []
    errors          = []
    current_address = red.network_address

    for hosts in sorted(hosts_per_subnet, reverse=True):
        if hosts < 1:
            errors.append(f"Hosts inválido: {hosts}")
            continue
        bits_needed = math.ceil(math.log2(hosts + 2))
        new_prefix  = 32 - bits_needed

        if new_prefix < red.prefixlen:
            errors.append(f"No caben {hosts} hosts dentro de {base_network}")
            continue
        if new_prefix > 30:
            new_prefix = 30  # mínimo /30 para tener 2 hosts

        try:
            sub = ipaddress.IPv4Network(f"{current_address}/{new_prefix}", strict=False)
            # Verificar que la subred esté dentro de la red base
            if not sub.subnet_of(red):
                errors.append(f"Subred {sub} excede el rango de {base_network}")
                break
            subnets.append({
                "network":      str(sub.network_address),
                "mask":         str(sub.netmask),
                "cidr":         sub.prefixlen,
                "hosts_needed": hosts,
                "hosts_usable": sub.num_addresses - 2,
                "first":        str(sub.network_address + 1),
                "last":         str(sub.broadcast_address - 1),
                "broadcast":    str(sub.broadcast_address),
                "next_network": str(sub.broadcast_address + 1),
            })
            current_address = sub.broadcast_address + 1
        except Exception as e:
            errors.append(f"Error calculando subred para {hosts} hosts: {e}")
            break

    return {"subnets": subnets, "errors": errors, "base_network": base_network}


def wildcard_to_netmask(wildcard):
    try:
        wc_parts   = [int(x) for x in wildcard.split(".")]
        mask_parts = [255 - w for w in wc_parts]
        return ".".join(str(m) for m in mask_parts)
    except Exception:
        raise ValueError(f"Wildcard inválida: {wildcard}")


def netmask_to_wildcard(netmask):
    try:
        mask_parts = [int(x) for x in netmask.split(".")]
        wc_parts   = [255 - m for m in mask_parts]
        return ".".join(str(w) for w in wc_parts)
    except Exception:
        raise ValueError(f"Máscara inválida: {netmask}")


def bandwidth_calc(mbps, duration_minutes):
    """Calcula datos transferidos dado un ancho de banda y duración."""
    if mbps <= 0 or duration_minutes <= 0:
        raise ValueError("mbps y duration_minutes deben ser positivos")
    bits     = mbps * 1_000_000 * 60 * duration_minutes
    byte_val = bits / 8
    return {
        "bits":      bits,
        "bytes":     byte_val,
        "kilobytes": byte_val / 1024,
        "megabytes": byte_val / (1024 ** 2),
        "gigabytes": byte_val / (1024 ** 3),
        "terabytes": byte_val / (1024 ** 4),
    }


def transfer_time(file_size_mb, speed_mbps, efficiency=0.9):
    """
    Calcula el tiempo de transferencia de un archivo.
    efficiency: factor de eficiencia del enlace (por defecto 90%).
    """
    if file_size_mb <= 0 or speed_mbps <= 0:
        raise ValueError("Tamaño y velocidad deben ser positivos")
    effective_mbps = speed_mbps * efficiency
    seconds = (file_size_mb * 8) / effective_mbps
    return {
        "seconds":          round(seconds, 2),
        "minutes":          round(seconds / 60, 2),
        "hours":            round(seconds / 3600, 4),
        "effective_mbps":   round(effective_mbps, 2),
        "efficiency_pct":   int(efficiency * 100),
    }


def decibels_to_mw(dbm):
    return round(10 ** (dbm / 10), 6)


def mw_to_dbm(mw):
    if mw <= 0:
        raise ValueError("mW debe ser mayor a 0")
    return round(10 * math.log10(mw), 2)


def freespace_loss(distance_km, freq_ghz):
    """Pérdida en espacio libre (FSPL) en dB."""
    if distance_km <= 0 or freq_ghz <= 0:
        raise ValueError("Distancia y frecuencia deben ser positivas")
    fspl = 92.45 + 20 * math.log10(distance_km) + 20 * math.log10(freq_ghz)
    return round(fspl, 2)


def link_budget(tx_power_dbm, tx_gain_dbi, rx_gain_dbi,
                distance_km, freq_ghz, rx_sensitivity_dbm):
    """
    Calcula el margen de enlace (link budget) para un enlace inalámbrico.
    Retorna el margen disponible en dB (positivo = enlace OK).
    """
    fspl   = freespace_loss(distance_km, freq_ghz)
    eirp   = tx_power_dbm + tx_gain_dbi
    rx_lvl = eirp - fspl + rx_gain_dbi
    margin = rx_lvl - rx_sensitivity_dbm
    return {
        "fspl_db":            round(fspl, 2),
        "eirp_dbm":           round(eirp, 2),
        "rx_level_dbm":       round(rx_lvl, 2),
        "rx_sensitivity_dbm": rx_sensitivity_dbm,
        "margin_db":          round(margin, 2),
        "link_ok":            margin >= 0,
        "quality":            _link_quality(margin),
    }


def _link_quality(margin_db):
    if margin_db >= 20: return "Excelente"
    if margin_db >= 10: return "Bueno"
    if margin_db >= 3:  return "Marginal"
    return "Insuficiente"


def snr_calc(signal_dbm, noise_dbm):
    """Relación señal-ruido en dB."""
    return round(signal_dbm - noise_dbm, 2)


def poe_power(voltage, current_a):
    return round(voltage * current_a, 2)


def poe_current(power_w, voltage):
    if voltage <= 0:
        raise ValueError("Voltaje debe ser positivo")
    return round(power_w / voltage, 3)


def poe_standard(power_w):
    """Identifica el estándar PoE adecuado según la potencia requerida."""
    standards = [
        (15.4,  "802.3af (PoE)   — hasta 15.4 W"),
        (30.0,  "802.3at (PoE+)  — hasta 30 W"),
        (60.0,  "802.3bt Tipo 3 (PoE++) — hasta 60 W"),
        (90.0,  "802.3bt Tipo 4 (PoE++) — hasta 90 W"),
    ]
    for limit, name in standards:
        if power_w <= limit:
            return {"standard": name, "max_w": limit, "ok": True}
    return {"standard": "Excede PoE estándar — usar inyector/fuente dedicada", "max_w": 90, "ok": False}


def cidr_to_mask(cidr):
    if not 0 <= int(cidr) <= 32:
        raise ValueError("CIDR debe estar entre 0 y 32")
    return str(ipaddress.IPv4Network(f"0.0.0.0/{cidr}", strict=False).netmask)


def mask_to_cidr(mask):
    try:
        return ipaddress.IPv4Network(f"0.0.0.0/{mask}", strict=False).prefixlen
    except ValueError:
        raise ValueError(f"Máscara inválida: {mask}")


def ipv6_compress(ipv6):
    try:
        return str(ipaddress.IPv6Address(ipv6).compressed)
    except ValueError:
        raise ValueError(f"Dirección IPv6 inválida: {ipv6}")


def ipv6_expand(ipv6):
    try:
        return str(ipaddress.IPv6Address(ipv6).exploded)
    except ValueError:
        raise ValueError(f"Dirección IPv6 inválida: {ipv6}")


def ipv6_info(ipv6):
    """Información completa de una dirección IPv6."""
    addr = ipaddress.IPv6Address(ipv6)
    return {
        "compressed":   str(addr.compressed),
        "expanded":     str(addr.exploded),
        "is_private":   addr.is_private,
        "is_loopback":  addr.is_loopback,
        "is_multicast": addr.is_multicast,
        "is_link_local": addr.is_link_local,
        "ipv4_mapped":  str(addr.ipv4_mapped) if addr.ipv4_mapped else None,
    }


def ethernet_frame_size(payload_bytes):
    """Tamaño total de un frame Ethernet (incluye cabeceras y CRC)."""
    return 18 + payload_bytes  # 14 Ethernet header + 4 CRC


def max_cable_distance(speed_mbps):
    standards = {10: 100, 100: 100, 1000: 100, 10000: 55}
    dist = standards.get(int(speed_mbps), 100)
    return {"speed_mbps": speed_mbps, "max_distance_m": dist,
            "note": "Cat5e/Cat6 UTP estándar"}


def power_consumption(voltage, current_a, hours_daily):
    if voltage <= 0 or current_a <= 0 or hours_daily <= 0:
        raise ValueError("Todos los parámetros deben ser positivos")
    watts       = voltage * current_a
    kwh_daily   = watts * hours_daily / 1000
    kwh_monthly = kwh_daily * 30
    kwh_yearly  = kwh_daily * 365
    return {
        "watts":        round(watts, 2),
        "kwh_daily":    round(kwh_daily, 4),
        "kwh_monthly":  round(kwh_monthly, 2),
        "kwh_yearly":   round(kwh_yearly, 2),
    }


def ups_autonomy(battery_ah, voltage, load_watts, efficiency=0.85):
    """Calcula la autonomía de un UPS en horas y minutos."""
    if load_watts <= 0:
        raise ValueError("Carga debe ser positiva")
    wh    = battery_ah * voltage * efficiency
    hours = wh / load_watts
    return {
        "hours":   round(hours, 2),
        "minutes": round(hours * 60, 0),
        "wh":      round(wh, 1),
    }


def dBm_to_dBW(dbm):
    return round(dbm - 30, 2)


def dBW_to_dBm(dbw):
    return round(dbw + 30, 2)


def frequency_to_wavelength(freq_mhz):
    c = 299_792_458
    wl = c / (freq_mhz * 1_000_000)
    return round(wl, 4)


def ospf_cost(bandwidth_mbps, reference_bw_mbps=100):
    """Costo OSPF. reference_bw_mbps puede ajustarse para redes Gigabit (1000)."""
    if bandwidth_mbps <= 0:
        raise ValueError("Ancho de banda debe ser positivo")
    cost = reference_bw_mbps / bandwidth_mbps
    return max(1, int(cost))  # Costo mínimo = 1


def cable_length_resistance(ohms_per_km, target_ohms):
    if ohms_per_km <= 0:
        raise ValueError("Resistencia por km debe ser positiva")
    return round(target_ohms / ohms_per_km, 2)


def ascii_to_binary(text):
    return " ".join(format(ord(c), "08b") for c in text)


def binary_to_ascii(binary):
    chars = binary.split()
    return "".join(chr(int(c, 2)) for c in chars)


def hex_to_dec(hex_val):
    return int(str(hex_val), 16)


def dec_to_hex(dec_val):
    return hex(int(dec_val))


def octet_to_binary(octet):
    return format(int(octet), "08b")


def calculate_vlan_id(vlan_range):
    parts = str(vlan_range).split("-")
    if len(parts) == 2:
        return list(range(int(parts[0]), int(parts[1]) + 1))
    return [int(vlan_range)]


def summarize_routes(networks):
    """
    Agrupa una lista de redes IPv4 en el menor número de rutas resumidas.
    networks: lista de strings tipo ['192.168.1.0/24', '192.168.2.0/24']
    """
    nets = [ipaddress.IPv4Network(n, strict=False) for n in networks]
    collapsed = list(ipaddress.collapse_addresses(nets))
    return [str(n) for n in collapsed]


def ip_in_subnet(ip, network):
    """Verifica si una IP pertenece a una subred."""
    try:
        return ipaddress.ip_address(ip) in ipaddress.IPv4Network(network, strict=False)
    except ValueError as e:
        raise ValueError(f"IP o red inválida: {e}")


def next_subnet(network_str):
    """Devuelve la siguiente subred del mismo tamaño."""
    net  = ipaddress.IPv4Network(network_str, strict=False)
    next_ip = net.broadcast_address + 1
    return str(ipaddress.IPv4Network(f"{next_ip}/{net.prefixlen}", strict=False))
