# TechBot

Asistente técnico para redes, CCTV, control de acceso y sistemas.  
Interfaz web responsiva — funciona en **PC (Windows/Linux)**, **Android (Termux)** y como **PWA instalable**.

---

## Inicio rápido

```bash
pip install -r requirements.txt
python run_webapp.py
```

Abrir `http://localhost:5000`.  
En el móvil (misma WiFi): `http://<TU-IP>:5000`.

### Android (Termux)

```bash
pkg install python
pip install -r requirements.txt
python run_webapp.py
```

### APK Android

El directorio `android/` contiene un proyecto Android Studio (WebView).  
Compilar: `cd android && ./build-apk.sh` (requiere Android SDK).

---

## Contenido

- [Escáner de Red](#escáner-de-red)
- [Herramientas](#herramientas)
- [Test de Velocidad](#test-de-velocidad)
- [Monitoreo Continuo](#monitoreo-continuo)
- [SNMP](#snmp)
- [Planificación IP](#planificación-ip)
- [Topología](#topología)
- [APIs CCTV](#apis-cctv)
- [Control de Acceso](#control-de-acceso)
- [Diagnóstico](#diagnóstico)
- [Diagnóstico de UPS](#diagnóstico-de-ups)
- [Comandos](#comandos)
- [Protocolos y Puertos](#protocolos-y-puertos)
- [Calculadoras](#calculadoras)
- [MAC Lookup](#mac-lookup)
- [UPS / Zabbix](#ups--zabbix)
- [Scripts Python](#scripts-python)
- [PWA (App Instalable)](#pwa-app-instalable)
- [APK Android](#apk-android)
- [Dependencias](#dependencias)
- [Arquitectura](#arquitectura)

---

## Escáner de Red

| Función | Descripción |
|---------|-------------|
| **Ping + OS** | Ping por TCP connect (22, 80, 443, 8080, 8443, 3389, 9090). Sin bins externos. Fallback ICMP si disponible. Detecta SO por TTL |
| **Escaneo Rápido** | 29 puertos comunes en paralelo |
| **Descubrir Hosts** | Encuentra hosts activos en una subred (TCP ping multihilo) |
| **Trazar Ruta** | Traceroute hasta un host |
| **Puertos CCTV** | 17 puertos específicos de cámaras, DVR y NVR |
| **Puertos Control de Acceso** | 10 puertos de controladores |
| **Buscar CCTV/AC** | Descubre dispositivos en toda una subred |
| **Escaneo Personalizado** | Puertos definidos por el usuario |
| **Auto-detectar subred** | Botón que detecta tu IP y sugiere la subred |
| **Presets** | 192.168.0.0/24 · 192.168.1.0/24 · 10.0.0.0/24 · 172.16.0.0/24 |

> El ping usa TCP connect en vez de ICMP para funcionar **sin privilegios en cualquier SO**.  
> Si el binario `ping` está disponible (Linux, Windows, Termux), se usa como fallback para obtener TTL.

---

## Herramientas

Sección **🧰 Herramientas** en el menú. Todas con Python estándar (sin bins externos):

| Herramienta | Descripción |
|-------------|-------------|
| **DNS** | Consulta A, AAAA, PTR, ALL, MX |
| **Certificado SSL** | Verifica CN, emisor, SANs, días restantes, protocolo y cifrado |
| **Headers HTTP** | Muestra cabeceras de seguridad (HSTS, CSP, XFO, etc.) |
| **Wake-on-LAN** | Enciende un equipo remoto mediante magic packet |
| **Generar Token** | Contraseñas y tokens seguros |
| **Lector QR** | Escanea códigos QR con la cámara y rellena campos automáticamente |
| **Mi IP** | Detecta IP local y subred |

---

## Test de Velocidad

Mide descarga, subida, ping, servidor e **IP pública** usando Ookla (`speedtest-cli`).  
Se ejecuta en segundo plano — podés usar otras secciones mientras termina.  
Guarda los últimos 10 resultados en el navegador.

---

## Monitoreo Continuo

Escanea una subred automáticamente cada cierto intervalo.  
Detecta hosts nuevos y desconectados.  
Notifica cambios mediante **ntfy.sh**.

Se configura en Escáner → **⏱️ Monitoreo Continuo de Subred**.

---

## SNMP

Operaciones Walk, Get y Set sobre dispositivos SNMP.  
Muestra sistema, interfaces, tabla MAC, rutas y almacenamiento.  
Detecta fabricante y tipo de dispositivo (switch, router, CCTV, UPS).

---

## Planificación IP (IPAM)

Gestión local de redes, reservas IP, ámbitos DHCP, registros DNS (A, AAAA, CNAME, MX, TXT), VLANs y sitios.  
Búsqueda de redes libres, sugerencia de IP disponible y cálculo de uso.  
Persistencia en archivos JSON.

---

## Topología

Editor visual de topología de red con **Cytoscape.js**.

- **Manual**: agregar nodos (router, switch, firewall, servidor, PC, AP, cámara, NVR, DVR, nube, área) y conexiones (Ethernet, fibra, WiFi)
- **Auto-descubrir**: a partir de una IP semilla + comunidad SNMP, descubre dispositivos por tabla ARP y LLDP
- **Estado en vivo**: ping a cada nodo
- **Simulador**: animación de paquetes ICMP
- **Guardar / Cargar**: persistencia en JSON

---

## APIs CCTV

Conéctate en vivo a **Hikvision** (ISAPI), **Dahua** (CGI) y **ZKTeco**.  
Información del dispositivo, capturas de pantalla, eventos, PTZ, registros y almacenamiento.

> Si da error 401, habilitar "Autenticación Básica" en la configuración web del dispositivo.

---

## Control de Acceso

**21 fabricantes** con conexión y comandos:

Hikvision · Dahua · ZKTeco · Lenel · Paxton · HID · Gallagher · Avigilon · Aperio · Dormakaba · Schneider · JCI · Stanley · Bosch · Siemens · CDVI · SALTO · Nedap · 2N · Kantech · Wiegand

---

## Diagnóstico

**15 procedimientos guiados** y diagnóstico automático CCTV:

- Diagnóstico de Red Básico
- Cámara IP No Responde
- Servidor Linux
- Switch Cisco
- Firewall FortiGate
- Router MikroTik
- Diagnóstico WiFi
- Enlace de Fibra Óptica
- DVR/NVR No Responde
- UPS
- Diagnóstico automático: ping + puertos + HTTP + API por fabricante

---

## Diagnóstico de UPS

Manual interactivo completo con 8 secciones:

1. **🔍 Inspección Física** — luces, pitidos, ventilador, cables, olores
2. **📊 Análisis de Estado** — tensión, carga, batería, temperatura
3. **🔋 Pruebas de Batería** — rápida, profunda, tiempo real, tensión en reposo
4. **⚠️ Síntomas y Soluciones** — 8 problemas comunes con causa y solución
5. **🛠️ Mantenimiento Preventivo** — limpieza, ciclo de batería, reemplazo
6. **📋 Árbol de Decisiones** — flujo para diagnosticar paso a paso
7. **🔧 Comandos** — NUT, APC, CyberPower, SNMP
8. **Soluciones Paso a Paso** — 7 guías detalladas:

   | Guía | Pasos |
   |------|-------|
   | Reemplazar batería VRLA | 11 pasos con advertencias de seguridad |
   | Cambiar fusible interno | 10 pasos + qué hacer si vuelve a quemarse |
   | Reemplazar ventilador | 8 pasos con verificación de flujo de aire |
   | UPS no enciende | 9 pasos: toma → fusible → batería → placa |
   | No cambia a batería | 7 pasos: conexiones → tensión → relé → inversor |
   | Autonomía reducida | 8 pasos con pruebas de carga y temperatura |
   | Reset por software | NUT, APC, CyberPower y reset físico |

---

## Comandos

Comandos organizados por fabricante con búsqueda integrada:

Cisco · MikroTik · Fortinet · Linux · Windows · CCTV

También: Docker, Git, Kubernetes, MySQL, PostgreSQL, MongoDB, AWS, Azure, GCP, VMware, Proxmox, VirtualBox, Python/Dev, Prometheus, Grafana, ELK, Zabbix.

---

## Protocolos y Puertos

- **59 protocolos** con puerto, transporte y capa OSI
- **644 puertos** comunes con servicio asociado
- Búsqueda por nombre, número o servicio

---

## Calculadoras

| Categoría | Calculadoras |
|-----------|-------------|
| **Redes** | Subredes, VLSM, ancho de banda, tiempo de transferencia, CIDR/máscara |
| **Conversión** | Bytes, temperatura, dBm↔mW, AWG↔mm² |
| **Electrónica** | Ley de Ohm, divisor de tensión, baterías, paneles solares |
| **CCTV** | Almacenamiento y ancho de banda (12 resoluciones × 6 códecs), RAID, PoE |

---

## MAC Lookup

Base de ~2500 OUI. Buscar por MAC o por nombre de fabricante.

---

## UPS / Zabbix

- Monitoreo por **SNMP** (12 fabricantes), **NUT**, **Modbus TCP**, **PowerChute**, **apcupsd**, **pwrstat**
- Detección automática del protocolo
- Estimación de vida de batería
- Integración con **Zabbix** (hosts, problemas, alertas por ntfy.sh)

---

## Scripts Python

Funciones de Network, DHCP, DNS, Seguridad y Sistema.  
Código visible y copiable desde la interfaz.

---

## PWA (App Instalable)

TechBot es una **Progressive Web App**:

- `manifest.json` con icono SVG
- Service worker: caché de estáticos, red primero para API
- Modo offline: protocolos, puertos y referencias funcionan sin internet

En Chrome Android: menú → "Agregar a pantalla de inicio".

---

## APK Android

El directorio `android/` contiene un proyecto Android Studio.

**Características:**
- WebView a pantalla completa con barra de URL
- Deslizar para recargar
- Cámara para lector QR
- URL configurable (localhost o servidor remoto)
- Tema oscuro, orientación adaptable
- Sin dependencias externas

**Compilar:**
```bash
export ANDROID_HOME=$HOME/Android/Sdk
cd android
./build-apk.sh
```

**Instalar:**
```bash
adb install app/build/outputs/apk/debug/app-debug.apk
```

---

## Dependencias

```txt
flask>=3.0.0
requests>=2.31.0
speedtest-cli>=2.1.3
```

Todo lo demás usa **librería estándar de Python** (socket, ssl, ipaddress, threading, json, etc.).  
No requiere bins externos obligatorios — ping, dig, traceroute son opcionales.

---

## Arquitectura

```
run_webapp.py          → Inicia el servidor Flask
webapp/
  app.py               → 80+ rutas API
  static/
    css/style.css      → Estilos responsivos
    js/app.js          → Frontend completo (JavaScript vanilla)
    manifest.json      → Manifiesto PWA
    sw.js              → Service worker
    icons/             → Iconos
  templates/
    index.html         → Plantilla HTML
techbot/
  scanner/             → Escáner de red (TCP ping, puertos, traceroute)
  tools.py             → DNS, SSL, WOL, HTTP, Token, IP local
  monitor.py           → Monitoreo continuo de subred
  tasks.py             → Tareas en segundo plano
  speedtest.py         → Test de velocidad
  snmp/                → Operaciones SNMP
  ipam/                → Planificación IP
  topology/            → Editor de topología + auto-descubrimiento
  protocols/           → Base de protocolos y puertos
  commands/            → Comandos por fabricante
  calculators/         → Calculadoras técnicas
  diagnostics/         → Procedimientos de diagnóstico
  apis/                → Clientes CCTV (Hikvision, Dahua, ZKTeco)
  access_control/      → Control de acceso (21 fabricantes)
  scripts/             → Scripts Python
  mac_lookup.py        → Base OUI
  ups/                 → Monitoreo UPS + manual de diagnóstico
  zabbix/              → Integración Zabbix
android/               → Proyecto APK Android
```

---

## Licencia

Uso interno y educativo.
