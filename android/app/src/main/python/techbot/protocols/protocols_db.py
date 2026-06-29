PROTOCOLS = {
    "HTTP": {
        "name": "Hypertext Transfer Protocol",
        "port": 80,
        "transport": "TCP",
        "description": "Protocolo base para la transferencia de páginas web. Sin cifrar.",
        "layer": "Aplicación (Capa 7)"
    },
    "HTTPS": {
        "name": "Hypertext Transfer Protocol Secure",
        "port": 443,
        "transport": "TCP",
        "description": "Versión segura de HTTP con cifrado SSL/TLS.",
        "layer": "Aplicación (Capa 7)"
    },
    "FTP": {
        "name": "File Transfer Protocol",
        "port": 21,
        "transport": "TCP",
        "description": "Protocolo para transferencia de archivos. No cifrado.",
        "layer": "Aplicación (Capa 7)"
    },
    "SFTP": {
        "name": "SSH File Transfer Protocol",
        "port": 22,
        "transport": "TCP",
        "description": "Transferencia de archivos sobre SSH con cifrado.",
        "layer": "Aplicación (Capa 7)"
    },
    "SSH": {
        "name": "Secure Shell",
        "port": 22,
        "transport": "TCP",
        "description": "Acceso remoto seguro con cifrado. También usado para SFTP, SCP.",
        "layer": "Aplicación (Capa 7)"
    },
    "Telnet": {
        "name": "Telnet",
        "port": 23,
        "transport": "TCP",
        "description": "Acceso remoto sin cifrar. Obsoleto, reemplazado por SSH.",
        "layer": "Aplicación (Capa 7)"
    },
    "SMTP": {
        "name": "Simple Mail Transfer Protocol",
        "port": 25,
        "transport": "TCP",
        "description": "Protocolo para envío de correo electrónico.",
        "layer": "Aplicación (Capa 7)"
    },
    "POP3": {
        "name": "Post Office Protocol v3",
        "port": 110,
        "transport": "TCP",
        "description": "Protocolo para descarga de correo electrónico desde servidor.",
        "layer": "Aplicación (Capa 7)"
    },
    "IMAP": {
        "name": "Internet Message Access Protocol",
        "port": 143,
        "transport": "TCP",
        "description": "Protocolo para acceso a correo electrónico en servidor remoto.",
        "layer": "Aplicación (Capa 7)"
    },
    "DNS": {
        "name": "Domain Name System",
        "port": 53,
        "transport": "UDP/TCP",
        "description": "Resolución de nombres de dominio a direcciones IP.",
        "layer": "Aplicación (Capa 7)"
    },
    "DHCP": {
        "name": "Dynamic Host Configuration Protocol",
        "port": 67-68,
        "transport": "UDP",
        "description": "Asignación automática de direcciones IP y configuración de red.",
        "layer": "Aplicación (Capa 7)"
    },
    "SNMP": {
        "name": "Simple Network Management Protocol",
        "port": 161-162,
        "transport": "UDP",
        "description": "Gestión y monitoreo de dispositivos de red.",
        "layer": "Aplicación (Capa 7)"
    },
    "NTP": {
        "name": "Network Time Protocol",
        "port": 123,
        "transport": "UDP",
        "description": "Sincronización de reloj en dispositivos de red.",
        "layer": "Aplicación (Capa 7)"
    },
    "TCP": {
        "name": "Transmission Control Protocol",
        "port": "N/A",
        "transport": "N/A",
        "description": "Protocolo orientado a conexión con confirmación de entrega. Confiable.",
        "layer": "Transporte (Capa 4)"
    },
    "UDP": {
        "name": "User Datagram Protocol",
        "port": "N/A",
        "transport": "N/A",
        "description": "Protocolo no orientado a conexión, sin confirmación. Rápido.",
        "layer": "Transporte (Capa 4)"
    },
    "IP": {
        "name": "Internet Protocol",
        "port": "N/A",
        "transport": "N/A",
        "description": "Protocolo de interconexión de redes. Enruta paquetes.",
        "layer": "Red (Capa 3)"
    },
    "ICMP": {
        "name": "Internet Control Message Protocol",
        "port": "N/A",
        "transport": "N/A",
        "description": "Protocolo de mensajes de control y error (ping, traceroute).",
        "layer": "Red (Capa 3)"
    },
    "ARP": {
        "name": "Address Resolution Protocol",
        "port": "N/A",
        "transport": "N/A",
        "description": "Resolución de direcciones IP a direcciones MAC.",
        "layer": "Enlace (Capa 2)"
    },
    "RARP": {
        "name": "Reverse Address Resolution Protocol",
        "port": "N/A",
        "transport": "N/A",
        "description": "Resolución de direcciones MAC a direcciones IP.",
        "layer": "Enlace (Capa 2)"
    },
    "Ethernet": {
        "name": "Ethernet",
        "port": "N/A",
        "transport": "N/A",
        "description": "Estándar de red de área local por cable (IEEE 802.3).",
        "layer": "Enlace (Capa 2) y Física (Capa 1)"
    },
    "WiFi": {
        "name": "Wireless Fidelity (IEEE 802.11)",
        "port": "N/A",
        "transport": "N/A",
        "description": "Estándar para redes inalámbricas de área local.",
        "layer": "Enlace (Capa 2) y Física (Capa 1)"
    },
    "OSPF": {
        "name": "Open Shortest Path First",
        "port": "N/A (IP 89)",
        "transport": "IP",
        "description": "Protocolo de enrutamiento dinámico de estado de enlace.",
        "layer": "Red (Capa 3)"
    },
    "BGP": {
        "name": "Border Gateway Protocol",
        "port": 179,
        "transport": "TCP",
        "description": "Protocolo de enrutamiento entre sistemas autónomos (Internet).",
        "layer": "Aplicación (Capa 7)"
    },
    "EIGRP": {
        "name": "Enhanced Interior Gateway Routing Protocol",
        "port": "N/A (IP 88)",
        "transport": "IP",
        "description": "Protocolo de enrutamiento propietario de Cisco.",
        "layer": "Red (Capa 3)"
    },
    "RIP": {
        "name": "Routing Information Protocol",
        "port": 520,
        "transport": "UDP",
        "description": "Protocolo de enrutamiento por vector de distancia.",
        "layer": "Aplicación (Capa 7)"
    },
    "PPP": {
        "name": "Point-to-Point Protocol",
        "port": "N/A",
        "transport": "N/A",
        "description": "Protocolo para comunicación directa entre dos nodos.",
        "layer": "Enlace (Capa 2)"
    },
    "PPPoE": {
        "name": "PPP over Ethernet",
        "port": "N/A",
        "transport": "N/A",
        "description": "PPP encapsulado sobre Ethernet (usado en ADSL/fibra).",
        "layer": "Enlace (Capa 2)"
    },
    "VLAN": {
        "name": "Virtual Local Area Network (IEEE 802.1Q)",
        "port": "N/A",
        "transport": "N/A",
        "description": "Segmentación lógica de redes en switches.",
        "layer": "Enlace (Capa 2)"
    },
    "STP": {
        "name": "Spanning Tree Protocol (IEEE 802.1D)",
        "port": "N/A",
        "transport": "N/A",
        "description": "Protocolo para evitar bucles en redes con switches.",
        "layer": "Enlace (Capa 2)"
    },
    "RSTP": {
        "name": "Rapid Spanning Tree Protocol (IEEE 802.1w)",
        "port": "N/A",
        "transport": "N/A",
        "description": "Versión mejorada de STP con convergencia más rápida.",
        "layer": "Enlace (Capa 2)"
    },
    "LACP": {
        "name": "Link Aggregation Control Protocol (IEEE 802.3ad)",
        "port": "N/A",
        "transport": "N/A",
        "description": "Agregación de enlaces para aumentar ancho de banda y redundancia.",
        "layer": "Enlace (Capa 2)"
    },
    "RADIUS": {
        "name": "Remote Authentication Dial-In User Service",
        "port": 1812-1813,
        "transport": "UDP",
        "description": "Autenticación, autorización y accounting para usuarios de red.",
        "layer": "Aplicación (Capa 7)"
    },
    "TACACS+": {
        "name": "Terminal Access Controller Access Control System Plus",
        "port": 49,
        "transport": "TCP",
        "description": "Protocolo de autenticación y autorización de Cisco.",
        "layer": "Aplicación (Capa 7)"
    },
    "LDAP": {
        "name": "Lightweight Directory Access Protocol",
        "port": 389,
        "transport": "TCP",
        "description": "Acceso a directorios de información (Active Directory).",
        "layer": "Aplicación (Capa 7)"
    },
    "SMB": {
        "name": "Server Message Block",
        "port": 445,
        "transport": "TCP",
        "description": "Protocolo para compartir archivos e impresoras en red.",
        "layer": "Aplicación (Capa 7)"
    },
    "RDP": {
        "name": "Remote Desktop Protocol",
        "port": 3389,
        "transport": "TCP",
        "description": "Escritorio remoto de Microsoft Windows.",
        "layer": "Aplicación (Capa 7)"
    },
    "NFS": {
        "name": "Network File System",
        "port": 2049,
        "transport": "TCP/UDP",
        "description": "Protocolo para compartir archivos en sistemas Unix/Linux.",
        "layer": "Aplicación (Capa 7)"
    },
    "MQTT": {
        "name": "Message Queuing Telemetry Transport",
        "port": 1883,
        "transport": "TCP",
        "description": "Protocolo ligero para IoT y mensajería máquina a máquina.",
        "layer": "Aplicación (Capa 7)"
    },
    "SIP": {
        "name": "Session Initiation Protocol",
        "port": 5060-5061,
        "transport": "TCP/UDP",
        "description": "Protocolo para señalización de comunicaciones VoIP.",
        "layer": "Aplicación (Capa 7)"
    },
    "H.323": {
        "name": "H.323",
        "port": 1720,
        "transport": "TCP",
        "description": "Protocolo de videoconferencia y VoIP.",
        "layer": "Aplicación (Capa 7)"
    },
    "IGMP": {
        "name": "Internet Group Management Protocol",
        "port": "N/A",
        "transport": "N/A",
        "description": "Protocolo para gestión de grupos multicast.",
        "layer": "Red (Capa 3)"
    },
    "VRRP": {
        "name": "Virtual Router Redundancy Protocol",
        "port": "N/A",
        "transport": "N/A",
        "description": "Protocolo para alta disponibilidad de puertas de enlace.",
        "layer": "Red (Capa 3)"
    },
    "HSRP": {
        "name": "Hot Standby Router Protocol",
        "port": "N/A (UDP 1985)",
        "transport": "UDP",
        "description": "Protocolo de redundancia de routers propietario de Cisco.",
        "layer": "Aplicación (Capa 7)"
    },
    "IS-IS": {
        "name": "Intermediate System to Intermediate System",
        "port": "N/A",
        "transport": "N/A",
        "description": "Protocolo de enrutamiento jerárquico de estado de enlace.",
        "layer": "Red (Capa 3)"
    },
    "LLDP": {
        "name": "Link Layer Discovery Protocol (IEEE 802.1AB)",
        "port": "N/A",
        "transport": "N/A",
        "description": "Protocolo de descubrimiento de vecinos en capa 2.",
        "layer": "Enlace (Capa 2)"
    },
    "CDP": {
        "name": "Cisco Discovery Protocol",
        "port": "N/A",
        "transport": "N/A",
        "description": "Protocolo de descubrimiento de vecinos propietario de Cisco.",
        "layer": "Enlace (Capa 2)"
    },
    "NetFlow": {
        "name": "NetFlow",
        "port": 2055,
        "transport": "UDP",
        "description": "Protocolo de monitoreo de tráfico de red de Cisco.",
        "layer": "Aplicación (Capa 7)"
    },
    "IPsec": {
        "name": "Internet Protocol Security",
        "port": "N/A (IP 50-51)",
        "transport": "IP",
        "description": "Conjunto de protocolos para comunicación segura a nivel IP.",
        "layer": "Red (Capa 3)"
    },
    "SSL/TLS": {
        "name": "Secure Sockets Layer / Transport Layer Security",
        "port": "Varios",
        "transport": "TCP",
        "description": "Protocolo de cifrado para comunicaciones seguras en internet.",
        "layer": "Aplicación (Capa 7)"
    },
    "SCP": {
        "name": "Secure Copy Protocol",
        "port": 22,
        "transport": "TCP",
        "description": "Copia segura de archivos sobre SSH.",
        "layer": "Aplicación (Capa 7)"
    },
    "LDAPS": {
        "name": "LDAP over SSL",
        "port": 636,
        "transport": "TCP",
        "description": "LDAP sobre SSL/TLS.",
        "layer": "Aplicación (Capa 7)"
    },
    "IMAPS": {
        "name": "IMAP over SSL",
        "port": 993,
        "transport": "TCP",
        "description": "IMAP sobre SSL/TLS.",
        "layer": "Aplicación (Capa 7)"
    },
    "POP3S": {
        "name": "POP3 over SSL",
        "port": 995,
        "transport": "TCP",
        "description": "POP3 sobre SSL/TLS.",
        "layer": "Aplicación (Capa 7)"
    },
    "SMTPS": {
        "name": "SMTP over SSL",
        "port": 465,
        "transport": "TCP",
        "description": "SMTP sobre SSL/TLS.",
        "layer": "Aplicación (Capa 7)"
    },
    "TFTP": {
        "name": "Trivial File Transfer Protocol",
        "port": 69,
        "transport": "UDP",
        "description": "Transferencia básica de archivos sin autenticación.",
        "layer": "Aplicación (Capa 7)"
    },
    "gRPC": {
        "name": "gRPC Remote Procedure Call",
        "port": 50051,
        "transport": "HTTP/2",
        "description": "Framework de RPC de alto rendimiento de Google.",
        "layer": "Aplicación (Capa 7)"
    },
    "WebSocket": {
        "name": "WebSocket",
        "port": 80-443,
        "transport": "TCP",
        "description": "Protocolo para comunicación bidireccional en tiempo real sobre HTTP.",
        "layer": "Aplicación (Capa 7)"
    },
    "IPMI": {
        "name": "Intelligent Platform Management Interface",
        "port": 623,
        "transport": "UDP",
        "description": "Interfaz para gestión remota de servidores (BMC).",
        "layer": "Aplicación (Capa 7)"
    },
    "Syslog": {
        "name": "System Logging Protocol",
        "port": 514,
        "transport": "UDP",
        "description": "Protocolo para envío de logs de sistemas y dispositivos.",
        "layer": "Aplicación (Capa 7)"
    },
    "NUT": {
        "name": "Network UPS Tools",
        "port": 3493,
        "transport": "TCP",
        "description": "Protocolo de monitoreo y gestión de UPS (SAI). Permite consultar estado, batería, carga y eventos de sistemas de alimentación ininterrumpida.",
        "layer": "Aplicación (Capa 7)"
    },
    "APC PowerChute": {
        "name": "APC PowerChute",
        "port": 3551,
        "transport": "TCP",
        "description": "Agente de monitoreo de UPS APC. Proporciona estado y control de los sistemas APC Smart-UPS y Back-UPS.",
        "layer": "Aplicación (Capa 7)"
    },
}


def get_protocol(name):
    name = name.upper()
    return PROTOCOLS.get(name, None)

def list_protocols():
    return list(PROTOCOLS.keys())

def search_protocols(query):
    query = query.lower()
    results = {}
    for name, info in PROTOCOLS.items():
        if query in name.lower() or query in info["description"].lower():
            results[name] = info
    return results
