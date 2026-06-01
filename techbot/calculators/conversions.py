def bytes_to_human(size_bytes):
    units = ['B', 'KB', 'MB', 'GB', 'TB', 'PB']
    i = 0
    size = float(size_bytes)
    while size >= 1024 and i < len(units) - 1:
        size /= 1024
        i += 1
    return f"{size:.2f} {units[i]}"

def human_to_bytes(size_str):
    units = {'B': 1, 'KB': 1024, 'MB': 1024**2, 'GB': 1024**3, 'TB': 1024**4}
    size_str = size_str.strip()
    for unit in units:
        if size_str.upper().endswith(unit):
            num = float(size_str[:-len(unit)].strip())
            return int(num * units[unit])
    return int(float(size_str))

def binary_to_decimal(binary_str):
    return int(binary_str, 2)

def decimal_to_binary(decimal):
    return format(decimal, 'b')

def hex_to_binary(hex_str):
    return format(int(hex_str, 16), 'b')

def binary_to_hex(binary_str):
    return hex(int(binary_str, 2))

def ascii_to_hex(text):
    return text.encode('utf-8').hex()

def hex_to_ascii(hex_str):
    bytes_obj = bytes.fromhex(hex_str)
    return bytes_obj.decode('utf-8', errors='replace')

def decimal_to_octal(decimal):
    return oct(decimal)

def octal_to_decimal(octal_str):
    return int(octal_str, 8)

def ip_to_decimal(ip):
    parts = ip.split('.')
    return (int(parts[0]) << 24) + (int(parts[1]) << 16) + (int(parts[2]) << 8) + int(parts[3])

def decimal_to_ip(decimal):
    return f"{(decimal >> 24) & 0xFF}.{(decimal >> 16) & 0xFF}.{(decimal >> 8) & 0xFF}.{decimal & 0xFF}"

def celsius_to_fahrenheit(c):
    return (c * 9/5) + 32

def fahrenheit_to_celsius(f):
    return (f - 32) * 5/9

def celsius_to_kelvin(c):
    return c + 273.15

def kelvin_to_celsius(k):
    return k - 273.15

def meters_to_feet(m):
    return m * 3.28084

def feet_to_meters(ft):
    return ft / 3.28084

def kilometers_to_miles(km):
    return km * 0.621371

def miles_to_kilometers(miles):
    return miles / 0.621371

def watts_to_hp(watts):
    return watts / 745.7

def hp_to_watts(hp):
    return hp * 745.7

def rpm_to_rads(rpm):
    return rpm * 0.10472

def rads_to_rpm(rads):
    return rads / 0.10472

def dbm_to_mw(dbm):
    return 10 ** (dbm / 10)

def mw_to_dbm(mw):
    import math
    if mw <= 0:
        return float('-inf')
    return 10 * math.log10(mw)

def dbi_to_db(dbi, gain=0):
    return dbi + gain

def minutes_to_hours(minutes):
    return minutes / 60

def hours_to_minutes(hours):
    return hours * 60

def days_to_seconds(days):
    return days * 86400

def seconds_to_days(seconds):
    return seconds / 86400

def bps_to_mbps(bps):
    return bps / 1000000

def mbps_to_bps(mbps):
    return mbps * 1000000

def percent_to_decimal(percent):
    return percent / 100

def decimal_to_percent(decimal):
    return decimal * 100

def kva_to_kw(kva, power_factor=0.8):
    return kva * power_factor

def kw_to_kva(kw, power_factor=0.8):
    return kw / power_factor

def awg_to_mm2(awg):
    table = {
        0: 53.49, 1: 42.41, 2: 33.63, 3: 26.67, 4: 21.15,
        5: 16.77, 6: 13.30, 7: 10.55, 8: 8.367, 9: 6.632,
        10: 5.261, 11: 4.172, 12: 3.309, 13: 2.624, 14: 2.081,
        15: 1.650, 16: 1.309, 17: 1.038, 18: 0.823, 19: 0.653,
        20: 0.518, 21: 0.410, 22: 0.326, 23: 0.258, 24: 0.205,
        25: 0.162, 26: 0.129, 27: 0.102, 28: 0.081, 29: 0.064,
        30: 0.051
    }
    return table.get(awg, "Valor no encontrado")

def mm2_to_awg(mm2):
    table = {
        53.49: 0, 42.41: 1, 33.63: 2, 26.67: 3, 21.15: 4,
        16.77: 5, 13.30: 6, 10.55: 7, 8.367: 8, 6.632: 9,
        5.261: 10, 4.172: 11, 3.309: 12, 2.624: 13, 2.081: 14,
        1.650: 15, 1.309: 16, 1.038: 17, 0.823: 18, 0.653: 19,
        0.518: 20, 0.410: 21, 0.326: 22, 0.258: 23, 0.205: 24,
        0.162: 25, 0.129: 26, 0.102: 27, 0.081: 28, 0.064: 29,
        0.051: 30
    }
    closest = min(table.keys(), key=lambda k: abs(k - mm2))
    return table[closest]
