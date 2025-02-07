# linux_gui/system_info.py

import time
import re
import logging
from linux_gui.session_manager import SessionManager

logger = logging.getLogger(__name__)


class SystemInfo:
    """
    Класс для получения информации о системе удалённого Linux-хоста через SSH.
    Использует SessionManager для установления и поддержки SSH-соединения.

    Методы:
      - get_system_info(): возвращает словарь с данными по CPU, RAM и дискам.
    """

    def __init__(self, hostname: str, username: str = "", password: str = "", port: int = 22, timeout: int = 10):
        """
        Инициализация параметров подключения.

        :param hostname: IP-адрес или доменное имя удалённого хоста.
        :param username: Имя пользователя для SSH (по умолчанию пустая строка).
        :param password: Пароль для SSH (по умолчанию пустая строка).
        :param port: Порт SSH (по умолчанию 22).
        :param timeout: Таймаут подключения (в секундах).
        """
        self.hostname = hostname
        self.username = username
        self.password = password
        self.port = port
        self.timeout = timeout

    def get_client(self):
        """
        Получает клиентское SSH-соединение через SessionManager.
        """
        return SessionManager.get_instance(self.hostname, self.username, self.password).get_client()

    def get_system_info(self) -> dict:
        """
        Получает информацию о системе:
          - CPU: процент загрузки и количество ядер.
          - RAM: процент использования и общий объём в GB.
          - Disks: список разделов с информацией о размере, свободном месте и использовании.

        :return: Словарь с ключами "CPU", "RAM" и "Disks", либо с ключом "error" в случае ошибки.
        """
        try:
            client = self.get_client()

            cpu_usage = self.get_cpu_usage(client)
            cores = self.get_cpu_cores(client)
            mem_used, mem_total, mem_used_percent = self.get_memory_info(client)
            disks = self.get_disks_info(client)

            info = {
                "CPU": {"Load": cpu_usage, "Cores": cores},
                "RAM": {"UsedPercent": mem_used_percent, "TotalGB": round(mem_total, 1)},
                "Disks": disks,
            }
            return info

        except Exception as e:
            logger.error(f"Ошибка получения системной информации: {e}")
            return {"error": str(e)}
        # Не закрываем соединение здесь, так как SessionManager управляет жизненным циклом сессии

    def get_cpu_usage(self, client) -> int:
        """
        Получает процент загрузки CPU путём двух последовательных чтений /proc/stat с небольшим интервалом.

        :param client: SSHClient из SessionManager.
        :return: Загруженность CPU в процентах (целое число).
        """
        cmd = "cat /proc/stat | grep '^cpu '"
        # Первое чтение
        stdin, stdout, stderr = client.exec_command(cmd)
        first_line = stdout.read().decode()
        values = first_line.strip().split()
        if len(values) < 5:
            return 0
        total1 = sum(int(val) for val in values[1:])
        idle1 = int(values[4])

        time.sleep(0.1)

        # Второе чтение
        stdin, stdout, stderr = client.exec_command(cmd)
        second_line = stdout.read().decode()
        values2 = second_line.strip().split()
        total2 = sum(int(val) for val in values2[1:])
        idle2 = int(values2[4])

        delta_total = total2 - total1
        delta_idle = idle2 - idle1
        if delta_total == 0:
            return 0
        usage = 100.0 * (delta_total - delta_idle) / delta_total
        return round(usage)

    def get_cpu_cores(self, client) -> int:
        """
        Определяет количество ядер процессора с помощью команды nproc.

        :param client: SSHClient из SessionManager.
        :return: Количество ядер.
        """
        stdin, stdout, stderr = client.exec_command("nproc")
        cores_str = stdout.read().decode().strip()
        try:
            return int(cores_str)
        except Exception as e:
            logger.error(f"Ошибка получения количества ядер: {e}")
            return 0

    def get_memory_info(self, client) -> tuple:
        """
        Получает информацию об оперативной памяти из /proc/meminfo.

        :param client: SSHClient из SessionManager.
        :return: Кортеж (использовано_КБ, общий_объём_в_GB, процент_использования)
        """
        cmd = "cat /proc/meminfo"
        stdin, stdout, stderr = client.exec_command(cmd)
        meminfo = stdout.read().decode()

        total_match = re.search(r'^MemTotal:\s+(\d+)\s+kB', meminfo, re.MULTILINE)
        avail_match = re.search(r'^MemAvailable:\s+(\d+)\s+kB', meminfo, re.MULTILINE)
        if total_match and avail_match:
            total_kb = int(total_match.group(1))
            avail_kb = int(avail_match.group(1))
            used_kb = total_kb - avail_kb
            used_percent = 100 * used_kb / total_kb
            total_gb = total_kb / (1024 * 1024)
            return used_kb, total_gb, round(used_percent)
        else:
            return 0, 0, 0

    def get_disks_info(self, client) -> list:
        """
        Получает информацию о дисковых разделах с помощью команды df.

        Используются только разделы, отличные от tmpfs и devtmpfs.

        :param client: SSHClient из SessionManager.
        :return: Список словарей, каждый из которых содержит:
                 - "Letter": точка монтирования (например, "/")
                 - "TotalGB": общий объём раздела в GB
                 - "FreeGB": свободное место в GB
                 - "UsedPercent": процент использования раздела
        """
        disks = []
        cmd = "df -B1 --output=target,size,avail,pcent -x tmpfs -x devtmpfs"
        stdin, stdout, stderr = client.exec_command(cmd)
        output = stdout.read().decode()
        lines = output.splitlines()
        if not lines or len(lines) < 2:
            return disks

        # Пропускаем заголовок
        for line in lines[1:]:
            if not line.strip():
                continue
            parts = line.split()
            if len(parts) < 4:
                continue

            mount_point = parts[0]
            try:
                size_bytes = int(parts[1])
                avail_bytes = int(parts[2])
            except ValueError:
                continue

            used_percent_str = parts[3]
            if used_percent_str.endswith('%'):
                try:
                    used_percent = float(used_percent_str[:-1])
                except ValueError:
                    used_percent = 0
            else:
                used_percent = 0

            total_gb = size_bytes / (1024 ** 3)
            free_gb = avail_bytes / (1024 ** 3)

            disk_info = {
                "Letter": mount_point,
                "TotalGB": total_gb,
                "FreeGB": free_gb,
                "UsedPercent": used_percent,
            }
            disks.append(disk_info)
        return disks
