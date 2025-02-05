#!/usr/bin/env python
import sys
import logging
import threading
import subprocess
import pythoncom
import wmi

from PySide6.QtCore import QObject, Signal, QThread, QTimer
from PySide6.QtWidgets import QApplication

# ----------------- КОД RDPWorker -----------------
class RDPWorker(QThread):
    finished = Signal(object)
    error = Signal(str)

    def __init__(self, func, *args, **kwargs):
        super().__init__()
        self.func = func
        self.args = args
        self.kwargs = kwargs

    def run(self):
        logger = logging.getLogger(__name__)
        try:
            logger.debug("Initializing COM in RDPWorker thread (MTA)")
            # Используем многопоточный режим для COM
            pythoncom.CoInitializeEx(pythoncom.COINIT_MULTITHREADED)
        except Exception as e:
            logger.exception("Ошибка инициализации COM: %s", e)
            self.error.emit(f"Ошибка инициализации COM: {str(e)}")
            return

        try:
            logger.debug("Executing function %s", self.func.__name__)
            result = self.func(*self.args, **self.kwargs)
            logger.debug("Function %s returned: %s", self.func.__name__, result)
            self.finished.emit(result)
        except Exception as e:
            logger.exception("Ошибка выполнения функции в потоке:")
            self.error.emit(f"Ошибка в потоке: {str(e)}")
        finally:
            try:
                pythoncom.CoUninitialize()
                logger.debug("COM uninitialized in RDPWorker thread")
            except Exception as e:
                logger.exception("Ошибка при вызове CoUninitialize: %s", e)

# ----------------- КОД RDPManager -----------------
class RDPManager(QObject):
    updated = Signal(dict)
    error = Signal(str)

    def __init__(self, hostname):
        super().__init__()
        self.hostname = hostname
        self.lock = threading.Lock()
        self.worker_thread = None  # Для отслеживания запущенного потока

    def refresh(self):
        self._execute_in_thread(self._safe_refresh)

    def _safe_refresh(self):
        logger = logging.getLogger(__name__)
        try:
            # Создаем подключение к WMI (без повторной инициализации COM)
            conn = wmi.WMI(
                self.hostname,
                impersonation_level="impersonate",
                authentication_level="pktPrivacy"
            )
            with self.lock:
                status = {
                    'enabled': self._get_rdp_status(conn),
                    'port': self._get_rdp_port(conn),
                    'users': self._get_rdp_users(conn)
                }
                return status
        except Exception as e:
            self.error.emit(f"Ошибка обновления: {str(e)}")
            return None

    def _get_rdp_status(self, conn):
        try:
            reg = conn.StdRegProv
            key = r"SYSTEM\CurrentControlSet\Control\Terminal Server"
            result, deny_ts = reg.GetDWORDValue(0x80000002, key, "fDenyTSConnections")
            return deny_ts == 0
        except Exception as e:
            self.error.emit(f"Ошибка получения статуса RDP: {str(e)}")
            return False

    def _get_rdp_port(self, conn):
        try:
            reg = conn.StdRegProv
            key = r"SYSTEM\CurrentControlSet\Control\Terminal Server\WinStations\RDP-Tcp"
            result, port = reg.GetDWORDValue(0x80000002, key, "PortNumber")
            return port
        except Exception as e:
            self.error.emit(f"Ошибка получения порта: {str(e)}")
            return 3389

    def _get_rdp_users(self, conn):
        try:
            group = self._get_rdp_group(conn)
            if group is None:
                self.error.emit("Группа RDP не найдена")
                return []
            users = group.associators(wmi_result_class="Win32_UserAccount")
            return [u.Name for u in users] if users else []
        except Exception as e:
            self.error.emit(f"Ошибка получения пользователей RDP: {str(e)}")
            return []

    def _get_rdp_group(self, conn):
        try:
            # Локализованные имена группы
            group_names = [
                "Remote Desktop Users",
                "Пользователи удаленного рабочего стола",
                "Remotedesktopbenutzer"  # Немецкий
            ]
            for name in group_names:
                groups = conn.Win32_Group(Name=name)
                if groups:
                    return groups[0]
            group = conn.Win32_Group(SID='S-1-5-32-555')
            if group:
                return group[0]
            raise Exception("Группа RDP не найдена")
        except Exception as e:
            self.error.emit(f"Ошибка поиска группы: {str(e)}")
            raise

    def update_settings(self, enabled=None, port=None, users=None):
        self._execute_in_thread(self._safe_update_settings, enabled, port, users)

    def _safe_update_settings(self, enabled, port, users):
        try:
            conn = wmi.WMI(
                self.hostname,
                impersonation_level="impersonate",
                authentication_level="pktPrivacy"
            )
            with self.lock:
                if enabled is not None:
                    self._set_rdp_status(conn, enabled)
                if port is not None:
                    self._set_rdp_port(conn, port)
                if users is not None:
                    self._sync_rdp_users(conn, users)
                status = {
                    'enabled': self._get_rdp_status(conn),
                    'port': self._get_rdp_port(conn),
                    'users': self._get_rdp_users(conn)
                }
                return status
        except Exception as e:
            self.error.emit(f"Ошибка обновления настроек: {str(e)}")
            return None

    def _set_rdp_status(self, conn, enabled):
        try:
            value = 0 if enabled else 1
            reg = conn.StdRegProv
            key = r"SYSTEM\CurrentControlSet\Control\Terminal Server"
            reg.SetDWORDValue(0x80000002, key, "fDenyTSConnections", value)
            # На время тестирования отключаем изменение правил брандмауэра
            # self._manage_firewall_rule(enabled)
        except Exception as e:
            self.error.emit(f"Ошибка изменения статуса RDP: {str(e)}")

    def _set_rdp_port(self, conn, port):
        try:
            reg = conn.StdRegProv
            key = r"SYSTEM\CurrentControlSet\Control\Terminal Server\WinStations\RDP-Tcp"
            reg.SetDWORDValue(0x80000002, key, "PortNumber", int(port))
            self._update_firewall_port(port)
        except Exception as e:
            self.error.emit(f"Ошибка изменения порта: {str(e)}")

    def _sync_rdp_users(self, conn, users):
        try:
            current_users = set(self._get_rdp_users(conn))
            new_users = set(users)
            valid_users = []
            for user in new_users:
                if conn.Win32_UserAccount(Name=user):
                    valid_users.append(user)
                else:
                    self.error.emit(f"Пользователь {user} не существует")
            group = self._get_rdp_group(conn)
            for user in set(valid_users) - current_users:
                self._run_wmic_command(f'net localgroup "{group.Name}" {user} /add')
            for user in current_users - set(valid_users):
                self._run_wmic_command(f'net localgroup "{group.Name}" {user} /delete')
        except Exception as e:
            self.error.emit(f"Ошибка синхронизации пользователей: {str(e)}")

    def _run_wmic_command(self, command):
        try:
            result = subprocess.run(
                ['powershell', '-Command', f'Start-Process cmd -ArgumentList "/c {command}" -Verb RunAs'],
                check=True,
                timeout=15,
                capture_output=True,
                text=True
            )
            if result.returncode != 0:
                self.error.emit(f"Ошибка выполнения: {result.stdout.strip()}")
                return False
            return True
        except subprocess.TimeoutExpired:
            self.error.emit("Таймаут выполнения команды")
            return False
        except Exception as e:
            self.error.emit(f"Неожиданная ошибка: {str(e)}")
            return False

    def _manage_firewall_rule(self, enable):
        try:
            subprocess.run(
                ['powershell', '-Command', 'Enable-NetFirewallRule -DisplayName "Remote Desktop*"'],
                check=True,
                timeout=10
            )
        except subprocess.TimeoutExpired:
            self.error.emit("Таймаут изменения правил брандмауэра")
        except Exception as e:
            self.error.emit(f"Ошибка брандмауэра: {str(e)}")

    def _update_firewall_port(self, port):
        try:
            subprocess.run(
                ['powershell', '-Command', f'Set-NetFirewallRule -DisplayName "Remote Desktop*" -LocalPort {port}'],
                check=True,
                timeout=10
            )
        except subprocess.TimeoutExpired:
            self.error.emit("Таймаут обновления порта брандмауэра")
        except Exception as e:
            self.error.emit(f"Ошибка обновления порта: {str(e)}")

    def _execute_in_thread(self, func, *args, **kwargs):
        self.worker_thread = RDPWorker(func, *args, **kwargs)
        self.worker_thread.finished.connect(self._handle_result)
        self.worker_thread.error.connect(self.error.emit)
        self.worker_thread.start()

    def _handle_result(self, result):
        if result is None:
            self.error.emit("Не удалось получить данные RDP")
        else:
            self.updated.emit(result)

# ----------------- MAIN: ТЕСТЕР -----------------
if __name__ == "__main__":
    # Настройка логирования (DEBUG для подробного вывода)
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # Создаем Qt-приложение (нужно для работы QThread и сигналов)
    app = QApplication(sys.argv)

    # Используем указанный IP для тестирования
    TEST_IP = "10.254.44.36"
    manager = RDPManager(TEST_IP)

    def print_update(result):
        print("Update result:", result)
        # Для теста попробуем изменить настройки:
        new_enabled = not result.get("enabled", False)
        print("Теперь обновляем настройки (меняем состояние RDP на:", new_enabled,")")
        manager.update_settings(enabled=new_enabled)

    def print_error(error_message):
        print("Error:", error_message)

    # Подключаем сигналы для вывода результатов
    manager.updated.connect(print_update)
    manager.error.connect(print_error)

    # Запускаем первоначальное обновление через 1 секунду (чтобы приложение полностью инициализировалось)
    QTimer.singleShot(1000, manager.refresh)

    # Запускаем главный цикл Qt-приложения
    sys.exit(app.exec())
