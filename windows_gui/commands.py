import subprocess
import platform
import logging
from notifications import Notification
import winreg

logger = logging.getLogger(__name__)


def get_rdp_port(ip: str) -> int:
    """
    Получает порт RDP удалённого компьютера через реестр.
    По умолчанию возвращает 3389.
    """
    try:
        # Подключаемся к реестру удалённого компьютера
        with winreg.ConnectRegistry(ip, winreg.HKEY_LOCAL_MACHINE) as reg:
            # Путь указывается относительно корня HKEY_LOCAL_MACHINE
            reg_path = r"System\CurrentControlSet\Control\Terminal Server\WinStations\RDP-Tcp"
            with winreg.OpenKey(reg, reg_path) as key:
                port, _ = winreg.QueryValueEx(key, "PortNumber")
                return port
    except Exception as e:
        logger.warning("Не удалось получить порт RDP, используется 3389. Ошибка: %s", e)
        return 3389



def run_powershell(hostname: str) -> None:
    """
    Открывает удалённый PowerShell сессией Enter-PSSession на удалённом ПК.
    Команда запускается через cmd, чтобы открыть новое окно PowerShell с указанной командой.
    """
    if platform.system() != "Windows":
        Notification("Функция доступна только на Windows", "error").show_notification()
        return

    # Формируем команду для запуска PowerShell с переходом в удалённую сессию.
    command = f'cmd /c start powershell -NoExit -Command "Enter-PSSession -ComputerName {hostname}"'
    execute_command(command, "PowerShell открыт")


def open_compmgmt(hostname: str) -> None:
    """
    Открывает оснастку управления компьютером удалённого ПК.
    """
    if platform.system() != "Windows":
        Notification("Функция доступна только на Windows", "error").show_notification()
        return

    command = f"compmgmt.msc /computer:{hostname}"
    execute_command(command, "Открыто управление компьютером")


def open_rdp(ip: str) -> None:
    """
    Подключается к удалённому рабочему столу (RDP), учитывая нестандартный порт.
    """
    if platform.system() != "Windows":
        Notification("Функция доступна только на Windows", "error").show_notification()
        return

    port = get_rdp_port(ip)
    command = f"mstsc /v:{ip}:{port}"
    execute_command(command, f"Запущен RDP-клиент (порт {port})")


def open_shadow_rdp(ip: str) -> None:
    """
    Shadow RDP: определяет активную сессию и подключается к ней.
    Используется команда qwinsta, вывод которой на русской ОС содержит "Активно".
    """
    if platform.system() != "Windows":
        Notification("Функция доступна только на Windows", "error").show_notification()
        return

    try:
        result = subprocess.run(
            ["qwinsta", f"/server:{ip}"],
            capture_output=True,
            text=True,
            encoding="cp866"
        )
        logger.debug("qwinsta output: %s", result.stdout)
        lines = result.stdout.splitlines()
        session_id = None

        # Пропускаем первую строку (заголовок) и ищем строку с активной сессией.
        for line in lines[1:]:
            parts = line.split()
            if "Активно" in parts:
                # Ожидаем, что ID находится под индексом 2 (при корректном формате строки)
                if len(parts) >= 3:
                    session_id = parts[2]
                    break

        if session_id:
            command = f"mstsc /shadow:{session_id} /v:{ip} /control"
            execute_command(command, f"Shadow RDP запущен (Сессия {session_id})")
        else:
            Notification("Нет активных сессий для Shadow RDP", "warning").show_notification()

    except Exception as e:
        logger.exception("Ошибка при запуске Shadow RDP")
        Notification(f"Ошибка при запуске Shadow RDP: {e}", "error").show_notification()


def open_c_drive(ip: str) -> None:
    """
    Открывает общий ресурс C$ удалённого ПК в проводнике.
    """
    if platform.system() != "Windows":
        Notification("Функция доступна только на Windows", "error").show_notification()
        return

    command = f"explorer \\\\{ip}\\C$"
    execute_command(command, "Открыт доступ к C$")


def open_cmd(hostname: str) -> None:
    """
    Открывает локальный CMD и сразу подключается к удалённому ПК с помощью winrs.
    Используется ключ /k, чтобы окно оставалось открытым.
    """
    if platform.system() != "Windows":
        Notification("Функция доступна только на Windows", "error").show_notification()
        return

    command = f'cmd /c start cmd /k "winrs -r:{hostname} cmd"'
    execute_command(command, "CMD запущен и подключен к удалённому ПК")


def execute_command(command: str, success_message: str) -> None:
    """
    Запускает указанную команду через subprocess.Popen и отображает уведомление об успехе.

    :param command: Команда для выполнения.
    :param success_message: Сообщение об успешном выполнении.
    """
    try:
        logger.debug("Выполнение команды: %s", command)
        subprocess.Popen(command, shell=True)
        Notification(success_message, "success").show_notification()
    except Exception as e:
        logger.exception("Ошибка при выполнении команды: %s", command)
        Notification(f"Ошибка: {e}", "error").show_notification()
