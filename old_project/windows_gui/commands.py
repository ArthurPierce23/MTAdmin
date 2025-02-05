import subprocess
import os
import re
import socket

def run_psexec(ip):
    psexec_path = os.path.join(os.path.dirname(__file__), '..', '..', 'windows', 'programs', 'psexec', 'psexec.exe')
    command = f'start cmd /k "{psexec_path} -i -d \\\\{ip} cmd"'
    subprocess.Popen(command, shell=True)

def is_host_available(ip, port=445, timeout=3):
    """Проверяет доступность хоста по указанному порту"""
    try:
        with socket.create_connection((ip, port), timeout):
            return True
    except (socket.error, socket.timeout):
        return False


def configure_winrm(ip):
    """Настраивает TrustedHosts для WinRM, если это необходимо"""
    try:
        # Проверяем текущие настройки TrustedHosts
        result = subprocess.run(
            'winrm get winrm/config/client',
            shell=True,
            capture_output=True,
            text=True,
            encoding='cp866'
        )

        # Если IP не в списке TrustedHosts, добавляем его
        if ip not in result.stdout:
            subprocess.run(
                f'winrm set winrm/config/client @{{TrustedHosts="{ip}"}}',
                shell=True,
                check=True
            )
    except subprocess.CalledProcessError as e:
        raise Exception(f"Ошибка настройки WinRM: {e.stderr}") from e

def run_winrs(ip):
    """Запускает WinRS с предварительной проверкой настроек"""
    try:
        if not is_host_available(ip, 5985):
            raise Exception("Хост недоступен для WinRM (порт 5985)")

        configure_winrm(ip)

        # Убедимся, что указаны правильные учетные данные (если нужно)
        # Попробуем указать логин и пароль явно, если это необходимо
        username = "ncc\a.n.danilenko"  # Заменить на реальное имя пользователя
        password = "AlArAnAn23!"  # Заменить на реальный пароль

        # Команда с явным указанием учетных данных
        subprocess.run(
            f'winrs -r:{ip} -u:{username} -p:{password} cmd',
            shell=True,
            check=True
        )
    except subprocess.CalledProcessError as e:
        raise Exception(f"Ошибка WinRS: {e.stderr}") from e



def get_shadow_session_id(ip):
    """Возвращает ID первого активного пользовательского сеанса"""
    result = subprocess.run(
        f'qwinsta /server:{ip}',
        shell=True,
        capture_output=True,
        encoding='cp866'
    )

    # Парсинг вывода с учетом фиксированной ширины колонок
    for line in result.stdout.splitlines():
        if line.strip().startswith(('rdp-tcp', 'console')) and 'active' in line.lower():
            parts = re.split(r'\s{2,}', line.strip())
            if len(parts) >= 3:
                return parts[2]

    raise Exception("Активные пользовательские сеансы не найдены")


def run_shadow_rdp(ip, session_id=None):
    """
    Подключается к удаленному сеансу через Shadow RDP
    Если session_id не указан, автоматически находит первый активный сеанс
    """
    try:
        if not session_id:
            session_id = get_shadow_session_id(ip)

        subprocess.run(
            f"mstsc /shadow:{session_id} /v:{ip} /control",
            shell=True,
            check=True
        )
    except subprocess.CalledProcessError as e:
        raise Exception(f"Ошибка подключения: {e.stderr}") from e


# Примеры других функций с улучшениями:

def run_compmgmt(ip):
    """Запускает управление компьютером с проверкой доступности"""
    if not is_host_available(ip):
        raise Exception("Хост недоступен")

    subprocess.run(f'mmc compmgmt.msc /computer={ip}', shell=True, check=True)


def run_rdp(ip):
    """Запускает RDP соединение с таймаутом подключения"""
    try:
        subprocess.run(
            f'mstsc /v:{ip} /timeout:30',
            shell=True,
            check=True,
            timeout=60
        )
    except subprocess.TimeoutExpired:
        raise Exception("Таймаут подключения превышен")


def open_c_drive(ip):
    """Открывает доступ к диску C: с обработкой сетевых ошибок"""
    unc_path = f"\\\\{ip}\\C$"
    try:
        subprocess.run(f'explorer {unc_path}', shell=True, check=True)
    except subprocess.CalledProcessError:
        raise Exception("Не удалось открыть сетевой диск. Проверьте права доступа.")