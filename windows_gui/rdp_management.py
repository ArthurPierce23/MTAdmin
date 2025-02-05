from pypsexec.client import Client
import threading
import logging

logger = logging.getLogger(__name__)

class RDPManagerSync:
    def __init__(self, hostname: str):
        self.hostname = hostname
        self.lock = threading.Lock()
        self.refresh_lock = threading.Lock()  # Отдельный лок для refresh()

    def run_remote_command(self, command: str) -> str:
        """Выполняет команду на удалённом ПК через PsExec и защищает от зависаний."""
        print(f"🚀 Выполняю команду на {self.hostname}: {command}")

        client = None
        try:
            client = Client(self.hostname, encrypt=False)
            client.connect()
            client.create_service()

            stdout, stderr, exit_code = client.run_executable("cmd.exe", arguments=f'/c {command}')

            return stdout.decode("cp866").strip() if exit_code == 0 else f"Ошибка: {stderr.decode('cp866').strip()}"

        except Exception as e:
            print(f"❌ Ошибка выполнения команды: {e}")
            return f"Ошибка: {e}"

        finally:
            if client:
                client.remove_service()
                client.disconnect()
                print(f"🔌 Соединение с {self.hostname} закрыто")

    def refresh(self) -> dict:
        """Получает текущие настройки RDP, защищая вызов локом."""
        print(f"🔄 refresh() вызван для {self.hostname}")

        try:
            with self.refresh_lock:
                status = {
                    "enabled": self._get_rdp_status(),
                    "port": self._get_rdp_port(),
                    "users": self._get_rdp_users(),
                }

            print(f"✅ refresh() завершён для {self.hostname}: {status}")
            return status

        except Exception as e:
            print(f"❌ Ошибка в refresh() для {self.hostname}: {e}")
            logger.exception("Ошибка получения данных RDP")
            raise e

    def update_settings(self, enabled=None, port=None, users=None) -> dict:
        """Изменяет настройки RDP."""
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
            logger.exception("Ошибка обновления настроек RDP")
            raise e

    def _get_rdp_status(self) -> bool:
        """Проверяет, включен ли RDP, парся значение реестрового ключа."""
        output = self.run_remote_command(
            'reg query "HKLM\\SYSTEM\\CurrentControlSet\\Control\\Terminal Server" /v fDenyTSConnections'
        )
        print(f"Вывод проверки RDP: {output}")
        # Ищем строку с именем ключа
        for line in output.splitlines():
            if "fDenyTSConnections" in line:
                # Ожидается формат:
                # fDenyTSConnections    REG_DWORD    0x0  или  0x1
                tokens = line.split()
                if len(tokens) >= 3:
                    value = tokens[-1].lower()
                    # Если значение равно 0x0, значит RDP включён
                    return value == "0x0"
        # Если не удалось распарсить, считаем, что RDP выключен
        return False

    def _get_rdp_port(self) -> int:
        """Получает порт RDP."""
        output = self.run_remote_command(
            'reg query "HKLM\\SYSTEM\\CurrentControlSet\\Control\\Terminal Server\\WinStations\\RDP-Tcp" /v PortNumber'
        )
        for line in output.splitlines():
            if "PortNumber" in line:
                return int(line.split()[-1], 16)  # Значение в hex
        raise Exception("Не удалось определить порт RDP")

    def _get_rdp_users(self) -> list:
        """Получает список пользователей RDP, убирая лишний текст."""
        possible_group_names = ["Remote Desktop Users", "Пользователи удаленного рабочего стола"]

        for group_name in possible_group_names:
            output = self.run_remote_command(f'net localgroup "{group_name}"')
            users = []
            is_users_section = False
            for line in output.splitlines():
                line = line.strip()

                # Начало/конец списка пользователей
                if "-----" in line:
                    is_users_section = not is_users_section
                    continue

                # Список пользователей
                if is_users_section and line and "Команда выполнена успешно." not in line:
                    users.append(line)

            if users:
                self.rdp_group_name = group_name
                return users

        raise Exception("Группа RDP не найдена. Проверьте локализацию системы.")

    def add_user(self, username: str):
        """Добавляет пользователя в группу RDP без удаления остальных."""
        if not hasattr(self, "rdp_group_name"):
            self._get_rdp_users()  # Определяем правильное название группы

        command = f'net localgroup "{self.rdp_group_name}" "{username}" /add'
        result = self.run_remote_command(command)

        logger.info(f"Добавление пользователя {username}: {result}")
        return result

    def _set_rdp_status(self, enable: bool):
        """Включает или выключает RDP и перезапускает службу для применения изменений."""
        # fDenyTSConnections = 0 -> RDP включён, 1 -> RDP выключен
        value = "0" if enable else "1"
        cmd = f'reg add "HKLM\\SYSTEM\\CurrentControlSet\\Control\\Terminal Server" /v fDenyTSConnections /t REG_DWORD /d {value} /f'
        result = self.run_remote_command(cmd)
        print(f"Команда установки RDP статуса: {cmd} -> {result}")

        firewall_cmd = "Enable-NetFirewallRule -DisplayName 'Remote Desktop*'" if enable else "Disable-NetFirewallRule -DisplayName 'Remote Desktop*'"
        fw_result = self.run_remote_command(f'powershell -Command "{firewall_cmd}"')
        print(f"Команда настройки фаервола: {firewall_cmd} -> {fw_result}")

        # Перезапуск службы для применения изменений
        svc_cmd = 'net stop TermService && net start TermService'
        svc_result = self.run_remote_command(svc_cmd)
        print(f"Перезапуск службы RDP: {svc_cmd} -> {svc_result}")

    def _set_rdp_port(self, port: int):
        """Изменяет порт RDP."""
        self.run_remote_command(
            f'reg add "HKLM\\SYSTEM\\CurrentControlSet\\Control\\Terminal Server\\WinStations\\RDP-Tcp" /v PortNumber /t REG_DWORD /d {port} /f'
        )
        self.run_remote_command(
            f'powershell -Command "Set-NetFirewallRule -DisplayName \'Remote Desktop*\' -LocalPort {port}"'
        )

    def _set_rdp_users(self, users: list):
        """Добавляет или удаляет пользователей из RDP-группы с учетом локализации."""
        if not hasattr(self, "rdp_group_name"):
            self._get_rdp_users()  # Определяем правильное название группы

        current_users = set(self._get_rdp_users())
        new_users = set(users)

        for user in new_users - current_users:
            self.run_remote_command(f'net localgroup "{self.rdp_group_name}" {user} /add')

        for user in current_users - new_users:
            self.run_remote_command(f'net localgroup "{self.rdp_group_name}" {user} /delete')
