import subprocess
import logging
import re
import platform

# Проверяем, Windows ли это
if platform.system() == "Windows":
    import wmi  # Только для Windows

EXCLUDED_USERNAMES = {'SYSTEM', 'LOCAL SERVICE', 'pdqdeployment', 'NETWORK SERVICE', 'СИСТЕМА'}

def get_active_users(ip):
    try:
        if ip in ('localhost', '127.0.0.1'):
            return _get_local_users()
        else:
            return _get_remote_users(ip)
    except Exception as e:
        logging.error(f"Ошибка получения пользователей: {str(e)}")
        return f"Исключение: {str(e)}"

def _get_local_users():
    """Получает активных пользователей локального ПК"""
    try:
        if platform.system() != "Windows":
            logging.warning("Функция _get_local_users() недоступна на Linux.")
            return []

        cmd = ["quser"]
        result = subprocess.run(
            cmd, capture_output=True, text=True, encoding='utf-8', errors='ignore', shell=True
        )

        if result.returncode != 0:
            logging.error("Команда quser завершилась с ошибкой.")
            return []

        return _parse_quser_output(result.stdout)

    except Exception as e:
        logging.error(f"Ошибка при выполнении quser: {str(e)}")
        return []

def _get_remote_users(ip):
    """Получает активных пользователей на удаленном Windows-компьютере"""
    if platform.system() != "Windows":
        logging.warning(f"Попытка выполнить _get_remote_users() на Linux. Возвращаем заглушку.")
        return [{"username": "Недоступно", "state": "ОС не поддерживается"}]

    try:
        # Используем WMI для получения активных пользователей
        c = wmi.WMI(computer=ip)
        users = []
        for session in c.Win32_ComputerSystem():
            for user in session.UserName.split(','):
                if user.strip() and user not in EXCLUDED_USERNAMES:
                    users.append({"username": user.strip(), "state": "Активно"})
        return users

    except Exception as e:
        logging.error(f"Ошибка WMI для {ip}: {str(e)}")
        return []

def _parse_quser_output(output):
    """Разбирает вывод команды quser"""
    users = []
    lines = [line.strip() for line in output.split('\n') if line.strip()]

    if len(lines) < 2:
        logging.warning("Не найдено активных пользователей.")
        return users

    for line in lines[1:]:
        parts = re.split(r'\s{2,}', line)
        if len(parts) >= 4:
            username = parts[0].strip()
            if username not in EXCLUDED_USERNAMES:
                users.append({
                    "username": username,
                    "state": parts[3].strip()  # Получаем состояние из 4-й колонки
                })

    return users
