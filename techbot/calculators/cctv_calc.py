# Calculadora de Almacenamiento y Ancho de Banda para Cámaras CCTV
# Versión mejorada — múltiples grupos, codecs detallados, 3 modos

BITRATE_TABLE = {
    "CIF (352x240)":     {"H.264 Baseline": 256, "H.264 Main": 320, "H.264 High": 384, "H.265": 160, "H.265+": 96, "MJPEG": 1500},
    "D1 (704x480)":      {"H.264 Baseline": 512, "H.264 Main": 640, "H.264 High": 768, "H.265": 320, "H.265+": 192, "MJPEG": 4000},
    "960H (960x576)":    {"H.264 Baseline": 768, "H.264 Main": 1024, "H.264 High": 1280, "H.265": 512, "H.265+": 300, "MJPEG": 5000},
    "HD 720p (1280x720)": {"H.264 Baseline": 1024, "H.264 Main": 1536, "H.264 High": 2048, "H.265": 1024, "H.265+": 512, "MJPEG": 10000},
    "1MP (1280x960)":    {"H.264 Baseline": 1536, "H.264 Main": 2048, "H.264 High": 2560, "H.265": 1280, "H.265+": 640, "MJPEG": 12000},
    "2MP / 1080p":       {"H.264 Baseline": 2048, "H.264 Main": 3072, "H.264 High": 4096, "H.265": 2048, "H.265+": 1024, "MJPEG": 20000},
    "3MP (2048x1536)":   {"H.264 Baseline": 3072, "H.264 Main": 4096, "H.264 High": 5120, "H.265": 3072, "H.265+": 1536, "MJPEG": 25000},
    "4MP (2688x1520)":   {"H.264 Baseline": 4096, "H.264 Main": 5120, "H.264 High": 6144, "H.265": 4096, "H.265+": 2048, "MJPEG": 30000},
    "5MP (2592x1944)":   {"H.264 Baseline": 5120, "H.264 Main": 6144, "H.264 High": 8192, "H.265": 5120, "H.265+": 2560, "MJPEG": 35000},
    "6MP (3072x2048)":   {"H.264 Baseline": 6144, "H.264 Main": 8192, "H.264 High": 10240, "H.265": 6144, "H.265+": 3072, "MJPEG": 40000},
    "8MP / 4K (3840x2160)": {"H.264 Baseline": 8192, "H.264 Main": 10240, "H.264 High": 12288, "H.265": 8192, "H.265+": 4096, "MJPEG": 50000},
    "12MP (4000x3000)":  {"H.264 Baseline": 12288, "H.264 Main": 15360, "H.264 High": 18432, "H.265": 12288, "H.265+": 6144, "MJPEG": 60000},
}

CODECS = list(list(BITRATE_TABLE.values())[0].keys())

RESOLUTIONS = list(BITRATE_TABLE.keys())

RESOLUTION_INFO = {
    "CIF (352x240)":     (352, 240, 0.3),
    "D1 (704x480)":      (704, 480, 0.8),
    "960H (960x576)":    (960, 576, 1.2),
    "HD 720p (1280x720)": (1280, 720, 2.1),
    "1MP (1280x960)":    (1280, 960, 2.8),
    "2MP / 1080p":       (1920, 1080, 4.0),
    "3MP (2048x1536)":   (2048, 1536, 6.0),
    "4MP (2688x1520)":   (2688, 1520, 8.0),
    "5MP (2592x1944)":   (2592, 1944, 10.0),
    "6MP (3072x2048)":   (3072, 2048, 12.0),
    "8MP / 4K (3840x2160)": (3840, 2160, 16.0),
    "12MP (4000x3000)":  (4000, 3000, 24.0),
}

SMART_CODECS = {
    "Ninguno": 1.0,
    "H.264+ (Hikvision)": 0.5,
    "H.265+ (Hikvision)": 0.35,
    "Smart Codec (Dahua)": 0.5,
    "H.265 Premium (Dahua)": 0.35,
    "Zipstream (Axis)": 0.5,
}

SCENE_FACTORS = {
    "Muy baja": 0.5,
    "Baja": 0.75,
    "Normal": 1.0,
    "Alta": 1.3,
    "Muy alta": 1.6,
}

HDD_MODELS = [
    (500, "500 GB", "WD Purple / Seagate SkyHawk"),
    (1000, "1 TB", "WD Purple / Seagate SkyHawk"),
    (2000, "2 TB", "WD Purple / Seagate SkyHawk"),
    (4000, "4 TB", "WD Purple / Seagate SkyHawk"),
    (6000, "6 TB", "WD Purple Pro / Seagate SkyHawk"),
    (8000, "8 TB", "WD Purple Pro / Seagate SkyHawk"),
    (10000, "10 TB", "WD Purple Pro / Seagate SkyHawk"),
    (12000, "12 TB", "WD Purple Pro / Seagate SkyHawk"),
    (14000, "14 TB", "WD Purple Pro / Seagate SkyHawk"),
    (16000, "16 TB", "WD Purple Pro / Seagate SkyHawk"),
    (18000, "18 TB", "WD Purple Pro / Seagate SkyHawk"),
    (20000, "20 TB", "WD Purple Pro / Seagate SkyHawk"),
]


def get_bitrate_kbps(resolution, codec):
    res = BITRATE_TABLE.get(resolution)
    if not res:
        raise ValueError(f"Resolución no soportada: {resolution}")
    rate = res.get(codec)
    if rate is None:
        raise ValueError(f"Codec {codec} no soportado para {resolution}")
    return rate


def calc_group(group, recording_hours=24, motion_percent=100):
    cameras = group.get("cameras", 1)
    resolution = group["resolution"]
    codec = group["codec"]
    fps = group.get("fps", 15)
    smart = group.get("smart_codec", "Ninguno")
    scene = group.get("scene", "Normal")

    base_kbps = get_bitrate_kbps(resolution, codec)
    smart_factor = SMART_CODECS.get(smart, 1.0)
    scene_factor = SCENE_FACTORS.get(scene, 1.0)

    if "8MP" in resolution or "4K" in resolution or "12MP" in resolution:
        ref_fps = 20
    elif "5MP" in resolution or "6MP" in resolution:
        ref_fps = 25
    else:
        ref_fps = 30

    fps_factor = fps / ref_fps
    bitrate_kbps = base_kbps * smart_factor * scene_factor * fps_factor
    bitrate_mbps = bitrate_kbps / 1000

    recording_ratio = recording_hours / 24.0
    motion_ratio = motion_percent / 100.0

    storage_per_day_gb = bitrate_mbps * 86400 / 8 / 1024 * recording_ratio * motion_ratio
    storage_per_day_gb_total = storage_per_day_gb * cameras

    return {
        "bitrate_kbps": round(bitrate_kbps, 0),
        "bitrate_mbps": round(bitrate_mbps, 2),
        "storage_per_day_gb": round(storage_per_day_gb, 2),
        "storage_per_day_gb_total": round(storage_per_day_gb_total, 2),
        "cameras": cameras,
    }


def calc_full(groups, recording_hours=24, motion_percent=100,
              retention_days=30, total_storage_gb=2000):
    group_results = []
    total_bitrate_mbps = 0
    total_storage_per_day_gb = 0
    total_cameras = 0

    for g in groups:
        r = calc_group(g, recording_hours, motion_percent)
        group_results.append(r)
        total_bitrate_mbps += r["bitrate_mbps"] * r["cameras"]
        total_storage_per_day_gb += r["storage_per_day_gb"] * r["cameras"]
        total_cameras += r["cameras"]

    total_bandwidth_mbps = round(total_bitrate_mbps, 2)
    total_bandwidth_kbps = round(total_bitrate_mbps * 1000, 0)

    # Saving Time
    saving_days = round(total_storage_gb / total_storage_per_day_gb, 1) if total_storage_per_day_gb > 0 else 0
    saving_weeks = round(saving_days / 7, 1)
    saving_months = round(saving_days / 30, 1)

    # Disk Space
    required_gb = round(total_storage_per_day_gb * retention_days, 2)
    required_tb = round(required_gb / 1024, 2)

    # Network
    switch_ports_needed = total_cameras
    poe_watts = total_cameras * 7.5  # ~7.5W per IP camera average (PoE)
    if total_bandwidth_mbps < 100:
        switch_speed = "100 Mbps (Fast Ethernet)"
    elif total_bandwidth_mbps < 1000:
        switch_speed = "1 Gbps (Gigabit)"
    else:
        switch_speed = "10 Gbps (SFP+)"

    return {
        "groups": group_results,
        "total_cameras": total_cameras,
        "recording_hours": recording_hours,
        "motion_percent": motion_percent,
        "saving_time": {
            "days": saving_days,
            "weeks": saving_weeks,
            "months": saving_months,
            "disk_size_gb": total_storage_gb,
            "disk_size_tb": round(total_storage_gb / 1024, 2),
        },
        "disk_space": {
            "required_gb": required_gb,
            "required_tb": required_tb,
            "retention_days": retention_days,
            "recommended_hdds": _recommend_hdds(required_gb),
        },
        "bandwidth": {
            "total_kbps": total_bandwidth_kbps,
            "total_mbps": total_bandwidth_mbps,
            "per_camera_mbps_avg": round(total_bandwidth_mbps / total_cameras, 2) if total_cameras else 0,
            "recommended_switch": switch_speed,
            "switch_ports": switch_ports_needed,
            "poe_budget_watts": round(poe_watts, 0),
        },
    }


def compute(groups, recording_hours=24, motion_percent=100,
            retention_days=30, total_storage_gb=2000):
    return calc_full(groups, recording_hours, motion_percent,
                     retention_days, total_storage_gb)


def _recommend_hdds(total_gb):
    if total_gb <= 0:
        return [{"count": 1, "size_label": "1 TB", "size_gb": 1000, "total_gb": 1000,
                 "raid0": 1000, "raid1": 1000, "raid5": 1000, "raid10": 0, "model": "WD Purple"}]
    suggestions = []
    for size, label, model in HDD_MODELS:
        count = max(1, -(-total_gb // size))
        if count <= 16:
            suggestions.append({
                "count": count,
                "size_label": label,
                "size_gb": size,
                "total_gb": count * size,
                "model": model,
                "raid0": count * size,
                "raid1": (count // 2) * size if count >= 2 else size,
                "raid5": (count - 1) * size if count >= 3 else (count // 2) * size if count >= 2 else size,
                "raid10": (count // 2) * size if count >= 4 else 0,
            })
    return suggestions[:6]
