# /database/db_manager.py

import sqlite3
import os
from datetime import datetime

# Определяем путь к базе данных (mtadmin.sqlite) рядом с файлом db_manager.py
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "mtadmin.sqlite")


def init_db():
    """
    Инициализирует базу данных.
    Если базы данных или таблицы не существует, она будет создана.
    """
    conn = sqlite3.connect(DB_PATH)
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
    conn.close()


def add_connection(ip: str, os_name: str, last_connection: datetime):
    """
    Добавляет или обновляет запись в базе данных.
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    try:
        cursor.execute('''
            INSERT INTO connections (ip, os, last_connection, rm)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(ip) DO UPDATE SET last_connection = excluded.last_connection
        ''', (ip, os_name, last_connection.isoformat(), None))
        conn.commit()
    except sqlite3.IntegrityError:
        pass
    finally:
        conn.close()



def get_all_connections():
    """
    Возвращает список всех записей из базы данных.

    :return: Список кортежей (rm, ip, os, last_connection)
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        SELECT rm, ip, os, last_connection
        FROM connections
        ORDER BY last_connection DESC
    ''')
    rows = cursor.fetchall()
    conn.close()
    return rows

def update_rm(ip: str, new_rm: str):
    """
    Обновляет номер РМ для указанного IP-адреса.
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        UPDATE connections
        SET rm = ?
        WHERE ip = ?
    ''', (new_rm, ip))
    conn.commit()
    conn.close()

def delete_rm(ip: str):
    """
    Удаляет запись с указанным IP-адресом из базы данных.
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        DELETE FROM connections WHERE ip = ?
    ''', (ip,))
    conn.commit()
    conn.close()


if __name__ == "__main__":
    # Инициализация базы данных для тестирования
    init_db()
    # Пример добавления подключения
    add_connection("192.168.0.10", "Windows", datetime.now())
    add_connection("192.168.0.10", "Windows", datetime.now())  # Повторное подключение — дубликат не будет добавлен.
    add_connection("192.168.0.11", "Linux", datetime.now())

    # Вывод всех записей
    for record in get_all_connections():
        print(record)
