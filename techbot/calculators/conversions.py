"""
conversions.py — Conversiones de unidades para TechBot
Cubre: datos, temperatura, longitud, energía, electricidad, RF, tiempo y más.
"""
import math


# ── Datos / Almacenamiento ────────────────────────────────────

def bytes_to_human(size_bytes):
    """Convierte bytes a la unidad más legible."""
    if size_bytes < 0:
        raise ValueError("El tamaño no puede ser negativo")
    units = ["B", "KB", "MB", "GB", "TB", "PB", "EB"]
    size  = float(size_bytes)
    i     = 0
    while size >= 1024 and i < len(units) - 1:
        size /= 1024
        i += 1
    return f"{size:.2f} {units[i]}"

def human_to_bytes(size_str):
    """Convierte '1.5 GB' → bytes."""
    units = {"B": 1, "KB": 1024, "MB": 1024**2, "GB": 1024**3,
             "TB": 1024**4, "PB": 1024**5}
    size_str = size_str.strip().upper()
    for unit, factor in sorted(units.items(), key=lambda x: -len(x[0])):
        if size_str.endswith(unit):
            num = float(size_str[: -len(unit)].strip())
            return int(num * factor)
    return int(float(size_str))

def bits_to_bytes(bits):
    return bits / 8

def bytes_to_bits(byte_val):
    return byte_val * 8

def bps_to_mbps(bps):
    return round(bps / 1_000_000, 4)

def mbps_to_bps(mbps):
    return int(mbps * 1_000_000)

def mbps_to_gbps(mbps):
    return round(mbps / 1000, 4)

def gbps_to_mbps(gbps):
    return round(gbps * 1000, 2)


# ── Temperatura ───────────────────────────────────────────────

def celsius_to_fahrenheit(c):
    return round((c * 9 / 5) + 32, 2)

def fahrenheit_to_celsius(f):
    return round((f - 32) * 5 / 9, 2)

def celsius_to_kelvin(c):
    return round(c + 273.15, 2)

def kelvin_to_celsius(k):
    if k < 0:
        raise ValueError("Kelvin no puede ser negativo")
    return round(k - 273.15, 2)

def fahrenheit_to_kelvin(f):
    return celsius_to_kelvin(fahrenheit_to_celsius(f))

def kelvin_to_fahrenheit(k):
    return celsius_to_fahrenheit(kelvin_to_celsius(k))


# ── Longitud / Distancia ──────────────────────────────────────

def meters_to_feet(m):
    return round(m * 3.28084, 4)

def feet_to_meters(ft):
    return round(ft / 3.28084, 4)

def kilometers_to_miles(km):
    return round(km * 0.621371, 4)

def miles_to_kilometers(miles):
    return round(miles / 0.621371, 4)

def meters_to_inches(m):
    return round(m * 39.3701, 4)

def inches_to_meters(inch):
    return round(inch / 39.3701, 4)

def cm_to_inches(cm):
    return round(cm / 2.54, 4)

def inches_to_cm(inch):
    return round(inch * 2.54, 4)


# ── Potencia y energía eléctrica ──────────────────────────────

def watts_to_hp(watts):
    return round(watts / 745.7, 4)

def hp_to_watts(hp):
    return round(hp * 745.7, 2)

def kva_to_kw(kva, power_factor=0.8):
    return round(kva * power_factor, 4)

def kw_to_kva(kw, power_factor=0.8):
    if power_factor <= 0:
        raise ValueError("Factor de potencia debe ser positivo")
    return round(kw / power_factor, 4)

def kw_to_kwh(kw, hours):
    return round(kw * hours, 4)

def kwh_to_joules(kwh):
    return round(kwh * 3_600_000, 2)

def joules_to_kwh(joules):
    return round(joules / 3_600_000, 6)

def watts_to_dbm(watts):
    if watts <= 0:
        raise ValueError("Potencia debe ser positiva")
    return round(10 * math.log10(watts * 1000), 2)

def dbm_to_watts(dbm):
    return round(10 ** (dbm / 10) / 1000, 6)


# ── RF / Señal ────────────────────────────────────────────────

def dbm_to_mw(dbm):
    return round(10 ** (dbm / 10), 6)

def mw_to_dbm(mw):
    if mw <= 0:
        raise ValueError("mW debe ser positivo")
    return round(10 * math.log10(mw), 2)

def dbi_to_dbd(dbi):
    """Convierte ganancia dBi a dBd (dBd = dBi - 2.15)."""
    return round(dbi - 2.15, 2)

def dbd_to_dbi(dbd):
    return round(dbd + 2.15, 2)

def dbm_signal_quality(dbm):
    """Clasifica la calidad de señal WiFi/celular según dBm."""
    if dbm >= -50:   return {"quality": "Excelente", "description": "Señal muy fuerte"}
    if dbm >= -60:   return {"quality": "Buena",     "description": "Buena señal"}
    if dbm >= -70:   return {"quality": "Regular",   "description": "Señal aceptable"}
    if dbm >= -80:   return {"quality": "Pobre",     "description": "Señal débil"}
    return               {"quality": "Muy pobre",    "description": "Señal casi inexistente"}


# ── Cables eléctricos ─────────────────────────────────────────

AWG_TO_MM2 = {
    0: 53.49, 1: 42.41, 2: 33.63, 3: 26.67, 4: 21.15,
    5: 16.77, 6: 13.30, 7: 10.55, 8: 8.367, 9: 6.632,
    10: 5.261, 11: 4.172, 12: 3.309, 13: 2.624, 14: 2.081,
    15: 1.650, 16: 1.309, 17: 1.038, 18: 0.823, 19: 0.653,
    20: 0.518, 21: 0.410, 22: 0.326, 23: 0.258, 24: 0.205,
    25: 0.162, 26: 0.129, 27: 0.102, 28: 0.081, 29: 0.064,
    30: 0.051,
}

def awg_to_mm2(awg):
    awg = int(awg)
    result = AWG_TO_MM2.get(awg)
    if result is None:
        raise ValueError(f"AWG {awg} no soportado. Rango válido: 0–30")
    return result

def mm2_to_awg(mm2):
    mm2 = float(mm2)
    if mm2 <= 0:
        raise ValueError("El área debe ser positiva")
    closest = min(AWG_TO_MM2.items(), key=lambda kv: abs(kv[1] - mm2))
    return {"awg": closest[0], "mm2_exact": closest[1], "mm2_input": mm2}

def awg_info(awg):
    """Información completa de un calibre AWG."""
    awg = int(awg)
    mm2 = awg_to_mm2(awg)
    diameter_mm = round(math.sqrt(mm2 * 4 / math.pi), 3)
    # Resistencia típica del cobre a 20°C (Ω/km)
    r_km = round(17.241 / mm2, 3)
    return {
        "awg":          awg,
        "mm2":          mm2,
        "diameter_mm":  diameter_mm,
        "resistance_ohm_per_km": r_km,
        "typical_use":  _awg_typical_use(awg),
    }

def _awg_typical_use(awg):
    if awg <= 4:   return "Acometidas industriales, tableros principales"
    if awg <= 8:   return "Circuitos de alta potencia, aires acondicionados"
    if awg <= 12:  return "Circuitos de 20A, tomas corrientes, CCTV alimentación"
    if awg <= 16:  return "Alumbrado, circuitos de 15A"
    if awg <= 18:  return "Cableado de señal, PoE, cámaras IP"
    if awg <= 22:  return "Control, alarmas, intercomunicación"
    return              "Señal de baja potencia, datos"


# ── Tiempo ────────────────────────────────────────────────────

def minutes_to_hours(minutes):
    return round(minutes / 60, 4)

def hours_to_minutes(hours):
    return round(hours * 60, 2)

def days_to_seconds(days):
    return int(days * 86400)

def seconds_to_days(seconds):
    return round(seconds / 86400, 4)

def seconds_to_hms(seconds):
    """Convierte segundos a formato hh:mm:ss."""
    seconds = int(seconds)
    h = seconds // 3600
    m = (seconds % 3600) // 60
    s = seconds % 60
    return {"hours": h, "minutes": m, "seconds": s,
            "formatted": f"{h:02d}:{m:02d}:{s:02d}"}


# ── Ángulo / Movimiento ───────────────────────────────────────

def rpm_to_rads(rpm):
    return round(rpm * 0.10472, 4)

def rads_to_rpm(rads):
    return round(rads / 0.10472, 4)

def degrees_to_radians(deg):
    return round(math.radians(deg), 6)

def radians_to_degrees(rad):
    return round(math.degrees(rad), 4)


# ── Numérico / Bases ──────────────────────────────────────────

def binary_to_decimal(binary_str):
    return int(str(binary_str), 2)

def decimal_to_binary(decimal):
    return format(int(decimal), "b")

def hex_to_binary(hex_str):
    return format(int(str(hex_str), 16), "b")

def binary_to_hex(binary_str):
    return hex(int(str(binary_str), 2))

def decimal_to_octal(decimal):
    return oct(int(decimal))

def octal_to_decimal(octal_str):
    return int(str(octal_str), 8)

def decimal_to_hex(decimal):
    return hex(int(decimal))

def hex_to_decimal(hex_str):
    return int(str(hex_str), 16)


# ── Texto / Encoding ──────────────────────────────────────────

def ascii_to_hex(text):
    return text.encode("utf-8").hex()

def hex_to_ascii(hex_str):
    return bytes.fromhex(hex_str).decode("utf-8", errors="replace")

def text_to_base64(text):
    import base64
    return base64.b64encode(text.encode("utf-8")).decode("utf-8")

def base64_to_text(b64_str):
    import base64
    return base64.b64decode(b64_str.encode("utf-8")).decode("utf-8", errors="replace")


# ── IP / Redes ────────────────────────────────────────────────

def ip_to_decimal(ip):
    parts = ip.split(".")
    if len(parts) != 4:
        raise ValueError(f"IP inválida: {ip}")
    return sum(int(p) << (8 * (3 - i)) for i, p in enumerate(parts))

def decimal_to_ip(decimal):
    decimal = int(decimal)
    return ".".join(str((decimal >> (8 * i)) & 0xFF) for i in reversed(range(4)))


# ── Porcentajes ───────────────────────────────────────────────

def percent_to_decimal(percent):
    return round(percent / 100, 6)

def decimal_to_percent(decimal):
    return round(decimal * 100, 4)
