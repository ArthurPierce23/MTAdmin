import os
import logging
from .commands import SSHConnection  # ✅ Импорт нашего класса

logger = logging.getLogger(__name__)
SCRIPTS_DIR = os.path.join(os.path.dirname(__file__), "scripts")  # ✅ Путь к скриптам


def list_scripts():
    """Список всех скриптов в директории"""
    if not os.path.exists(SCRIPTS_DIR):
        os.makedirs(SCRIPTS_DIR)
    return [f for f in os.listdir(SCRIPTS_DIR)
            if os.path.isfile(os.path.join(SCRIPTS_DIR, f))]


def add_script(name: str, content: str):
    """Добавление нового скрипта с правами на исполнение"""
    path = os.path.join(SCRIPTS_DIR, name)
    with open(path, "w") as f:
        f.write(content)
    os.chmod(path, 0o755)


def delete_script(name: str):
    """Удаление скрипта"""
    os.remove(os.path.join(SCRIPTS_DIR, name))


def rename_script(old_name: str, new_name: str):
    """Переименование скрипта"""
    os.rename(
        os.path.join(SCRIPTS_DIR, old_name),
        os.path.join(SCRIPTS_DIR, new_name)
    )


def execute_script(ssh_connection: SSHConnection, script_name: str) -> tuple[str, str]:
    """Выполняет скрипт через SSH-подключение"""
    try:
        script_path = os.path.join(SCRIPTS_DIR, script_name)

        if not os.path.exists(script_path):
            error_msg = f"Скрипт '{script_name}' не найден!"
            logger.error(error_msg)
            return "", error_msg

        with open(script_path, "r") as f:
            script_content = f.read()

        # ✅ Используем наш метод execute_command
        output, error = ssh_connection.execute_command(
            f"bash -s <<'EOF'\n{script_content}\nEOF"
        )

        logger.info(f"Скрипт '{script_name}' выполнен. Вывод: {output[:100]}...")
        return output, error

    except Exception as e:
        error_msg = f"Ошибка выполнения: {str(e)}"
        logger.exception(error_msg)
        return "", error_msg