import math


# ── Ley de Ohm ────────────────────────────────────────────────

def ohms_law_v(i, r):
    """V = I × R"""
    return round(i * r, 4)

def ohms_law_i(v, r):
    """I = V / R"""
    if r == 0:
        raise ValueError("Resistencia no puede ser 0")
    return round(v / r, 4)

def ohms_law_r(v, i):
    """R = V / I"""
    if i == 0:
        raise ValueError("Corriente no puede ser 0")
    return round(v / i, 4)

def ohms_law_full(v=None, i=None, r=None, p=None):
    """
    Dado cualquier par de valores (V, I, R, P), calcula los restantes.
    Retorna todos los valores: voltaje, corriente, resistencia y potencia.
    """
    known = {k: val for k, val in {"v": v, "i": i, "r": r, "p": p}.items() if val is not None}
    if len(known) < 2:
        raise ValueError("Se necesitan al menos 2 valores")

    if "v" in known and "i" in known:
        v, i = known["v"], known["i"]
        r = v / i if i != 0 else None
        p = v * i
    elif "v" in known and "r" in known:
        v, r = known["v"], known["r"]
        i = v / r if r != 0 else None
        p = (v ** 2) / r if r != 0 else None
    elif "i" in known and "r" in known:
        i, r = known["i"], known["r"]
        v = i * r
        p = (i ** 2) * r
    elif "p" in known and "v" in known:
        p, v = known["p"], known["v"]
        i = p / v if v != 0 else None
        r = (v ** 2) / p if p != 0 else None
    elif "p" in known and "i" in known:
        p, i = known["p"], known["i"]
        v = p / i if i != 0 else None
        r = p / (i ** 2) if i != 0 else None
    elif "p" in known and "r" in known:
        p, r = known["p"], known["r"]
        v = math.sqrt(p * r) if p * r >= 0 else None
        i = math.sqrt(p / r) if r != 0 else None
    else:
        raise ValueError("Combinación de parámetros no soportada")

    return {
        "voltage_v":    round(v, 4) if v is not None else None,
        "current_a":    round(i, 4) if i is not None else None,
        "resistance_r": round(r, 4) if r is not None else None,
        "power_w":      round(p, 4) if p is not None else None,
    }


# ── Potencia ──────────────────────────────────────────────────

def power_v_i(v, i):
    return round(v * i, 4)

def power_v_r(v, r):
    if r == 0:
        raise ValueError("Resistencia no puede ser 0")
    return round((v ** 2) / r, 4)

def power_i_r(i, r):
    return round((i ** 2) * r, 4)


# ── Resistencias y capacitores ────────────────────────────────

def resistor_series(*resistors):
    return round(sum(resistors), 6)

def resistor_parallel(*resistors):
    valid = [r for r in resistors if r != 0]
    if not valid:
        return 0
    inv_sum = sum(1 / r for r in valid)
    return round(1 / inv_sum, 6) if inv_sum != 0 else 0

def capacitor_series(*caps):
    valid = [c for c in caps if c != 0]
    if not valid:
        return 0
    inv_sum = sum(1 / c for c in valid)
    return round(1 / inv_sum, 10) if inv_sum != 0 else 0

def capacitor_parallel(*caps):
    return round(sum(caps), 10)


# ── Divisores y transformadores ───────────────────────────────

def voltage_divider(vin, r1, r2):
    """Vout = Vin × R2 / (R1 + R2)"""
    if r1 + r2 == 0:
        raise ValueError("R1 + R2 no puede ser 0")
    vout = vin * r2 / (r1 + r2)
    return {
        "vout":       round(vout, 4),
        "vin":        vin,
        "r1":         r1,
        "r2":         r2,
        "ratio":      round(r2 / (r1 + r2), 4),
        "current_ma": round(vin / (r1 + r2) * 1000, 4),
    }

def transformer_turns(vp, vs, np=None, ns=None):
    """Calcula relación de transformador."""
    if np and ns:
        return {"vs_calc": round(vp * ns / np, 4)}
    if np:
        return {"ns_calc": round(np * vs / vp, 4)}
    if ns:
        return {"np_calc": round(ns * vp / vs, 4)}
    return {"ratio": round(vp / vs, 4)}


# ── Señales AC ────────────────────────────────────────────────

def duty_cycle(ton, tperiod):
    if tperiod <= 0:
        raise ValueError("Periodo debe ser positivo")
    return round(ton / tperiod * 100, 2)

def rms_voltage(vpeak):
    return round(vpeak / math.sqrt(2), 4)

def rms_current(ipeak):
    return round(ipeak / math.sqrt(2), 4)

def peak_voltage(vrms):
    return round(vrms * math.sqrt(2), 4)

def peak_to_peak(vrms):
    return round(vrms * math.sqrt(2) * 2, 4)


# ── Componentes reactivos ─────────────────────────────────────

def frequency_lc(l_h, c_f):
    """Frecuencia de resonancia LC."""
    if l_h <= 0 or c_f <= 0:
        raise ValueError("L y C deben ser positivos")
    return round(1 / (2 * math.pi * math.sqrt(l_h * c_f)), 4)

def capacitive_reactance(c_f, freq_hz):
    if c_f == 0 or freq_hz == 0:
        return float("inf")
    return round(1 / (2 * math.pi * freq_hz * c_f), 4)

def inductive_reactance(l_h, freq_hz):
    return round(2 * math.pi * freq_hz * l_h, 4)

def impedance_rlc(r, l_h, c_f, freq_hz):
    """Impedancia de un circuito RLC serie."""
    xl = inductive_reactance(l_h, freq_hz)
    xc = capacitive_reactance(c_f, freq_hz)
    z  = math.sqrt(r ** 2 + (xl - xc) ** 2)
    return {
        "impedance_ohm":   round(z, 4),
        "xl_ohm":          round(xl, 4),
        "xc_ohm":          round(xc, 4),
        "phase_angle_deg": round(math.degrees(math.atan2(xl - xc, r)), 2),
    }


# ── Cables ────────────────────────────────────────────────────

RESISTIVITY = {
    "cobre":    1.68e-8,
    "aluminio": 2.65e-8,
    "oro":      2.44e-8,
    "plata":    1.59e-8,
}

def wire_resistance(length_m, material_or_rho, area_mm2):
    """Resistencia de un conductor."""
    if isinstance(material_or_rho, str):
        rho = RESISTIVITY.get(material_or_rho.lower())
        if rho is None:
            raise ValueError(f"Material desconocido. Opciones: {list(RESISTIVITY.keys())}")
    else:
        rho = float(material_or_rho)
    if area_mm2 <= 0:
        raise ValueError("Área debe ser positiva")
    area_m2 = area_mm2 / 1e6
    return round(rho * length_m / area_m2, 6)

def voltage_drop(length_m, current_a, resistance_per_km):
    """Caída de tensión en cable de ida y vuelta."""
    r_total = resistance_per_km * length_m / 1000
    vd = 2 * current_a * r_total
    return round(vd, 4)

def voltage_drop_pct(vd, vin):
    """Porcentaje de caída de tensión."""
    return round(vd / vin * 100, 2)

def cable_voltage_drop_3phase(length_m, i_a, r_km, x_km=0, pf=0.85):
    """Caída de tensión en sistema trifásico."""
    r   = r_km * length_m / 1000
    x   = x_km * length_m / 1000
    vd  = math.sqrt(3) * i_a * (r * pf + x * math.sin(math.acos(pf)))
    return round(vd, 4)

def max_cable_length(voltage, current_a, material, area_mm2, max_drop_pct=3):
    """
    Calcula la longitud máxima de cable para un % de caída de tensión dado.
    Retorna la longitud máxima en metros (ida y vuelta).
    """
    rho    = RESISTIVITY.get(material.lower(), 1.68e-8)
    area_m2 = area_mm2 / 1e6
    vd_max = voltage * max_drop_pct / 100
    # vd = 2 × I × rho × L / area → L = vd × area / (2 × I × rho)
    if current_a == 0:
        raise ValueError("Corriente no puede ser 0")
    length = (vd_max * area_m2) / (2 * current_a * rho)
    return {
        "max_length_m":   round(length, 1),
        "max_drop_v":     round(vd_max, 3),
        "max_drop_pct":   max_drop_pct,
        "area_mm2":       area_mm2,
        "material":       material,
    }


# ── Trifásico ────────────────────────────────────────────────

def three_phase_power(vll, i, pf, efficiency=1.0):
    """Potencia trifásica activa."""
    return round(math.sqrt(3) * vll * i * pf * efficiency, 2)

def three_phase_current(power_w, vll, pf):
    """Corriente en sistema trifásico."""
    if vll <= 0 or pf <= 0:
        raise ValueError("Voltaje y factor de potencia deben ser positivos")
    return round(power_w / (math.sqrt(3) * vll * pf), 4)

def three_phase_apparent_power(vll, i):
    return round(math.sqrt(3) * vll * i, 2)

def three_phase_reactive_power(vll, i, pf):
    phi = math.acos(pf)
    return round(math.sqrt(3) * vll * i * math.sin(phi), 2)

def power_factor_correction(p_kw, current_pf, target_pf, voltage_v, freq_hz=60):
    """
    Calcula el capacitor necesario para corregir el factor de potencia.
    Retorna la capacidad en kVAR y µF.
    """
    phi1 = math.acos(current_pf)
    phi2 = math.acos(target_pf)
    q_kvar = p_kw * (math.tan(phi1) - math.tan(phi2))
    c_uf   = q_kvar * 1000 / (2 * math.pi * freq_hz * voltage_v ** 2) * 1e6
    return {
        "q_kvar_needed":  round(q_kvar, 3),
        "capacitor_uf":   round(c_uf, 2),
        "current_pf":     current_pf,
        "target_pf":      target_pf,
    }


# ── Baterías y energía solar ──────────────────────────────────

def battery_capacity(load_w, hours, voltage, dod=0.8):
    """
    Calcula la capacidad de batería necesaria.
    dod: profundidad de descarga (default 80%).
    """
    if voltage <= 0:
        raise ValueError("Voltaje debe ser positivo")
    wh         = load_w * hours
    ah         = wh / voltage
    ah_adj     = ah / dod
    return {
        "wh":           round(wh, 2),
        "ah":           round(ah, 2),
        "ah_adjusted":  round(ah_adj, 2),  # Capacidad real considerando DoD
        "dod_pct":      int(dod * 100),
        "voltage":      voltage,
        "note":         f"Con DoD={int(dod*100)}%, necesitás {round(ah_adj,2)} Ah nominales",
    }

def solar_panel_required(load_kwh, sun_hours, panel_w=450, system_efficiency=0.8):
    """
    Calcula cuántos paneles solares se necesitan.
    system_efficiency: pérdidas por cableado, inversor, temperatura (default 80%).
    """
    if sun_hours <= 0:
        raise ValueError("Horas de sol deben ser positivas")
    daily_wh    = load_kwh * 1000
    panels_real = daily_wh / (panel_w * sun_hours * system_efficiency)
    panels      = math.ceil(panels_real)
    total_w     = panels * panel_w
    return {
        "panels_needed":    panels,
        "panels_exact":     round(panels_real, 2),
        "panel_w":          panel_w,
        "total_peak_w":     total_w,
        "daily_generation_kwh": round(total_w * sun_hours * system_efficiency / 1000, 2),
        "system_efficiency_pct": int(system_efficiency * 100),
    }

def solar_system_full(load_w, hours_daily, sun_hours,
                       panel_w=450, battery_voltage=48,
                       battery_dod=0.8, autonomy_days=1,
                       system_efficiency=0.8):
    """
    Dimensionamiento completo de sistema solar fotovoltaico.
    """
    daily_kwh    = load_w * hours_daily / 1000
    panels_info  = solar_panel_required(daily_kwh, sun_hours, panel_w, system_efficiency)
    bat_load_wh  = load_w * hours_daily * autonomy_days
    bat_info     = battery_capacity(load_w * autonomy_days, hours_daily, battery_voltage, battery_dod)

    return {
        "load_w":           load_w,
        "hours_daily":      hours_daily,
        "daily_kwh":        round(daily_kwh, 3),
        "panels":           panels_info,
        "batteries":        bat_info,
        "autonomy_days":    autonomy_days,
        "recommended_inverter_w": round(load_w * 1.25, 0),  # 25% de margen
    }


# ── Código de colores de resistencias ────────────────────────

COLOR_VALUES = {
    "negro": 0, "marron": 1, "rojo": 2, "naranja": 3,
    "amarillo": 4, "verde": 5, "azul": 6, "violeta": 7,
    "gris": 8, "blanco": 9,
}
COLOR_MULTIPLIERS = {
    "negro": 1, "marron": 10, "rojo": 100, "naranja": 1_000,
    "amarillo": 10_000, "verde": 100_000, "azul": 1_000_000,
    "violeta": 10_000_000, "plata": 0.01, "dorado": 0.1,
}
COLOR_TOLERANCE = {
    "marron": "±1%", "rojo": "±2%", "verde": "±0.5%", "azul": "±0.25%",
    "violeta": "±0.1%", "gris": "±0.05%", "dorado": "±5%", "plata": "±10%",
}

def resistor_color_code(bands):
    """Decodifica el código de colores de una resistencia (4 o 5 bandas)."""
    bands = [b.lower() for b in bands]
    try:
        if len(bands) == 4:
            val = (COLOR_VALUES[bands[0]] * 10 + COLOR_VALUES[bands[1]]) * COLOR_MULTIPLIERS[bands[2]]
            tol = COLOR_TOLERANCE.get(bands[3], "desconocida")
        elif len(bands) == 5:
            val = (COLOR_VALUES[bands[0]] * 100 + COLOR_VALUES[bands[1]] * 10 + COLOR_VALUES[bands[2]]) * COLOR_MULTIPLIERS[bands[3]]
            tol = COLOR_TOLERANCE.get(bands[4], "desconocida")
        else:
            raise ValueError("Se necesitan 4 o 5 bandas")
        return {"value_ohms": val, "tolerance": tol,
                "formatted": _format_resistance(val)}
    except KeyError as e:
        raise ValueError(f"Color no reconocido: {e}")

def _format_resistance(ohms):
    if ohms >= 1_000_000:
        return f"{ohms/1_000_000:.2f} MΩ"
    if ohms >= 1_000:
        return f"{ohms/1_000:.2f} kΩ"
    return f"{ohms:.2f} Ω"
