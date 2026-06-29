# PilotEye / TechBot

**Asistente técnico portátil** para redes, CCTV, control de acceso y sistemas.

Funciona en **4 plataformas**: PC (Windows/Linux) · macOS · Android (Termux) · APK Android

---

## Índice

- [Inicio rápido](#inicio-rápido)
- [Manual del Usuario](#manual-del-usuario)
  - [Escáner de Red](#-escáner-de-red)
  - [Herramientas](#-herramientas)
  - [SNMP](#-snmp)
  - [Topología](#-topología)
  - [Speedtest](#-speedtest)
  - [CCTV](#-cctv)
  - [Control de Acceso](#-control-de-acceso)
  - [IPAM](#-ipam)
  - [Auditoría](#-auditoría)
  - [Calculadoras](#-calculadoras)
  - [WiFi](#-wifi)
  - [UPS / Zabbix](#-ups--zabbix)
  - [Scripts](#-scripts)
  - [Protocolos y Puertos](#-protocolos-y-puertos)
  - [Comandos](#-comandos)
  - [MAC Lookup](#-mac-lookup)
  - [Diagnóstico CCTV](#-diagnóstico-cctv)
  - [Ancho de Banda](#-ancho-de-banda)
- [API REST (115 endpoints)](#api-rest)
- [Stack Técnico](#stack-técnico)
- [APK Android](#apk-android)
- [Despliegue](#despliegue)

---

## Inicio rápido

### PC
```bash
pip install -r requirements.txt
python run_webapp.py
# Abrir http://localhost:5000
```

### Android Termux
```bash
pkg install python
pip install -r requirements.txt
python run_webapp.py
```

### APK Android
```bash
export ANDROID_HOME=$HOME/Android/Sdk
cd android && ./build-apk.sh
adb install app/build/outputs/apk/debug/app-debug.apk
```

### PWA
Abrí la web en Chrome Android → menú → "Agregar a pantalla de inicio".

---

## Manual del Usuario

### 🔍 Escáner de Red

Escanéo TCP/UDP sin binarios externos. Todo implementado con sockets Python puros.

| Función | Descripción |
|---------|-------------|
| **Ping** | TCP connect al puerto 80 (no requiere ICMP). Detecta OS por TTL. |
| **Quick Scan** | Escanéa 29 puertos comunes en 3 segundos. |
| **Descubrir** | Escanéa una subred completa (CIDR) buscando hosts activos. |
| **Traceroute** | IP_TTL sobre UDP, puro sin traceroute binario. |
| **Scan Puertos** | Escanéa puertos TCP específicos. |
| **Scan UDP** | Escanéa puertos UDP. |
| **Scan CCTV** | Detecta cámaras Hikvision, Dahua, etc. por puertos conocidos. |
| **Scan AC** | Detecta controladores de acceso (HID, Lenel, etc.). |
| **Comparar** | Compara dos escanéos para detectar cambios. |
| **Monitoreo** | Monitoreo continuo con alertas vía ntfy.sh. |

**Uso típico:**
1. Ingresá una IP en el campo "Host"
2. Seleccioná Quick Scan para un chequeo rápido
3. Usá Discover para mapear toda una red (ej: `192.168.1.0/24`)

### 🧰 Herramientas

| Herramienta | Descripción |
|-------------|-------------|
| **DNS Lookup** | Resolución A, AAAA, MX, NS, TXT, CNAME |
| **SSL Check** | Verifica certificado SSL: CN, SANs, emisor, expiración, protocolo, cifrado |
| **HTTP Headers** | Muestra headers de respuesta + análisis de seguridad (HSTS, CSP, X-Frame-Options) |
| **WHOIS** | Consulta WHOIS de dominio o IP |
| **WOL** | Wake-on-LAN: envía magic packet a una MAC |
| **Generar Token** | Token aleatorio configurable (longitud, dígitos, símbolos) |
| **NTP** | Consulta hora NTP a servidor público |
| **Port Knock** | Envía secuencia de port knocking |
| **HTTP Status** | Verifica código de estado HTTP |
| **Latencia** | Mide latencia continua a un host |
| **Mi IP** | Muestra IP pública y local |

### 📡 SNMP

Implementación **SNMP v1/v2c pura** en Python (sin binarios externos). Codifica/decodifica BER ASN.1 directamente sobre UDP.

| Función | Descripción |
|---------|-------------|
| **Check** | Verifica si SNMP responde en un host |
| **Sistema** | Información del sistema (sysDescr, sysName, uptime, contacto, ubicación) |
| **Interfaces** | Lista interfaces con tipo, MTU, velocidad, MAC, estado, tráfico |
| **Detectar** | Detecta fabricante del dispositivo por sysObjectID |
| **Walk** | Camina un árbol OID completo |
| **MIBs** | Navegador interactivo de OIDs — 60+ MIBs organizadas en categorías |

**MIBs disponibles:**
- 💻 Sistema (sysDescr, sysName, sysUpTime, sysContact, sysLocation)
- 🔌 Interfaces (ifDescr, ifType, ifSpeed, ifPhysAddress, ifIn/OutOctets, errores)
- 🌐 Red/IP (ipForwarding, ARP table, estadísticas IP)
- 🔗 Bridge/Switch (MAC table FDB, STP)
- 💾 Almacenamiento (hrStorageDescr, tamaño, usado)
- 🧠 Memoria/Sistema (hrSystemUptime, procesos, usuarios)
- 🔗 TCP/UDP (conexiones, segmentos, datagramas)
- 📊 Estadísticas SNMP (paquetes, versiones, community strings, errores)

**Uso típico:**
1. Ingresá IP del dispositivo
2. Community string (default: `public`)
3. Check → Sistema → Interfaces → MIBs

### 🌐 Topología

Editor visual de topología de red basado en Cytoscape.js.

| Función | Descripción |
|---------|-------------|
| **Editor** | Arrastrar y soltar nodos, conexiones, etiquetas |
| **Auto-descubrimiento** | Detecta dispositivos via TCP scan + ARP local + SNMP ARP |
| **Iconos** | Router, switch, cámara, servidor, firewall, AP, UPS, NAS, impresora |
| **Guardar/Cargar** | Topologías persistentes en localStorage |
| **Exportar** | Exporta como imagen o JSON |

### 🚀 Speedtest

Test de velocidad multi-stream (6 conexiones paralelas).

- Download y upload de 10 segundos
- Servidor personalizable
- Medición en Mbps con gráfico en tiempo real
- Sin dependencias externas (urllib + threading)
- Funciona detrás de NAT/proxy

### 📷 CCTV

Diagnóstico y configuración de cámaras CCTV.

| Función | Descripción |
|---------|-------------|
| **Conexión** | Conecta a Hikvision (ISAPI), Dahua (CGI), ZKTeco |
| **Info** | Datos del dispositivo, firmware, capacidad |
| **Snapshot** | Captura instantánea desde la cámara |
| **PTZ** | Control PTZ (presets, movimiento absoluto/relativo) |
| **Eventos** | Eventos de alarma, detección de movimiento |
| **Diagnóstico** | 15 procedimientos guiados para troubleshooting |
| **Configuración** | Cambiar IP, password, datetime, DHCP, factory reset |
| **RTSP** | URLs RTSP por fabricante |
| **Credenciales** | Base de credenciales por defecto por marca |
| **Pinout** | Pinout de conectores (RJ45, BNC, alimentación) |
| **Storage** | Estimación de almacenamiento por días, codec, resolución |

### 🔐 Control de Acceso

Soporta **21 fabricantes**: Hikvision, Dahua, ZKTeco, Lenel, Kantech, Paxton, Gallagher, HID, Bosch, CDVI, DDS, ADT, Suprema, NEDAP, Kisi, Brivo, SALTO, Genetec, Axis, iClass, Vanderbilt.

| Función | Descripción |
|---------|-------------|
| **Conectar** | Autentica contra el controlador |
| **Estado** | Puertas, lectores, eventos |
| **Auditoría** | Trae eventos de acceso (get_audit_trail) |
| **Comandos** | Abrir puerta, bloquear, modo mantenimiento |

### 🖥️ IPAM (IP Address Management)

Gestión completa de direccionamiento IP.

| Función | Descripción |
|---------|-------------|
| **Redes** | Agregar, editar, eliminar subredes (CIDR) |
| **Reservas** | Reservas IP con MAC, hostname, descripción |
| **DHCP** | Configuración de pools DHCP |
| **DNS** | Registros A, AAAA, CNAME, MX, TXT |
| **VLANs** | Gestión de VLANs con ID, nombre, subred |
| **Sitios** | Organización por sitios/ubicaciones |
| **Subnet usage** | Porcentaje de uso por subred |
| **Sugerir IP** | Encuentra IP libre disponible |

### 📋 Auditoría

Genera un informe de seguridad completo de un host.

**Datos recolectados:**
- Ping (estado, OS, TTL, latencia)
- Puertos abiertos (29 puertos comunes, con nivel de riesgo)
- Dispositivos CCTV detectados
- Traceroute (ruta de red)
- Certificado SSL (si aplica)
- HTTP Headers con análisis de seguridad
- WHOIS

**Score de seguridad:**
- **A** (90–100): Excelente
- **B** (75–89): Buena
- **C** (55–74): Aceptable
- **D** (35–54): Deficiente
- **F** (0–34): Crítica

**Recomendaciones automáticas** según hallazgos (puertos críticos, SSL expirado, headers faltantes, etc.)

### ⚡ Calculadoras

| Calculadora | Descripción |
|-------------|-------------|
| **Subredes/VLSM** | Cálculo de subredes, broadcast, hosts, wildcard |
| **Ancho de Banda** | Tiempo de transferencia, conversión unidades |
| **Ohm** | Voltaje, corriente, resistencia, potencia |
| **dBm ↔ mW** | Conversión de unidades de potencia RF |
| **CCTV Storage** | Días de grabación según codec, resolución, FPS |
| **PoE** | Presupuesto de energía PoE |
| **RAID** | Capacidad efectiva según nivel RAID |
| **Conversiones** | Decimal, binario, hex, IP, máscara |

### 📶 WiFi

| Plataforma | Método |
|------------|--------|
| **Android APK** | WifiManager nativo vía TechBotBridge.java |
| **Android Termux** | termux-wifi-scaninfo |
| **Linux** | iw dev scan |
| **Windows** | netsh wlan show networks |
| **macOS** | /System/Library/PrivateFrameworks/Apple80211.framework/airport |

Maneja SSID ocultos, errores de permiso, interfaces múltiples.

### 🔋 UPS / Zabbix

| Función | Descripción |
|---------|-------------|
| **Manual UPS** | 8 secciones interactivas: topología, componentes, baterías, instalación, mantenimiento |
| **NUT** | Monitoreo UPS via NUT (Network UPS Tools) sobre TCP puro (puerto 3493) |
| **Zabbix** | Conexión API Zabbix, lista de hosts, alertas, estado |

### 📜 Scripts

Scripts Python ejecutables directamente desde la UI.

| Categoría | Scripts |
|-----------|---------|
| **Network** | ping, traceroute, dns_lookup, http_check, ssl_check, whois, speedtest, port_scan |
| **DHCP** | dhcp_discover, dhcp_lease_check, dhcp_starvation |
| **DNS** | dns_resolve, dns_reverse, dns_zone_transfer, dns_mx, dns_spf, dns_dmarc |
| **Seguridad** | check_http_security, check_snmp_public, check_rdp_security, ssl_cert_check, check_mysql_security |
| **Sistema** | audit_log, security_info, pam_config, limits_config, package_updates, services_list, docker_status, disk_usage, network_connections, process_list |

### 📡 Protocolos y Puertos

Base de datos de **59 protocolos** y **644 puertos** con búsqueda.

- Protocolos: HTTP, DNS, DHCP, SNMP, FTP, SSH, SMTP, etc.
- Puertos: número, protocolo, descripción, riesgo

### 📋 Comandos

Base de comandos por fabricante/sistema.

| Categoría | Comandos |
|-----------|----------|
| **Cisco** | show, configure, interface, vlan, routing, acl, ospf, bgp, stp |
| **MikroTik** | interface, ip, routing, dhcp, firewall, bridge, capsman |
| **Fortinet** | config system, config router, diagnose, execute |
| **Linux** | systemd, network, firewall, disk, process, docker, lvm |
| **Windows** | ipconfig, netstat, wmic, powershell, dns, bitsadmin |
| **CCTV** | Hikvision ISAPI, Dahua CGI, RTSP |
| **Docker/K8s** | docker, kubectl |
| **Git** | config, branch, commit, remote, log, stash, tags |

### 🔍 MAC Lookup

Base de ~2500 OUI. Busca fabricante por MAC address.

### 📋 Diagnóstico CCTV

15 procedimientos guiados para troubleshooting de cámaras y NVRs:

1. Cámara no enciende
2. Cámara no muestra imagen
3. Imagen borrosa / fuera de foco
4. Visión nocturna no funciona
5. Cámara se desconecta intermitentemente
6. No se puede acceder vía web
7. Cable de red dañado
8. Puerto PoE no funciona
9. Grabación no funciona
10. Almacenamiento lleno
11. Audio no funciona
12. PTZ no responde
13. Configuración de red perdida
14. Cámara no responde a ping
15. Fallo de alimentación

### 🔌 Ancho de Banda

Monitoreo de ancho de banda via SNMP.

- Polling de interfaces (ifInOctets/ifOutOctets)
- Gráfico en tiempo real (SVG)
- Conversión a Mbps
- Múltiples interfaces simultáneas

---

## API REST

**115 endpoints** documentados. Todos responden en JSON.

| Ruta | Método | Descripción |
|------|--------|-------------|
| `/api/status` | GET | Estado del servidor |
| `/api/protocols` | GET | Lista de protocolos |
| `/api/protocols/<name>` | GET | Detalle de protocolo |
| `/api/ports` | GET | Lista de puertos |
| `/api/ports/<port>` | GET | Detalle de puerto |
| `/api/commands` | GET | Lista de comandos por categoría |
| `/api/calculators` | GET | Lista de calculadoras |
| `/api/calculators/run` | POST | Ejecutar calculadora |
| `/api/diagnostics` | GET | Lista de diagnósticos |
| `/api/diagnostics/<name>` | GET | Detalle de diagnóstico |
| `/api/diagnostics/cctv/*` | GET | Diagnóstico CCTV por fabricante |
| `/api/cctv` | GET | Estado CCTV |
| `/api/cctv/connect` | POST | Conectar cámara |
| `/api/cctv/command` | POST | Comando CCTV |
| `/api/access-control` | GET | Estado control de acceso |
| `/api/access-control/connect` | POST | Conectar controlador |
| `/api/access-control/command` | POST | Comando AC |
| `/api/scanner/ping` | GET | Ping a host |
| `/api/scanner/quick-scan` | GET | Escaneo rápido |
| `/api/scanner/discover` | GET | Descubrir hosts en subred |
| `/api/scanner/traceroute` | GET | Traceroute |
| `/api/scanner/scan-ports` | GET | Escaneo de puertos TCP |
| `/api/scanner/scan-ports-udp` | GET | Escaneo de puertos UDP |
| `/api/scanner/scan-cctv` | GET | Detectar CCTV en host |
| `/api/scanner/scan-ac` | GET | Detectar AC en host |
| `/api/scanner/discover-cctv` | GET | Descubrir CCTV en subred |
| `/api/scanner/compare` | POST | Comparar dos escaneos |
| `/api/tools/dns` | GET | DNS lookup |
| `/api/tools/dns/mx` | GET | MX records |
| `/api/tools/ssl` | GET | SSL certificate check |
| `/api/tools/http-headers` | GET | HTTP headers |
| `/api/tools/whois` | GET | WHOIS lookup |
| `/api/tools/wol` | POST | Wake-on-LAN |
| `/api/tools/token` | GET | Generar token |
| `/api/tools/local-ip` | GET | IP local |
| `/api/tools/ntp` | GET | Consulta NTP |
| `/api/tools/port-knock` | POST | Port knocking |
| `/api/tools/http-status` | GET | HTTP status code |
| `/api/tools/ping-latency` | GET | Latencia continua |
| `/api/snmp/info` | GET | Info SNMP + MIBs |
| `/api/snmp/get` | GET | SNMP get |
| `/api/snmp/walk` | GET | SNMP walk |
| `/api/snmp/check` | GET | SNMP check |
| `/api/snmp/system` | GET | SNMP system info |
| `/api/snmp/interfaces` | GET | SNMP interfaces |
| `/api/snmp/detect-device` | GET | Detectar fabricante |
| `/api/snmp/cctv-info` | GET | Info CCTV via SNMP |
| `/api/wifi/scan` | GET | Escanear WiFi |
| `/api/wifi/interfaces` | GET | Interfaces WiFi |
| `/api/dhcp/discover` | GET | DHCP discover |
| `/api/bandwidth/poll` | GET | Polling ancho de banda |
| `/api/bandwidth/traffic` | GET | Tráfico actual |
| `/api/ipam/*` | GET/POST/DELETE | IPAM completo |
| `/api/topology/*` | GET/POST/DELETE | Topología |
| `/api/scripts` | GET | Scripts disponibles |
| `/api/scripts/<cat>/<func>` | GET | Código de script |
| `/api/mac-lookup` | GET | MAC OUI lookup |
| `/api/tasks` | GET | Tareas activas |
| `/api/speedtest` | POST | Ejecutar speedtest |
| `/api/monitor/*` | GET/POST | Monitoreo continuo |
| `/api/ups/*` | GET | UPS diagnostics |
| `/api/ups/zabbix/*` | GET/POST | Integración Zabbix |

---

## Stack Técnico

```
Backend:    Flask + Python estándar (socket, ssl, ipaddress, threading, urllib)
Frontend:   Vanilla JS + Cytoscape.js + CSS custom properties (5 temas)
APK:        Chaquopy (Python 3.11) + WebView + WifiManager bridge Java
PWA:        manifest.json + service worker (caché + offline)
```

### Implementaciones puras (sin binarios externos)

- **SNMP:** BER encoder/decoder ASN.1 sobre UDP socket
- **Speedtest:** 6 streams paralelos, urllib, threading
- **Ping:** TCP connect (sin ICMP requerido)
- **Traceroute:** IP_TTL + UDP probes
- **DHCP:** DHCPDISCOVER broadcast
- **NUT:** TCP raw (puerto 3493)
- **DNS, SSL, HTTP, WOL:** socket + ssl + http.client
- **QR:** BarcodeDetector API + jsQR fallback

### Dependencias

```
flask>=3.0.0
requests>=2.31.0
```

Todo lo demás usa librería estándar de Python.

---

## APK Android

Proyecto Android Studio con Chaquopy (Python 3.11 embebido).

- WebView fullscreen (sin barra de URL visible)
- Servidor Flask embebido (inicio automático)
- WifiManager nativo vía TechBotBridge.java
- Cámara para QR
- Tema oscuro
- Orientación adaptable

### Build

```bash
export ANDROID_HOME=$HOME/Android/Sdk
cd android
./build-apk.sh
# APK en: android/app/build/outputs/apk/debug/app-debug.apk
```

### Requisitos

- Android Studio + SDK 24+
- Chaquopy plugin 15.0.1

---

## Despliegue

### Producción (Flask)
```bash
pip install -r requirements.txt
python run_webapp.py
# Por defecto en 0.0.0.0:5000
```

### Con Gunicorn
```bash
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 run_webapp:app
```

### Docker (opcional)
```dockerfile
FROM python:3.11-slim
COPY . /app
WORKDIR /app
RUN pip install -r requirements.txt
EXPOSE 5000
CMD ["python", "run_webapp.py"]
```
