import subprocess
import time
from notifications import Notification

def run_powershell(hostname):
    """Открывает удалённый PowerShell сессией Enter-PSSession на удалённом ПК."""
    # Запуск через cmd, чтобы открыть новое окно PowerShell с заданной командой
    command = f'cmd /c start powershell -NoExit -Command "Enter-PSSession -ComputerName {hostname}"'
    execute_command(command, "PowerShell открыт")

def open_compmgmt(hostname):
    """Открывает оснастку управления компьютером удаленного ПК."""
    command = f"compmgmt.msc /computer:{hostname}"
    execute_command(command, "Открыто управление компьютером")

def open_rdp(ip):
    """Подключение к RDP."""
    command = f"mstsc /v:{ip}"
    execute_command(command, "Запущен RDP-клиент")

def open_shadow_rdp(ip):
    """
    Shadow RDP: определяет активную сессию и подключается к ней.
    Используется qwinsta, вывод которого на русской ОС содержит 'Активно'.
    """
    try:
        result = subprocess.run(["qwinsta", f"/server:{ip}"], capture_output=True, text=True, encoding="cp866")
        lines = result.stdout.splitlines()
        session_id = None

        # Пропускаем первую строку (заголовок) и ищем строку с активной сессией.
        for line in lines[1:]:
            parts = line.split()
            # Если в строке присутствует статус "Активно"
            if "Активно" in parts:
                # По заголовку столбцов: СЕАНС, ПОЛЬЗОВАТЕЛЬ, ID, СТАТУС, ...
                # ID находится под индексом 2 (при условии, что строка корректная)
                if len(parts) >= 3:
                    session_id = parts[2]
                    break

        if session_id:
            command = f"mstsc /shadow:{session_id} /v:{ip} /control"
            execute_command(command, f"Shadow RDP запущен (Сессия {session_id})")
        else:
            Notification("Нет активных сессий для Shadow RDP", "warning").show_notification()

    except Exception as e:
        Notification(f"Ошибка при запуске Shadow RDP: {str(e)}", "error").show_notification()

def open_c_drive(ip):
    """Открывает C$ удаленного ПК в проводнике."""
    command = f"explorer \\\\{ip}\\C$"
    execute_command(command, "Открыт доступ к C$")

def open_cmd(hostname):
    """
    Открывает локальный CMD и сразу подключается к удалённому ПК с помощью winrs.
    Используется ключ /k, чтобы окно оставалось открытым.
    """
    command = f'cmd /c start cmd /k "winrs -r:{hostname} cmd"'
    execute_command(command, "CMD запущен и подключен к удалённому ПК")

def execute_command(command, success_message):
    """Запускает команду и показывает уведомление."""
    try:
        subprocess.Popen(command, shell=True)
        Notification(success_message, "success").show_notification()
    except Exception as e:
        Notification(f"Ошибка: {str(e)}", "error").show_notification()
