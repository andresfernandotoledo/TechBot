import socket
import ipaddress
import struct
import os
import sys
import concurrent.futures
import subprocess


SERVICE_PORTS = {
    21: "FTP", 22: "SSH", 23: "Telnet", 25: "SMTP", 53: "DNS",
    80: "HTTP", 110: "POP3", 111: "RPC", 123: "NTP", 135: "MSRPC",
    139: "NetBIOS", 143: "IMAP", 161: "SNMP", 162: "SNMP Trap",
    389: "LDAP", 443: "HTTPS", 445: "SMB", 465: "SMTPS",
    500: "IPsec", 514: "Syslog", 554: "RTSP", 587: "SMTP Sub",
    631: "IPP", 636: "LDAPS", 993: "IMAPS", 995: "POP3S",
    1080: "SOCKS", 1194: "OpenVPN", 1433: "MSSQL", 1521: "Oracle",
    1701: "L2TP", 1723: "PPTP", 1812: "RADIUS", 2049: "NFS",
    2082: "cPanel", 2083: "cPanel SSL", 2181: "ZooKeeper",
    2375: "Docker", 2376: "Docker TLS", 3128: "Squid", 3306: "MySQL",
    3389: "RDP", 3690: "SVN", 4369: "Erlang", 4444: "Metasploit",
    5000: "Flask", 5001: "Synology", 5060: "SIP", 5432: "PostgreSQL",
    5555: "ADB", 5601: "Kibana", 5666: "Nagios", 5672: "RabbitMQ",
    5800: "VNC HTTP", 5900: "VNC", 5984: "CouchDB", 5985: "WinRM",
    5986: "WinRMS", 6379: "Redis", 6443: "K8s API", 8080: "HTTP Proxy",
    8086: "InfluxDB", 8443: "HTTPS Alt", 9000: "SonarQube",
    9090: "Prometheus", 9092: "Kafka", 9100: "NodeExp",
    9200: "Elasticsearch", 9300: "ES Transport", 9418: "Git",
    10050: "Zabbix", 11211: "Memcached", 27017: "MongoDB",
    32400: "Plex", 50070: "Hadoop NN", 50075: "Hadoop DN",
    3493: "NUT (UPS)", 3551: "APC PowerChute",
     # ─── CCTV ──────────────────────────────────────────────────
     3478: "STUN (VoIP/CCTV)", 3480: "Bosch CCTV",
    34567: "Hikvision SDK", 34568: "Hikvision ISAPI", 34569: "Hikvision Stream",
    34570: "Hikvision Alarm", 34571: "Hikvision Event", 34572: "Hikvision PTZ",
    35555: "Dahua Debug", 35556: "Dahua P2P", 35557: "Dahua Alarm",
    36666: "Dahua ONVIF Alt", 37200: "Dahua NVR", 37443: "Dahua HTTPS",
    37775: "Dahua DB", 37776: "Dahua Config", 37777: "Dahua SDK",
    37778: "Dahua Stream", 37779: "Dahua Event",
    38000: "Dahua Cloud", 38001: "Dahua Cloud Alt", 38002: "Dahua P2P Alt",
    39000: "Hikvision Cloud", 39001: "Hikvision Cloud Alt", 39999: "Hikvision P2P",
    50000: "Hikvision ISAPI Alt", 50001: "Hikvision Stream Alt",
    50002: "Hikvision Alarm Alt", 51000: "Hikvision P2P Alt",
    52000: "Hikvision Event Alt", 52001: "Hikvision PTZ Alt",
    53000: "Hikvision Config Alt", 54000: "Hikvision Debug Alt",
     7000: "AXIS SDK", 8000: "Hikvision HTTP",
     8083: "AXIS Param", 8084: "AXIS VAPIX", 8085: "AXIS CGI",
     8087: "AXIS JPEG", 8088: "AXIS MJPG",
    8091: "Panasonic CCTV", 8092: "Panasonic NVR", 8093: "Panasonic Stream",
    8094: "Samsung CCTV", 8095: "Hanwha NVR", 8096: "Hanwha Stream",
    8097: "Hanwha PTZ", 8098: "Arecont CCTV", 8099: "Arecont Stream",
    8100: "Geovision CCTV", 8101: "Geovision NVR", 8102: "Geovision Stream",
    8103: "Mobotix CCTV", 8104: "Mobotix Stream", 8105: "Mobotix Config",
    8106: "ACTi CCTV", 8107: "ACTi Stream", 8108: "ACTi Config", 8109: "ACTi NVR",
    8200: "Hikvision Streaming",
    8554: "RTSP Alt", 8555: "RTSP Alt2", 8556: "Samsung RTSP",
    8557: "Hanwha RTSP", 8558: "Dahua RTSP", 8559: "Hikvision RTSP",
    8560: "AXIS RTSP", 8561: "Panasonic RTSP", 8562: "Bosch RTSP",
    8563: "VIVOTEK RTSP", 8564: "Geovision RTSP", 8565: "Arecont RTSP",
    8566: "ACTi RTSP", 8567: "Mobotix RTSP", 8568: "Sanyo RTSP",
    8569: "Pelco RTSP", 8570: "Sony RTSP",
    8600: "ONVIF Media", 8601: "ONVIF Event", 8602: "ONVIF Device",
    8603: "ONVIF PTZ", 8604: "ONVIF Analytics", 8605: "ONVIF Recording",
    8606: "ONVIF Display", 8607: "ONVIF Receiver", 8608: "ONVIF Imaging",
    8609: "ONVIF Metadata", 8610: "ONVIF Storage", 8611: "ONVIF Security",
    8622: "Pelco CCTV", 8623: "Pelco NVR", 8624: "Pelco Stream", 8625: "Pelco PTZ",
    8626: "Sanyo CCTV", 8627: "Sanyo NVR", 8628: "Sanyo Stream",
    8629: "Sony CCTV", 8630: "Sony NVR", 8631: "Sony Stream",
    8632: "Bosch CCTV Alt", 8633: "Bosch NVR", 8634: "Bosch Stream",
    8635: "Bosch Config", 8636: "Bosch Alarm", 8637: "Bosch Event",
    8638: "Bosch Recording", 8639: "Bosch Video SDK",
    8640: "IndigoVision CCTV", 8641: "IndigoVision Stream",
    8642: "IndigoVision Config", 8643: "IndigoVision NVR",
    8644: "March Networks CCTV", 8645: "March Networks NVR",
    8646: "March Networks Stream",
    8647: "Honeywell CCTV", 8648: "Honeywell NVR", 8649: "Honeywell Stream",
    8650: "Honeywell Config", 8651: "Honeywell Alarm", 8652: "Honeywell Event",
    8653: "Honeywell Video SDK", 8654: "Honeywell RTSP", 8655: "Honeywell HTTPS",
    8656: "Dahua VTO", 8657: "Dahua VTO Config", 8658: "Dahua VTO Stream",
    8659: "Dahua VTO RTSP", 8660: "Dahua VTO ONVIF",
    8661: "Hikvision Doorbell", 8662: "Hikvision Doorbell Stream",
    8663: "Hikvision Doorbell Config", 8664: "Hikvision Doorbell RTSP",
    8665: "Hikvision Intercom", 8666: "Dahua Intercom",
    8667: "Dahua Intercom Config", 8668: "Hikvision Intercom Stream",
    8669: "Hikvision Intercom Config",
    8670: "Commax Doorbell", 8671: "Commax Intercom",
    8672: "Kocom Doorbell", 8673: "Kocom Intercom",
    8674: "BTICINO Doorbell", 8675: "BTICINO Intercom",
    8676: "Urmet Doorbell", 8677: "Urmet Intercom",
    8678: "Fermax Doorbell", 8679: "Fermax Intercom",
    8680: "Golmar Doorbell", 8681: "Golmar Intercom",
    8684: "Siedle Doorbell", 8685: "Siedle Intercom",
    8686: "Elvox Doorbell", 8687: "Elvox Intercom",
    8688: "TCS Doorbell", 8689: "TCS Intercom",
    8692: "DoorBird Doorbell", 8693: "DoorBird Stream",
    8694: "DoorBird RTSP", 8695: "DoorBird ONVIF", 8696: "DoorBird Config",
    8697: "Ring Doorbell", 8698: "Ring Doorbell Stream", 8699: "Ring Doorbell Config",
    8700: "Nest Doorbell", 8701: "Nest Doorbell Stream", 8702: "Nest Doorbell Config",
    8888: "Dahua HTTP", 8899: "ONVIF",
    9393: "VIVOTEK", 9500: "Cisco CCTV", 9505: "Verint CCTV",
    9999: "Uruu CCTV",
    # ─── Access Control ────────────────────────────────────────
    4370: "ZKTeco SDK", 4371: "ZKTeco Push", 4372: "ZKTeco Event",
    4373: "ZKTeco Config", 4374: "ZKTeco DB", 4375: "ZKTeco TCP",
    4376: "ZKTeco SSL", 4377: "ZKTeco UDP", 4378: "ZKTeco HTTP",
    4379: "ZKTeco HTTPS", 4380: "ZKTeco LiveCapture", 4381: "ZKTeco Fingerprint",
    4382: "ZKTeco Face", 4383: "ZKTeco Palm", 4384: "ZKTeco Card",
    4385: "ZKTeco PIN", 4386: "ZKTeco User", 4387: "ZKTeco Attendance",
    4388: "ZKTeco Timezone", 4389: "ZKTeco Holiday", 4390: "ZKTeco Door",
    4391: "ZKTeco Relay", 4392: "ZKTeco Sensor", 4393: "ZKTeco Alarm",
    4394: "ZKTeco Log", 4395: "ZKTeco Photo", 4396: "ZKTeco Record",
    4397: "ZKTeco Transaction", 4398: "ZKTeco Command", 4399: "ZKTeco Debug",
    3456: "Kantech ioEdge", 3457: "Kantech ioEdge Alt",
    3458: "Kantech Config", 3459: "Kantech Event", 3460: "Kantech Alarm",
    3461: "Kantech Door", 3462: "Kantech Relay", 3463: "Kantech Input",
    3464: "Kantech Output", 3465: "Kantech API", 3466: "Kantech SDK",
    3467: "Kantech Web", 3468: "Kantech DB",
    5099: "Lenel / Paxton", 5100: "Lenel / Paxton Alt",
    5101: "Lenel LNS", 5102: "Lenel Event", 5103: "Lenel Config",
    5104: "Lenel DB", 5105: "Lenel Alarm", 5106: "Lenel Badge",
    5107: "Lenel Photo ID", 5108: "Lenel Elevator", 5109: "Lenel CCTV Integration",
    5110: "Lenel API", 5111: "Lenel Web", 5112: "Lenel HTTPS",
    5113: "Lenel Comm Server", 5114: "Lenel Host", 5115: "Lenel Remote",
    5116: "Lenel SDK",
    7000: "HID VertX", 7001: "HID VertX Alt", 7002: "HID VertX Config",
    7003: "HID VertX Event", 7004: "HID Edge", 7005: "HID Edge Alt",
    7006: "HID Edge Config", 7007: "HID Edge Event", 7008: "HID Edge HTTPS",
    7009: "HID Reader", 7010: "HID Reader Config", 7011: "HID iCLASS",
    7012: "HID iCLASS Config", 7013: "HID Signo", 7014: "HID Signo Config",
    7015: "HID OMNIKEY", 7016: "HID OMNIKEY Config", 7017: "HID API",
    7018: "HID Web", 7019: "HID Cloud",
     8091: "2N RFID", 8092: "2N PIN", 8093: "2N Fingerprint",
     8094: "2N Face", 8095: "2N Card", 8096: "2N Keypad", 8097: "2N Intercom",

    5121: "Paxton 10G", 5122: "Paxton 10G Config",
    4445: "SALTO Config", 4446: "SALTO Event",
    4447: "SALTO Door", 4448: "SALTO Relay", 4449: "SALTO Input",
    4450: "SALTO Output", 4451: "SALTO Alarm", 4452: "SALTO Badge",
    4453: "SALTO Card", 4454: "SALTO Token", 4455: "SALTO Audit",
    4456: "SALTO API", 4457: "SALTO SDK", 4458: "SALTO Web",
    4459: "SALTO HTTP", 4460: "SALTO HTTPS", 4461: "SALTO DB",
    10629: "CDVI AT200", 10630: "CDVI Config", 10631: "CDVI Event",
    10632: "CDVI Door", 10633: "CDVI Relay", 10634: "CDVI Input",
    10635: "CDVI Output", 10636: "CDVI Alarm", 10637: "CDVI Badge",
    10638: "CDVI Card", 10639: "CDVI Token",
    6000: "Nedap AEOS", 6001: "Nedap AEOS Alt", 6002: "Nedap Config",
    6003: "Nedap Event", 6004: "Nedap Door", 6005: "Nedap Relay",
    6006: "Nedap Input", 6007: "Nedap Output", 6008: "Nedap Alarm",
    6009: "Nedap Badge", 6010: "Nedap Card", 6011: "Nedap Token",
    6012: "Nedap API", 6013: "Nedap SDK", 6014: "Nedap Web",
    6015: "Nedap HTTP", 6016: "Nedap HTTPS", 6017: "Nedap TCP",
    6018: "Nedap UDP", 6019: "Nedap SSL",
    6080: "Nedap CrossEntry", 6081: "Nedap CrossEntry Config",
    6082: "Nedap CrossEntry Event", 6083: "Nedap CrossEntry Door",
    6084: "Nedap CrossEntry Relay", 6085: "Nedap CrossEntry Input",
    6086: "Nedap CrossEntry Output", 6087: "Nedap CrossEntry Alarm",
    6088: "Nedap CrossEntry Badge", 6089: "Nedap CrossEntry Card",
    6090: "Nedap CrossEntry Token",
    6200: "Assa Abloy Aperio", 6201: "Assa Abloy Aperio Config",
    6202: "Assa Abloy Aperio Event", 6203: "Assa Abloy Aperio Door",
    6204: "Assa Abloy Aperio Relay", 6205: "Assa Abloy Aperio Input",
    6206: "Assa Abloy Aperio Output", 6207: "Assa Abloy Aperio Alarm",
    6208: "Assa Abloy Aperio Badge", 6209: "Assa Abloy Aperio Card",
    6210: "Assa Abloy Aperio Token", 6211: "Assa Abloy Aperio API",
    6212: "Assa Abloy Aperio SDK", 6213: "Assa Abloy Aperio Web",
    6214: "Assa Abloy Aperio HTTP", 6215: "Assa Abloy Aperio HTTPS",
    6216: "Assa Abloy Aperio DB",
    6300: "Dormakaba", 6301: "Dormakaba Config", 6302: "Dormakaba Event",
    6303: "Dormakaba Door", 6304: "Dormakaba Relay", 6305: "Dormakaba Input",
    6306: "Dormakaba Output", 6307: "Dormakaba Alarm", 6308: "Dormakaba Badge",
    6309: "Dormakaba Card", 6310: "Dormakaba Token", 6311: "Dormakaba API",
    6312: "Dormakaba SDK", 6313: "Dormakaba Web", 6314: "Dormakaba HTTP",
    6315: "Dormakaba HTTPS", 6316: "Dormakaba DB",
    6400: "Schneider ACL", 6401: "Schneider Config", 6402: "Schneider Event",
    6403: "Schneider Door", 6404: "Schneider Relay", 6405: "Schneider Input",
    6406: "Schneider Output", 6407: "Schneider Alarm", 6408: "Schneider Badge",
    6409: "Schneider Card", 6410: "Schneider Token", 6411: "Schneider API",
    6412: "Schneider SDK", 6413: "Schneider Web", 6414: "Schneider HTTP",
    6415: "Schneider HTTPS", 6416: "Schneider DB",
    6500: "Johnson Controls", 6501: "Johnson Config", 6502: "Johnson Event",
    6503: "Johnson Door", 6504: "Johnson Relay", 6505: "Johnson Input",
    6506: "Johnson Output", 6507: "Johnson Alarm", 6508: "Johnson Badge",
    6509: "Johnson Card", 6510: "Johnson Token", 6511: "Johnson API",
    6512: "Johnson SDK", 6513: "Johnson Web", 6514: "Johnson HTTP",
    6515: "Johnson HTTPS", 6516: "Johnson DB",
    6600: "Stanley ACL", 6601: "Stanley Config", 6602: "Stanley Event",
    6603: "Stanley Door", 6604: "Stanley Relay", 6605: "Stanley Input",
    6606: "Stanley Output", 6607: "Stanley Alarm", 6608: "Stanley Badge",
    6609: "Stanley Card", 6610: "Stanley Token", 6611: "Stanley API",
    6612: "Stanley SDK", 6613: "Stanley Web", 6614: "Stanley HTTP",
    6615: "Stanley HTTPS", 6616: "Stanley DB",
    6700: "Gallagher ACL", 6701: "Gallagher Config", 6702: "Gallagher Event",
    6703: "Gallagher Door", 6704: "Gallagher Relay", 6705: "Gallagher Input",
    6706: "Gallagher Output", 6707: "Gallagher Alarm", 6708: "Gallagher Badge",
    6709: "Gallagher Card", 6710: "Gallagher Token", 6711: "Gallagher API",
    6712: "Gallagher SDK", 6713: "Gallagher Web", 6714: "Gallagher HTTP",
    6715: "Gallagher HTTPS", 6716: "Gallagher DB",
    6800: "Avigilon ACM", 6801: "Avigilon ACM Config", 6802: "Avigilon ACM Event",
    6803: "Avigilon ACM Door", 6804: "Avigilon ACM Relay", 6805: "Avigilon ACM Input",
    6806: "Avigilon ACM Output", 6807: "Avigilon ACM Alarm", 6808: "Avigilon ACM Badge",
    6809: "Avigilon ACM Card", 6810: "Avigilon ACM Token", 6811: "Avigilon ACM API",
    6812: "Avigilon ACM SDK", 6813: "Avigilon ACM Web", 6814: "Avigilon ACM HTTP",
    6815: "Avigilon ACM HTTPS", 6816: "Avigilon ACM DB",
    6900: "Bosch ACL", 6901: "Bosch ACL Config", 6902: "Bosch ACL Event",
    6903: "Bosch ACL Door", 6904: "Bosch ACL Relay", 6905: "Bosch ACL Input",
    6906: "Bosch ACL Output", 6907: "Bosch ACL Alarm", 6908: "Bosch ACL Badge",
    6909: "Bosch ACL Card", 6910: "Bosch ACL Token", 6911: "Bosch ACL API",
    6912: "Bosch ACL SDK", 6913: "Bosch ACL Web", 6914: "Bosch ACL HTTP",
    6915: "Bosch ACL HTTPS", 6916: "Bosch ACL DB",
    68000: "Siemens SiPass", 68001: "Siemens SiPass Config",
    68002: "Siemens SiPass Event", 68003: "Siemens SiPass Door",
    68004: "Siemens SiPass Relay", 68005: "Siemens SiPass Input",
    68006: "Siemens SiPass Output", 68007: "Siemens SiPass Alarm",
    68008: "Siemens SiPass Badge", 68009: "Siemens SiPass Card",
    68010: "Siemens SiPass Token", 68011: "Siemens SiPass API",
    68012: "Siemens SiPass SDK", 68013: "Siemens SiPass Web",
    68014: "Siemens SiPass HTTP", 68015: "Siemens SiPass HTTPS",
    68016: "Siemens SiPass DB",
}

# Identificación de dispositivos CCTV y AC por banner HTTP
CCTV_AC_SIGNATURES = {
    "Hikvision": ["hikvision", "isapi", "ivms", "hik", "ds-2cd", "ds-76", "ds-77", "ds-96", "idvr", "nvr"],
    "Dahua": ["dahua", "dvr", "nvr", "xvr", "cgi-bin", "sd222", "sd492", "ipc-hf", "dhi-"],
    "ZKTeco": ["zkteco", "iclock", "zk", "attendance", "biometric", "uface", "mb460", "inbio"],
    "AXIS": ["axis", "axis communications", "axis-", "axis camera"],
    "Bosch": ["bosch", "bosch security", "divar", "diagbox"],
    "Vivotek": ["vivotek", "vvtk", "network camera"],
    "ONVIF": ["onvif", "www.onvif.org"],
    "Honeywell": ["honeywell", "hrdv", "hrm", "honeywell video"],
    "Panasonic": ["panasonic", "i-pro", "wv-"],
    "Samsung": ["samsung", "wiseview", "samsung techwin", "hanwha"],
    "ACTi": ["acti", "acti camera"],
    "Geovision": ["geovision", "gv-"],
    "Mobotix": ["mobotix", "mx-"],
    "Arecont": ["arecont", "arecont vision"],
    "Lenel": ["lenel", "onguard", "lencode"],
    "paxton": ["paxton", "paxton net2", "10g"],
    "Kantech": ["kantech", "kantech ioe", "kantech ac"],
    "2N": ["2n", "2n helios", "2n telecom", "2n access"],
    "CDVI": ["cdvi", "cdvi at200", "cdvi ac"],
    "HID": ["hid", "hid global", "vertx", "hid reader"],
    "Assa Abloy": ["assa", "abloy", "assa abloy", "aperio"],
    "SALTO": ["salto", "salto systems", "sallto"],
    "Nedap": ["nedap", "nedap aeos", "nedap ac"],
}


def _check_cctv_banner(banner, port):
    """Identifica si un banner corresponde a CCTV o AC."""
    banner_lower = banner.lower()
    for vendor, keywords in CCTV_AC_SIGNATURES.items():
        for kw in keywords:
            if kw in banner_lower:
                return vendor
    # Detección por puerto
    cctv_ports = {554: "RTSP CCTV", 8000: "Hikvision SDK", 37777: "Dahua SDK",
                  8899: "ONVIF", 4370: "ZKTeco SDK", 8200: "CCTV Stream"}
    if port in cctv_ports:
        return cctv_ports[port]
    return None


def identify_device(host, timeout=3):
    """Intenta identificar el tipo de dispositivo CCTV/AC."""
    results = {}
    test_ports = [80, 443, 554, 8080, 8899, 8000, 37777, 4370]
    for port in test_ports:
        try:
            banner = grab_banner(host, port, timeout)
            if banner:
                vendor = _check_cctv_banner(banner, port)
                if vendor:
                    results[port] = vendor
                    continue
                if port == 554 and "RTSP" in banner:
                    results[port] = "RTSP Server"
                elif "HTTP" in banner or "HTTP" in str(banner):
                    results[port] = "HTTP Server"
        except (socket.timeout, socket.gaierror, OSError):
            pass
    return results


def scan_cctv(host, timeout=2):
    """Escanea específicamente puertos de CCTV y AC."""
    cctv_ports = [80, 443, 554, 8000, 8090, 8200, 8888, 8899, 37777, 3480, 7000,
                  8443, 8080, 9393, 9505, 34567, 35555, 7547, 4370, 5099, 5100, 8081, 8082]
    results = scan_ports(host, cctv_ports, timeout)
    enriched = []
    for r in results:
        port = r["port"]
        banner = grab_banner(host, port, timeout)
        vendor = _check_cctv_banner(banner, port) if banner else None
        enriched.append({
            **r,
            "device_type": vendor or "CCTV/AC",
            "banner_preview": banner[:80] if banner else ""
        })
    return enriched


def scan_access_control(host, timeout=2):
    """Escanea específicamente puertos de control de acceso."""
    ac_ports = [80, 443, 8080, 8081, 8082, 4370, 5099, 5100, 8443, 3000, 8899]
    results = scan_ports(host, ac_ports, timeout)
    enriched = []
    for r in results:
        port = r["port"]
        banner = grab_banner(host, port, timeout)
        is_ac = False
        ac_vendor = None
        if banner:
            ac_vendor = _check_cctv_banner(banner, port)
            is_ac = ac_vendor is not None or port in (4370, 5099, 5100)
        if port == 4370:
            ac_vendor = "ZKTeco SDK"
            is_ac = True
        enriched.append({
            **r,
            "device_type": ac_vendor or "AC Device",
            "is_access_control": is_ac,
            "banner_preview": banner[:80] if banner else ""
        })
    return enriched


def discover_cctv(subnet, timeout=2):
    """Descubre dispositivos CCTV/AC en una subred."""
    hosts = discover_hosts(subnet, timeout)
    devices = []
    for host in hosts:
        cctv_results = scan_cctv(host, timeout)
        if cctv_results:
            identity = identify_device(host, timeout)
            device_types = set()
            for r in cctv_results:
                if r.get("device_type") and r["device_type"] not in ("CCTV/AC",):
                    device_types.add(r["device_type"])
            devices.append({
                "ip": host,
                "open_ports": [r["port"] for r in cctv_results],
                "device_type": list(device_types) if device_types else ["Posible CCTV/AC"],
                "services": [{"port": r["port"], "service": r["service"], "banner": r.get("banner_preview", "")} for r in cctv_results],
            })
    return devices

ONVIF_PORTS = [80, 8080, 8899]
CCTV_PORTS = [80, 443, 554, 8000, 8090, 8200, 8888, 8899, 37777, 3480, 7000,
              8443, 8080, 9393, 9505, 34567, 35555, 7547]
AC_PORTS = [80, 443, 8080, 8081, 8082, 4370, 5099, 5100, 8443, 3000]


def scan_port(host, port, timeout=1.5):
    """Escanea un puerto individual."""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        result = sock.connect_ex((host, port))
        sock.close()
        if result == 0:
            banner = grab_banner(host, port, timeout)
            service = SERVICE_PORTS.get(port, "Desconocido")
            return port, "open", service, banner
        return port, "closed", "", ""
    except:
        return port, "error", "", ""


def scan_ports(host, ports=None, timeout=1.5, max_threads=100):
    """Escanea múltiples puertos en paralelo."""
    if ports is None:
        ports = list(SERVICE_PORTS.keys())
    results = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_threads) as executor:
        futures = {executor.submit(scan_port, host, p, timeout): p for p in ports}
        for future in concurrent.futures.as_completed(futures):
            port, state, service, banner = future.result()
            if state == "open":
                results.append({"port": port, "state": state, "service": service})
    results.sort(key=lambda x: x["port"])
    return results


def grab_banner(host, port, timeout=2):
    """Intenta obtener banner del servicio."""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        sock.connect((host, port))
        banner = sock.recv(1024)
        sock.close()
        return banner.decode("utf-8", errors="replace").strip()
    except:
        return ""


def ping_host(host, timeout=2):
    """Ping a un host."""
    try:
        param = "-n" if os.name == "nt" else "-c"
        cmd = ["ping", param, "1", "-W", str(timeout), str(host)]
        result = subprocess.run(cmd, capture_output=True, timeout=timeout+1)
        return result.returncode == 0
    except:
        return False


def discover_hosts(subnet, timeout=2, max_threads=50):
    """Descubre hosts activos en una subred mediante ping."""
    network = ipaddress.ip_network(subnet, strict=False)
    hosts = []
    ip_list = [str(ip) for ip in network.hosts()]

    with concurrent.futures.ThreadPoolExecutor(max_workers=max_threads) as executor:
        futures = {executor.submit(ping_host, ip, timeout): ip for ip in ip_list}
        for future in concurrent.futures.as_completed(futures):
            ip = futures[future]
            if future.result():
                hosts.append(ip)
    return sorted(hosts, key=lambda ip: [int(o) for o in ip.split(".")])


def quick_scan(host, timeout=1.5):
    """Escaneo rápido de puertos más comunes (incluye CCTV y AC)."""
    common = [21, 22, 23, 25, 53, 80, 110, 111, 135, 139, 143, 161,
              389, 443, 445, 465, 554, 587, 636, 993, 995, 1433, 1521,
              1723, 2049, 3306, 3389, 5432, 5900, 5985, 5986, 6379,
              8080, 8443, 9090, 9200, 27017,
              8000, 8200, 8899, 37777, 4370, 5099, 5100, 3480, 7000,
              8081, 8082, 34567, 35555, 8090, 8888]
    return scan_ports(host, common, timeout)


def os_detection(host, timeout=2):
    """Detección básica de SO por TTL y análisis de puertos."""
    try:
        param = "-n" if os.name == "nt" else "-c"
        cmd = ["ping", param, "1", str(host)]
        result = subprocess.run(cmd, capture_output=True, timeout=timeout+1)
        output = result.stdout.decode()

        ttl_match = None
        for line in output.split("\n"):
            if "ttl=" in line.lower():
                ttl_match = line
                break

        if ttl_match:
            import re
            ttls = re.findall(r'ttl[=:]\s*(\d+)', ttl_match, re.IGNORECASE)
            if ttls:
                ttl = int(ttls[0])
                if ttl <= 64:
                    return "Linux/Unix (TTL=%d)" % ttl
                elif ttl <= 128:
                    return "Windows (TTL=%d)" % ttl
                elif ttl <= 255:
                    return "Cisco/Network (TTL=%d)" % ttl
        return "Desconocido"
    except:
        return "Error"


def traceroute(host, max_hops=30, timeout=2):
    """Traceroute simple."""
    results = []
    for ttl in range(1, max_hops + 1):
        try:
            param = "-n" if os.name == "nt" else "-c"
            ttl_flag = "-i" if os.name == "nt" else "-t"
            cmd = ["ping", param, "1", ttl_flag, str(ttl), "-W", "1", str(host)]
            result = subprocess.run(cmd, capture_output=True, timeout=timeout)
            output = result.stdout.decode()

            hop_ip = "***"
            for line in output.split("\n"):
                if "from" in line.lower():
                    import re
                    ips = re.findall(r'\d+\.\d+\.\d+\.\d+', line)
                    if ips:
                        hop_ip = ips[0]
                        break
            results.append({"hop": ttl, "ip": hop_ip})
        except:
            results.append({"hop": ttl, "ip": "***"})
    return results


def dns_scan(domain, record_type="A"):
    """Consulta DNS."""
    try:
        import socket as s
        if record_type.upper() == "A":
            return {"query": domain, "type": "A", "result": s.gethostbyname(domain)}
        elif record_type.upper() == "MX":
            # Simple MX via socket - won't work in most cases
            return {"query": domain, "type": "MX", "result": "Usar dig/nslookup"}
        return {"query": domain, "type": record_type, "result": "No disponible"}
    except Exception as e:
        return {"error": str(e)}


def service_detection(host, port, timeout=3):
    """Detección avanzada de servicio según respuestas."""
    probes = {
        21: b"", 22: b"", 23: b"", 25: b"",
        80: b"GET / HTTP/1.0\r\n\r\n",
        443: b"", 3306: b"", 5432: b"",
        6379: b"PING\r\n", 8080: b"GET / HTTP/1.0\r\n\r\n",
    }
    probe = probes.get(port, b"")
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        sock.connect((host, port))
        if probe:
            sock.send(probe)
        response = sock.recv(2048)
        sock.close()
        return response.decode("utf-8", errors="replace").strip()
    except:
        return ""


def scan_top_ports(host, count=100):
    """Escanea los N puertos más comunes."""
    top = sorted(SERVICE_PORTS.keys())[:count]
    return scan_ports(host, top)


def export_scan_results(results, filename="scan_result.txt"):
    """Exporta resultados a archivo."""
    with open(filename, "w") as f:
        f.write("Puerto\tEstado\tServicio\n")
        f.write("-" * 40 + "\n")
        for r in results:
            f.write(f"{r['port']}\t{r['state']}\t{r['service']}\n")
    return filename


def compare_port_scans(scan1, scan2):
    """Compara dos escaneos y muestra diferencias."""
    ports1 = {r["port"]: r for r in scan1}
    ports2 = {r["port"]: r for r in scan2}
    new = [p for p in ports2 if p not in ports1]
    removed = [p for p in ports1 if p not in ports2]
    return {
        "new_ports": [ports2[p] for p in new],
        "removed_ports": [ports1[p] for p in removed],
        "total_before": len(scan1),
        "total_after": len(scan2),
    }
