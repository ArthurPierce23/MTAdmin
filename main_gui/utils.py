# utils.py
import re
import platform
import subprocess
import socket
import struct
from functools import lru_cache
import ctypes



def is_valid_ip(ip):
    """Проверяет корректность IPv4-адреса."""
    pattern = r"^((25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$"
    return bool(re.match(pattern, ip))


@lru_cache(maxsize=128)
def _ping_ip(ip, timeout=2):
    """Проверяет доступность IP-адреса через ping с кэшированием"""
    try:
        command = ['ping', '-c', '1', '-W', str(timeout), ip] if platform.system().lower() != 'windows' else \
                  ['ping', '-n', '1', '-w', str(timeout * 1000), ip]
        return subprocess.call(command, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=timeout + 1) == 0
    except (subprocess.TimeoutExpired, Exception):
        return False


def _get_os_via_ttl(ttl):
    """Определяет ОС по значению TTL."""
    if ttl <= 64:
        return "Linux/Unix"
    elif 65 <= ttl <= 128:
        return "Windows"
    return "Неизвестно"


def _check_tcp_port(ip, port, timeout=2):
    """Проверяет состояние TCP-порта."""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(timeout)
            return s.connect_ex((ip, port)) == 0
    except socket.error:
        return False


def detect_os(ip, timeout=3):
    """Определяет ОС с обработкой таймаутов"""
    if not is_valid_ip(ip):
        return "Неверный IP"

    if not _ping_ip(ip, timeout):
        return "Недоступен"

    ttl = None
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_RAW, socket.IPPROTO_ICMP) as s:
            s.settimeout(2)
            packet = struct.pack('!BBHHH', 8, 0, 0, 0, 0)
            s.sendto(packet, (ip, 1))
            response = s.recvfrom(256)[0]
            ttl = response[8]
    except (PermissionError, socket.error):
        ttl = None

    port_results = {22: _check_tcp_port(ip, 22), 3389: _check_tcp_port(ip, 3389)}

    if ttl:
        os_guess = _get_os_via_ttl(ttl)
        if "Windows" in os_guess and port_results[3389]:
            return "Windows"
        if "Linux" in os_guess and port_results[22]:
            return "Linux"
        return os_guess

    if port_results[3389]:
        return "Windows"
    if port_results[22]:
        return "Linux"

    return "Неизвестно"