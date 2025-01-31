import re
import platform
import subprocess
import socket
import struct
import concurrent.futures
from functools import lru_cache


def is_valid_ip(ip):
    """Проверяет корректность IPv4-адреса."""
    pattern = r"^((25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$"
    return bool(re.match(pattern, ip))


@lru_cache(maxsize=128)
def _ping_ip(ip, timeout=1):
    """Проверяет доступность IP через ping."""
    try:
        command = ['ping', '-c', '1', '-W', str(timeout), ip] if platform.system().lower() != 'windows' else \
                  ['ping', '-n', '1', '-w', str(timeout * 1000), ip]
        return subprocess.call(command, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=timeout + 1) == 0
    except subprocess.TimeoutExpired:
        return False


def _get_os_via_ttl(ttl):
    """Определяет ОС по значению TTL."""
    if ttl is None:
        return "Неизвестно"
    if ttl <= 64:
        return "Linux"
    elif 65 <= 128:
        return "Windows"
    return "Неизвестно"


def _check_tcp_port(ip, port, timeout=1):
    """Проверяет, открыт ли TCP-порт."""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(timeout)
            return s.connect_ex((ip, port)) == 0
    except socket.error:
        return False


def _detect_os_via_sockets(ip):
    """Анализ TCP-ответов без ICMP для определения ОС"""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(1)
            s.connect((ip, 135))  # RPC Endpoint Mapper (обычно Windows)
            data = s.recv(1024)
            if data:
                return "Windows"
    except (socket.timeout, socket.error):
        pass
    return "Неизвестно"


def _get_ttl(ip, timeout=1):
    """Получает TTL пакета (если не блокируется брандмауэром)"""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_RAW, socket.IPPROTO_ICMP) as s:
            s.settimeout(timeout)
            packet = struct.pack('!BBHHH', 8, 0, 0, 0, 0)  # ICMP Echo Request
            s.sendto(packet, (ip, 1))
            response = s.recvfrom(256)[0]
            return response[8] if len(response) > 8 else None
    except (PermissionError, socket.error):
        return None


def detect_os(ip, timeout=2):
    """Определяет ОС через TTL, порты и TCP-анализ"""

    if not is_valid_ip(ip):
        return "Неверный IP"

    # Проверяем доступность IP
    if not _ping_ip(ip, timeout):
        print(f"[DEBUG] {ip} не отвечает на ping.")
        return "Недоступен"

    # 🔥 Ключевые Windows и Linux порты
    windows_ports = [3389, 49003, 445, 137, 139, 135, 5985, 5986]
    linux_ports = [22]

    all_ports = windows_ports + linux_ports

    # 🔥 Проверяем порты параллельно
    with concurrent.futures.ThreadPoolExecutor() as executor:
        results = list(executor.map(lambda port: _check_tcp_port(ip, port, timeout), all_ports))

    open_ports = {port: results[i] for i, port in enumerate(all_ports)}

    print(f"[DEBUG] Открытые порты: {open_ports}")

    # 🔥 Логика определения ОС:
    if any(open_ports[p] for p in windows_ports):
        return "Windows"

    if open_ports[22]:
        return "Linux"  # Теперь Linux определяется корректно!

    # 🔥 Если порты не помогли — проверяем TTL
    ttl = _get_ttl(ip, timeout)
    print(f"[DEBUG] TTL: {ttl}")

    if ttl:
        return _get_os_via_ttl(ttl)

    # 🔥 Если вообще ничего не сработало — пробуем анализ TCP-ответов
    return _detect_os_via_sockets(ip)
