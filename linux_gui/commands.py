import subprocess
import logging
import platform
import sys
from pathlib import Path

# Настройка логирования (при необходимости можно изменить уровень или добавить обработчики)
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)


def find_vnc_client() -> str:
    """
    Возвращает путь к VNC-клиенту (vnc.exe), который хранится в папке software.

    Если программа запущена как .exe (через PyInstaller) – ищем в папке, где распакованы файлы.
    Если программа запущена из исходного кода – ищем в папке software в корне проекта.

    :return: Путь к vnc.exe, если найден, иначе пустая строка.
    """
    if platform.system() != "Windows":
        logger.error("Поддерживаются только системы Windows.")
        return ""

    # Определяем базовую директорию для поиска
    if getattr(sys, 'frozen', False):
        # Запуск в виде .exe, PyInstaller распаковывает файлы в sys._MEIPASS
        base_dir = Path(sys._MEIPASS)
        logger.debug("Запуск в режиме frozen (PyInstaller).")
    else:
        # Запуск из исходного кода: поднимаемся на один уровень вверх от директории текущего модуля
        base_dir = Path(__file__).resolve().parent.parent
        logger.debug("Запуск из исходного кода (например, через PyCharm).")

    vnc_path = base_dir / "software" / "vnc.exe"
    logger.info(f"Ищем VNC-клиент по пути: {vnc_path}")

    if vnc_path.is_file():
        logger.info(f"Найден VNC-клиент: {vnc_path}")
        return str(vnc_path)
    else:
        logger.error(f"VNC-клиент не найден по пути: {vnc_path}")
        return ""


def start_ssh_session(ip: str, username: str) -> bool:
    """
    Запускает локальный cmd и подключается к удалённому хосту по SSH.

    :param ip: IP-адрес удалённого хоста.
    :param username: Имя пользователя для подключения.
    :return: True, если процесс успешно запущен, иначе False.
    """
    command = f'start cmd /k "ssh {username}@{ip}"'
    logger.info(f"Запуск SSH с командой: {command}")

    try:
        subprocess.run(command, shell=True, check=True)
        logger.info("SSH-сессия успешно запущена.")
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"Ошибка запуска SSH-сессии: {e}")
        return False


def start_vnc_session(ip: str) -> bool:
    """
    Запускает VNC-клиент для подключения к удалённому хосту.

    :param ip: IP-адрес удалённого хоста.
    :return: True, если процесс успешно запущен, иначе False.
    """
    vnc_client = find_vnc_client()
    if not vnc_client:
        logger.error("Не удалось найти VNC-клиент для запуска.")
        return False

    command = f'start "" "{vnc_client}" {ip}'
    logger.info(f"Запуск VNC с командой: {command}")

    try:
        subprocess.run(command, shell=True, check=True)
        logger.info("VNC-сессия успешно запущена.")
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"Ошибка запуска VNC-сессии: {e}")
        return False


if __name__ == '__main__':
    # Пример использования функций для тестирования
    test_ip = "192.168.1.100"
    test_username = "user"

    # Запуск SSH-сессии
    if start_ssh_session(test_ip, test_username):
        logger.info("SSH-сессия запущена.")
    else:
        logger.error("Не удалось запустить SSH-сессию.")

    # Запуск VNC-сессии
    if start_vnc_session(test_ip):
        logger.info("VNC-сессия запущена.")
    else:
        logger.error("Не удалось запустить VNC-сессию.")
