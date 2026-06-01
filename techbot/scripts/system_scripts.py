import os
import sys
import shutil
import subprocess
import platform


def disk_usage(path="/"):
    total, used, free = shutil.disk_usage(path)
    return {
        "total": f"{total // (2**30)} GB",
        "used": f"{used // (2**30)} GB",
        "free": f"{free // (2**30)} GB",
        "percent_used": round(used / total * 100, 1)
    }

def list_running_processes():
    if sys.platform == "linux":
        return subprocess.getoutput("ps aux --sort=-%mem | head -30")
    elif sys.platform == "win32":
        return subprocess.getoutput("tasklist")
    return "No soportado"

def system_info():
    return {
        "system": platform.system(),
        "node": platform.node(),
        "release": platform.release(),
        "version": platform.version(),
        "machine": platform.machine(),
        "processor": platform.processor()
    }

def cpu_info():
    if sys.platform == "linux":
        return subprocess.getoutput("lscpu | grep -E 'Model name|CPU(s)|Thread|Core'")
    return "No soportado"

def memory_info():
    if sys.platform == "linux":
        return subprocess.getoutput("free -h")
    elif sys.platform == "win32":
        return subprocess.getoutput("systeminfo | findstr Memory")
    return "No soportado"

def uptime():
    if sys.platform == "linux":
        return subprocess.getoutput("uptime")
    return "No soportado"

def list_open_ports():
    if sys.platform == "linux":
        return subprocess.getoutput("ss -tuln")
    elif sys.platform == "win32":
        return subprocess.getoutput("netstat -an")
    return "No soportado"

def list_usb_devices():
    if sys.platform == "linux":
        return subprocess.getoutput("lsusb")
    return "No soportado"

def list_pci_devices():
    if sys.platform == "linux":
        return subprocess.getoutput("lspci")
    return "No soportado"

def list_network_interfaces():
    if sys.platform == "linux":
        return subprocess.getoutput("ip link show")
    elif sys.platform == "win32":
        return subprocess.getoutput("ipconfig")
    return "No soportado"

def kernel_version():
    if sys.platform == "linux":
        return subprocess.getoutput("uname -a")
    return platform.uname().version

def environment_variables():
    return dict(os.environ)

def large_files(path="/", size="+100M"):
    if sys.platform == "linux":
        return subprocess.getoutput(f"find {path} -type f -size {size} 2>/dev/null | head -50")
    return "No soportado"

def check_service_status(service):
    if sys.platform == "linux":
        return subprocess.getoutput(f"systemctl status {service} 2>&1 | head -20")
    elif sys.platform == "win32":
        return subprocess.getoutput(f"sc query {service}")
    return "No soportado"

def installed_packages():
    if sys.platform == "linux":
        return subprocess.getoutput("dpkg --get-selections 2>/dev/null | head -50 || rpm -qa 2>/dev/null | head -50")
    return "No soportado"

def file_hash(filepath, algo="sha256"):
    import hashlib
    h = hashlib.new(algo)
    with open(filepath, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            h.update(chunk)
    return h.hexdigest()

def directory_size(path):
    total = 0
    for dirpath, dirnames, filenames in os.walk(path):
        for f in filenames:
            fp = os.path.join(dirpath, f)
            if os.path.exists(fp):
                total += os.path.getsize(fp)
    return total

def list_cron_jobs():
    if sys.platform == "linux":
        return subprocess.getoutput("crontab -l 2>/dev/null || echo 'No cron jobs'")
    return "No soportado"

def list_services():
    if sys.platform == "linux":
        return subprocess.getoutput("systemctl list-units --type=service --state=running | head -40")
    return "No soportado"

def docker_info():
    try:
        return subprocess.getoutput("docker info 2>/dev/null | head -20")
    except:
        return "Docker no disponible"

def docker_containers():
    try:
        return subprocess.getoutput("docker ps -a 2>/dev/null")
    except:
        return "Docker no disponible"

def docker_images():
    try:
        return subprocess.getoutput("docker images 2>/dev/null")
    except:
        return "Docker no disponible"
