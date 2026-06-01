# TechBot Web App

Asistente técnico para técnicos de redes, CCTV, control de acceso y sistemas — completamente en español. Interfaz web responsiva, funciona en PC y móvil.

## Inicio rápido

```bash
pip install -r requirements.txt
python run_webapp.py
```

Abrir `http://localhost:5000` en el navegador. Desde el móvil en la misma WiFi: `http://<IP-DE-TU-PC>:5000`.

## Funcionalidades

### 🌐 Protocolos de Red
Catálogo de 59 protocolos con puerto, transporte, capa OSI y descripción. Filtro por nombre.

### 🔌 Puertos Comunes
Base con 644 puertos TCP/UDP. Búsqueda por número o servicio. Incluye puertos CCTV y control de acceso.

### ⌨️ Comandos por Fabricante
Comandos organizados por categoría para **Cisco, MikroTik, Fortinet, Linux, Windows y CCTV** (165 comandos: RTSP, snapshots, ONVIF, Hikvision ISAPI, Dahua CGI, ZKTeco HTTP, diagnóstico). Búsqueda integrada, pestalla por fabricante.

### 🧮 Calculadoras Técnicas
- **Redes**: subredes, VLSM, ancho de banda, tiempo de transferencia, CIDR/máscara
- **Conversión**: bytes, temperatura, dBm ↔ mW, AWG ↔ mm²
- **Electrónica**: ley de Ohm, divisor de tensión, baterías, paneles solares
- **CCTV**: almacenamiento/ancho de banda por grupos de cámaras, 12 resoluciones, 6 codecs, RAID, PoE budget

### 📷 APIs CCTV
Conectate en vivo a **Hikvision** (ISAPI), **Dahua** (CGI) y **ZKTeco**. Ingresás IP, puerto, usuario y contraseña; ves la info del dispositivo y podés ejecutar comandos (snapshot, reboot, eventos, etc.). Las APIs usan autenticación básica — en firmwares modernos hay que habilitarla en la web del dispositivo.

### 🔍 Diagnóstico CCTV Automático
Escanea 17 puertos, detecta el fabricante por firma HTTP, verifica DVR/NVR, estado de discos, y prueba cada API por vendor. También incluye procedimientos guiados: DVR/NVR no responde, pérdida de video, visión nocturna, etc.

### 🔍 Escáner de Red
Ping + detección de SO por TTL, escaneo rápido de puertos comunes, descubrimiento de hosts por subred, traceroute, escaneo específico de puertos CCTV y control de acceso, identificación de dispositivos.

### 📡 SNMP
Walk, Get, Set. Información del sistema, interfaces, tabla MAC, tabla de rutas, almacenamiento. Detecta vendor y tipo de dispositivo (switch, router, CCTV, UPS).

### 🌐 IPAM (Planificación IP)
Gestión local de redes, reservaciones IP, scopes DHCP, registros DNS (A/AAAA/CNAME/MX/TXT), VLANs y sitios. Búsqueda de redes libres, sugerencia de IP disponible, cálculo de uso de subred. Todo se guarda en archivos JSON.

### 🏷 MAC Lookup
Base de ~2500 OUI. Buscá por MAC (cualquier formato: `AA:BB:CC`, `AA-BB-CC`, `AABBCC`) o por nombre de fabricante. Listado completo de fabricantes agrupados.

### 🚪 Control de Acceso
Soporte para **21 vendors**: Hikvision, Dahua, ZKTeco, Lenel, Paxton, HID, Gallagher, Avigilon, Aperio, Dormakaba, Schneider, JCI, Stanley, Bosch, Siemens, CDVI, SALTO, Nedap, 2N, Kantech, Wiegand. Conexión en vivo con el dispositivo, abrir/cerrar puerta, ver estado y eventos.

### 🐍 Scripts Python
Funciones de red y sistema listas para copiar. Categorizadas y con el código fuente visible en la misma interfaz.

### 🔋 UPS (SAI)
Monitoreo de UPS por **SNMP** (12 vendors con MIBs), **NUT**, **Modbus TCP**, **PowerChute**, **apcupsd**, **pwrstat** (CyberPower). Detección automática del protocolo, estimación de vida de batería, procedimiento de diagnóstico.

### ⚡ Speedtest
Test de velocidad vía Ookla Speedtest. Mide bajada, subida, ping, servidor e IP pública. Se ejecuta en segundo plano — podés seguir usando la app mientras termina. Los últimos 10 resultados se guardan en el navegador.

### ⏳ Tareas en Segundo Plano
Todas las herramientas de red (speedtest, escáner, diagnóstico CCTV, UPS) se ejecutan en segundo plano. Iniciás un test o escaneo, ves "Ejecutando..." y podés cambiar a otra ficha sin esperar. Cuando termina, el resultado aparece automáticamente.

## Notas

- La interfaz está diseñada para uso móvil (cards, scroll horizontal, modal tipo bottom sheet).
- No requiere base de datos externa — IPAM usa archivos JSON.
- Para APIs CCTV: habilitar "Autenticación Básica" en la web del dispositivo si da error 401.
- Speedtest requiere `speedtest-cli` (incluido en `requirements.txt`). La primera ejecución puede tardar ~30s.
