import math


def ohms_law_v(i, r):
    return i * r

def ohms_law_i(v, r):
    return v / r if r != 0 else 0

def ohms_law_r(v, i):
    return v / i if i != 0 else 0

def power_v_i(v, i):
    return v * i

def power_v_r(v, r):
    return (v ** 2) / r if r != 0 else 0

def power_i_r(i, r):
    return (i ** 2) * r

def resistor_series(*resistors):
    return sum(resistors)

def resistor_parallel(*resistors):
    if not resistors:
        return 0
    inv_sum = sum(1 / r for r in resistors if r != 0)
    return 1 / inv_sum if inv_sum != 0 else 0

def capacitor_series(*caps):
    if not caps:
        return 0
    inv_sum = sum(1 / c for c in caps if c != 0)
    return 1 / inv_sum if inv_sum != 0 else 0

def capacitor_parallel(*caps):
    return sum(caps)

def voltage_divider(vin, r1, r2):
    return vin * r2 / (r1 + r2)

def frequency_lc(l_h, c_f):
    return 1 / (2 * math.pi * math.sqrt(l_h * c_f))

def capacitive_reactance(c_f, freq_hz):
    return 1 / (2 * math.pi * freq_hz * c_f) if c_f != 0 else float('inf')

def inductive_reactance(l_h, freq_hz):
    return 2 * math.pi * freq_hz * l_h

def wire_resistance(length_m, resistivity, area_mm2):
    rho = {
        "cobre": 1.68e-8,
        "aluminio": 2.65e-8,
        "oro": 2.44e-8,
        "plata": 1.59e-8,
    }
    rho_val = rho.get(resistivity.lower(), resistivity)
    area_m2 = area_mm2 / 1e6
    return rho_val * length_m / area_m2

def voltage_drop(length_m, current_a, resistance_per_km):
    r_total = resistance_per_km * length_m / 1000
    return 2 * current_a * r_total

def transformer_turns(vp, vs, np=None, ns=None):
    if np and ns:
        return vp * ns / np
    if vp and vs and np:
        return np * vs / vp
    if vp and vs and ns:
        return ns * vp / vs
    return None

def duty_cycle(ton, tperiod):
    return ton / tperiod * 100

def rms_voltage(vpeak):
    return vpeak / math.sqrt(2)

def rms_current(ipeak):
    return ipeak / math.sqrt(2)

def peak_voltage(vrms):
    return vrms * math.sqrt(2)

def three_phase_power(vll, i, pf, efficiency=1.0):
    return math.sqrt(3) * vll * i * pf * efficiency

def three_phase_current(power_w, vll, pf):
    return power_w / (math.sqrt(3) * vll * pf)

def battery_capacity(load_w, hours, voltage, dod=0.8):
    wh = load_w * hours
    ah = wh / voltage
    return {
        "wh": wh,
        "ah": ah,
        "ah_adjusted": ah / dod
    }

def solar_panel_required(load_kwh, sun_hours, panel_w=450):
    daily_wh = load_kwh * 1000
    panels = daily_wh / (panel_w * sun_hours * 0.8)
    return math.ceil(panels)

def resistor_color_code(bands):
    colors = {
        "negro": 0, "marron": 1, "rojo": 2, "naranja": 3,
        "amarillo": 4, "verde": 5, "azul": 6, "violeta": 7,
        "gris": 8, "blanco": 9
    }
    multipliers = {
        "negro": 1, "marron": 10, "rojo": 100, "naranja": 1000,
        "amarillo": 10000, "verde": 100000, "azul": 1000000,
    }
    if len(bands) == 4:
        val = (colors[bands[0]] * 10 + colors[bands[1]]) * multipliers[bands[2]]
        return val
    if len(bands) == 5:
        val = (colors[bands[0]] * 100 + colors[bands[1]] * 10 + colors[bands[2]]) * multipliers[bands[3]]
        return val
    return 0

def cable_voltage_drop_3phase(length_m, i_a, r_km, x_km=0, pf=0.85):
    r = r_km * length_m / 1000
    x = x_km * length_m / 1000
    vd = math.sqrt(3) * i_a * (r * pf + x * math.sin(math.acos(pf)))
    return vd
