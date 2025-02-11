import os
import sys
import sqlite3
import shutil
import logging
from datetime import datetime
from typing import List, Tuple

logger = logging.getLogger(__name__)


def get_project_root() -> str:
    """
    Возвращает корневую папку проекта:
      - Если приложение скомпилировано (.exe): папка, где находится .exe.
      - Если запущено из исходного кода: родительская папка модуля.
    """
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    else:
        # При разработке файл db_manager.py находится в папке /database/
        return os.path.dirname(os.path.abspath(__file__))


# Определяем путь к базе данных
if getattr(sys, 'frozen', False):
    # При компиляции БД располагается в той же папке, что и .exe
    DB_PATH = os.path.join(os.path.dirname(sys.executable), "mtadmin.sqlite")
else:
    # При разработке база находится в папке /database/ рядом с db_manager.py
    DB_PATH = os.path.join(get_project_root(), "mtadmin.sqlite")


def init_db() -> None:
    """
    Инициализирует базу данных.
    Если база или таблица не существует, она будет создана.
    """
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS connections (
                ip TEXT PRIMARY KEY,
                os TEXT,
                last_connection TEXT,
                rm TEXT
            )
        ''')
        conn.commit()


def add_connection(ip: str, os_name: str, last_connection: datetime) -> None:
    """
    Добавляет или обновляет запись в базе данных.

    :param ip: IP-адрес подключения.
    :param os_name: Имя операционной системы.
    :param last_connection: Время последнего подключения.
    """
    try:
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO connections (ip, os, last_connection, rm)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(ip) DO UPDATE SET last_connection = excluded.last_connection
            ''', (ip, os_name, last_connection.isoformat(), None))
            conn.commit()
    except sqlite3.IntegrityError as e:
        logger.error(f"IntegrityError при добавлении подключения для {ip}: {e}")


def get_all_connections() -> List[Tuple[str, str, str, str]]:
    """
    Возвращает список всех записей из базы данных.

    :return: Список кортежей (rm, ip, os, last_connection)
    """
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT rm, ip, os, last_connection
            FROM connections
            ORDER BY last_connection DESC
        ''')
        rows = cursor.fetchall()
    return rows


def update_rm(ip: str, new_rm: str) -> None:
    """
    Обновляет значение поля rm для записи с указанным IP-адресом.

    :param ip: IP-адрес записи.
    :param new_rm: Новое значение для поля rm.
    """
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE connections
            SET rm = ?
            WHERE ip = ?
        ''', (new_rm, ip))
        conn.commit()


def delete_rm(ip: str) -> None:
    """
    Удаляет запись с указанным IP-адресом из базы данных.

    :param ip: IP-адрес для удаления.
    """
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute('''
            DELETE FROM connections WHERE ip = ?
        ''', (ip,))
        conn.commit()


def export_db(export_path: str) -> bool:
    """
    Экспортирует базу данных, копируя файл базы данных по указанному пути.

    :param export_path: Путь для сохранения копии базы данных.
    :return: True, если экспорт прошёл успешно, иначе False.
    """
    try:
        shutil.copyfile(DB_PATH, export_path)
        logger.info(f"База данных экспортирована в {export_path}")
        return True
    except Exception as e:
        logger.error(f"Ошибка экспорта базы данных: {e}")
        return False


def import_db(import_path: str) -> bool:
    """
    Импортирует базу данных, копируя файл базы данных из указанного пути.
    Текущий файл базы данных будет перезаписан.

    :param import_path: Путь к файлу базы данных для импорта.
    :return: True, если импорт прошёл успешно, иначе False.
    """
    try:
        shutil.copyfile(import_path, DB_PATH)
        logger.info(f"База данных импортирована из {import_path}")
        return True
    except Exception as e:
        logger.error(f"Ошибка импорта базы данных: {e}")
        return False


if __name__ == "__main__":
    # Инициализация базы данных для тестирования
    init_db()
    # Примеры добавления подключений
    add_connection("192.168.0.10", "Windows", datetime.now())
    add_connection("192.168.0.10", "Windows", datetime.now())  # Повторное подключение – обновит время.
    add_connection("192.168.0.11", "Linux", datetime.now())

    # Вывод всех записей
    for record in get_all_connections():
        print(record)
