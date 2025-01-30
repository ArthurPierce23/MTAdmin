# db_manager.py (исправленный путь к БД)
import sqlite3
import os
from datetime import datetime
from pathlib import Path

DB_PATH = Path(__file__).parent / "mtadmin.sqlite"


def init_db():
    """Создает таблицы в базе данных, если их нет."""
    Path(DB_PATH).parent.mkdir(exist_ok=True)

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS recent_connections (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ip TEXT NOT NULL,
            date TEXT NOT NULL
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS workstation_map (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ip TEXT UNIQUE NOT NULL,
            rm_number TEXT DEFAULT '',
            os TEXT DEFAULT 'Неизвестно',
            last_seen TEXT NOT NULL
        )
    """)

    conn.commit()
    conn.close()

def add_recent_connection(ip):
    """Добавляет новое подключение в историю, без удаления старых записей"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    cursor.execute("""
        INSERT INTO recent_connections (ip, date)
        VALUES (?, ?)
    """, (ip, now))

    conn.commit()
    conn.close()

def get_recent_connections():
    """Возвращает список последних 10 подключений."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT ip, date FROM recent_connections ORDER BY date DESC LIMIT 10")
    connections = cursor.fetchall()
    conn.close()
    return connections

def clear_recent_connections():
    """Очищает таблицу недавних подключений"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM recent_connections")
    conn.commit()
    conn.close()

def add_to_workstation_map(ip, os_name):
    """Добавляет или обновляет запись в карте рабочих мест."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM workstation_map WHERE ip = ?", (ip,))
    existing = cursor.fetchone()

    if existing:
        cursor.execute("""
            UPDATE workstation_map
            SET os = ?, last_seen = datetime('now')
            WHERE ip = ?
        """, (os_name, ip))
    else:
        cursor.execute("""
            INSERT INTO workstation_map (ip, os, last_seen)
            VALUES (?, ?, datetime('now'))
        """, (ip, os_name))

    conn.commit()
    conn.close()

def get_workstation_map():
    """Получение карты рабочих мест"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT rm_number, ip, os, last_seen FROM workstation_map")
    data = cursor.fetchall()
    conn.close()
    return data

def remove_from_workstation_map(ip):
    """Удаляет ПК из карты рабочих мест по IP"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM workstation_map WHERE ip = ?", (ip,))
    conn.commit()
    conn.close()