import paramiko
import logging
import platform
import subprocess
import shutil
import threading
from typing import Tuple, Optional, Callable
import shutil

# Настройка логирования
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# === Универсальная функция для запуска команд ===
def run_command_async(command: list, on_error: Optional[Callable[[str], None]] = None):
    def task():
        try:
            logger.info(f"Выполнение команды: {' '.join(command)}")
            process = subprocess.Popen(command, stderr=subprocess.PIPE)
            _, stderr = process.communicate()
            if stderr:
                error_message = stderr.decode().strip()
                logger.error(f"Ошибка выполнения команды: {error_message}")
                if on_error:
                    on_error(error_message)
        except Exception as e:
            logger.exception(f"Ошибка запуска команды: {str(e)}")
            if on_error:
                on_error(str(e))

    thread = threading.Thread(target=task)
    thread.start()

# === Поиск доступного терминала для Linux ===
def get_linux_terminal():
    terminals = [
        {'name': 'x-terminal-emulator', 'args': ['-e']},
        {'name': 'gnome-terminal', 'args': ['--']},
        {'name': 'konsole', 'args': ['-e']},
        {'name': 'xfce4-terminal', 'args': ['-x']},
        {'name': 'xterm', 'args': ['-e']},
        {'name': 'kitty', 'args': ['-e']}
    ]
    for term in terminals:
        if shutil.which(term['name']):
            return term
    return None

# === Упрощённые функции подключения ===
def connect_ssh(ip: str, username: str, on_error=None):
    """Подключение по SSH с проверкой наличия терминала."""
    try:
        logger.info(f"Подключение к {ip} как {username}")
        if platform.system() == "Windows":
            command = ["cmd", "/k", f"ssh {username}@{ip}"]
        else:
            # Проверка наличия терминала
            terminal = shutil.which("gnome-terminal") or shutil.which("x-terminal-emulator")
            if not terminal:
                error_message = "Не найден установленный терминал. Установите gnome-terminal или x-terminal-emulator."
                logger.error(error_message)
                if on_error:
                    on_error(error_message)
                return

            command = [terminal, "--", "ssh", f"{username}@{ip}"]

        subprocess.Popen(command)
        logger.info(f"SSH-сессия открыта для {ip}")
    except Exception as e:
        logger.exception(f"Ошибка подключения по SSH к {ip}: {e}")
        if on_error:
            on_error(str(e))


def connect_vnc(ip: str, on_error: Optional[Callable[[str], None]] = None):
    viewer = "vncviewer.exe" if platform.system() == "Windows" else "vncviewer"
    run_command_async([viewer, ip], on_error)

def connect_ftp(ip: str, on_error: Optional[Callable[[str], None]] = None):
    command = ["cmd", "/k", f"ftp {ip}"] if platform.system() == "Windows" else ["ftp", ip]
    run_command_async(command, on_error)

def connect_telnet(ip: str, on_error: Optional[Callable[[str], None]] = None):
    command = ["cmd", "/k", f"telnet {ip}"] if platform.system() == "Windows" else ["telnet", ip]
    run_command_async(command, on_error)

# === Класс для управления SSH-сессией ===
class SSHConnection:
    """Класс для управления SSH-подключением к Linux"""

    def __init__(self, host: str, username: str, password: str):
        self.host = host
        self.username = username
        self.password = password
        self.client = paramiko.SSHClient()  # ✅ Ядро подключения

    def connect(self):
        """Устанавливает SSH-соединение"""
        self.client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        self.client.connect(
            hostname=self.host,
            username=self.username,
            password=self.password,
            timeout=10
        )
        logger.info(f"SSH подключение к {self.host} установлено")

    def execute_command(self, command: str) -> tuple[str, str]:
        """Выполняет команду на удаленном хосте"""
        try:
            stdin, stdout, stderr = self.client.exec_command(command)
            output = stdout.read().decode().strip()
            error = stderr.read().decode().strip()
            return output, error
        except Exception as e:
            logger.error(f"Ошибка выполнения команды: {str(e)}")
            return "", str(e)

    def close(self):
        """Закрывает соединение"""
        self.client.close()
        logger.info(f"SSH подключение к {self.host} закрыто")