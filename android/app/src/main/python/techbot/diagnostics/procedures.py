DIAGNOSTIC_PROCEDURES = {
    "Diagnóstico de Red Básico": """1. Verificar conectividad física (cables, LEDs de actividad en switch y NIC).
2. Verificar configuración IP: ipconfig (Windows) o ip a (Linux).
3. Hacer ping a la puerta de enlace (gateway).
4. Hacer ping a un servidor DNS (ej. 8.8.8.8).
5. Hacer ping a un dominio (ej. google.com).
6. Ejecutar traceroute (tracert en Windows, traceroute en Linux).
7. Verificar resolución DNS con nslookup o dig.
""",
    "Diagnóstico de Cámara IP No Responde": """1. Verificar alimentación (PoE o fuente de poder).
2. Verificar conexión física (cable Ethernet, conectores).
3. Descubrir IP usando SADP (Hikvision) o ConfigTool (Dahua).
4. Hacer ping a la dirección IP de la cámara.
5. Acceder por navegador web a la IP de la cámara.
6. Verificar puertos abiertos con nmap o telnet.
7. Realizar reset de fábrica si es necesario (botón de reset).

🎯 Diagnóstico automático disponible en: /api/diagnostics/cctv/<host>
   Ejecuta pruebas de ping, puertos, HTTP, RTSP y detección de fabricante.
""",
    "Diagnóstico de Servidor Linux": """1. Verificar uptime: uptime.
2. Verificar carga de CPU: top o htop.
3. Verificar uso de memoria: free -h.
4. Verificar uso de disco: df -h.
5. Listar procesos: ps aux.
6. Revisar logs del sistema: journalctl -xe.
7. Verificar puertos abiertos: ss -tuln.
8. Verificar conexiones de red: ss -tup.
9. Revisar archivos de log específicos (/var/log/).
""",
    "Diagnóstico de Switch Cisco": """1. show interface status.
2. show interface counters.
3. show mac address-table.
4. show vlan brief.
5. show spanning-tree.
6. show logging.
7. show errdisable recovery.
8. Verificar estado PoE: show power inline.
9. Verificar vecinos CDP/LLDP: show cdp neighbors / show lldp neighbors.
""",
    "Diagnóstico de Firewall FortiGate": """1. show system status.
2. diagnose sys top.
3. diagnose debug flow.
4. Revisar políticas de firewall: show firewall policy.
5. Revisar reglas NAT: show firewall vip / show firewall ippool.
6. Verificar estado VPN: show vpn ipsec.
7. Revisar logs: execute log display.
""",
    "Diagnóstico de Router MikroTik": """1. /system resource print.
2. /interface print.
3. /ip address print.
4. /ip route print.
5. /ip firewall filter print.
6. /ip dhcp-server lease print.
7. /log print.
8. /tool sniffer quick.
""",
    "Diagnóstico WiFi": """1. Verificar canal WiFi con iwlist (Linux) o airodump-ng.
2. Verificar interferencias en el espectro.
3. Medir nivel de señal con iwconfig.
4. Verificar clientes conectados al AP.
5. Analizar espectro con Wireshark.
6. Cambiar canal en router/AP si hay congestión.
7. Actualizar firmware del AP/router.
""",
    "Diagnóstico de Enlace de Fibra Óptica": """1. Verificar potencia óptica con power meter en ambos extremos.
2. Verificar limpieza de conectores (pulido).
3. Revisar estado de OLT y ONT.
4. Verificar atenuación en el enlace.
5. Realizar OTDR test para localizar fallas.
6. Verificar estado de los módulos SFP.
7. Realizar loopback test para aislar fallas.
""",
    "Diagnóstico de DVR/NVR No Responde": """1. Verificar alimentación (fuente 12V/48V PoE+).
2. Verificar LEDs del panel frontal (Power, HDD, Net, Alarm).
3. Conectar monitor VGA/HDMI para ver salida de video local.
4. Verificar IP del DVR/NVR (menú Config. Red o SADP/ConfigTool).
5. Hacer ping al DVR/NVR desde la misma red.
6. Acceder por navegador web a la IP (puertos 80/443/8000).
7. Verificar puertos DMSS/P2P (Hik-Connect: 8100-8102, Dahua: 8200).
8. Revisar si el servicio DHCP asignó IP diferente.
9. Verificar estado del disco duro (menú Almacenamiento).
10. Probar reset de fábrica (botón reset o pin en panel posterior).
""",
    "Diagnóstico de Disco Duro en DVR/NVR": """1. Acceder al menú de almacenamiento del DVR/NVR.
2. Verificar estado de cada HDD (Normal, Advertencia, Fallo).
3. Revisar SMART si está disponible (sda, sdb, etc.).
4. Verificar capacidad total vs. días de grabación configurados.
5. Comprobar formato del HDD (EXT4 habitual en NVR Linux).
6. Escuchar ruidos mecánicos anormales (clic de muerte).
7. Probar con HDD nuevo/vacío para descartar fallo del disco.
8. Verificar temperatura del disco (>55°C puede causar fallos).
9. Si usa NAS/iSCSI/NFS, probar conectividad desde el NVR.
10. En Hikvision: /ISAPI/System/Storage/status (API).
11. En Dahua: /cgi-bin/storageManager.cgi?action=query&type=hddInfo.
""",
    "Diagnóstico de Pérdida de Video en Cámara": """1. Verificar conexión física (cable Ethernet, conector RJ45).
2. Verificar alimentación PoE (LEDs en switch PoE y cámara).
3. Comprobar si la cámara responde a ping.
4. Acceder a la cámara directamente por navegador web.
5. Verificar si el DVR/NVR perdió la cámara (Cámara Desconectada).
6. Revisar logs del NVR/DVR para eventos de pérdida de video.
7. Verificar integridad del cable con tester de red.
8. Probar con cámara en otro puerto del switch PoE.
9. Verificar voltaje PoE (debe ser >44V para alimentación estable).
10. Si es inalámbrica, verificar intensidad de señal WiFi.
""",
    "Diagnóstico de Visión Nocturna": """1. Verificar que los LEDs IR enciendan (mirar cámara en oscuridad).
2. Comprobar si el sensor de luz (LDR) está bloqueado por suciedad.
3. Verificar el modo día/noche en la interfaz (ICR/IR Cut Filter).
4. En la configuración de la cámara, probar forzar modo noche.
5. Si la imagen se ve rosada/blanca de noche: IRC atascado o dañado.
6. Verificar distancia de iluminación IR (alcance especificado).
7. Probar iluminación externa IR si la cámara no tiene IR integrado.
8. Verificar si hay telarañas u obstrucciones frente a la cámara.
9. Revisar si el problema es general o solo en ciertas horas.
10. Actualizar firmware de la cámara si el IRC falla intermitentemente.
""",
    "Diagnóstico de Acceso Remoto a DVR/NVR": """1. Verificar que el DVR/NVR tenga IP pública o DDNS configurado.
2. Probar acceso desde red local primero.
3. Verificar puertos forwardeados en el router (80/443/8000/554/37777).
4. Usar portchecker online para verificar puertos desde internet.
5. Verificar P2P (Hik-Connect/DMSS) como alternativa al forward.
6. Comprobar que el DVR/NVR tenga salida a internet (ping 8.8.8.8).
7. Verificar DNS configurado en el DVR/NVR (8.8.8.8 recomendado).
8. Si usa DDNS, verificar que el hostname resuelva correctamente.
9. Revisar logs del router para conexiones bloqueadas/denegadas.
10. Probar con app móvil (Hik-Connect, DMSS, gDMSS, iVMS).
""",
    "Diagnóstico de Cableado Estructurado": """1. Verificar categoría del cable (Cat5e mínimo para PoE/PoE+).
2. Medir longitud del cable con tester (>100m puede causar pérdida).
3. Probar continuidad de todos los pares (1-2, 3-6, 4-5, 7-8).
4. Verificar que el cable no pase cerca de fuentes de interferencia.
5. Probar con cable patch cord conocido bueno para descartar.
6. Verificar estado de los conectores RJ45 (cuchillas levantadas).
7. Comprobar que el cable esté certificado para PoE (AWG 23-24).
8. Si hay problemas intermitentes, probar otros puertos del switch.
9. Verificar PoE budget del switch (no sobrecargar).
10. Revisar cableado horizontal vs. vertical (no exceder 90m+10m patch).
""",
    "Diagnóstico de Licencias y Activación de Cámaras": """1. Identificar el modelo exacto de cámara/NVR.
2. Verificar si la cámara requiere licencia adicional (Hikvision ACU/ACU Plus).
3. Comprobar canales disponibles vs. canales activos en el NVR.
4. En HikVision: verificar licencias en /ISAPI/System/customizedLicense.
5. En Dahua: verificar licencias en SmartPSS o ConfigTool.
6. Verificar estado de prueba/activación de licencias de IA (ANPR, Face).
7. Si la cámara aparece bloqueada, usar SADP para activación manual.
8. Verificar número de serie (SN) para registro de licencia.
9. Contactar al proveedor si las licencias no se reflejan.
10. Probar reset de fábrica y reactivación si persiste el problema.
""",
}
