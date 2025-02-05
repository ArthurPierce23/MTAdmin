import re
import subprocess
import platform
import socket
from typing import Optional, Tuple


def is_potential_ip(text: str) -> bool:
    """Проверяет, состоит ли строка только из цифр и точек (потенциальный IP)."""
    return bool(re.match(r'^[\d.]+$', text))


def is_partial_ip(text: str) -> bool:
    """Проверяет, введён ли частичный IP (например, '192.168.')."""
    return bool(re.match(r'^(\d{1,3}\.){0,3}\d{0,3}$', text))


def is_valid_ip(ip: str) -> bool:
    """
    Проверяет, что строка соответствует формату A.B.C.D, где каждое число от 0 до 255.
    """
    pattern = re.compile(r'^(\d{1,3}\.){3}\d{1,3}$')
    if not pattern.match(ip):
        return False
    parts = ip.split('.')
    return all(0 <= int(part) <= 255 for part in parts)


def is_valid_hostname(hostname: str) -> bool:
    """
    Проверяет, является ли строка допустимым именем ПК (буквы, цифры, дефис, от 1 до 63 символов).
    """
    return bool(re.match(r'^[a-zA-Z0-9]([a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?$', hostname))


def is_valid_input(text: str) -> bool:
    """
    Проверяет, корректен ли ввод – либо валидный IP, либо валидное имя ПК, либо частичный IP.
    """
    return is_valid_ip(text) or is_valid_hostname(text) or is_partial_ip(text)


def ping_ip(ip: str, timeout: int = 1000) -> Tuple[bool, str]:
    """
    Выполняет ping заданного IP-адреса.

    :param ip: IP-адрес для проверки
    :param timeout: таймаут (в мс для Windows, в секундах для Linux)
    :return: Кортеж (доступен ли хост, вывод команды ping)
    """
    system = platform.system().lower()
    if system == 'windows':
        cmd = f"ping -n 1 -w {timeout} {ip}"
        shell_flag = True
    else:
        timeout_sec = max(1, int(timeout / 1000))
        cmd = ["ping", "-c", "1", "-W", str(timeout_sec), ip]
        shell_flag = False

    try:
        output = subprocess.check_output(cmd, stderr=subprocess.STDOUT, universal_newlines=True, shell=shell_flag)
        return True, output
    except subprocess.CalledProcessError as e:
        return False, e.output
    except UnicodeDecodeError:
        return False, "Ошибка декодирования вывода ping."


def detect_os(ip: str) -> Optional[str]:
    """
    Определяет операционную систему удалённого ПК по TTL в ответе ping.

    :param ip: IP-адрес для проверки
    :return: "Windows", "Linux/Unix" или None, если определить не удалось.
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
            return "Linux/Unix"
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

    if not ping_ip(ip)[0]:
        return None  # Хост недоступен, нет смысла делать обратный DNS-запрос.

    try:
        hostname, _, _ = socket.gethostbyaddr(ip)
        return hostname
    except socket.herror:
        return None
