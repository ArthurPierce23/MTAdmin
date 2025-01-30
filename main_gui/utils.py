import re
import platform
import subprocess

def is_valid_ip(ip):
    """Проверяет корректность IP-адреса."""
    return bool(re.match(r"^(?:[0-9]{1,3}\.){3}[0-9]{1,3}$", ip))

def detect_os(ip):
    """Определяет ОС по IP."""
    try:
        output = subprocess.check_output(f"nmap -O {ip}", shell=True, stderr=subprocess.DEVNULL)
        if b"Linux" in output:
            return "Linux"
        elif b"Windows" in output:
            return "Windows"
    except:
        pass
    return "Неизвестно"
