import re
import subprocess
import platform
import socket
import ipaddress
from typing import Optional, Tuple

def is_potential_ip(text: str) -> bool:
    """Проверяет, состоит ли строка только из цифр и точек (потенциальный IP)."""
    return bool(text) and all(c.isdigit() or c == '.' for c in text)

def is_partial_ip(text: str) -> bool:
    """
    Проверяет, введён ли частичный IP (например, '192.168.').
    Строка не должна быть пустой и может содержать от нуля до трёх точек.
    """
    if not text:
        return False
    pattern = re.compile(r'^(\d{1,3}\.){0,3}\d{0,3}$')
    return bool(pattern.fullmatch(text))

def is_valid_ip(ip: str) -> bool:
    """
    Проверяет, что строка является корректным IPv4 адресом.
    Использует модуль ipaddress для валидации.
    """
    try:
        ipaddress.IPv4Address(ip)
        return True
    except ipaddress.AddressValueError:
        return False

def is_valid_hostname(hostname: str) -> bool:
    """
    Проверяет, является ли строка допустимым именем хоста.
    Поддерживаются многоуровневые доменные имена:
    каждая метка (отделённая точками) должна быть от 1 до 63 символов и соответствовать шаблону.
    """
    if not hostname or len(hostname) > 253:
        return False
    labels = hostname.split('.')
    label_regex = re.compile(r'^[a-zA-Z0-9]([a-zA-Z0-9-]*[a-zA-Z0-9])?$')
    return all(label and len(label) <= 63 and label_regex.fullmatch(label) for label in labels)

def is_valid_input(text: str) -> bool:
    """
    Проверяет, корректен ли ввод – либо валидный IPv4 адрес, либо валидное имя хоста, либо частичный IP.
    """
    return is_valid_ip(text) or is_valid_hostname(text) or is_partial_ip(text)

def ping_ip(ip: str, timeout: int = 1000) -> Tuple[bool, str]:
    """
    Выполняет ping заданного IP-адреса.

    :param ip: IP-адрес для проверки
    :param timeout: таймаут (в мс для Windows, в секундах для Linux/Mac)
    :return: Кортеж (доступен ли хост, вывод команды ping)
    """
    system = platform.system().lower()

    if system == 'windows':
        # В Windows timeout задаётся в миллисекундах.
        cmd = ["ping", "-n", "1", "-w", str(timeout), ip]
        shell_flag = True
        python_timeout = None  # Полагаться на внутренний timeout ping.
    elif system == 'darwin':
        # На macOS ping не поддерживает параметр timeout – используем timeout через Python.
        cmd = ["ping", "-c", "1", ip]
        shell_flag = False
        python_timeout = timeout / 1000.0
    else:
        # Для Linux: -W принимает время в секундах (минимум 1 секунда).
        timeout_sec = max(1, int(timeout / 1000))
        cmd = ["ping", "-c", "1", "-W", str(timeout_sec), ip]
        shell_flag = False
        python_timeout = None

    try:
        result = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            universal_newlines=True,
            shell=shell_flag,
            timeout=python_timeout
        )
        if result.returncode == 0:
            return True, result.stdout
        else:
            return False, result.stdout
    except subprocess.TimeoutExpired:
        return False, "Ping timed out."
    except Exception as e:
        return False, f"Ошибка выполнения ping: {e}"

def detect_os(ip: str) -> Optional[str]:
    """
    Определяет операционную систему удалённого ПК по TTL в ответе ping.

    :param ip: IP-адрес для проверки
    :return: "Windows", "Linux/Unix", "Сетевое устройство (роутер, коммутатор и т. д.)" или None, если определить не удалось.
    """
    reachable, output = ping_ip(ip)
    if not reachable:
        return None

    match = re.search(r"TTL=(\d+)", output, re.IGNORECASE)
    if match:
        ttl = int(match.group(1))
        if 110 <= ttl <= 130:
            return "Windows"
        elif 50 <= ttl <= 70:
            return "Linux"
        elif ttl > 200:
            return "Сетевое устройство (роутер, коммутатор и т. д.)"
    return None

def get_pc_name(ip: str) -> Optional[str]:
    """
    Получает имя ПК по IP через обратный DNS-запрос.

    :param ip: IP-адрес
    :return: Имя ПК или None, если не удалось определить.
    """
    if not is_valid_ip(ip):
        return None

    try:
        hostname, _, _ = socket.gethostbyaddr(ip)
        return hostname
    except socket.herror:
        return None
    except Exception:
        return None
