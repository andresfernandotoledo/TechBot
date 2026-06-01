# Calculadora de Almacenamiento y Ancho de Banda para Cámaras CCTV
# Versión mejorada — múltiples grupos, codecs detallados, PoE configurable, NVR channels, RAID corregido

BITRATE_TABLE = {
    "CIF (352x240)":        {"H.264 Baseline": 256,   "H.264 Main": 320,   "H.264 High": 384,   "H.265": 160,  "H.265+": 96,   "MJPEG": 1500},
    "D1 (704x480)":         {"H.264 Baseline": 512,   "H.264 Main": 640,   "H.264 High": 768,   "H.265": 320,  "H.265+": 192,  "MJPEG": 4000},
    "960H (960x576)":       {"H.264 Baseline": 768,   "H.264 Main": 1024,  "H.264 High": 1280,  "H.265": 512,  "H.265+": 300,  "MJPEG": 5000},
    "HD 720p (1280x720)":   {"H.264 Baseline": 1024,  "H.264 Main": 1536,  "H.264 High": 2048,  "H.265": 1024, "H.265+": 512,  "MJPEG": 10000},
    "1MP (1280x960)":       {"H.264 Baseline": 1536,  "H.264 Main": 2048,  "H.264 High": 2560,  "H.265": 1280, "H.265+": 640,  "MJPEG": 12000},
    "2MP / 1080p":          {"H.264 Baseline": 2048,  "H.264 Main": 3072,  "H.264 High": 4096,  "H.265": 2048, "H.265+": 1024, "MJPEG": 20000},
    "3MP (2048x1536)":      {"H.264 Baseline": 3072,  "H.264 Main": 4096,  "H.264 High": 5120,  "H.265": 3072, "H.265+": 1536, "MJPEG": 25000},
    "4MP (2688x1520)":      {"H.264 Baseline": 4096,  "H.264 Main": 5120,  "H.264 High": 6144,  "H.265": 4096, "H.265+": 2048, "MJPEG": 30000},
    "5MP (2592x1944)":      {"H.264 Baseline": 5120,  "H.264 Main": 6144,  "H.264 High": 8192,  "H.265": 5120, "H.265+": 2560, "MJPEG": 35000},
    "6MP (3072x2048)":      {"H.264 Baseline": 6144,  "H.264 Main": 8192,  "H.264 High": 10240, "H.265": 6144, "H.265+": 3072, "MJPEG": 40000},
    "8MP / 4K (3840x2160)": {"H.264 Baseline": 8192,  "H.264 Main": 10240, "H.264 High": 12288, "H.265": 8192, "H.265+": 4096, "MJPEG": 50000},
    "12MP (4000x3000)":     {"H.264 Baseline": 12288, "H.264 Main": 15360, "H.264 High": 18432, "H.265": 12288,"H.265+": 6144, "MJPEG": 60000},
}

CODECS = list(list(BITRATE_TABLE.values())[0].keys())
RESOLUTIONS = list(BITRATE_TABLE.keys())

RESOLUTION_INFO = {
    "CIF (352x240)":        (352,  240,  0.3),
    "D1 (704x480)":         (704,  480,  0.8),
    "960H (960x576)":       (960,  576,  1.2),
    "HD 720p (1280x720)":   (1280, 720,  2.1),
    "1MP (1280x960)":       (1280, 960,  2.8),
    "2MP / 1080p":          (1920, 1080, 4.0),
    "3MP (2048x1536)":      (2048, 1536, 6.0),
    "4MP (2688x1520)":      (2688, 1520, 8.0),
    "5MP (2592x1944)":      (2592, 1944, 10.0),
    "6MP (3072x2048)":      (3072, 2048, 12.0),
    "8MP / 4K (3840x2160)": (3840, 2160, 16.0),
    "12MP (4000x3000)":     (4000, 3000, 24.0),
}

SMART_CODECS = {
    "Ninguno":                  1.0,
    "H.264+ (Hikvision)":       0.5,
    "H.265+ (Hikvision)":       0.35,
    "Smart Codec (Dahua)":      0.5,
    "H.265 Premium (Dahua)":    0.35,
    "Zipstream (Axis)":         0.5,
}

SCENE_FACTORS = {
    "Muy baja": 0.5,
    "Baja":     0.75,
    "Normal":   1.0,
    "Alta":     1.3,
    "Muy alta": 1.6,
}

# PoE estándar por tipo de cámara (vatios)
POE_PROFILES = {
    "IP Domo estándar":     7.0,
    "IP Bala estándar":     7.5,
    "IP PTZ":               25.0,
    "IP Fisheye":           9.0,
    "IP 4K":                12.0,
    "IP con calefactor":    15.0,
    "IP con IR largo":      10.0,
    "Genérico":             7.5,
}

# Límites de canales por tipo de NVR
NVR_CHANNEL_LIMITS = {
    "4ch": 4, "8ch": 8, "16ch": 16, "32ch": 32, "64ch": 64, "128ch": 128,
}

HDD_MODELS = [
    (500,   "500 GB", "WD Purple / Seagate SkyHawk"),
    (1000,  "1 TB",   "WD Purple / Seagate SkyHawk"),
    (2000,  "2 TB",   "WD Purple / Seagate SkyHawk"),
    (4000,  "4 TB",   "WD Purple / Seagate SkyHawk"),
    (6000,  "6 TB",   "WD Purple Pro / Seagate SkyHawk AI"),
    (8000,  "8 TB",   "WD Purple Pro / Seagate SkyHawk AI"),
    (10000, "10 TB",  "WD Purple Pro / Seagate SkyHawk AI"),
    (12000, "12 TB",  "WD Purple Pro / Seagate SkyHawk AI"),
    (14000, "14 TB",  "WD Purple Pro / Seagate SkyHawk AI"),
    (16000, "16 TB",  "WD Purple Pro / Seagate SkyHawk AI"),
    (18000, "18 TB",  "WD Purple Pro / Seagate SkyHawk AI"),
    (20000, "20 TB",  "WD Purple Pro / Seagate SkyHawk AI"),
]


def get_bitrate_kbps(resolution, codec):
    res = BITRATE_TABLE.get(resolution)
    if not res:
        raise ValueError(f"Resolución no soportada: {resolution}. Opciones: {', '.join(BITRATE_TABLE.keys())}")
    rate = res.get(codec)
    if rate is None:
        raise ValueError(f"Codec '{codec}' no soportado para {resolution}. Opciones: {', '.join(res.keys())}")
    return rate


def calc_group(group, recording_hours=24, motion_percent=100):
    cameras      = max(1, int(group.get("cameras", 1)))
    resolution   = group["resolution"]
    codec        = group["codec"]
    fps          = max(1, min(int(group.get("fps", 15)), 60))
    smart        = group.get("smart_codec", "Ninguno")
    scene        = group.get("scene", "Normal")
    poe_profile  = group.get("poe_profile", "Genérico")
    poe_w_each   = float(group.get("poe_watts", POE_PROFILES.get(poe_profile, 7.5)))

    base_kbps    = get_bitrate_kbps(resolution, codec)
    smart_factor = SMART_CODECS.get(smart, 1.0)
    scene_factor = SCENE_FACTORS.get(scene, 1.0)

    if "8MP" in resolution or "4K" in resolution or "12MP" in resolution:
        ref_fps = 20
    elif "5MP" in resolution or "6MP" in resolution:
        ref_fps = 25
    else:
        ref_fps = 30

    fps_factor   = fps / ref_fps
    bitrate_kbps = base_kbps * smart_factor * scene_factor * fps_factor
    bitrate_mbps = bitrate_kbps / 1000

    recording_ratio = recording_hours / 24.0
    motion_ratio    = motion_percent / 100.0

    storage_per_day_gb       = bitrate_mbps * 86400 / 8 / 1024 * recording_ratio * motion_ratio
    storage_per_day_gb_total = storage_per_day_gb * cameras
    poe_total_w              = poe_w_each * cameras

    return {
        "cameras":                  cameras,
        "resolution":               resolution,
        "codec":                    codec,
        "fps":                      fps,
        "smart_codec":              smart,
        "scene":                    scene,
        "bitrate_kbps":             round(bitrate_kbps, 0),
        "bitrate_mbps":             round(bitrate_mbps, 2),
        "storage_per_day_gb":       round(storage_per_day_gb, 2),
        "storage_per_day_gb_total": round(storage_per_day_gb_total, 2),
        "poe_watts_each":           round(poe_w_each, 1),
        "poe_watts_total":          round(poe_total_w, 1),
    }


def calc_full(groups, recording_hours=24, motion_percent=100,
              retention_days=30, total_storage_gb=2000,
              nvr_channels=None):
    """
    Calcula almacenamiento, ancho de banda y PoE para un conjunto de grupos de cámaras.

    Args:
        groups:           Lista de dicts con configuración por grupo.
        recording_hours:  Horas de grabación por día (1–24).
        motion_percent:   Porcentaje de actividad/movimiento (1–100).
        retention_days:   Días de retención deseados.
        total_storage_gb: Almacenamiento total disponible en GB.
        nvr_channels:     Límite de canales del NVR (None = sin límite).

    Returns:
        Dict con resultados por grupo, totales, almacenamiento, ancho de banda y PoE.
    """
    group_results          = []
    total_bitrate_mbps     = 0.0
    total_storage_per_day  = 0.0
    total_cameras          = 0
    total_poe_w            = 0.0

    for g in groups:
        r = calc_group(g, recording_hours, motion_percent)
        group_results.append(r)
        total_bitrate_mbps    += r["bitrate_mbps"] * r["cameras"]
        total_storage_per_day += r["storage_per_day_gb_total"]
        total_cameras         += r["cameras"]
        total_poe_w           += r["poe_watts_total"]

    # ── Alertas NVR ───────────────────────────────────────────
    nvr_warnings = []
    if nvr_channels and total_cameras > nvr_channels:
        nvr_warnings.append(
            f"⚠ El NVR de {nvr_channels} canales no alcanza para {total_cameras} cámaras. "
            f"Necesitás {total_cameras - nvr_channels} canales adicionales o un NVR más grande."
        )

    # ── Tiempo de grabación con almacenamiento dado ────────────
    saving_days   = round(total_storage_gb / total_storage_per_day, 1) if total_storage_per_day > 0 else 0
    saving_weeks  = round(saving_days / 7, 1)
    saving_months = round(saving_days / 30, 1)

    # ── Espacio requerido para retención deseada ───────────────
    required_gb = round(total_storage_per_day * retention_days, 2)
    required_tb = round(required_gb / 1024, 2)

    # ── Ancho de banda y switch recomendado ────────────────────
    total_bandwidth_mbps = round(total_bitrate_mbps, 2)
    total_bandwidth_kbps = round(total_bitrate_mbps * 1000, 0)

    if total_bandwidth_mbps < 100:
        switch_speed = "Fast Ethernet 100 Mbps"
    elif total_bandwidth_mbps < 900:
        switch_speed = "Gigabit Ethernet 1 Gbps"
    else:
        switch_speed = "10 Gbps (SFP+)"

    # ── PoE budget ────────────────────────────────────────────
    poe_switch_options = _poe_switch_recommendation(total_poe_w, total_cameras)

    # ── Alerta de almacenamiento insuficiente ─────────────────
    storage_warnings = []
    if total_storage_gb < required_gb:
        deficit = round(required_gb - total_storage_gb, 1)
        storage_warnings.append(
            f"⚠ El almacenamiento disponible ({total_storage_gb} GB) es insuficiente. "
            f"Faltan {deficit} GB para cubrir {retention_days} días de retención."
        )

    return {
        "groups":          group_results,
        "total_cameras":   total_cameras,
        "recording_hours": recording_hours,
        "motion_percent":  motion_percent,
        "warnings":        nvr_warnings + storage_warnings,
        "saving_time": {
            "days":        saving_days,
            "weeks":       saving_weeks,
            "months":      saving_months,
            "disk_size_gb": total_storage_gb,
            "disk_size_tb": round(total_storage_gb / 1024, 2),
        },
        "disk_space": {
            "required_gb":      required_gb,
            "required_tb":      required_tb,
            "retention_days":   retention_days,
            "per_day_gb":       round(total_storage_per_day, 2),
            "recommended_hdds": _recommend_hdds(required_gb),
        },
        "bandwidth": {
            "total_kbps":          total_bandwidth_kbps,
            "total_mbps":          total_bandwidth_mbps,
            "per_camera_mbps_avg": round(total_bandwidth_mbps / total_cameras, 2) if total_cameras else 0,
            "recommended_switch":  switch_speed,
            "switch_ports":        total_cameras,
        },
        "poe": {
            "total_watts":        round(total_poe_w, 1),
            "recommended_switch": poe_switch_options,
        },
        "nvr": {
            "total_cameras":    total_cameras,
            "channels_limit":   nvr_channels,
            "channels_ok":      (total_cameras <= nvr_channels) if nvr_channels else True,
        },
    }


def compute(groups, recording_hours=24, motion_percent=100,
            retention_days=30, total_storage_gb=2000, nvr_channels=None):
    """Punto de entrada principal. Alias de calc_full."""
    return calc_full(
        groups, recording_hours, motion_percent,
        retention_days, total_storage_gb, nvr_channels,
    )


def _poe_switch_recommendation(total_w, total_cameras):
    """Sugiere el switch PoE adecuado según el presupuesto total."""
    budgets = [65, 130, 150, 185, 250, 370, 400, 500, 740, 800]
    models  = [
        "Switch PoE 65W (ej. TP-Link TL-SF1008P)",
        "Switch PoE 130W (ej. TP-Link TL-SG1008PE)",
        "Switch PoE 150W (ej. Ubiquiti USW-Lite-8-PoE)",
        "Switch PoE 185W (ej. Cisco SG110-16HP)",
        "Switch PoE 250W (ej. TP-Link TL-SG1218MPE)",
        "Switch PoE 370W (ej. Hikvision DS-3E0518P-E)",
        "Switch PoE 400W (ej. Ubiquiti USW-Pro-24-PoE)",
        "Switch PoE 500W (ej. Netgear GS752TP)",
        "Switch PoE 740W (ej. Ubiquiti USW-Pro-48-PoE)",
        "Switch PoE 800W+ (consultar especificaciones del proyecto)",
    ]
    # Agregar 20% de margen de seguridad al presupuesto requerido
    required = total_w * 1.20
    suggestions = []
    for budget, model in zip(budgets, models):
        if budget >= required:
            suggestions.append({"model": model, "budget_w": budget, "cameras_fit": total_cameras})
            if len(suggestions) >= 2:
                break
    if not suggestions:
        suggestions.append({
            "model": "Switch PoE industrial / multicapa requerido",
            "budget_w": round(required, 0),
            "cameras_fit": total_cameras,
        })
    return suggestions


def _recommend_hdds(total_gb):
    """Recomienda combinaciones de HDD para cubrir el almacenamiento requerido, con cálculo RAID corregido."""
    if total_gb <= 0:
        return [{
            "count": 1, "size_label": "1 TB", "size_gb": 1000,
            "total_raw_gb": 1000, "model": "WD Purple",
            "raid0_gb": 1000, "raid1_gb": 1000,
            "raid5_gb": 0, "raid10_gb": 0,
            "raid5_note": "RAID 5 requiere mínimo 3 discos",
            "raid10_note": "RAID 10 requiere mínimo 4 discos (par)",
        }]
    suggestions = []
    for size, label, model in HDD_MODELS:
        count = max(1, -(-int(total_gb) // size))  # ceil division
        if count > 16:
            continue
        raw_gb = count * size

        # RAID 0: toda la capacidad, sin redundancia
        raid0 = raw_gb

        # RAID 1: solo 2 discos (espejo). Si count > 2, se usan 2 discos.
        if count >= 2:
            raid1 = size  # un espejo = capacidad de 1 disco
            raid1_note = f"1 espejo de {label}"
        else:
            raid1 = size
            raid1_note = "Sin redundancia (1 disco)"

        # RAID 5: mínimo 3 discos — capacidad = (n-1) × tamaño
        if count >= 3:
            raid5 = (count - 1) * size
            raid5_note = f"{count} discos → {count - 1} × {label} útiles"
        else:
            raid5 = 0
            raid5_note = f"RAID 5 requiere mínimo 3 discos (tenés {count})"

        # RAID 10: mínimo 4 discos pares — capacidad = (n/2) × tamaño
        if count >= 4 and count % 2 == 0:
            raid10 = (count // 2) * size
            raid10_note = f"{count} discos → {count // 2} × {label} útiles"
        elif count >= 4:
            # Redondear a par inferior
            even = count - 1
            raid10 = (even // 2) * size
            raid10_note = f"Se usan {even} discos (par) → {even // 2} × {label} útiles"
        else:
            raid10 = 0
            raid10_note = f"RAID 10 requiere mínimo 4 discos pares (tenés {count})"

        suggestions.append({
            "count":        count,
            "size_label":   label,
            "size_gb":      size,
            "total_raw_gb": raw_gb,
            "model":        model,
            "raid0_gb":     raid0,
            "raid1_gb":     raid1,
            "raid1_note":   raid1_note,
            "raid5_gb":     raid5,
            "raid5_note":   raid5_note,
            "raid10_gb":    raid10,
            "raid10_note":  raid10_note,
        })
    return suggestions[:6]


# ── Funciones auxiliares adicionales ──────────────────────────

def estimate_nvr_bandwidth(cameras, resolution, codec, fps=15):
    """Calcula el ancho de banda total estimado para un NVR."""
    kbps = get_bitrate_kbps(resolution, codec)
    ref_fps = 30
    total_mbps = (kbps * fps / ref_fps / 1000) * cameras
    return {
        "cameras":     cameras,
        "total_mbps":  round(total_mbps, 2),
        "total_kbps":  round(total_mbps * 1000, 0),
        "switch_port": "Gigabit" if total_mbps > 100 else "Fast Ethernet",
    }


def storage_for_retention(bitrate_mbps, cameras, retention_days,
                           recording_hours=24, motion_percent=100):
    """Calcula cuánto almacenamiento se necesita dado un bitrate y retención."""
    ratio        = (recording_hours / 24.0) * (motion_percent / 100.0)
    per_day_gb   = bitrate_mbps * 86400 / 8 / 1024 * ratio * cameras
    total_gb     = per_day_gb * retention_days
    return {
        "per_day_gb":     round(per_day_gb, 2),
        "total_gb":       round(total_gb, 2),
        "total_tb":       round(total_gb / 1024, 2),
        "retention_days": retention_days,
    }


def poe_budget_check(cameras_list, switch_budget_w):
    """
    Verifica si el presupuesto PoE del switch es suficiente.
    cameras_list: lista de dicts con {"count": N, "watts": W}
    """
    total_w = sum(c["count"] * c["watts"] for c in cameras_list)
    ok = total_w <= switch_budget_w
    margin = switch_budget_w - total_w
    return {
        "total_required_w": round(total_w, 1),
        "switch_budget_w":  switch_budget_w,
        "ok":               ok,
        "margin_w":         round(margin, 1),
        "margin_pct":       round(margin / switch_budget_w * 100, 1) if switch_budget_w else 0,
        "status":           "✅ OK" if ok else f"❌ Excedido por {round(-margin, 1)} W",
    }
