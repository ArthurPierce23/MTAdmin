from pypsexec.client import Client
import threading
import logging
from typing import Any, Dict, List

logger = logging.getLogger(__name__)


class RDPManagerSync:
    """
    Класс для управления настройками RDP на удалённом ПК через PsExec.

    Позволяет выполнять удалённые команды, получать статус RDP,
    порт, список пользователей, а также изменять настройки RDP.
    """

    def __init__(self, hostname: str) -> None:
        """
        Инициализация менеджера RDP.

        :param hostname: Имя хоста или IP-адрес удалённого ПК.
        """
        self.hostname: str = hostname
        self.lock = threading.Lock()
        self.refresh_lock = threading.Lock()  # Отдельный лок для метода refresh()

    def run_remote_command(self, command: str) -> str:
        """
        Выполняет команду на удалённом ПК через PsExec и защищает от зависаний.

        :param command: Команда, которую необходимо выполнить на удалённом ПК.
        :return: Результат выполнения команды (stdout, либо сообщение об ошибке).
        """
        logger.debug(f"🚀 Выполняю команду на {self.hostname}: {command}")
        client = None
        try:
            client = Client(self.hostname, encrypt=False)
            client.connect()
            client.create_service()

            stdout, stderr, exit_code = client.run_executable("cmd.exe", arguments=f'/c {command}')

            if exit_code == 0:
                result = stdout.decode("cp866").strip()
                logger.debug(f"✅ Результат команды: {result}")
                return result
            else:
                error_result = stderr.decode("cp866").strip()
                logger.error(f"❌ Ошибка выполнения команды: {error_result}")
                return f"Ошибка: {error_result}"
        except Exception as e:
            logger.exception(f"❌ Ошибка выполнения команды: {e}")
            return f"Ошибка: {e}"
        finally:
            if client:
                try:
                    client.remove_service()
                except Exception as rem_err:
                    logger.error(f"❌ Ошибка при удалении службы: {rem_err}")
                client.disconnect()
                logger.debug(f"🔌 Соединение с {self.hostname} закрыто")

    def refresh(self) -> Dict[str, Any]:
        """
        Получает текущие настройки RDP, защищая вызов локом.

        :return: Словарь со статусом RDP, портом и списком пользователей.
        :raises Exception: При ошибке получения данных.
        """
        logger.debug(f"🔄 refresh() вызван для {self.hostname}")
        try:
            with self.refresh_lock:
                status: Dict[str, Any] = {
                    "enabled": self._get_rdp_status(),
                    "port": self._get_rdp_port(),
                    "users": self._get_rdp_users(),
                }
            logger.debug(f"✅ refresh() завершён для {self.hostname}: {status}")
            return status
        except Exception as e:
            logger.exception(f"❌ Ошибка в refresh() для {self.hostname}: {e}")
            raise

    def update_settings(self, enabled: bool = None, port: int = None, users: List[str] = None) -> Dict[str, Any]:
        """
        Изменяет настройки RDP.

        :param enabled: True для включения RDP, False для отключения.
        :param port: Новый порт для RDP.
        :param users: Список пользователей, которые должны быть членами RDP-группы.
        :return: Обновлённые настройки RDP (результат refresh()).
        :raises Exception: При ошибке обновления настроек.
        """
        try:
            with self.lock:
                if enabled is not None:
                    self._set_rdp_status(enabled)
                if port is not None:
                    self._set_rdp_port(port)
                if users is not None:
                    self._set_rdp_users(users)
                return self.refresh()
        except Exception as e:
            logger.exception(f"Ошибка обновления настроек RDP: {e}")
            raise

    def _get_rdp_status(self) -> bool:
        """
        Проверяет, включен ли RDP, парся значение реестрового ключа.

        :return: True, если RDP включён, иначе False.
        """
        output = self.run_remote_command(
            'reg query "HKLM\\SYSTEM\\CurrentControlSet\\Control\\Terminal Server" /v fDenyTSConnections'
        )
        logger.debug(f"Вывод проверки RDP: {output}")
        for line in output.splitlines():
            if "fDenyTSConnections" in line:
                tokens = line.split()
                if len(tokens) >= 3:
                    value = tokens[-1].lower()
                    # Значение 0x0 означает, что RDP включён
                    return value == "0x0"
        # Если парсинг не удался, считаем, что RDP выключен
        return False

    def _get_rdp_port(self) -> int:
        """
        Получает порт RDP.

        :return: Порт RDP (в десятичном виде).
        :raises Exception: Если не удалось определить порт.
        """
        output = self.run_remote_command(
            'reg query "HKLM\\SYSTEM\\CurrentControlSet\\Control\\Terminal Server\\WinStations\\RDP-Tcp" /v PortNumber'
        )
        for line in output.splitlines():
            if "PortNumber" in line:
                port_hex = line.split()[-1]
                port_dec = int(port_hex, 16)
                logger.debug(f"Определён порт RDP: {port_dec}")
                return port_dec
        raise Exception("Не удалось определить порт RDP")

    def _get_rdp_users(self) -> List[str]:
        """
        Получает список пользователей RDP, учитывая возможное различие формата вывода.

        :return: Список пользователей RDP.
        :raises Exception: Если не удалось получить список.
        """
        possible_group_names = ["Remote Desktop Users", "Пользователи удаленного рабочего стола"]

        for group_name in possible_group_names:
            output = self.run_remote_command(f'net localgroup "{group_name}"')
            if "Указанная локальная группа не существует" in output:
                logger.debug(f"Группа {group_name} не существует, пробую следующий вариант.")
                continue

            users: List[str] = []
            in_users_section = False
            for line in output.splitlines():
                line = line.strip()
                if line.startswith("Члены"):
                    in_users_section = True
                    continue
                if in_users_section and set(line) == {"-"}:
                    continue
                if in_users_section and "Команда выполнена успешно" in line:
                    break
                if in_users_section and line:
                    users.append(line)

            if users or "Команда выполнена успешно" in output:
                self.rdp_group_name = group_name
                logger.debug(f"Получены пользователи RDP из группы {group_name}: {users}")
                return users

        raise Exception(
            "Не удалось получить список пользователей RDP. Проверьте локализацию системы или права доступа.")

    def add_user(self, username: str) -> str:
        """
        Добавляет пользователя в группу RDP без удаления остальных.

        :param username: Имя пользователя для добавления.
        :return: Результат выполнения команды.
        """
        if not hasattr(self, "rdp_group_name"):
            self._get_rdp_users()  # Определяем правильное название группы

        command = f'net localgroup "{self.rdp_group_name}" "{username}" /add'
        result = self.run_remote_command(command)
        logger.info(f"Добавление пользователя {username}: {result}")
        return result

    def _set_rdp_status(self, enable: bool) -> None:
        """
        Включает или выключает RDP и перезапускает службу для применения изменений.

        :param enable: True для включения RDP, False для отключения.
        """
        # fDenyTSConnections: 0 - RDP включён, 1 - RDP выключен
        value = "0" if enable else "1"
        cmd = f'reg add "HKLM\\SYSTEM\\CurrentControlSet\\Control\\Terminal Server" /v fDenyTSConnections /t REG_DWORD /d {value} /f'
        result = self.run_remote_command(cmd)
        logger.debug(f"Команда установки RDP статуса: {cmd} -> {result}")

        firewall_cmd = "Enable-NetFirewallRule -DisplayName 'Remote Desktop*'" if enable else "Disable-NetFirewallRule -DisplayName 'Remote Desktop*'"
        fw_result = self.run_remote_command(f'powershell -Command "{firewall_cmd}"')
        logger.debug(f"Команда настройки фаервола: {firewall_cmd} -> {fw_result}")

        svc_cmd = 'net stop TermService && net start TermService'
        svc_result = self.run_remote_command(svc_cmd)
        logger.debug(f"Перезапуск службы RDP: {svc_cmd} -> {svc_result}")

    def _set_rdp_port(self, port: int) -> None:
        """
        Изменяет порт RDP, обновляет правило брандмауэра и перезапускает службу,
        чтобы новый порт начал действовать.

        :param port: Новый порт для RDP.
        """
        # Изменяем порт в реестре
        reg_cmd = (
            f'reg add "HKLM\\SYSTEM\\CurrentControlSet\\Control\\Terminal Server\\WinStations\\RDP-Tcp" '
            f'/v PortNumber /t REG_DWORD /d {port} /f'
        )
        reg_result = self.run_remote_command(reg_cmd)
        logger.debug(f"Изменение порта в реестре выполнено: {reg_result}")

        # Обновляем правило брандмауэра для RDP.
        # Если правило с шаблоном "Remote Desktop*" уже существует, меняем для него порт,
        # иначе создаём новое правило для нового порта.
        fw_cmd = (
            'powershell -Command "'
            '$rule = Get-NetFirewallRule -DisplayName \'Remote Desktop*\' -ErrorAction SilentlyContinue;'
            'if ($rule) {'
            f'    $rule | Set-NetFirewallRule -LocalPort {port}'
            '} else {'
            f'    New-NetFirewallRule -Name \'RDP_{port}\' -DisplayName \'Remote Desktop (Port {port})\' '
            f'-Direction Inbound -Protocol TCP -LocalPort {port} -Action Allow'
            '}"'
        )
        fw_result = self.run_remote_command(fw_cmd)
        logger.debug(f"Обновление/создание правила брандмауэра выполнено: {fw_result}")

        # Перезапускаем службу RDP (TermService), чтобы изменения вступили в силу
        svc_cmd = 'net stop TermService && net start TermService'
        svc_result = self.run_remote_command(svc_cmd)
        logger.debug(f"Перезапуск службы RDP выполнен: {svc_result}")

        logger.debug(f"Порт RDP изменён на {port}, обновлены правила брандмауэра и перезапущены службы.")

    def _set_rdp_users(self, users: List[str]) -> None:
        """
        Добавляет или удаляет пользователей из RDP-группы с учетом локализации.

        :param users: Новый список пользователей для RDP.
        """
        if not hasattr(self, "rdp_group_name"):
            self._get_rdp_users()  # Определяем правильное название группы

        current_users = set(self._get_rdp_users())
        new_users = set(users)

        for user in new_users - current_users:
            self.run_remote_command(f'net localgroup "{self.rdp_group_name}" {user} /add')
            logger.info(f"Пользователь {user} добавлен в группу {self.rdp_group_name}")

        for user in current_users - new_users:
            self.run_remote_command(f'net localgroup "{self.rdp_group_name}" {user} /delete')
            logger.info(f"Пользователь {user} удалён из группы {self.rdp_group_name}")
