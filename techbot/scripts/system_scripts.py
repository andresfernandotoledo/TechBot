import os
import sys
import shutil
import subprocess
import platform


def disk_usage(path="/"):

    # Calcula el uso del disco en una ruta. Usa shutil.disk_usage() que devuelve total, usado y libre en bytes. Convierte a GB para legibilidad.
    total, used, free = shutil.disk_usage(path)
    return {
        "total": f"{total // (2**30)} GB",
        "used": f"{used // (2**30)} GB",
        "free": f"{free // (2**30)} GB",
        "percent_used": round(used / total * 100, 1)
    }

def list_running_processes():

    # Lista procesos en ejecución. En Linux ordena por uso de memoria con 'ps aux --sort=-%mem'. En Windows usa 'tasklist'.
    if sys.platform == "linux":
        return subprocess.getoutput("ps aux --sort=-%mem | head -30")
    elif sys.platform == "win32":
        return subprocess.getoutput("tasklist")
    return "No soportado"

def system_info():

    # Información del sistema: sistema operativo, hostname, versión, kernel, arquitectura y procesador. Usa platform module.
    return {
        "system": platform.system(),
        "node": platform.node(),
        "release": platform.release(),
        "version": platform.version(),
        "machine": platform.machine(),
        "processor": platform.processor()
    }

def cpu_info():

    # Información detallada de la CPU. En Linux ejecuta lscpu y filtra modelo, núcleos, hilos. Solo Linux.
    if sys.platform == "linux":
        return subprocess.getoutput("lscpu | grep -E 'Model name|CPU(s)|Thread|Core'")
    return "No soportado"

def memory_info():

    # Muestra uso de memoria RAM. En Linux 'free -h', en Windows 'systeminfo | findstr Memory'. Muestra total, usada, disponible.
    if sys.platform == "linux":
        return subprocess.getoutput("free -h")
    elif sys.platform == "win32":
        return subprocess.getoutput("systeminfo | findstr Memory")
    return "No soportado"

def uptime():

    # Muestra tiempo de actividad del sistema. En Linux 'uptime' que da carga y tiempo encendido.
    if sys.platform == "linux":
        return subprocess.getoutput("uptime")
    return "No soportado"

def list_open_ports():

    # Lista puertos en escucha. En Linux 'ss -tuln', en Windows 'netstat -an'. Muestra protocolo, IP local y puerto.
    if sys.platform == "linux":
        return subprocess.getoutput("ss -tuln")
    elif sys.platform == "win32":
        return subprocess.getoutput("netstat -an")
    return "No soportado"

def list_usb_devices():

    # Lista dispositivos USB conectados. En Linux 'lsusb'. Muestra fabricante, producto y ID USB.
    if sys.platform == "linux":
        return subprocess.getoutput("lsusb")
    return "No soportado"

def list_pci_devices():

    # Lista dispositivos PCI. En Linux 'lspci'. Muestra tarjetas de red, GPU, controladores SATA, etc.
    if sys.platform == "linux":
        return subprocess.getoutput("lspci")
    return "No soportado"

def list_network_interfaces():

    # Lista interfaces de red. En Linux 'ip link show', en Windows 'ipconfig'. Muestra nombre, MAC, estado.
    if sys.platform == "linux":
        return subprocess.getoutput("ip link show")
    elif sys.platform == "win32":
        return subprocess.getoutput("ipconfig")
    return "No soportado"

def kernel_version():

    # Muestra versión del kernel. En Linux 'uname -a'. En otras plataformas usa platform.uname().version.
    if sys.platform == "linux":
        return subprocess.getoutput("uname -a")
    return platform.uname().version

def environment_variables():

    # Obtiene todas las variables de entorno del sistema usando os.environ. Devuelve un dict con nombre=valor.
    return dict(os.environ)

def large_files(path="/", size="+100M"):

    # Busca archivos grandes en una ruta. En Linux usa 'find' con tamaño mínimo. Por defecto busca >100MB. Muestra los primeros 50.
    if sys.platform == "linux":
        return subprocess.getoutput(f"find {path} -type f -size {size} 2>/dev/null | head -50")
    return "No soportado"

def check_service_status(service):

    # Verifica el estado de un servicio. En Linux 'systemctl status', en Windows 'sc query'. Muestra si está activo, habilitado, etc.
    if sys.platform == "linux":
        return subprocess.getoutput(f"systemctl status {service} 2>&1 | head -20")
    elif sys.platform == "win32":
        return subprocess.getoutput(f"sc query {service}")
    return "No soportado"

def installed_packages():

    # Lista paquetes instalados. En Debian/Ubuntu 'dpkg --get-selections', en RHEL 'rpm -qa'. Muestra los primeros 50.
    if sys.platform == "linux":
        return subprocess.getoutput("dpkg --get-selections 2>/dev/null | head -50 || rpm -qa 2>/dev/null | head -50")
    return "No soportado"

def file_hash(filepath, algo="sha256"):

    # Calcula hash de un archivo. Usa hashlib con el algoritmo especificado (sha256 por defecto). Lee en chunks de 4KB para archivos grandes.
    import hashlib
    h = hashlib.new(algo)
    with open(filepath, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            h.update(chunk)
    return h.hexdigest()

def directory_size(path):

    # Calcula el tamaño total de un directorio recursivamente. Usa os.walk() para recorrer todos los subdirectorios y sumar tamaños.
    total = 0
    for dirpath, dirnames, filenames in os.walk(path):
        for f in filenames:
            fp = os.path.join(dirpath, f)
            if os.path.exists(fp):
                total += os.path.getsize(fp)
    return total

def list_cron_jobs():

    # Lista tareas programadas (cron). En Linux 'crontab -l'. Muestra las tareas del usuario actual.
    if sys.platform == "linux":
        return subprocess.getoutput("crontab -l 2>/dev/null || echo 'No cron jobs'")
    return "No soportado"

def list_services():

    # Lista servicios del sistema en ejecución. En Linux 'systemctl list-units --type=service --state=running'. Muestra los primeros 40.
    if sys.platform == "linux":
        return subprocess.getoutput("systemctl list-units --type=service --state=running | head -40")
    return "No soportado"

def docker_info():

    # Información de Docker. Ejecuta 'docker info'. Muestra versiones, número de contenedores, imágenes, plugins, etc.
    try:
        return subprocess.getoutput("docker info 2>/dev/null | head -20")
    except:
        return "Docker no disponible"

def docker_containers():

    # Lista contenedores Docker. 'docker ps -a' muestra todos (incluso detenidos). Incluye ID, imagen, estado, puertos.
    try:
        return subprocess.getoutput("docker ps -a 2>/dev/null")
    except:
        return "Docker no disponible"

def docker_images():

    # Lista imágenes Docker descargadas. 'docker images' muestra repositorio, tag, ID, fecha de creación y tamaño.
    try:
        return subprocess.getoutput("docker images 2>/dev/null")
    except:
        return "Docker no disponible"


def disk_io_stats():
    """Muestra estadísticas de I/O de discos"""

    # Estadísticas de I/O de disco. En Linux iostat o /proc/diskstats. Muestra lecturas/escrituras por segundo y tiempos de espera.
    if sys.platform == "linux":
        return subprocess.getoutput("iostat -x 1 1 2>/dev/null || cat /proc/diskstats | head -30")
    return "No soportado"


def network_bandwidth():
    """Muestra uso de ancho de banda por interfaz"""

    # Muestra uso de ancho de banda por interfaz. Prueba nload, bmon, sar o lee /proc/net/dev como fallback.
    if sys.platform == "linux":
        return subprocess.getoutput("nload -t 1000 2>/dev/null || bmon -o ascii 2>/dev/null || sar -n DEV 1 1 2>/dev/null || cat /proc/net/dev")
    return "No soportado"


def swapon_info():
    """Muestra información de memoria swap"""

    # Información de memoria swap. En Linux 'swapon --show' o /proc/swaps. Muestra partición, tipo, tamaño y usado.
    if sys.platform == "linux":
        return subprocess.getoutput("swapon --show 2>/dev/null || cat /proc/swaps")
    return "No soportado"


def zombie_processes():
    """Lista procesos zombie"""

    # Busca procesos zombie (estado Z). En Linux 'ps aux | grep -w Z'. Los zombies son procesos muertos que el padre no recolectó.
    if sys.platform == "linux":
        return subprocess.getoutput("ps aux | grep -w Z 2>/dev/null | grep -v grep")
    return "No soportado"


def top_memory_processes(count=10):
    """Muestra los procesos que más memoria consumen"""

    # Muestra los procesos que más memoria RAM consumen. En Linux 'ps aux --sort=-%mem'. En Windows 'tasklist /sort:mem'.
    try:
        num = int(count)
    except (ValueError, TypeError):
        num = 10
    if sys.platform == "linux":
        return subprocess.getoutput(f"ps aux --sort=-%mem | head -{num + 1}")
    elif sys.platform == "win32":
        return subprocess.getoutput("tasklist /sort:mem /fi \"memusage gt 50000\"")
    return "No soportado"


def top_cpu_processes(count=10):
    """Muestra los procesos que más CPU consumen"""

    # Muestra los procesos que más CPU consumen. En Linux 'ps aux --sort=-%cpu'. En Windows 'tasklist /sort:CPU'.
    try:
        num = int(count)
    except (ValueError, TypeError):
        num = 10
    if sys.platform == "linux":
        return subprocess.getoutput(f"ps aux --sort=-%cpu | head -{num + 1}")
    elif sys.platform == "win32":
        return subprocess.getoutput("tasklist /sort:CPU")
    return "No soportado"


def disk_partitions():
    """Muestra particiones de disco y punto de montaje"""

    # Muestra particiones de disco. En Linux lsblk o fdisk o df -h. En Windows 'wmic logicaldisk'. Muestra punto de montaje y sistema de archivos.
    if sys.platform == "linux":
        return subprocess.getoutput("lsblk -o NAME,SIZE,TYPE,MOUNTPOINT,FSTYPE 2>/dev/null || fdisk -l 2>/dev/null | head -40 || df -h")
    elif sys.platform == "win32":
        return subprocess.getoutput("wmic logicaldisk get deviceid,size,freespace")
    return subprocess.getoutput("df -h")


def inode_usage(path="/"):
    """Muestra uso de inodos en una partición"""

    # Muestra uso de inodos en una partición. En Linux 'df -i'. Útil cuando el disco tiene espacio pero no más inodos (archivos pequeños).
    if sys.platform == "linux":
        return subprocess.getoutput(f"df -i {path}")
    return "No soportado"


def logged_users():
    """Muestra usuarios logueados en el sistema"""

    # Muestra usuarios logueados. En Linux 'who -a' o 'w'. Muestra usuario, terminal, hora de inicio, IP de origen.
    if sys.platform == "linux":
        return subprocess.getoutput("who -a 2>/dev/null || w")
    return subprocess.getoutput("who")


def last_logins(count=20):
    """Muestra los últimos inicios de sesión"""

    # Últimos inicios de sesión. En Linux 'last' o 'lastlog'. Muestra historial de conexiones con IP y duración.
    try:
        num = int(count) if isinstance(count, (int, str)) and str(count).isdigit() else 20
    except:
        num = 20
    if sys.platform == "linux":
        return subprocess.getoutput(f"last -{num} 2>/dev/null || lastlog")
    return subprocess.getoutput("lastlog 2>/dev/null || echo 'No soportado'")


def failed_logins():
    """Muestra intentos fallidos de inicio de sesión"""

    # Muestra intentos fallidos de login. En Linux 'lastb', /var/log/auth.log o journalctl. Filtra 'Failed password'.
    if sys.platform == "linux":
        return subprocess.getoutput("lastb 2>/dev/null | head -30 || cat /var/log/auth.log 2>/dev/null | grep 'Failed password' | tail -20 || journalctl -xe -n 30 2>/dev/null | grep -i fail | tail -20")
    return "No soportado"


def selinux_status():
    """Muestra estado de SELinux"""

    # Estado de SELinux. 'getenforce' devuelve Enforcing, Permissive o Disabled. 'sestatus' da información detallada.
    if sys.platform == "linux":
        return subprocess.getoutput("getenforce 2>/dev/null || sestatus 2>/dev/null || echo 'No disponible'")
    return "No soportado"


def firewall_rules():
    """Muestra reglas del firewall"""

    # Muestra reglas del firewall. En Linux prueba iptables, nftables, ufw. En Windows 'netsh advfirewall show allprofiles'.
    if sys.platform == "linux":
        return subprocess.getoutput("iptables -L -n -v 2>/dev/null | head -50 || nft list ruleset 2>/dev/null | head -50 || ufw status verbose 2>/dev/null")
    elif sys.platform == "win32":
        return subprocess.getoutput("netsh advfirewall show allprofiles")
    return "No soportado"


def system_logs(lines=30):
    """Muestra las últimas líneas del log del sistema"""

    # Últimas líneas del log del sistema. En Linux journalctl o tail de /var/log/syslog. Muestra las últimas N líneas (30 por defecto).
    try:
        num = int(lines) if str(lines).isdigit() else 30
    except:
        num = 30
    if sys.platform == "linux":
        return subprocess.getoutput(f"journalctl -n {num} --no-pager 2>/dev/null || tail -{num} /var/log/syslog 2>/dev/null || tail -{num} /var/log/messages 2>/dev/null")
    return "No soportado"


def system_load():
    """Muestra carga del sistema (load average)"""

    # Carga del sistema (load average). Lee /proc/loadavg. Muestra promedios de 1, 5 y 15 minutos. <1 es bueno, >núcleos es malo.
    if sys.platform == "linux":
        return subprocess.getoutput("cat /proc/loadavg")
    return "No soportado"


def python_version():
    """Muestra la versión de Python y módulos clave instalados"""

    # Versión de Python y módulos clave instalados (Flask, requests, Django). Útil para verificar dependencias.
    import platform
    info = {
        "python_version": platform.python_version(),
        "executable": sys.executable,
    }
    try:
        import flask; info["flask"] = flask.__version__
    except ImportError:
        pass
    try:
        import requests; info["requests"] = requests.__version__
    except ImportError:
        pass
    try:
        import django; info["django"] = django.__version__
    except ImportError:
        pass
    return info


def ssh_connections():
    """Muestra conexiones SSH activas"""

    # Muestra conexiones SSH activas. Busca conexiones TCP al puerto 22 con 'ss -tnp' o 'netstat'. Incluye IP origen.
    if sys.platform == "linux":
        return subprocess.getoutput("ss -tnp 2>/dev/null | grep ':22' || netstat -tnpa 2>/dev/null | grep ':22' || who -u")
    return "No soportado"


def listening_ports():
    """Muestra puertos en escucha en el sistema"""

    # Puertos en escucha en el sistema. En Linux 'ss -tulpn', en Windows 'netstat -an | findstr LISTEN'. Muestra servicio y IP.
    if sys.platform == "linux":
        return subprocess.getoutput("ss -tulpn 2>/dev/null || netstat -tulpn 2>/dev/null")
    elif sys.platform == "win32":
        return subprocess.getoutput("netstat -an | findstr LISTEN")
    return "No soportado"


def fs_inotify_watches():
    """Muestra límites y uso de inotify watches"""

    # Límites de inotify. Lee /proc/sys/fs/inotify/max_user_watches. Cuenta watches actuales. Importante para IDEs y servicios.
    if sys.platform == "linux":
        max_user = subprocess.getoutput("cat /proc/sys/fs/inotify/max_user_watches")
        count = subprocess.getoutput("find /proc/*/fd -lname anon_inode:inotify 2>/dev/null | awk '{print $1}' | wc -l")
        return {"max_user_watches": max_user, "current_inotify_count": count or "0"}
    return "No soportado"


def file_descriptors():
    """Muestra límites de file descriptors"""

    # Límites de archivos abiertos (file descriptors). 'ulimit -n' muestra límite soft, 'ulimit -Hn' el hard. Ajustable en /etc/security/limits.conf.
    if sys.platform == "linux":
        soft = subprocess.getoutput("ulimit -n")
        hard = subprocess.getoutput("ulimit -Hn")
        return {"soft_limit": soft, "hard_limit": hard}
    return "No soportado"


def systemd_failed_services():
    """Lista servicios systemd que fallaron"""

    # Lista servicios systemd que fallaron al iniciar. 'systemctl --failed' muestra servicios en estado failed con descripción.
    if sys.platform == "linux":
        return subprocess.getoutput("systemctl --failed --no-pager")
    return "No soportado"


def kernel_parameters(param=None):
    """Muestra parámetros del kernel (sysctl)"""

    # Parámetros del kernel (sysctl). Sin argumento muestra net.ipv4, net.core, vm.swappiness. Con argumento muestra un parámetro específico.
    if sys.platform == "linux":
        if param:
            return subprocess.getoutput(f"sysctl {param} 2>/dev/null || echo 'Parámetro no encontrado'")
        return subprocess.getoutput("sysctl -a 2>/dev/null | grep -E 'net.ipv4|net.core|kernel.hostname|vm.swappiness' | head -30")
    return "No soportado"


def timedate_info():
    """Muestra configuración de fecha y hora del sistema"""

    # Configuración de fecha y hora. En Linux 'timedatectl' muestra zona horaria, sincronización NTP, hora UTC/local.
    if sys.platform == "linux":
        return subprocess.getoutput("timedatectl 2>/dev/null || cat /etc/timezone 2>/dev/null || date")
    return subprocess.getoutput("date")


def locale_info():
    """Muestra configuración regional del sistema"""

    # Configuración regional (locale). En Linux 'locale' muestra LANG, LC_ALL, etc. Importante para caracteres especiales y formato de moneda.
    if sys.platform == "linux":
        return subprocess.getoutput("locale 2>/dev/null || cat /etc/default/locale 2>/dev/null || echo 'No disponible'")
    return "No soportado"


def debian_services_list():
    """Lista servicios disponibles en sistema Debian/Ubuntu"""

    # Lista servicios disponibles al estilo Debian. 'service --status-all' o lista /etc/init.d/. Muestra todos los servicios instalados.
    if sys.platform == "linux":
        return subprocess.getoutput("service --status-all 2>/dev/null || ls /etc/init.d/ 2>/dev/null | head -40")
    return "No soportado"


def dmesg_recent():
    """Muestra mensajes recientes del kernel"""

    # Últimos mensajes del kernel. 'dmesg | tail -40'. Muestra eventos de hardware, drivers, errores del kernel.
    if sys.platform == "linux":
        return subprocess.getoutput("dmesg 2>/dev/null | tail -40")
    return "No soportado"


def usb_details():
    """Muestra detalles de dispositivos USB conectados"""

    # Detalles de dispositivos USB. En Linux 'lsusb -v' o 'lsusb'. Muestra fabricante, producto, velocidad, puerto.
    if sys.platform == "linux":
        return subprocess.getoutput("lsusb -v 2>/dev/null | head -60 || lsusb")
    return "No soportado"


def samba_status():
    """Muestra estado de servicios Samba"""

    # Estado de Samba. 'smbstatus' muestra conexiones activas. 'systemctl status smbd' muestra si el servicio corre.
    if sys.platform == "linux":
        return subprocess.getoutput("smbstatus 2>/dev/null || systemctl status smbd 2>/dev/null | head -20 || echo 'Samba no disponible'")
    return "No soportado"


def nfs_status():
    """Muestra estado de servicios NFS"""

    # Estado de NFS. 'exportfs -v' muestra exportaciones. 'showmount -e localhost' muestra lo que está compartido. 'systemctl status nfs-server'.
    if sys.platform == "linux":
        return subprocess.getoutput("exportfs -v 2>/dev/null || showmount -e localhost 2>/dev/null || systemctl status nfs-server 2>/dev/null | head -10 || echo 'NFS no disponible'")
    return "No soportado"


def apache_status():
    """Muestra estado de Apache/Nginx"""

    # Estado del servidor web. Prueba systemctl status apache2, httpd o nginx. Muestra si está activo y la última actividad.
    if sys.platform == "linux":
        return subprocess.getoutput("systemctl status apache2 2>/dev/null | head -10 || systemctl status httpd 2>/dev/null | head -10 || systemctl status nginx 2>/dev/null | head -10 || echo 'No se detectó servidor web'")
    return "No soportado"


def mysql_status():
    """Muestra estado de MySQL/MariaDB"""

    # Estado de MySQL/MariaDB. 'systemctl status mysql', 'systemctl status mariadb' o 'mysqladmin ping'.
    if sys.platform == "linux":
        return subprocess.getoutput("systemctl status mysql 2>/dev/null | head -10 || systemctl status mariadb 2>/dev/null | head -10 || mysqladmin ping 2>/dev/null || echo 'MySQL no detectado'")
    return "No soportado"


def postgresql_status():
    """Muestra estado de PostgreSQL"""

    # Estado de PostgreSQL. 'systemctl status postgresql' o 'pg_isready' que prueba si acepta conexiones.
    if sys.platform == "linux":
        return subprocess.getoutput("systemctl status postgresql 2>/dev/null | head -10 || pg_isready 2>/dev/null || echo 'PostgreSQL no detectado'")
    return "No soportado"


def docker_network_ls():
    """Lista redes Docker"""

    # Lista redes Docker. 'docker network ls' muestra driver (bridge, host, overlay) y ámbito (local, swarm).
    try:
        return subprocess.getoutput("docker network ls 2>/dev/null || echo 'Docker no disponible'")
    except:
        return "Docker no disponible"


def docker_volume_ls():
    """Lista volúmenes Docker"""

    # Lista volúmenes Docker. 'docker volume ls' muestra volúmenes persistentes. Los volúmenes sobreviven a los contenedores.
    try:
        return subprocess.getoutput("docker volume ls 2>/dev/null || echo 'Docker no disponible'")
    except:
        return "Docker no disponible"


def docker_logs(container="", lines=20):
    """Muestra logs de un contenedor Docker"""

    # Logs de un contenedor Docker específico. 'docker logs --tail N nombre'. Sin nombre lista contenedores disponibles.
    try:
        num = int(lines) if str(lines).isdigit() else 20
    except:
        num = 20
    if not container:
        return subprocess.getoutput(f"docker ps --format '{{.Names}}' 2>/dev/null || echo 'No containers'")
    try:
        return subprocess.getoutput(f"docker logs --tail {num} {container} 2>&1")
    except Exception as e:
        return f"Error: {e}"


def docker_stats():
    """Muestra estadísticas de contenedores Docker (un snapshot)"""

    # Estadísticas en vivo de contenedores Docker. 'docker stats --no-stream' muestra un snapshot de CPU, memoria, I/O.
    try:
        return subprocess.getoutput("docker stats --no-stream 2>/dev/null || echo 'Docker no disponible'")
    except:
        return "Docker no disponible"


def disk_health():
    """Verifica salud de discos (SMART si disponible)"""

    # Salud de discos vía SMART. 'smartctl -H /dev/sdX' verifica si el disco está PASADO o FALLADO. Requiere smartctl instalado.
    if sys.platform == "linux":
        disks = subprocess.getoutput("ls /dev/sd? 2>/dev/null || ls /dev/nvme?n? 2>/dev/null || ls /dev/vd? 2>/dev/null")
        results = {}
        for d in disks.strip().split("\n"):
            d = d.strip()
            if d:
                smart = subprocess.getoutput(f"smartctl -H {d} 2>/dev/null | grep -E 'SMART|PASSED|FAILED' || echo 'SMART no disponible para {d}'")
                results[d] = smart
        return results if results else {"error": "No se encontraron discos o smartctl no instalado"}
    return "No soportado"


def disk_io_top():
    """Muestra procesos con mayor I/O de disco"""

    # Procesos con mayor I/O de disco. 'iotop -b -n 1' o 'iostat -x'. Útil para detectar procesos que saturan el disco.
    if sys.platform == "linux":
        return subprocess.getoutput("iotop -b -n 1 2>/dev/null | head -20 || iostat -x 1 1 2>/dev/null | tail -20 || echo 'iotop/iostat no disponible'")
    return "No soportado"


def network_sockets_summary():
    """Resumen de sockets de red por estado"""

    # Resumen de sockets de red por estado (ESTAB, LISTEN, TIME-WAIT, CLOSE-WAIT). Conteo con ss y grep.
    if sys.platform == "linux":
        established = subprocess.getoutput("ss -tun | grep -c ESTAB")
        listening = subprocess.getoutput("ss -tun | grep -c LISTEN")
        time_wait = subprocess.getoutput("ss -tun | grep -c TIME-WAIT")
        close_wait = subprocess.getoutput("ss -tun | grep -c CLOSE-WAIT")
        total = subprocess.getoutput("ss -tun | wc -l")
        return {
            "established": established, "listening": listening,
            "time_wait": time_wait, "close_wait": close_wait,
            "total_connections": total,
        }
    return "No soportado"


def memory_slots():
    """Muestra información de slots de memoria RAM"""

    # Información de slots de memoria RAM. 'dmidecode -t memory' muestra tamaño, tipo, velocidad y fabricante de cada módulo.
    if sys.platform == "linux":
        return subprocess.getoutput("dmidecode -t memory 2>/dev/null | grep -E 'Size|Type|Speed|Locator|Manufacturer|Part' | head -30 || echo 'dmidecode no disponible'")
    return "No soportado"


def bios_info():
    """Muestra información de la BIOS/UEFI"""

    # Información de BIOS/UEFI. 'dmidecode -t bios' muestra fabricante, versión, fecha de release y tamaño de ROM.
    if sys.platform == "linux":
        return subprocess.getoutput("dmidecode -t bios 2>/dev/null | grep -E 'Vendor|Version|Release|Date|ROM|BIOS' || echo 'dmidecode no disponible'")
    return "No soportado"


def hardware_summary():
    """Resumen de hardware del sistema"""

    # Resumen de hardware: CPU, núcleos, RAM, discos. En Linux usa lscpu, free, lsblk. Da una vista rápida de la máquina.
    if sys.platform == "linux":
        cpu = subprocess.getoutput("lscpu | grep 'Model name' | head -1 | cut -d: -f2 | xargs")
        cores = subprocess.getoutput("nproc --all 2>/dev/null || echo '?'")
        ram = subprocess.getoutput("free -h | grep Mem | awk '{print $2}'")
        disks = subprocess.getoutput("lsblk -d -o NAME,SIZE,MODEL 2>/dev/null | tail -n +2 | head -5")
        return {
            "cpu": cpu,
            "cores": cores,
            "ram": ram,
            "disks": disks.strip().split("\n") if disks.strip() else [],
        }
    return {"system": platform.system(), "node": platform.node(), "processor": platform.processor()}


def thermal_info():
    """Muestra temperaturas del sistema"""

    # Temperaturas del sistema. 'sensors' para CPU/GPU/chasis. Fallback: /sys/class/thermal/thermal_zone* temperaturas en miligrados.
    if sys.platform == "linux":
        sensors = subprocess.getoutput("sensors 2>/dev/null | grep -E 'Core|Package|temp|fan' | head -20 || cat /sys/class/thermal/thermal_zone*/temp 2>/dev/null | awk '{print $1/1000 \"°C\"}' || echo 'sensors no disponible'")
        return {"temperatures": sensors}
    return "No soportado"


def uptime_detailed():
    """Muestra uptime detallado del sistema"""

    # Uptime detallado. Lee /proc/uptime para segundos exactos. Calcula días, horas, minutos. Muestra boot time y load average.
    if sys.platform == "linux":
        uptime_sec = float(open("/proc/uptime").read().split()[0])
        days = int(uptime_sec // 86400)
        hours = int((uptime_sec % 86400) // 3600)
        mins = int((uptime_sec % 3600) // 60)
        boot_time = subprocess.getoutput("who -b 2>/dev/null | awk '{print $3, $4}'")
        return {
            "uptime_seconds": uptime_sec,
            "uptime_readable": f"{days}d {hours}h {mins}m",
            "boot_time": boot_time,
            "load": open("/proc/loadavg").read().strip() if os.path.exists("/proc/loadavg") else None,
        }
    return {"uptime": uptime()}


def os_release():
    """Muestra información de la distribución Linux"""

    # Información de la distribución Linux. Lee /etc/os-release (nombre, versión, ID). Fallback: uname -a.
    if sys.platform == "linux":
        for f in ["/etc/os-release", "/etc/lsb-release", "/etc/redhat-release"]:
            if os.path.exists(f):
                with open(f) as fh:
                    return fh.read().strip()
        return subprocess.getoutput("uname -a")
    return {"system": platform.system(), "release": platform.release()}


def kernel_modules():
    """Lista módulos del kernel cargados"""

    # Módulos del kernel cargados. 'lsmod' muestra nombre, tamaño y dependencias. Útil para ver qué drivers están activos.
    if sys.platform == "linux":
        return subprocess.getoutput("lsmod | head -40")
    return "No soportado"


def systemd_journal(since="1 hour ago"):
    """Muestra entradas del journald desde hace un tiempo"""

    # Entradas del journald. 'journalctl --since "1 hour ago"' muestra logs del sistema desde hace un tiempo específico.
    if sys.platform == "linux":
        return subprocess.getoutput(f"journalctl --since '{since}' --no-pager 2>/dev/null | tail -30 || echo 'journalctl no disponible'")
    return "No soportado"


def systemd_timers():
    """Lista timers de systemd"""

    # Timers de systemd (cron moderno). 'systemctl list-timers' muestra próxima ejecución, última ejecución y unidad asociada.
    if sys.platform == "linux":
        return subprocess.getoutput("systemctl list-timers --no-pager 2>/dev/null | head -30 || echo 'No timers'")
    return "No soportado"


def cron_check(user=""):
    """Muestra crontabs del sistema"""

    # Muestra crontabs. Sin usuario muestra crons del sistema (/etc/cron*) y del usuario actual. Con usuario específico 'crontab -u user -l'.
    if sys.platform == "linux":
        if user:
            return subprocess.getoutput(f"crontab -u {user} -l 2>/dev/null || echo 'No crontab for {user}'")
        system_crons = subprocess.getoutput("ls -la /etc/cron* 2>/dev/null | head -20")
        user_crons = subprocess.getoutput("crontab -l 2>/dev/null || echo 'No user crontab'")
        return {"system_crons": system_crons, "user_crontab": user_crons}
    return "No soportado"


def audit_log():
    """Muestra logs de auditoría (auditd)"""

    # Logs de auditoría (auditd). 'ausearch -m AVC' busca eventos de denegación. Fallback: /var/log/audit/audit.log.
    if sys.platform == "linux":
        return subprocess.getoutput("ausearch -m AVC 2>/dev/null | tail -20 || cat /var/log/audit/audit.log 2>/dev/null | tail -20 || echo 'auditd no disponible'")
    return "No soportado"


def security_info():
    """Información de seguridad del sistema"""

    # Información de seguridad del sistema. SELinux, firewall, AppArmor, fail2ban, config SSH, política de contraseñas y puertos abiertos.
    if sys.platform != "linux":
        return {"error": "Solo Linux"}

    info = {}
    info["selinux"] = subprocess.getoutput("getenforce 2>/dev/null || 'No disponible'")
    info["firewall"] = subprocess.getoutput("iptables -L -n --line-numbers 2>/dev/null | head -10 || nft list ruleset 2>/dev/null | head -10 || ufw status 2>/dev/null || echo 'No detectado'")
    info["apparmor"] = subprocess.getoutput("aa-status 2>/dev/null | head -5 || echo 'No disponible'")
    info["fail2ban"] = subprocess.getoutput("fail2ban-client status 2>/dev/null || echo 'No disponible'")
    info["ssh_config"] = subprocess.getoutput("grep -E 'PermitRootLogin|PasswordAuthentication|Port' /etc/ssh/sshd_config 2>/dev/null")
    info["passwd_maxdays"] = subprocess.getoutput("grep -E '^PASS_MAX_DAYS' /etc/login.defs 2>/dev/null")
    info["open_ports"] = subprocess.getoutput("ss -tulpn 2>/dev/null | grep LISTEN | wc -l")
    return info


def pam_config():
    """Muestra configuración de PAM"""

    # Configuración de PAM (Pluggable Authentication Modules). Lee /etc/pam.d/common-auth o system-auth. Módulos de autenticación.
    if sys.platform == "linux":
        return subprocess.getoutput("cat /etc/pam.d/common-auth 2>/dev/null | head -20 || cat /etc/pam.d/system-auth 2>/dev/null | head -20 || echo 'No disponible'")
    return "No soportado"


def limits_config():
    """Muestra límites del sistema (ulimit)"""

    # Límites del sistema. 'ulimit -a' muestra todos los límites del usuario. /etc/security/limits.conf muestra límites configurados.
    if sys.platform == "linux":
        return subprocess.getoutput("ulimit -a 2>/dev/null || cat /etc/security/limits.conf 2>/dev/null | grep -v '^#' | grep -v '^$' | head -20")
    return "No soportado"


def package_updates():
    """Lista actualizaciones de paquetes disponibles"""

    # Lista actualizaciones disponibles. En Debian/Ubuntu 'apt list --upgradable'. En RHEL 'yum check-update'.
    if sys.platform == "linux":
        apt = subprocess.getoutput("apt list --upgradable 2>/dev/null | head -30")
        if "upgradable" in apt:
            return apt
        yum = subprocess.getoutput("yum check-update 2>/dev/null | head -30")
        if yum:
            return yum
        return "No se pudo determinar (ni apt ni yum detectados)"
    return "No soportado"


def snap_list():
    """Lista paquetes Snap instalados"""

    # Paquetes Snap instalados. 'snap list' muestra nombre, versión, revisión y desarrollador.
    if sys.platform == "linux":
        return subprocess.getoutput("snap list 2>/dev/null || echo 'Snap no disponible'")
    return "No soportado"


def flatpak_list():
    """Lista paquetes Flatpak instalados"""

    # Paquetes Flatpak instalados. 'flatpak list' muestra nombre, ID, versión, rama y origen.
    if sys.platform == "linux":
        return subprocess.getoutput("flatpak list 2>/dev/null || echo 'Flatpak no disponible'")
    return "No soportado"


def ipmi_info():
    """Muestra información IPMI/BMC si está disponible"""

    # Información IPMI/BMC. 'ipmitool sensor' muestra sensores. 'ipmitool chassis status' muestra estado del chasis. Útil para servidores.
    if sys.platform == "linux":
        return subprocess.getoutput("ipmitool sensor 2>/dev/null | head -20 || ipmitool chassis status 2>/dev/null || echo 'IPMI no disponible'")
    return "No soportado"


def lvm_info():
    """Muestra información de LVM"""

    # Información de LVM (Logical Volume Manager). lvdisplay, vgdisplay, pvdisplay muestran volúmenes lógicos, grupos y físicos.
    if sys.platform == "linux":
        return subprocess.getoutput("lvdisplay 2>/dev/null | head -30 || vgdisplay 2>/dev/null | head -20 || pvdisplay 2>/dev/null | head -20 || echo 'LVM no detectado'")
    return "No soportado"


def zfs_info():
    """Muestra información de ZFS"""

    # Información de ZFS. 'zpool status' muestra estado de pools. 'zfs list' muestra datasets y volúmenes. Estado de redundancia y errores.
    if sys.platform == "linux":
        return subprocess.getoutput("zpool status 2>/dev/null | head -30 || zfs list 2>/dev/null | head -20 || echo 'ZFS no detectado'")
    return "No soportado"


def mdraid_info():
    """Muestra información de RAID por software (mdadm)"""

    # Información de RAID por software. /proc/mdstat muestra estado de arrays RAID, nivel, discos y sincronización.
    if sys.platform == "linux":
        return subprocess.getoutput("cat /proc/mdstat 2>/dev/null || mdadm --detail --scan 2>/dev/null || echo 'No RAID detectado'")
    return "No soportado"


def systemd_analyze():
    """Muestra tiempo de arranque (systemd-analyze)"""

    # Tiempo de arranque. 'systemd-analyze time' muestra total. 'systemd-analyze blame' muestra qué servicios tardan más en iniciar.
    if sys.platform == "linux":
        blame = subprocess.getoutput("systemd-analyze blame 2>/dev/null | head -20")
        time = subprocess.getoutput("systemd-analyze time 2>/dev/null")
        return {"boot_time": time, "blame": blame}
    return "No soportado"


def cert_expiry_local(cert_path):
    """Verifica fecha de expiración de un certificado local"""

    # Expiración de certificado local. Usa cryptography o openssl para leer el certificado y calcular días restantes.
    try:
        from cryptography import x509
        from cryptography.hazmat.backends import default_backend
        with open(cert_path, "rb") as f:
            cert = x509.load_pem_x509_certificate(f.read(), default_backend())
        expires = cert.not_valid_after
        remaining = (expires - datetime.now()).days
        return {"certificate": cert_path, "subject": cert.subject.rfc4514_string(), "issuer": cert.issuer.rfc4514_string(), "valid_until": str(expires), "days_remaining": remaining}
    except ImportError:
        output = subprocess.getoutput(f"openssl x509 -in {cert_path} -noout -dates -subject 2>/dev/null | head -10")
        return {"certificate": cert_path, "info": output[:500] if output else "openssl no disponible"}
    except Exception as e:
        return {"certificate": cert_path, "error": str(e)}


def command_exists(command):
    """Verifica si un comando existe en el sistema"""

    # Verifica si un comando existe en el sistema. Usa shutil.which() que busca en PATH. Devuelve True/False.
    return shutil.which(command) is not None


def find_large_logs(path="/var/log", size="+50M"):
    """Busca archivos de log grandes"""

    # Busca archivos de log grandes. En Linux find /var/log -name '*.log' -size +50M. Útil para diagnosticar discos llenos.
    if sys.platform == "linux":
        return subprocess.getoutput(f"find {path} -type f -name '*.log' -size {size} 2>/dev/null | head -20 || echo 'No se encontraron'")
    return "No soportado"


def systemd_units_failed():
    """Lista unidades systemd que fallaron"""

    # Alias de systemd_failed_services. Lista servicios systemd que fallaron.
    return systemd_failed_services()


def socket_stats():
    """Estadísticas de sockets UNIX"""

    # Estadísticas de sockets UNIX. 'ss -x' muestra sockets de dominio UNIX (comunicación entre procesos locales).
    if sys.platform == "linux":
        return subprocess.getoutput("ss -x 2>/dev/null | head -30 || echo 'No disponible'")
    return "No soportado"


def process_tree(pid=1):
    """Muestra árbol de procesos desde un PID"""

    # Árbol de procesos desde un PID. 'pstree -p' o 'ps --forest'. Muestra jerarquía de procesos padre-hijo.
    try:
        return subprocess.getoutput(f"pstree -p {pid} 2>/dev/null | head -40 || ps -eo pid,ppid,cmd --forest | head -40")
    except:
        return "No soportado"
