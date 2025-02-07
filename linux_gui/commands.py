import subprocess
import os
import logging
import platform

logger = logging.getLogger(__name__)


def find_vnc_client() -> str:
    """
    Возвращает путь к VNC-клиенту (vnc.exe), который лежит в папке software в корне проекта.

    :return: Путь к vnc.exe или пустая строка, если не найден
    """
    if platform.system() != "Windows":
        logger.error("Поддерживаются только системы Windows.")
        return ""

    # Определяем корневую директорию проекта как родительскую папку относительно текущего модуля
    current_module_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.abspath(os.path.join(current_module_dir, ".."))
    vnc_path = os.path.join(project_root, "software", "vnc.exe")

    if os.path.isfile(vnc_path):
        logger.info(f"Найден VNC-клиент: {vnc_path}")
        return vnc_path
    else:
        logger.error("VNC-клиент не найден по ожидаемому пути: " + vnc_path)
        return ""


def start_ssh_session(ip: str, username: str) -> bool:
    """
    Запускает локальный cmd и подключается к удалённому хосту по SSH.

    :param ip: IP-адрес удалённого хоста
    :param username: Имя пользователя для подключения
    :return: True, если процесс успешно запущен, иначе False
    """
    try:
        command = f'start cmd /k "ssh {username}@{ip}"'
        subprocess.run(command, shell=True, check=True)
        return True
    except Exception as e:
        logger.error(f"Ошибка запуска SSH: {e}")
        return False


def start_vnc_session(ip: str) -> bool:
    """
    Запускает VNC-клиент для подключения к удалённому хосту.

    :param ip: IP-адрес удалённого хоста
    :return: True, если процесс успешно запущен, иначе False
    """
    vnc_client = find_vnc_client()
    if not vnc_client:
        logger.error("Не удалось найти VNC-клиент.")
        return False

    try:
        # Формируем команду для запуска vnc.exe с передачей IP-адреса
        command = f'start "" "{vnc_client}" {ip}'
        subprocess.run(command, shell=True, check=True)
        return True
    except Exception as e:
        logger.error(f"Ошибка запуска VNC: {e}")
        return False
