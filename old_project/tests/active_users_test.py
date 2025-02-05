import logging
from old_project.windows_gui.rdp_management import (
    is_rdp_enabled,
    enable_rdp,
    get_rdp_port,
    set_rdp_port,
    get_rdp_users,
    add_rdp_user,
    remove_rdp_user
)
from old_project.windows_gui.session_manager import PowerShellSessionManager  # Замените на правильный путь к вашему классу

# Настройка логирования
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def main():
    # Параметры подключения
    ip = "10.254.44.36"  # Замените на IP-адрес вашего сервера
    username = "a.n.danilenko@neovox.ru"  # Замените на ваше имя пользователя, если необходимо
    password = "AlArAnAn23!"  # Замените на ваш пароль, если необходимо

    # Создаем экземпляр менеджера сессий
    session_manager = PowerShellSessionManager(ip, username, password)

    # Подключаемся к серверу
    if not session_manager.connect():
        logger.error("Не удалось подключиться к серверу.")
        return

    try:
        # Проверяем, включен ли RDP
        rdp_enabled = is_rdp_enabled(session_manager.session)
        logger.info(f"RDP включен: {rdp_enabled}")

        # Включаем RDP, если он выключен
        if not rdp_enabled:
            logger.info("Включаем RDP...")
            enable_rdp(session_manager.session, True)

        # Получаем текущий порт RDP
        current_port = get_rdp_port(session_manager.session)
        logger.info(f"Текущий порт RDP: {current_port}")

        # Устанавливаем новый порт RDP
        new_port = 3390  # Пример нового порта
        logger.info(f"Устанавливаем новый порт RDP: {new_port}")
        set_rdp_port(session_manager.session, new_port)

        # Получаем пользователей RDP
        rdp_users = get_rdp_users(session_manager.session)
        logger.info(f"Пользователи RDP: {rdp_users}")

        # Добавляем пользователя
        username_to_add = "v.v.maslo"  # Замените на имя пользователя, которого хотите добавить
        logger.info(f"Добавляем пользователя {username_to_add} в группу RDP...")
        add_rdp_user(session_manager.session, username_to_add)

        # Удаляем пользователя
        logger.info(f"Удаляем пользователя {username_to_add} из группы RDP...")
        remove_rdp_user(session_manager.session, username_to_add)

    except Exception as e:
        logger.error(f"Произошла ошибка: {e}")

    finally:
        # Закрываем сессию
        session_manager.close()

if __name__ == "__main__":
    main()