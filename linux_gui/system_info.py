import time
import re
import logging
from typing import Dict, List, Any, Optional
from linux_gui.session_manager import SessionManager
import paramiko  # для типизации SSHClient

logger = logging.getLogger(__name__)


class SystemInfo:
    """
    Класс для получения информации о системе удалённого Linux-хоста через SSH.
    Использует SessionManager для установления и поддержки SSH-соединения.
    """

    def __init__(
        self,
        hostname: str,
        username: str = "",
        password: str = "",
        port: int = 22,
        timeout: int = 10
    ) -> None:
        """
        Инициализация параметров подключения.

        :param hostname: IP-адрес или доменное имя удалённого хоста.
        :param username: Имя пользователя для SSH.
        :param password: Пароль для SSH.
        :param port: Порт SSH (по умолчанию 22).
        :param timeout: Таймаут подключения в секундах.
        """
        self.hostname: str = hostname
        self.username: str = username
        self.password: str = password
        self.port: int = port
        self.timeout: int = timeout

    def get_client(self) -> paramiko.SSHClient:
        """
        Получает SSH-клиент из SessionManager.
        Если получена root-сессия, возвращает её.

        :return: Экземпляр paramiko.SSHClient для выполнения команд.
        """
        session = SessionManager.get_instance(self.hostname, self.username, self.password)
        client = session.get_client()
        if session.root_session:
            logger.debug("🔑 Использую root-сессию для выполнения команд")
            return session.root_session
        return client

    def get_system_info(self) -> Dict[str, Any]:
        """
        Получает информацию о системе: загрузку CPU, количество ядер, данные о RAM,
        информацию о дисках, MAC-адрес и расширенные данные (модель CPU, материнской платы, uptime).

        :return: Словарь с данными о системе.
        """
        try:
            session = SessionManager.get_instance(self.hostname, self.username, self.password)
            session.connect()  # Переподключаемся, если соединение закрыто
            client = session.get_client()
            logger.debug("✅ Успешно подключились к SSH-серверу, начинаем сбор данных...")

            cpu_usage: int = self.get_cpu_usage(client)
            logger.debug(f"✅ CPU Load: {cpu_usage}%")

            cores: int = self.get_cpu_cores(client)
            logger.debug(f"✅ Ядер: {cores}")

            mem_used, mem_total, mem_used_percent = self.get_memory_info(client)
            logger.debug(f"✅ RAM: {mem_used_percent}% использовано из {mem_total:.1f} GB")

            disks: List[Dict[str, Any]] = self.get_disks_info(client)
            logger.debug(f"✅ Дисков найдено: {len(disks)}")

            mac_address: str = self.get_mac_address(client)
            logger.debug(f"✅ MAC-адрес: {mac_address}")

            extended_info: Dict[str, Any] = self.get_extended_info(client)
            logger.debug(f"✅ CPU Model: {extended_info.get('CPU_Model')}")
            logger.debug(f"✅ Motherboard Model: {extended_info.get('Motherboard_Model')}")
            logger.debug(f"✅ Uptime: {extended_info.get('Uptime')}")

            info: Dict[str, Any] = {
                "CPU": {"Load": cpu_usage, "Cores": cores},
                "RAM": {"UsedPercent": mem_used_percent, "TotalGB": round(mem_total, 1)},
                "Disks": disks,
                "MAC_Address": mac_address,
                "CPU_Model": extended_info.get("CPU_Model", "N/A"),
                "Motherboard_Model": extended_info.get("Motherboard_Model", "N/A"),
                "Uptime": extended_info.get("Uptime", "N/A"),
            }
            logger.debug("✅ Данные о системе успешно собраны.")
            return info

        except Exception as e:
            logger.error(f"❌ Ошибка получения системной информации: {e}")
            return {"error": str(e)}

    def get_cpu_usage(self, client: paramiko.SSHClient) -> int:
        """
        Получает процент загрузки CPU путём двух последовательных чтений /proc/stat.

        :param client: SSHClient для выполнения команды.
        :return: Загруженность CPU в процентах.
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

    def get_cpu_cores(self, client: paramiko.SSHClient) -> int:
        """
        Определяет количество ядер процессора с помощью команды nproc.

        :param client: SSHClient для выполнения команды.
        :return: Количество ядер.
        """
        stdin, stdout, stderr = client.exec_command("nproc")
        cores_str = stdout.read().decode().strip()
        try:
            return int(cores_str)
        except Exception as e:
            logger.error(f"Ошибка получения количества ядер: {e}")
            return 0

    def get_memory_info(self, client: paramiko.SSHClient) -> tuple:
        """
        Получает информацию об оперативной памяти из /proc/meminfo.

        :param client: SSHClient для выполнения команды.
        :return: Кортеж (использовано_КБ, общий_объём_в_GB, процент_использования).
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

    def get_disks_info(self, client: paramiko.SSHClient) -> List[Dict[str, Any]]:
        """
        Получает информацию о дисковых разделах с помощью команды df.
        Используются разделы, отличные от tmpfs и devtmpfs.

        :param client: SSHClient для выполнения команды.
        :return: Список словарей с информацией о разделах.
        """
        disks: List[Dict[str, Any]] = []
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

            try:
                used_percent = float(parts[3].rstrip('%'))
            except ValueError:
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

    def get_mac_address(self, client: paramiko.SSHClient) -> str:
        """
        Получает MAC-адрес основного (дефолтного) сетевого интерфейса.

        :param client: SSHClient для выполнения команды.
        :return: MAC-адрес или сообщение об ошибке.
        """
        cmd_default = "ip route | grep default"
        stdin, stdout, stderr = client.exec_command(cmd_default)
        default_route = stdout.read().decode().strip()
        interface: Optional[str] = None
        if default_route:
            parts = default_route.split()
            try:
                dev_index = parts.index("dev")
                interface = parts[dev_index + 1]
            except (ValueError, IndexError):
                interface = None

        if not interface:
            cmd_list = "ls /sys/class/net"
            stdin, stdout, stderr = client.exec_command(cmd_list)
            interfaces = stdout.read().decode().strip().split()
            non_loopback = [iface for iface in interfaces if iface != "lo"]
            if non_loopback:
                interface = non_loopback[0]
            else:
                return "Интерфейсы не найдены"

        cmd_mac = f"cat /sys/class/net/{interface}/address"
        stdin, stdout, stderr = client.exec_command(cmd_mac)
        mac_address = stdout.read().decode().strip()
        return mac_address

    def get_extended_info(self, client: paramiko.SSHClient) -> Dict[str, Any]:
        """
        Получает расширенную информацию: модель процессора, материнской платы и время работы системы (uptime).

        :param client: SSHClient для выполнения команд.
        :return: Словарь с ключами CPU_Model, Motherboard_Model и Uptime.
        """
        data: Dict[str, Any] = {}

        # Проверка прав пользователя
        stdin, stdout, stderr = client.exec_command("id -u")
        user_id = stdout.read().decode().strip()
        is_root: bool = (user_id == "0")
        logger.debug(f"👤 UID пользователя: {user_id} (Root: {is_root})")

        session = SessionManager.get_instance(self.hostname, self.username, self.password)
        root_password: Optional[str] = session.root_password if session.root_password else None

        if not is_root and not root_password:
            logger.error("❌ Ошибка: отсутствует root-пароль, невозможно выполнить sudo-команды")
            return {
                "CPU_Model": "Ошибка: требуется root-доступ",
                "Motherboard_Model": "Ошибка: требуется root-доступ",
                "Uptime": "Ошибка"
            }

        def execute_command(command: str, use_sudo: bool = False, timeout: int = 5) -> Optional[str]:
            """
            Вспомогательная функция для выполнения команды на удалённом хосте.
            При необходимости используется sudo с передачей root-пароля.

            :param command: Команда для выполнения.
            :param use_sudo: Флаг использования sudo.
            :param timeout: Таймаут команды.
            :return: Результат выполнения команды или None в случае ошибки.
            """
            try:
                if use_sudo and root_password:
                    full_command = f"echo '{root_password}' | sudo -S {command}"
                else:
                    full_command = command

                logger.debug(f"🛠️ Выполняю команду: {full_command}")
                stdin, stdout, stderr = client.exec_command(full_command, timeout=timeout, get_pty=True)
                if use_sudo and root_password:
                    stdin.write(root_password + "\n")
                    stdin.flush()

                output = stdout.read().decode().strip()
                error = stderr.read().decode().strip()

                if "incorrect password" in error.lower():
                    logger.error("❌ Ошибка: неверный пароль для sudo")
                    return "Ошибка: неверный пароль root"
                if "a terminal is required" in error:
                    logger.error("❌ sudo требует терминала!")
                    return "Ошибка: sudo требует терминала"
                if "sudo: no password was provided" in error:
                    logger.error("❌ sudo не получил пароль!")
                    return "Ошибка: не передан пароль root"
                if error:
                    logger.error(f"❌ Ошибка выполнения {command}: {error}")
                    return None

                # Очищаем возможные сообщения запроса пароля
                clean_output = re.sub(r"^\s*\S+\s*\[sudo\] пароль для root:\s*", "", output, flags=re.MULTILINE)
                return clean_output if clean_output else None

            except Exception as e:
                logger.error(f"⏳ Таймаут или ошибка при выполнении {command}: {e}")
                return None

        data["CPU_Model"] = execute_command("dmidecode -s processor-version", use_sudo=not is_root) or "Ошибка: требуется root-доступ"
        data["Motherboard_Model"] = execute_command("dmidecode -s baseboard-product-name", use_sudo=not is_root) or "Ошибка: требуется root-доступ"
        data["Uptime"] = execute_command("cat /proc/uptime | awk '{print $1}'") or "Ошибка"

        # Форматируем uptime (в часах)
        if data["Uptime"] and data["Uptime"] != "Ошибка":
            try:
                uptime_seconds = float(data["Uptime"])
                data["Uptime"] = f"{round(uptime_seconds / 3600, 1)} часов"
            except ValueError:
                data["Uptime"] = "Ошибка"

        logger.debug(f"✅ Расширенная информация: {data}")
        return data
