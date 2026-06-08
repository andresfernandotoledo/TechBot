# Módulo Avanzado de Gestión y Monitoreo de UPS
# Soporta: NUT, SNMP v1/v2c/v3, Modbus TCP, APC PowerChute,
# apcupsd, pwrstat, web HTTP, y todos los fabricantes principales

import subprocess
import re
import time
import socket
import json
from datetime import datetime, timedelta
from struct import pack, unpack

# ─── CONSTANTES ───────────────────────────────────────────────

NUT_PORT = 3493
APC_POWERCHUTE_PORT = 6547
APC_POWERCHUTE_SSL_PORT = 6548
APCUPSD_PORT = 3551
MODBUS_PORT = 502

# UPS-MIB (RFC 1628) — 1.3.6.1.2.1.33
UPS_MIB = {
    "upsIdentManufacturer": "1.3.6.1.2.1.33.1.1.1",
    "upsIdentModel": "1.3.6.1.2.1.33.1.1.2",
    "upsIdentUPSSoftwareVersion": "1.3.6.1.2.1.33.1.1.3",
    "upsIdentAgentSoftwareVersion": "1.3.6.1.2.1.33.1.1.4",
    "upsIdentName": "1.3.6.1.2.1.33.1.1.5",
    "upsIdentAttachedDevices": "1.3.6.1.2.1.33.1.1.6",
    "upsBatteryStatus": "1.3.6.1.2.1.33.1.2.1",
    "upsBatteryVoltage": "1.3.6.1.2.1.33.1.2.2",
    "upsBatteryTemperature": "1.3.6.1.2.1.33.1.2.3",
    "upsBatteryEstimatedChargeRemaining": "1.3.6.1.2.1.33.1.2.4",
    "upsBatteryEstimatedMinutesRemaining": "1.3.6.1.2.1.33.1.2.5",
    "upsBatteryChemistry": "1.3.6.1.2.1.33.1.2.6",
    "upsBatteryReplaceDate": "1.3.6.1.2.1.33.1.2.7",
    "upsBatteryTestResult": "1.3.6.1.2.1.33.1.2.8",
    "upsInputLineBads": "1.3.6.1.2.1.33.1.3.1",
    "upsInputNumLines": "1.3.6.1.2.1.33.1.3.2",
    "upsInputVoltage": "1.3.6.1.2.1.33.1.3.3.1.2",
    "upsInputCurrent": "1.3.6.1.2.1.33.1.3.3.1.3",
    "upsInputPower": "1.3.6.1.2.1.33.1.3.3.1.4",
    "upsOutputSource": "1.3.6.1.2.1.33.1.4.1",
    "upsOutputFrequency": "1.3.6.1.2.1.33.1.4.2",
    "upsOutputVoltage": "1.3.6.1.2.1.33.1.4.3.1.2",
    "upsOutputCurrent": "1.3.6.1.2.1.33.1.4.3.1.3",
    "upsOutputPower": "1.3.6.1.2.1.33.1.4.3.1.4",
    "upsOutputPercentLoad": "1.3.6.1.2.1.33.1.4.4.1.2",
    "upsAlarmPresent": "1.3.6.1.2.1.33.1.6.1",
    "upsConfigRatedVA": "1.3.6.1.2.1.33.1.8.1.1",
    "upsConfigRatedWatts": "1.3.6.1.2.1.33.1.8.1.2",
    "upsConfigInputVoltage": "1.3.6.1.2.1.33.1.8.2.1",
    "upsConfigOutputVoltage": "1.3.6.1.2.1.33.1.8.3.1",
}

# OIDs específicas de fabricantes
VENDOR_MIBS = {
    "APC": {
        "base": "1.3.6.1.4.1.318",
        "name": "PowerNet MIB",
        "oids": {
            "apcIdentModel": "1.3.6.1.4.1.318.1.1.1.1.1.1.0",
            "apcIdentSerial": "1.3.6.1.4.1.318.1.1.1.1.1.2.0",
            "apcIdentFirmware": "1.3.6.1.4.1.318.1.1.1.1.1.3.0",
            "apcIdentDateOfManufacture": "1.3.6.1.4.1.318.1.1.1.1.1.4.0",
            "apcBatteryStatus": "1.3.6.1.4.1.318.1.1.1.2.1.1.0",
            "apcBatteryReplaceDate": "1.3.6.1.4.1.318.1.1.1.2.1.2.0",
            "apcBatteryLastReplaceDate": "1.3.6.1.4.1.318.1.1.1.2.1.3.0",
            "apcBatteryTemperature": "1.3.6.1.4.1.318.1.1.1.2.1.4.0",
            "apcBatteryCapacity": "1.3.6.1.4.1.318.1.1.1.2.2.1.0",
            "apcBatteryVoltage": "1.3.6.1.4.1.318.1.1.1.2.2.2.0",
            "apcBatteryCurrent": "1.3.6.1.4.1.318.1.1.1.2.2.3.0",
            "apcBatteryTimeRemaining": "1.3.6.1.4.1.318.1.1.1.2.2.4.0",
            "apcBatteryTimeOnBattery": "1.3.6.1.4.1.318.1.1.1.2.2.5.0",
            "apcBatteryNumBatteries": "1.3.6.1.4.1.318.1.1.1.2.2.6.0",
            "apcInputLineVoltage": "1.3.6.1.4.1.318.1.1.1.3.2.1.0",
            "apcInputFrequency": "1.3.6.1.4.1.318.1.1.1.3.2.2.0",
            "apcOutputVoltage": "1.3.6.1.4.1.318.1.1.1.4.2.1.0",
            "apcOutputFrequency": "1.3.6.1.4.1.318.1.1.1.4.2.2.0",
            "apcOutputPower": "1.3.6.1.4.1.318.1.1.1.4.2.3.0",
            "apcOutputPercentLoad": "1.3.6.1.4.1.318.1.1.1.4.2.4.0",
            "apcOutputCurrent": "1.3.6.1.4.1.318.1.1.1.4.2.5.0",
            "apcOutputVA": "1.3.6.1.4.1.318.1.1.1.4.2.6.0",
            "apcRatedVA": "1.3.6.1.4.1.318.1.1.1.1.1.1.1.1.0",
            "apcTestBatteryStart": "1.3.6.1.4.1.318.1.1.1.1.1.5.0",
            "apcTestBatteryResult": "1.3.6.1.4.1.318.1.1.1.1.1.6.0",
            "apcAlarmPresent": "1.3.6.1.4.1.318.1.1.1.9.1.1.0",
        }
    },
    "APC RPD/Masterswitch": {
        "base": "1.3.6.1.4.1.318.1.1.12",
        "name": "APC Rack PDU / Masterswitch",
        "oids": {
            "rpdOutletState": "1.3.6.1.4.1.318.1.1.12.3.3.1.1.4",
            "rpdOutletName": "1.3.6.1.4.1.318.1.1.12.3.3.1.1.2",
        }
    },
    "Eaton": {
        "base": "1.3.6.1.4.1.534",
        "name": "Eaton Power Xpert",
        "oids": {
            "eatonIdentModel": "1.3.6.1.4.1.534.1.1.1.1.1.0",
            "eatonIdentSerial": "1.3.6.1.4.1.534.1.1.1.1.2.0",
            "eatonBatteryStatus": "1.3.6.1.4.1.534.1.2.1.1.0",
            "eatonBatteryVoltage": "1.3.6.1.4.1.534.1.2.1.2.0",
            "eatonBatteryCurrent": "1.3.6.1.4.1.534.1.2.1.3.0",
            "eatonBatteryCharge": "1.3.6.1.4.1.534.1.2.1.5.0",
            "eatonBatteryTimeRemaining": "1.3.6.1.4.1.534.1.2.1.6.0",
            "eatonBatteryTemperature": "1.3.6.1.4.1.534.1.2.1.7.0",
            "eatonInputVoltage": "1.3.6.1.4.1.534.1.3.1.0",
            "eatonInputFrequency": "1.3.6.1.4.1.534.1.3.2.0",
            "eatonOutputVoltage": "1.3.6.1.4.1.534.1.4.1.0",
            "eatonOutputFrequency": "1.3.6.1.4.1.534.1.4.2.0",
            "eatonOutputLoad": "1.3.6.1.4.1.534.1.4.3.0",
            "eatonOutputCurrent": "1.3.6.1.4.1.534.1.4.4.0",
            "eatonOutputPower": "1.3.6.1.4.1.534.1.4.5.0",
            "eatonRatedVA": "1.3.6.1.4.1.534.1.1.1.2.1.0",
            "eatonRatedWatts": "1.3.6.1.4.1.534.1.1.1.2.2.0",
        }
    },
    "CyberPower": {
        "base": "1.3.6.1.4.1.3808",
        "name": "CyberPower MIB",
        "oids": {
            "cpIdentModel": "1.3.6.1.4.1.3808.1.1.1.1.1.0",
            "cpIdentSerial": "1.3.6.1.4.1.3808.1.1.1.1.2.0",
            "cpBatteryStatus": "1.3.6.1.4.1.3808.1.1.1.2.1.1.0",
            "cpBatteryCapacity": "1.3.6.1.4.1.3808.1.1.1.2.1.2.0",
            "cpBatteryVoltage": "1.3.6.1.4.1.3808.1.1.1.2.1.3.0",
            "cpBatteryTemperature": "1.3.6.1.4.1.3808.1.1.1.2.1.4.0",
            "cpBatteryRuntimeRemaining": "1.3.6.1.4.1.3808.1.1.1.2.1.5.0",
            "cpInputVoltage": "1.3.6.1.4.1.3808.1.1.1.3.1.1.0",
            "cpInputFrequency": "1.3.6.1.4.1.3808.1.1.1.3.1.2.0",
            "cpOutputVoltage": "1.3.6.1.4.1.3808.1.1.1.4.1.1.0",
            "cpOutputFrequency": "1.3.6.1.4.1.3808.1.1.1.4.1.2.0",
            "cpOutputLoad": "1.3.6.1.4.1.3808.1.1.1.4.1.3.0",
            "cpOutputCurrent": "1.3.6.1.4.1.3808.1.1.1.4.1.4.0",
            "cpOutputPower": "1.3.6.1.4.1.3808.1.1.1.4.1.5.0",
        }
    },
    "Tripp Lite": {
        "base": "1.3.6.1.4.1.850",
        "name": "Tripp Lite MIB",
        "oids": {
            "tlIdentModel": "1.3.6.1.4.1.850.1.1.1.1.1.0",
            "tlBatteryStatus": "1.3.6.1.4.1.850.1.1.1.2.1.0",
            "tlBatteryCharge": "1.3.6.1.4.1.850.1.1.1.2.2.0",
            "tlBatteryVoltage": "1.3.6.1.4.1.850.1.1.1.2.3.0",
            "tlBatteryRuntimeRemaining": "1.3.6.1.4.1.850.1.1.1.2.4.0",
            "tlInputVoltage": "1.3.6.1.4.1.850.1.1.1.3.1.0",
            "tlOutputVoltage": "1.3.6.1.4.1.850.1.1.1.4.1.0",
            "tlOutputPercentLoad": "1.3.6.1.4.1.850.1.1.1.4.2.0",
        }
    },
    "Vertiv / Liebert": {
        "base": "1.3.6.1.4.1.17055",
        "name": "Vertiv Liebert MIB",
        "oids": {
            "liebertIdentModel": "1.3.6.1.4.1.17055.1.1.1.1.0",
            "liebertBatteryVoltage": "1.3.6.1.4.1.17055.1.2.1.0",
            "liebertBatteryCurrent": "1.3.6.1.4.1.17055.1.2.2.0",
            "liebertBatteryTemp": "1.3.6.1.4.1.17055.1.2.3.0",
            "liebertBatteryRuntime": "1.3.6.1.4.1.17055.1.2.4.0",
            "liebertInputVoltage": "1.3.6.1.4.1.17055.1.3.1.0",
            "liebertOutputVoltage": "1.3.6.1.4.1.17055.1.4.1.0",
            "liebertOutputLoad": "1.3.6.1.4.1.17055.1.4.2.0",
        }
    },
    "Delta": {
        "base": "1.3.6.1.4.1.5592",
        "name": "Delta MIB",
        "oids": {}
    },
    "Socomec": {
        "base": "1.3.6.1.4.1.18187",
        "name": "Socomec MIB",
        "oids": {}
    },
    "Riello UPS": {
        "base": "1.3.6.1.4.1.16022",
        "name": "Riello MIB",
        "oids": {}
    },
    "Gamatronic": {
        "base": "1.3.6.1.4.1.9889",
        "name": "Gamatronic MIB",
        "oids": {}
    },
    "Emerson / GE": {
        "base": "1.3.6.1.4.1.476",
        "name": "Emerson Network Power MIB",
        "oids": {}
    },
    "PowerWalker / Surtanc": {
        "base": "1.3.6.1.4.1.13040",
        "name": "PowerWalker MIB",
        "oids": {}
    },
}

UPS_SNMP_PATTERNS = {
    "APC": ["APC", "Smart-UPS", "Back-UPS", "Symmetra", "AP9630", "AP9631"],
    "Eaton": ["Eaton", "Powerware", "Pulsar", "Ellipse", "Evolution"],
    "CyberPower": ["CyberPower", "CP ", "OL", "OR", "PR"],
    "Tripp Lite": ["Tripp Lite", "TRIPP", "SMART", "SU"],
    "Vertiv / Liebert": ["Liebert", "Vertiv", "Chloride", "NX"],
    "Schneider Electric": ["Schneider", "APC", "Galaxy"],
    "Delta": ["Delta", "Delta Electronics"],
    "Socomec": ["Socomec", "Netys", "Modys"],
    "Riello UPS": ["Riello", "Multi Power"],
    "Gamatronic": ["Gamatronic"],
    "Emerson / GE": ["Emerson", "Liebert", "LIEBERT"],
    "PowerWalker / Surtanc": ["PowerWalker", "Surtanc", "VFI"],
}

BATTERY_STATUS_MAP = {
    1: "Desconocido",
    2: "Normal (en carga/mantenimiento)",
    3: "Batería baja (en respaldo)",
    4: "Sin batería",
}

OUTPUT_SOURCE_MAP = {
    1: "Otro",
    2: "Ninguno",
    3: "Normal (línea)",
    4: "Respaldo (batería)",
    5: "Bypass",
}

TEST_RESULT_MAP = {
    1: "OK (aprobado)",
    2: "No soportado",
    3: "No determinado",
    4: "Falló",
}

UPS_ALARM_DESCRIPTIONS = {
    "lowBattery": "Batería baja — reemplazar pronto",
    "onBattery": "En respaldo de batería — falta línea AC",
    "overload": "SOBRECARGA — reducir equipos conectados",
    "replaceBattery": "BATERÍA REQUIERE REEMPLAZO",
    "temperatureBad": "Sobrecalentamiento — revisar ventilación",
    "outputBad": "Fallo en salida — posible daño del inversor",
    "inputBad": "Problema en entrada AC — revisar toma corriente",
    "commFailure": "Fallo de comunicación — revisar cable SNMP",
    "fanFailure": "Fallo de ventilador — reemplazar ventilador",
    "shutdownImminent": "APAGADO INMINENTE — respaldo agotado",
    "noBattery": "Sin batería detectada — revisar conexión",
    "batteryTestFailed": "Prueba de batería FALLÓ — reemplazar",
    "groundFault": "Fallo de conexión a tierra",
    "internalFault": "Fallo interno del UPS — servicio técnico",
}

DIAGNOSTIC_PROCEDURE = {
  "title": "Manual de Diagnóstico de UPS",
  "sections": [
    {
      "icon": "🔍",
      "title": "1. Inspección Física",
      "checks": [
        {"q": "¿El UPS emite pitidos?", "ok": "Silencio o pitido breve al encender", "bad": "Intermitente = batería baja / Continuo = fallo grave", "tip": "Pitido cada 30s = batería descargada. Pitido continuo = sobrecarga o inversor dañado"},
        {"q": "¿Luces LED?", "ok": "Verde fijo = normal", "bad": "Rojo = problema / Ámbar = advertencia / Apagado = sin energía", "tip": "Consultar manual del fabricante para patrón de LEDs"},
        {"q": "¿Ventilador gira?", "ok": "Gira suavemente sin ruido extraño", "bad": "No gira o hace ruido (rodamientos secos)", "tip": "UPS sobrecargado o con ventilador tapado = sobrecalentamiento"},
        {"q": "¿Cables y conexiones?", "ok": "Firmes, sin oxidación, baterías bien conectadas", "bad": "Flojos, sulfatados, bornes corroídos", "tip": "Bornes de batería sulfatados → limpiar con bicarbonato y agua"},
        {"q": "¿Olor, fugas o deformaciones?", "ok": "Sin olor, sin líquido, sin hinchazón", "bad": "Olor a quemado / Líquido / Batería hinchada", "tip": "⚠️ Si la batería está hinchada, reemplazar URGENTE (riesgo de explosión)"},
      ]
    },
    {
      "icon": "📊",
      "title": "2. Análisis de Estado General",
      "checks": [
        {"q": "Tensión de entrada (220/110V)", "ok": "220V ±10% o 110V ±10%", "bad": "Fuera de rango o 0V", "tip": "0V = corte de línea. Si es constante, revisar instalación eléctrica"},
        {"q": "Tensión de salida", "ok": "220V ±5% o 110V ±5% estable", "bad": "Fluctuante o fuera de rango", "tip": "Si fluctúa sin carga → inversor dañado"},
        {"q": "Carga actual (load %)", "ok": "30-70% de la capacidad nominal", "bad": ">80% (sobrecarga) o <10% (infrautilizado)", "tip": ">80% → los equipos se apagarán al cortar la línea. <10% → estás desperdiciando capacidad"},
        {"q": "Carga de batería", "ok": "100% después de 4-6h de carga", "bad": "<80% después de 8h conectado", "tip": "Si no carga al 100%, la batería está sulfatada o el cargador falla"},
        {"q": "Autonomía restante", "ok": "≥ 80% de la especificación original", "bad": "< 50% de la original", "tip": "Ej: UPS nuevo daba 15min, ahora da 5min = batería a reemplazar"},
        {"q": "Temperatura interna", "ok": "20-35°C", "bad": ">40°C", "tip": ">40°C reduce vida de baterías un 50% por cada 10°C adicionales"},
      ]
    },
    {
      "icon": "🔋",
      "title": "3. Pruebas de Batería",
      "checks": [
        {"q": "Prueba rápida (10-30s)", "ok": "UPS cambia a batería y vuelve sin apagar equipos", "bad": "Se apaga o no cambia a batería", "tip": "Si se apaga durante la prueba → batería agotada o inversor dañado"},
        {"q": "Prueba profunda (5-15min)", "ok": "Mantiene carga durante toda la prueba", "bad": "Se apaga antes de tiempo", "tip": "Medir el tiempo que dura. Si es <50% de lo esperado → reemplazar baterías"},
        {"q": "Tiempo real con carga real", "ok": "Coincide con la prueba o es mayor", "bad": "Mucho menor que la prueba programada", "tip": "Conectá una carga conocida (ej: 500W) y cronometrá cuánto dura"},
        {"q": "Tensión en reposo (batería)", "ok": "12.5-13.0V (batería 12V) / 24.5-25.5V (24V)", "bad": "<12V (12V) o <24V (24V)", "tip": "Medir con multímetro en bornes de batería, SIN carga y SIN cargador"},
      ]
    },
    {
      "icon": "⚠️",
      "title": "4. Síntomas y Soluciones (por problema)",
      "checks": [
        {"q": "Pitido intermitente en línea normal", "ok": "Silencio", "bad": "Pitido cada 15-30s", "tip": "🔋 Batería agotada → ejecutar test de batería. Si charge <80%, reemplazar."},
        {"q": "Los equipos se apagan con UPS conectado", "ok": "Equipos funcionan normalmente", "bad": "Se apagan al cortar la línea o al conectar más equipos", "tip": "⚡ Sobrecarga → verificar load%. Desconectar equipos no críticos o ampliar UPS."},
        {"q": "No cambia a batería cuando corta la luz", "ok": "Cambia instantáneamente (0-10ms)", "bad": "Equipos se reinician o no cambia", "tip": "🔌 Fallo inversor/transferencia → si inputVoltage=0 pero outputSource≠4, servicio técnico."},
        {"q": "Autonomía muy corta (2-3min cuando daba 15min)", "ok": "Autonomía normal", "bad": "Cayó drásticamente", "tip": "⏳ Baterías envejecidas (>3-5 años) → medir tensión en reposo, programar reemplazo."},
        {"q": "UPS caliente al tacto", "ok": "Templado (30-40°C)", "bad": "Muy caliente (>50°C)", "tip": "🌡️ Sobrecalentamiento → mejorar ventilación, reducir carga <70%. Si persiste, ventilador dañado."},
        {"q": "No enciende ni con batería ni con línea", "ok": "Enciende normalmente", "bad": "No da señal de vida", "tip": "🪫 Fusible interno quemado o batería totalmente descargada. Probar reemplazo de fusible."},
        {"q": "Zumbido o vibración excesiva", "ok": "Silencio electromagnético normal", "bad": "Zumbido fuerte o vibración", "tip": "🔊 Transformador o bobina dañados → servicio técnico."},
        {"q": "Se dispara el térmico / fusible de entrada", "ok": "No se dispara", "bad": "Salta al conectar el UPS", "tip": "🔴 Cortocircuito interno o componentes de entrada dañados → no intentar reparar, llamar técnico."},
      ]
    },
    {
      "icon": "🛠️",
      "title": "5. Mantenimiento Preventivo",
      "checks": [
        {"q": "Frecuencia", "ok": "", "bad": "", "tip": "Cada 3 meses: inspección visual + prueba rápida. Cada 6 meses: prueba profunda + limpieza."},
        {"q": "Limpieza", "ok": "", "bad": "", "tip": "Limpiar rejillas de ventilación con aire comprimido (sin abrir). No usar líquidos."},
        {"q": "Ciclo de batería", "ok": "", "bad": "", "tip": "Descargar batería al 50% cada 3 meses y recargar completamente. Esto evita sulfatación."},
        {"q": "Reemplazo de baterías", "ok": "", "bad": "", "tip": "VRLA: cada 3-5 años. Li-Ion: cada 8-10 años. NiCd: cada 10-15 años."},
        {"q": "Registro de eventos", "ok": "", "bad": "", "tip": "Llevar log de pruebas, cambios de batería, cortes de luz. Ayuda a detectar tendencias."},
        {"q": "Monitoreo", "ok": "", "bad": "", "tip": "Usar NUT + upsmon para monitoreo centralizado. Configurar alertas SNMP trap o email."},
      ]
    },
    {
      "icon": "📋",
      "title": "6. Flujo de Diagnóstico (Árbol de decisiones)",
      "tree": [
        "¿El UPS enciende?",
        "  ├── No → ¿Hay línea? → No → Revisar cable, térmico, fusible",
        "  │   └── Sí → ¿Pitido continuo? → Sí → Inversor dañado → Servicio técnico",
        "  │       └── No → Fusible interno o batería 0V → Abrir y revisar",
        "  └── Sí → ¿Carga normal (LED verde)?",
        "      ├── No → LED rojo/ámbar → Revisar sección 2 (Análisis de Estado)",
        "      └── Sí → ¿Prueba de batería pasa?",
        "          ├── No → Batería agotada → Reemplazar",
        "          │   └── ¿Sigue fallando? → Cargador o placa de carga dañada",
        "          └── Sí → ¿Autonomía aceptable?",
        "              ├── Sí → UPS OK. Realizar mantenimiento preventivo.",
        "              └── No → Baterías envejecidas → Programar reemplazo",
      ]
    },
    {
      "icon": "🔧",
      "title": "8. Soluciones Paso a Paso",
      "solutions": [
        {
          "problem": "Reemplazar batería VRLA",
          "tools": "Destornillador, multímetro, batería nueva del mismo voltaje y capacidad",
          "steps": [
            "Apagar el UPS y desconectar de la corriente",
            "Esperar 5min para que se descarguen los capacitores internos",
            "Abrir la tapa del compartimiento de baterías (generalmente tapa frontal o inferior)",
            "Identificar los bornes: rojo = positivo (+), negro = negativo (-)",
            "CON PRECAUCIÓN: medir tensión con multímetro para confirmar que está descargada",
            "Desconectar primero el borne negativo (negro), luego el positivo (rojo)",
            "Sacar la batería vieja — NO hacer cortocircuito entre bornes con herramientas metálicas",
            "Colocar la batería nueva: conectar primero positivo (+), luego negativo (-)",
            "Cerrar tapa, conectar el UPS a la corriente y encender",
            "Dejar cargando 8-12h antes de hacer pruebas de autonomía",
            "Verificar que el UPS ya no emite pitidos y el LED está verde"
          ],
          "warnings": [
            "⚠️ Las baterías contienen ácido sulfúrico. No perforar ni incinerar.",
            "⚠️ Descartar la batería vieja en un punto limpio o centro de reciclaje.",
            "⚠️ Si la batería está hinchada o tiene fugas, usar guantes y gafas de protección."
          ]
        },
        {
          "problem": "Cambiar fusible interno",
          "tools": "Destornillador, fusible de repuesto del mismo amperaje y tipo",
          "steps": [
            "DESCONECTAR el UPS de la corriente y de todos los equipos",
            "Esperar 10min para descarga completa de capacitores",
            "Abrir la carcasa del UPS (tornillos generalmente en la parte inferior o trasera)",
            "Localizar el fusible en la placa principal (cerca de la entrada de corriente)",
            "Sacar el fusible con un extractor o pinza de plástico (NO metálica si hay carga)",
            "Inspeccionar visualmente: si está negro/roto o el filamento partido → quemado",
            "Verificar el amperaje impreso en el fusible o en la placa (ej: 10A 250V)",
            "Colocar el fusible nuevo del mismo amperaje exacto (NUNCA usar uno de mayor amperaje)",
            "Cerrar carcasa, conectar a corriente y probar",
            "Si el fusible vuelve a quemarse → hay cortocircuito en la placa → servicio técnico"
          ],
          "warnings": [
            "⚠️ NO reemplazar por un fusible de mayor amperaje (riesgo de incendio).",
            "⚠️ NO tocar componentes internos con las manos — algunos capacitores mantienen carga."
          ]
        },
        {
          "problem": "Reemplazar ventilador",
          "tools": "Destornillador, ventilador nuevo (medir tamaño: 40x40, 60x60, 80x80mm), pasta térmica (opcional)",
          "steps": [
            "Apagar UPS y desconectar de corriente. Esperar 5min",
            "Abrir la carcasa",
            "Identificar el ventilador (generalmente en la parte trasera o lateral)",
            "Desconectar el conector del ventilador de la placa (anotar posición/orientación)",
            "Sacar los tornillos que sujetan el ventilador a la carcasa",
            "Colocar el nuevo ventilador RESPETANDO LA DIRECCIÓN DEL FLUJO DE AIRE (flecha en el costado)",
            "Conectar a la placa en la misma posición que el original",
            "Cerrar carcasa, conectar corriente y verificar que gire suavemente"
          ],
          "warnings": [
            "⚠️ El ventilador debe tener el MISMO voltaje que el original (12V generalmente).",
            "⚠️ Si el ventilador no gira al encender, revisar la conexión o el conector en la placa."
          ]
        },
        {
          "problem": "UPS no enciende (sin señal de vida)",
          "steps": [
            "Verificar que el cable de corriente esté bien conectado al UPS y al toma",
            "Probar el toma con otro equipo (lámpara, cargador) para confirmar que haya tensión",
            "Si el toma tiene llave/interruptor, verificar que esté encendido",
            "Revisar el fusible interno (ver guía de cambio de fusible arriba)",
            "Medir tensión de batería con multímetro en los bornes internos",
            "  → Si < 12V (batería 12V) o < 24V (batería 24V): batería totalmente descargada o muerta",
            "  → Si 0V: fusible interno quemado o cable de batería desconectado",
            "Si la batería está baja pero el UPS sigue sin encender: conectar un cargador externo a la batería por 1h y reintentar",
            "Si aún así no enciende: placa de control dañada → servicio técnico"
          ],
          "warnings": [
            "⚠️ No abrir el UPS si está en garantía.",
            "⚠️ Internamente hay capacitores de alto voltaje. Esperar 10min desconectado antes de abrir."
          ]
        },
        {
          "problem": "UPS no cambia a batería cuando corta la luz",
          "steps": [
            "Verificar que la batería esté conectada internamente (bornes firmes, sin oxidación)",
            "Medir tensión de batería con multímetro: debe ser 12.5-13V (12V) o 25-26V (24V)",
            "  → Si es menor a 12V (12V): batería agotada → reemplazar",
            "  → Si es normal (12.5V+): el inversor o el relé de transferencia está dañado",
            "Escuchar si se escucha un 'clic' al cortar la luz (relé de transferencia)",
            "  → Si NO se escucha clic: placa de control o relé dañado → servicio técnico",
            "  → Si se escucha clic pero no hay salida: inversor dañado → servicio técnico"
          ],
          "warnings": [
            "⚠️ Probar con una carga pequeña (una lámpara LED) para no dañar equipos sensibles."
          ]
        },
        {
          "problem": "Autonomía muy reducida (baterías duran menos de 5min)",
          "steps": [
            "Ejecutar prueba de batería desde el software del UPS o manual",
            "Medir tensión en reposo (sin carga, sin cargador): debe ser 12.5-13V",
            "  → Si es < 12.4V: batería sulfatada o envejecida",
            "Medir tensión con carga (conectar una lámpara de 100W):",
            "  → Si cae por debajo de 11V inmediatamente: batería agotada → reemplazar",
            "Verificar temperatura del UPS durante la prueba:",
            "  → Si se calienta mucho > 45°C: ventilador sucio o carga muy alta",
            "Si la batería tiene más de 3 años → programar reemplazo",
            "Si la batería es nueva pero no dura → UPS tiene fuga interna o carga demasiado alta"
          ],
          "warnings": [
            "⚠️ No hacer pruebas de autonomía con equipos críticos conectados."
          ]
        },
        {
          "problem": "Resetear UPS por software",
          "tools": "NUT: upscmd, APC: apctest, CyberPower: pwrstat",
          "steps": [
            "OPCIÓN 1 — Reset por NUT:",
            "  upscmd <nombre> shutdown.return  — apaga y enciende cuando vuelva la línea",
            "  upscmd <nombre> test.battery.start.quick — test rápido",
            "OPCIÓN 2 — Reset físico (la mayoría de UPS):",
            "  Desconectar de la corriente y pulsar botón de encendido 10-15s (descarga residuos)",
            "  Esperar 30s, conectar a corriente sin equipos conectados",
            "  Encender el UPS y esperar que cargue 5min",
            "  Si enciende normalmente → conectar equipos de a uno",
            "OPCIÓN 3 — UPS con display:",
            "  Ingresar al menú de configuración → buscar 'Reset' o 'Factory Default'",
            "  Confirmar y esperar reinicio"
          ]
        },
      ]
    },
    {
      "icon": "🔧",
      "title": "7. Comandos por Herramienta",
      "tools": {
        "NUT": [
          "upsc <nombre>@<host>       — Estado completo del UPS",
          "upsc -l                    — Listar UPS disponibles",
          "upscmd <ups> shutdown.return  — Apagar y encender cuando vuelva la línea",
          "upscmd <ups> test.battery.start.quick — Test rápido (10s)",
          "upscmd <ups> test.battery.start.deep  — Test profundo (hasta que batería llegue a low)",
          "upscmd <ups> test.battery.stop        — Detener test",
        ],
        "APC (apcupsd)": [
          "apcaccess                 — Estado completo del APC UPS",
          "apcaccess status          — Resumen de estado",
          "apctest                   — Prueba interactiva de batería",
        ],
        "CyberPower (pwrstat)": [
          "pwrstat -status           — Estado completo",
          "pwrstat -pwroff           — Apagar salida",
          "pwrstat -pwron            — Encender salida",
          "pwrstat -test             — Ejecutar prueba de batería",
        ],
        "SNMP (cualquier vendor)": [
          "upsBatteryMinutesRemaining (1.3.6.1.2.1.33.1.2.3.0)  — Minutos restantes",
          "upsOutputPercentLoad (1.3.6.1.2.1.33.1.4.4.1.5.1)    — Carga actual (%)",
          "upsBatteryChargeRemaining (1.3.6.1.2.1.33.1.2.5.0)   — Carga batería (%)",
          "upsInputVoltage (1.3.6.1.2.1.33.1.3.3.1.3.1)         — Tensión entrada",
          "upsOutputVoltage (1.3.6.1.2.1.33.1.4.4.1.3.1)        — Tensión salida",
          "upsEstimatedMinutesRemaining (1.3.6.1.2.1.33.1.2.3.0) — Tiempo restante estimado",
        ],
      }
    },
  ]
}


def _run_cmd(cmd, timeout=10):
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        return r.stdout, r.stderr, r.returncode
    except FileNotFoundError:
        return "", "comando no encontrado", -1
    except subprocess.TimeoutExpired:
        return "", "timeout", -1


def _snmp_get_v2c(host, oid, community="public"):
    o, e, c = _run_cmd(["snmpget", "-v2c", "-c", community, "-Ovq", host, oid], 8)
    return o.strip() if c == 0 else None


def _snmp_get_v3(host, oid, user="", auth_proto="SHA", auth_pass="", priv_proto="AES", priv_pass=""):
    cmd = ["snmpget", "-v3", "-l", "authPriv", "-u", user]
    if auth_proto and auth_pass:
        cmd += ["-a", auth_proto.upper(), "-A", auth_pass]
    if priv_proto and priv_pass:
        cmd += ["-x", priv_proto.upper(), "-X", priv_pass]
    cmd += ["-Ovq", host, oid]
    o, e, c = _run_cmd(cmd, 10)
    return o.strip() if c == 0 else None


def _snmp_walk_v2c(host, oid, community="public"):
    o, e, c = _run_cmd(["snmpwalk", "-v2c", "-c", community, "-Ovq", host, oid], 15)
    if c != 0:
        return {}
    result = {}
    for line in o.strip().split("\n"):
        if not line:
            continue
        if " = " in line:
            k, v = line.split(" = ", 1)
            result[k.strip()] = v.strip()
        else:
            result[line] = ""
    return result


def _snmpwalk_v3(host, oid, user="", auth_proto="SHA", auth_pass="", priv_proto="AES", priv_pass=""):
    cmd = ["snmpwalk", "-v3", "-l", "authPriv", "-u", user]
    if auth_proto and auth_pass:
        cmd += ["-a", auth_proto.upper(), "-A", auth_pass]
    if priv_proto and priv_pass:
        cmd += ["-x", priv_proto.upper(), "-X", priv_pass]
    cmd += ["-Ovq", host, oid]
    o, e, c = _run_cmd(cmd, 20)
    if c != 0:
        return {}
    result = {}
    for line in o.strip().split("\n"):
        if not line:
            continue
        if " = " in line:
            k, v = line.split(" = ", 1)
            result[k.strip()] = v.strip()
        else:
            result[line] = ""
    return result


# ─── CLASE NUT AVANZADA ──────────────────────────────────────

class NUTClient:
    def __init__(self, ups_name="", host="localhost", port=3493):
        self.ups_name = ups_name
        self.host = host
        self.port = port

    def _dest(self, ups=""):
        u = ups or self.ups_name
        if not u:
            return ""
        if self.host != "localhost":
            return f"{u}@{self.host}:{self.port}"
        return u

    def is_available(self):
        return _run_cmd(["upsc", "-l"], 5)[2] == 0

    def list_ups(self):
        o, e, c = _run_cmd(["upsc", "-l"], 5)
        return [u.strip() for u in o.split("\n") if u.strip()] if c == 0 else []

    def get_status(self, ups=""):
        dest = self._dest(ups)
        if not dest:
            return {}
        o, e, c = _run_cmd(["upsc", dest], 10)
        if c != 0:
            return {}
        result = {}
        for line in o.strip().split("\n"):
            if ":" in line:
                k, v = line.split(":", 1)
                result[k.strip()] = v.strip()
        return result

    def run_command(self, command, ups=""):
        dest = self._dest(ups)
        if not dest:
            return {"error": "UPS no especificado"}
        o, e, c = _run_cmd(["upscmd", dest, command], 15)
        if c == 0:
            return {"status": "ok", "command": command, "output": o.strip()}
        return {"error": e.strip() or "comando falló"}

    def test_battery_quick(self, ups=""):
        return self.run_command("test.battery.start.quick", ups)

    def test_battery_deep(self, ups=""):
        return self.run_command("test.battery.start.deep", ups)

    def test_battery_cancel(self, ups=""):
        return self.run_command("test.battery.stop", ups)

    def shutdown_return(self, ups=""):
        return self.run_command("shutdown.return", ups)

    def load_off(self, ups=""):
        return self.run_command("load.off", ups)

    def load_on(self, ups=""):
        return self.run_command("load.on", ups)

    def get_daemon_status(self):
        o, e, c = _run_cmd(["upsmon", "-c", "status"], 5)
        if c == 0:
            return {"status": "running", "output": o.strip()}
        return {"status": "stopped", "error": e.strip()}

    def get_summary(self, ups=""):
        status = self.get_status(ups)
        if not status:
            return {"error": "No se pudo conectar al UPS"}
        def _(k, fallback="N/A", fmt=None):
            v = status.get(k, fallback)
            if v != fallback and fmt:
                return fmt(v)
            return v
        run = status.get("battery.runtime", "N/A")
        if run != "N/A":
            try:
                run = f"{int(run)/60:.1f} min"
            except:
                run = f"{run} seg"
        return {
            "fabricante": _("device.mfr", _("ups.mfr")),
            "modelo": _("device.model", _("ups.model")),
            "carga": _("ups.load", fmt=lambda v: f"{v}%"),
            "bateria": _("battery.charge", fmt=lambda v: f"{v}%"),
            "voltaje_bateria": _("battery.voltage", fmt=lambda v: f"{v}V"),
            "voltaje_entrada": _("input.voltage", fmt=lambda v: f"{v}V"),
            "voltaje_salida": _("output.voltage", fmt=lambda v: f"{v}V"),
            "frecuencia_salida": _("output.frequency", fmt=lambda v: f"{v} Hz"),
            "autonomia_restante": run,
            "temperatura": _("ups.temperature", fmt=lambda v: f"{v}°C"),
            "estado": _("ups.status"),
        }

    def diagnose(self, ups=""):
        s = self.get_status(ups)
        if not s:
            return {"error": "UPS no accesible"}
        issues = []
        warnings = []
        try:
            carga = float(s.get("ups.load", 0))
            if carga > 80:
                issues.append(f"Sobrecarga: {carga}% > 80%")
            elif carga > 60:
                warnings.append(f"Carga alta: {carga}%")
        except: pass
        try:
            bat = float(s.get("battery.charge", 100))
            if bat < 20:
                issues.append(f"Batería crítica: {bat}%")
            elif bat < 50:
                warnings.append(f"Batería baja: {bat}%")
        except: pass
        try:
            temp = float(s.get("ups.temperature", 0))
            if temp > 45:
                issues.append(f"Sobrecalentamiento: {temp}°C")
            elif temp > 35:
                warnings.append(f"Temperatura elevada: {temp}°C")
        except: pass
        return {
            "connected": True,
            "issues": issues,
            "warnings": warnings,
            "healthy": len(issues) == 0,
        }


# ─── CLASE SNMP AVANZADA ─────────────────────────────────────

class UPSSNMPClient:
    def __init__(self, host, community="public", snmp_version="v2c",
                 snmp_v3_user="", snmp_v3_auth_proto="SHA",
                 snmp_v3_auth_pass="", snmp_v3_priv_proto="AES",
                 snmp_v3_priv_pass=""):
        self.host = host
        self.community = community
        self.version = snmp_version
        self.v3_user = snmp_v3_user
        self.v3_auth_proto = snmp_v3_auth_proto
        self.v3_auth_pass = snmp_v3_auth_pass
        self.v3_priv_proto = snmp_v3_priv_proto
        self.v3_priv_pass = snmp_v3_priv_pass

    def _get(self, oid):
        if self.version == "v3":
            return _snmp_get_v3(self.host, oid, self.v3_user,
                                self.v3_auth_proto, self.v3_auth_pass,
                                self.v3_priv_proto, self.v3_priv_pass)
        return _snmp_get_v2c(self.host, oid, self.community)

    def _walk(self, oid):
        if self.version == "v3":
            return _snmpwalk_v3(self.host, oid, self.v3_user,
                                self.v3_auth_proto, self.v3_auth_pass,
                                self.v3_priv_proto, self.v3_priv_pass)
        return _snmp_walk_v2c(self.host, oid, self.community)

    def check_access(self):
        return self._get("1.3.6.1.2.1.1.1.0") is not None

    def get_sysdesc(self):
        return self._get("1.3.6.1.2.1.1.1.0")

    def get_vendor(self):
        sys = self.get_sysdesc() or ""
        for vendor, patterns in UPS_SNMP_PATTERNS.items():
            if any(p in sys for p in patterns):
                return vendor
        # Buscar por enterprise OID
        for vendor, info in VENDOR_MIBS.items():
            base = info["base"]
            test = self._get(f"{base}.1.1.1.0") or self._get(f"{base}.1.1.1.1.0") or self._get(base)
            if test:
                return vendor
        return "Desconocido"

    def get_vendor_specific(self):
        vendor = self.get_vendor()
        info = VENDOR_MIBS.get(vendor)
        if not info:
            return {}
        result = {"vendor": vendor, "mib": info["name"]}
        for name, oid in info["oids"].items():
            val = self._get(oid)
            if val is not None:
                result[name] = val
        return result

    def get_battery_status(self):
        val = self._get(UPS_MIB["upsBatteryStatus"])
        if val is not None:
            code = int(val)
            return {"codigo": code, "estado": BATTERY_STATUS_MAP.get(code, "Desconocido")}
        return {"estado": "No disponible"}

    def get_output_source(self):
        val = self._get(UPS_MIB["upsOutputSource"])
        if val is not None:
            code = int(val)
            return {"codigo": code, "fuente": OUTPUT_SOURCE_MAP.get(code, "Desconocido")}
        return {"fuente": "No disponible"}

    def get_test_result(self):
        val = self._get(UPS_MIB["upsBatteryTestResult"])
        if val is not None:
            code = int(val)
            return {"codigo": code, "resultado": TEST_RESULT_MAP.get(code, "Desconocido")}
        return {"resultado": "No disponible"}

    def get_percent_load(self):
        v = self._get(UPS_MIB["upsOutputPercentLoad"])
        return int(v) if v else None

    def get_battery_charge(self):
        v = self._get(UPS_MIB["upsBatteryEstimatedChargeRemaining"])
        return int(v) if v else None

    def get_minutes_remaining(self):
        v = self._get(UPS_MIB["upsBatteryEstimatedMinutesRemaining"])
        return int(v) if v else None

    def get_input_voltage(self):
        v = self._get(UPS_MIB["upsInputVoltage"])
        return float(v) if v else None

    def get_output_voltage(self):
        v = self._get(UPS_MIB["upsOutputVoltage"])
        return float(v) if v else None

    def get_output_frequency(self):
        v = self._get(UPS_MIB["upsOutputFrequency"])
        return float(v) if v else None

    def get_battery_voltage(self):
        v = self._get(UPS_MIB["upsBatteryVoltage"])
        return float(v) if v else None

    def get_battery_temperature(self):
        v = self._get(UPS_MIB["upsBatteryTemperature"])
        return float(v) if v else None

    def get_rated_va(self):
        v = self._get(UPS_MIB["upsConfigRatedVA"])
        return int(v) if v else None

    def get_rated_watts(self):
        v = self._get(UPS_MIB["upsConfigRatedWatts"])
        return int(v) if v else None

    def get_input_current(self):
        v = self._get(UPS_MIB["upsInputCurrent"])
        return float(v) if v else None

    def get_output_current(self):
        v = self._get(UPS_MIB["upsOutputCurrent"])
        return float(v) if v else None

    def get_output_power(self):
        v = self._get(UPS_MIB["upsOutputPower"])
        return float(v) if v else None

    def get_alarms(self):
        present = self._get(UPS_MIB["upsAlarmPresent"])
        if present and present != "0":
            walk = self._walk("1.3.6.1.2.1.33.1.6.2")
            alarms = []
            for k, v in walk.items():
                desc = UPS_ALARM_DESCRIPTIONS.get(v, f"Alarma: {v}")
                alarms.append({"oid": k, "code": v, "descripcion": desc})
            return alarms
        return []

    def get_full_status(self):
        if not self.check_access():
            return {"error": "SNMP no accesible"}
        r = {}
        for name, oid in UPS_MIB.items():
            v = self._get(oid)
            if v is not None:
                r[name] = v
        r["vendor"] = self.get_vendor()
        r["vendor_specific"] = self.get_vendor_specific()
        r["percent_load"] = self.get_percent_load()
        r["battery_charge"] = self.get_battery_charge()
        r["minutes_remaining"] = self.get_minutes_remaining()
        r["input_voltage"] = self.get_input_voltage()
        r["output_voltage"] = self.get_output_voltage()
        r["output_frequency"] = self.get_output_frequency()
        r["battery_voltage"] = self.get_battery_voltage()
        r["battery_temp"] = self.get_battery_temperature()
        r["rated_va"] = self.get_rated_va()
        r["rated_watts"] = self.get_rated_watts()
        r["input_current"] = self.get_input_current()
        r["output_current"] = self.get_output_current()
        r["output_power"] = self.get_output_power()
        r["alarms"] = self.get_alarms()
        r["battery_status_str"] = self.get_battery_status().get("estado", "")
        r["output_source_str"] = self.get_output_source().get("fuente", "")
        r["test_result_str"] = self.get_test_result().get("resultado", "")
        r["has_alarms"] = len(r["alarms"]) > 0
        return r

    def get_summary(self):
        s = self.get_full_status()
        if "error" in s:
            return s
        return {
            "host": self.host,
            "version_snmp": self.version,
            "vendor": s.get("vendor", "N/A"),
            "carga": f"{s.get('percent_load', 'N/A')}%",
            "bateria": f"{s.get('battery_charge', 'N/A')}%",
            "autonomia": f"{s.get('minutes_remaining', 'N/A')} min",
            "voltaje_entrada": f"{s.get('input_voltage', 'N/A')} V",
            "voltaje_salida": f"{s.get('output_voltage', 'N/A')} V",
            "frecuencia_salida": f"{s.get('output_frequency', 'N/A')} Hz",
            "voltaje_bateria": f"{s.get('battery_voltage', 'N/A')} V",
            "temp_bateria": f"{s.get('battery_temp', 'N/A')}°C",
            "corriente_entrada": f"{s.get('input_current', 'N/A')} A",
            "corriente_salida": f"{s.get('output_current', 'N/A')} A",
            "potencia_salida": f"{s.get('output_power', 'N/A')} W",
            "potencia_nominal": f"{s.get('rated_va', 'N/A')} VA / {s.get('rated_watts', 'N/A')} W",
            "estado_bateria": s.get("battery_status_str", "N/A"),
            "fuente_alimentacion": s.get("output_source_str", "N/A"),
            "ultimo_test": s.get("test_result_str", "N/A"),
            "alarmas": s.get("alarms", []),
            "fabricante": s.get("upsIdentManufacturer", "N/A"),
            "modelo": s.get("upsIdentModel", "N/A"),
        }

    def diagnose(self):
        s = self.get_full_status()
        if "error" in s:
            return {"error": s["error"]}
        issues = []
        warnings = []
        alarms = self.get_alarms()
        for a in alarms:
            issues.append(a["descripcion"])
        try:
            carga = float(s.get("percent_load", 0) or 0)
            if carga > 80:
                issues.append(f"Sobrecarga: {carga:.0f}%")
            elif carga > 60:
                warnings.append(f"Carga elevada: {carga:.0f}%")
        except: pass
        try:
            bat = float(s.get("battery_charge", 100) or 100)
            if bat < 20:
                issues.append(f"Batería críticamente baja: {bat:.0f}%")
            elif bat < 50:
                warnings.append(f"Batería baja: {bat:.0f}%")
        except: pass
        try:
            temp = float(s.get("battery_temp", 0) or 0)
            if temp > 45:
                issues.append(f"Sobrecalentamiento batería: {temp:.0f}°C")
            elif temp > 35:
                warnings.append(f"Temperatura batería elevada: {temp:.0f}°C")
        except: pass
        try:
            mins = s.get("minutes_remaining")
            if mins is not None and mins < 5:
                issues.append(f"Autonomía crítica: {mins} min")
            elif mins is not None and mins < 15:
                warnings.append(f"Autonomía baja: {mins} min")
        except: pass
        try:
            vin = float(s.get("input_voltage", 0) or 0)
            if vin > 0 and (vin < 105 or vin > 260):
                issues.append(f"Tensión de entrada fuera de rango: {vin}V")
        except: pass
        return {
            "connected": True,
            "host": self.host,
            "issues": issues,
            "warnings": warnings,
            "all_clear": len(issues) == 0,
        }

    def battery_health(self):
        s = self.get_full_status()
        if "error" in s:
            return {"error": s["error"]}
        charge = s.get("battery_charge")
        mins = s.get("minutes_remaining")
        temp = s.get("battery_temp")
        va = s.get("rated_va")
        load = s.get("percent_load")
        bat_v = s.get("battery_voltage")
        result = {
            "battery_charge_percent": charge,
            "runtime_minutes": mins,
            "temperature_c": temp,
            "battery_voltage": bat_v,
            "rated_va": va,
            "load_percent": load,
        }
        if charge is not None and charge < 50:
            result["health"] = "CRITICAL - Reemplazar batería"
            result["recommendation"] = "Programar reemplazo de batería URGENTE"
        elif charge is not None and charge < 70:
            result["health"] = "WARNING - Batería degradada"
            result["recommendation"] = "Monitorear, reemplazar pronto"
        elif charge is not None:
            result["health"] = "OK - Batería en buen estado"
            result["recommendation"] = "Continuar monitoreo normal"
        try:
            remaining_pct = 0
            if va and load and load > 0:
                remaining_pct = (mins / ((va * load / 100) / 100)) * 100 if mins else 0
                result["autonomy_vs_rated_pct"] = round(remaining_pct, 1)
        except: pass
        return result


# ─── CLASE MODBUS TCP ────────────────────────────────────────

class ModbusUPSClient:
    def __init__(self, host, port=502, unit_id=1):
        self.host = host
        self.port = port
        self.unit_id = unit_id
        self.sock = None

    def _connect(self):
        if self.sock:
            return True
        try:
            self.sock = socket.create_connection((self.host, self.port), timeout=5)
            return True
        except:
            return False

    def _close(self):
        if self.sock:
            self.sock.close()
            self.sock = None

    def _read_holding_registers(self, address, count=1):
        if not self._connect():
            return None
        # Modbus TCP: MBAP (7) + Function Code (1) + data
        tid = 1
        pid = 0
        length = 6 + count * 0
        unit = self.unit_id
        fc = 0x03  # Read Holding Registers
        req = pack(">HHHBHH", tid, pid, length, unit, fc, address, count)
        try:
            self.sock.sendall(req)
            resp = self.sock.recv(1024)
            if len(resp) >= 9:
                data = resp[9:]
                if len(data) >= count * 2:
                    return [unpack(">H", data[i:i+2])[0] for i in range(0, count*2, 2)]
        except:
            pass
        self._close()
        return None

    def check_access(self):
        self._close()
        r = self._read_holding_registers(0, 1)
        return r is not None

    def get_input_voltage(self):
        r = self._read_holding_registers(0x300, 1)
        return r[0] / 10.0 if r else None

    def get_output_voltage(self):
        r = self._read_holding_registers(0x301, 1)
        return r[0] / 10.0 if r else None

    def get_output_load(self):
        r = self._read_holding_registers(0x302, 1)
        return r[0] / 10.0 if r else None

    def get_battery_voltage(self):
        r = self._read_holding_registers(0x303, 1)
        return r[0] / 10.0 if r else None

    def get_battery_charge(self):
        r = self._read_holding_registers(0x304, 1)
        return r[0] if r else None

    def get_status(self):
        return {
            "input_voltage": self.get_input_voltage(),
            "output_voltage": self.get_output_voltage(),
            "output_load": self.get_output_load(),
            "battery_voltage": self.get_battery_voltage(),
            "battery_charge": self.get_battery_charge(),
        }


# ─── CLASE APC PowerChute ────────────────────────────────────

class PowerChuteClient:
    def __init__(self, host, port=6547, username="", password="", use_ssl=False):
        self.host = host
        self.port = APC_POWERCHUTE_SSL_PORT if use_ssl else port
        self.use_ssl = use_ssl
        self.auth = (username, password) if username else None

    def _req(self, path):
        import requests
        proto = "https" if self.use_ssl else "http"
        url = f"{proto}://{self.host}:{self.port}{path}"
        try:
            r = requests.get(url, auth=self.auth, timeout=10, verify=False)
            if r.status_code == 200:
                return r.text[:2000]
            return {"error": f"HTTP {r.status_code}"}
        except Exception as e:
            return {"error": str(e)}

    def get_status(self):
        return self._req("/api/v1/ups/status")

    def get_alarms(self):
        return self._req("/api/v1/ups/alarms")

    def get_battery(self):
        return self._req("/api/v1/ups/battery")

    def shutdown(self):
        import requests
        proto = "https" if self.use_ssl else "http"
        url = f"{proto}://{self.host}:{self.port}/api/v1/ups/shutdown"
        try:
            r = requests.post(url, auth=self.auth, timeout=10, verify=False)
            return {"status": "ok" if r.status_code == 200 else "error", "code": r.status_code}
        except Exception as e:
            return {"error": str(e)}


# ─── CLASE APCUPSD ──────────────────────────────────────────

class APCUPSDClient:
    def __init__(self, host="localhost", port=3551):
        self.host = host
        self.port = port

    def _connect(self):
        try:
            s = socket.create_connection((self.host, self.port), timeout=5)
            data = b""
            while True:
                chunk = s.recv(4096)
                if not chunk:
                    break
                data += chunk
                if b"\x00" in chunk or len(data) > 16384:
                    break
            s.close()
            return data.decode("utf-8", errors="replace")
        except:
            return None

    def get_status(self):
        raw = self._connect()
        if not raw:
            return {"error": "No se pudo conectar a apcupsd"}
        result = {}
        for line in raw.split("\n"):
            if ":" in line:
                k, v = line.split(":", 1)
                result[k.strip()] = v.strip()
        return result

    def get_summary(self):
        s = self.get_status()
        if "error" in s:
            return s
        return {
            "modelo": s.get("MODEL", "N/A"),
            "carga": s.get("LOADPCT", "N/A"),
            "bateria": s.get("BCHARGE", "N/A"),
            "voltaje_entrada": s.get("LINEV", "N/A"),
            "voltaje_salida": s.get("OUTPUTV", "N/A"),
            "autonomia": s.get("TIMELEFT", "N/A"),
            "estado": s.get("STATUS", "N/A"),
            "fabricante": s.get("UPSNAME", s.get("SERIALNO", "N/A")),
            "temperatura": s.get("ITEMP", "N/A"),
            "num_transferencias": s.get("NUMXFERS", "N/A"),
            "ultima_transferencia": s.get("XFERREASON", "N/A"),
            "tonelaje_bateria": s.get("NOMBATTV", "N/A"),
        }


# ─── DETECCIÓN INTELIGENTE ──────────────────────────────────

def detect_ups(host, community="public", snmp_version="v2c",
               snmp_v3_user="", snmp_v3_auth_pass="", snmp_v3_priv_pass="",
               modbus_port=502):
    results = {"host": host, "is_ups": False, "methods_tried": []}

    # SNMP
    try:
        client = UPSSNMPClient(host, community, snmp_version,
                                snmp_v3_user, "SHA", snmp_v3_auth_pass,
                                "AES", snmp_v3_priv_pass)
        if client.check_access():
            sysdesc = client.get_sysdesc() or ""
            vendor = client.get_vendor()
            bat = client.get_battery_status()
            load = client.get_percent_load()
            results["methods_tried"].append("snmp")
            if bat.get("codigo") or load is not None or "UPS" in sysdesc.upper() or "ups" in sysdesc.lower():
                mfr = client._get(UPS_MIB["upsIdentManufacturer"])
                model = client._get(UPS_MIB["upsIdentModel"])
                va = client.get_rated_va()
                results.update({
                    "is_ups": True,
                    "method": "SNMP",
                    "vendor": vendor,
                    "fabricante": mfr or vendor,
                    "modelo": model or sysdesc[:60],
                    "potencia_nominal_va": va,
                    "carga_percent": load,
                    "estado_bateria": bat.get("estado", ""),
                    "sysdesc": sysdesc[:100],
                })
                return results
    except: pass

    # NUT
    try:
        nut = NUTClient(host=host)
        ups_list = nut.list_ups()
        results["methods_tried"].append("nut")
        if ups_list:
            status = nut.get_summary(ups_list[0])
            results.update({
                "is_ups": True,
                "method": "NUT",
                "ups_name": ups_list[0],
                "status": status,
            })
            return results
    except: pass

    # Modbus TCP
    try:
        mod = ModbusUPSClient(host, modbus_port)
        if mod.check_access():
            results["methods_tried"].append("modbus")
            status = mod.get_status()
            if status.get("input_voltage") or status.get("output_voltage"):
                results.update({
                    "is_ups": True,
                    "method": "Modbus TCP",
                    "status": status,
                })
                return results
    except: pass

    # PowerChute
    try:
        pc = PowerChuteClient(host)
        status = pc.get_status()
        results["methods_tried"].append("powerchute")
        if isinstance(status, str) and ("ups" in status.lower() or "battery" in status.lower() or "status" in status.lower()):
            results.update({
                "is_ups": True,
                "method": "PowerChute",
                "status": status[:300],
            })
            return results
    except: pass

    # apcupsd
    try:
        apc = APCUPSDClient(host)
        status = apc.get_status()
        results["methods_tried"].append("apcupsd")
        if "error" not in status:
            results.update({
                "is_ups": True,
                "method": "apcupsd",
                "status": status,
            })
            return results
    except: pass

    return results


def check_nut_available():
    return _run_cmd(["which", "upsc"], 3)[2] == 0


def get_apcaccess_status(host=""):
    cmd = ["apcaccess"]
    if host:
        cmd.extend(["-h", host])
    o, e, c = _run_cmd(cmd, 10)
    if c != 0:
        return {"error": "apcaccess no disponible"}
    result = {}
    for line in o.split("\n"):
        if ":" in line:
            k, v = line.split(":", 1)
            result[k.strip()] = v.strip()
    return result


def get_pwrstat_status():
    o, e, c = _run_cmd(["pwrstat", "-status"], 10)
    if c != 0:
        return {"error": "pwrstat no disponible"}
    result = {}
    for line in o.split("\n"):
        if ":" in line:
            k, v = line.split(":", 1)
            result[k.strip()] = v.strip()
    return result


def estimate_battery_life(manufacture_date, battery_type="VRLA"):
    now = datetime.now()
    if isinstance(manufacture_date, str):
        try:
            manufacture_date = datetime.strptime(manufacture_date, "%Y-%m-%d")
        except:
            return {"error": "Formato de fecha inválido. Usar YYYY-MM-DD"}
    age_years = (now - manufacture_date).days / 365.25
    if battery_type.upper() == "VRLA":
        expected_life_years = 5
    elif battery_type.upper() == "LI-ION":
        expected_life_years = 10
    elif battery_type.upper() == "NICD":
        expected_life_years = 15
    else:
        expected_life_years = 5
    remaining = max(0, expected_life_years - age_years)
    health_pct = max(0, min(100, 100 * (1 - age_years / expected_life_years)))
    return {
        "fabricacion": manufacture_date.strftime("%Y-%m-%d"),
        "tipo": battery_type,
        "edad_anios": round(age_years, 1),
        "vida_esperada_anios": expected_life_years,
        "vida_restante_anios": round(remaining, 1),
        "salud_porcentaje": round(health_pct, 0),
        "recomendacion": "Reemplazar" if health_pct < 30 else "Monitorear" if health_pct < 60 else "OK",
    }
