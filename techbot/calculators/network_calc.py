import ipaddress
import math


def subnet_calc(ip, cidr):
    red = ipaddress.IPv4Network(f"{ip}/{cidr}", strict=False)
    return {
        "network": str(red.network_address),
        "broadcast": str(red.broadcast_address),
        "netmask": str(red.netmask),
        "wildcard": str(red.hostmask),
        "usable_hosts": red.num_addresses - 2,
        "first_ip": str(red.network_address + 1),
        "last_ip": str(red.broadcast_address - 1),
        "cidr": red.prefixlen
    }

def vlsm(base_network, hosts_per_subnet):
    red = ipaddress.IPv4Network(base_network, strict=False)
    subnets = []
    current_network = red.network_address
    prefix = red.prefixlen
    base_net = red

    for hosts in sorted(hosts_per_subnet, reverse=True):
        bits_needed = math.ceil(math.log2(hosts + 2))
        new_prefix = 32 - bits_needed
        if new_prefix <= prefix:
            break
        try:
            sub = ipaddress.IPv4Network(f"{current_network}/{new_prefix}", strict=False)
            subnets.append({
                "network": str(sub.network_address),
                "mask": str(sub.netmask),
                "cidr": sub.prefixlen,
                "hosts": sub.num_addresses - 2,
                "first": str(sub.network_address + 1),
                "last": str(sub.broadcast_address - 1),
                "broadcast": str(sub.broadcast_address)
            })
            current_network = sub.broadcast_address + 1
        except:
            break
    return subnets

def wildcard_to_netmask(wildcard):
    wc_parts = [int(x) for x in wildcard.split('.')]
    mask_parts = [255 - w for w in wc_parts]
    return '.'.join(str(m) for m in mask_parts)

def netmask_to_wildcard(netmask):
    mask_parts = [int(x) for x in netmask.split('.')]
    wc_parts = [255 - m for m in mask_parts]
    return '.'.join(str(w) for w in wc_parts)

def bandwidth_calc(mbps, duration_minutes):
    bits = mbps * 1000000 * 60 * duration_minutes
    bytes = bits / 8
    return {
        "bits": bits,
        "bytes": bytes,
        "megabytes": bytes / (1024 * 1024),
        "gigabytes": bytes / (1024 * 1024 * 1024)
    }

def transfer_time(file_size_mb, speed_mbps):
    speed_mbps = speed_mbps * 0.9
    seconds = (file_size_mb * 8) / speed_mbps
    return {
        "seconds": seconds,
        "minutes": seconds / 60,
        "hours": seconds / 3600
    }

def decibels_to_mw(dbm):
    return 10 ** (dbm / 10)

def mw_to_dbm(mw):
    return 10 * math.log10(mw)

def freespace_loss(distance_km, freq_ghz):
    return 92.45 + 20 * math.log10(distance_km) + 20 * math.log10(freq_ghz)

def snr_calc(signal_dbm, noise_dbm):
    return signal_dbm - noise_dbm

def cable_length_resistance(ohms_per_km, target_ohms):
    return target_ohms / ohms_per_km

def poe_power(voltage, current_a):
    return voltage * current_a

def poe_current(power_w, voltage):
    return power_w / voltage

def cidr_to_mask(cidr):
    return str(ipaddress.IPv4Network(f"0.0.0.0/{cidr}", strict=False).netmask)

def mask_to_cidr(mask):
    return ipaddress.IPv4Network(f"0.0.0.0/{mask}", strict=False).prefixlen

def ipv6_compress(ipv6):
    return str(ipaddress.IPv6Address(ipv6).compressed)

def ipv6_expand(ipv6):
    return str(ipaddress.IPv6Address(ipv6).exploded)

def connection_speed_test():
    import urllib.request
    import time
    url = "http://speedtest.tele2.net/1MB.zip"
    start = time.time()
    try:
        urllib.request.urlopen(url, timeout=10)
        duration = time.time() - start
        speed_mbps = (8 * 1) / duration
        return round(speed_mbps, 2)
    except:
        return None

def ethernet_frame_size(payload_bytes):
    return 18 + payload_bytes

def max_cable_distance(speed_mbps):
    standards = {
        10: 100,
        100: 100,
        1000: 100,
        10000: 55
    }
    return standards.get(speed_mbps, 100)

def power_consumption(voltage, current_a, hours_daily):
    watts = voltage * current_a
    kwh_daily = watts * hours_daily / 1000
    return {
        "watts": watts,
        "kwh_daily": kwh_daily,
        "kwh_monthly": kwh_daily * 30
    }

def ups_autonomy(battery_ah, voltage, load_watts):
    wh = battery_ah * voltage
    hours = wh / load_watts * 0.85
    return round(hours, 2)

def dBm_to_dBW(dbm):
    return dbm - 30

def dBW_to_dBm(dbw):
    return dbw + 30

def frequency_to_wavelength(freq_mhz):
    c = 299792458
    return c / (freq_mhz * 1000000)

def ascii_to_binary(text):
    return ' '.join(format(ord(c), '08b') for c in text)

def binary_to_ascii(binary):
    chars = binary.split()
    return ''.join(chr(int(c, 2)) for c in chars)

def hex_to_dec(hex_val):
    return int(hex_val, 16)

def dec_to_hex(dec_val):
    return hex(dec_val)

def octet_to_binary(octet):
    return format(octet, '08b')

def calculate_vlan_id(vlan_range):
    parts = vlan_range.split('-')
    if len(parts) == 2:
        return list(range(int(parts[0]), int(parts[1]) + 1))
    return [int(vlan_range)]

def ospf_cost(bandwidth_mbps):
    ref = 100
    return ref / bandwidth_mbps
