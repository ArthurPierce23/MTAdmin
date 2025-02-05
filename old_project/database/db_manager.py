import sqlite3
import logging
from pathlib import Path
from datetime import datetime

logger = logging.getLogger(__name__)
DB_PATH = Path(__file__).parent / "mtadmin.sqlite"

# Схема таблиц
TABLES = {
    'recent_connections': '''
        CREATE TABLE IF NOT EXISTS recent_connections (
            id INTEGER PRIMARY KEY,
            ip TEXT NOT NULL,
            date TEXT NOT NULL
        )
    ''',
    'workstation_map': '''
        CREATE TABLE IF NOT EXISTS workstation_map (
            ip TEXT PRIMARY KEY,
            rm_number TEXT DEFAULT '',
            os TEXT DEFAULT 'Неизвестно',
            last_seen TEXT NOT NULL
        )
    '''
}

# Индексы
INDEXES = [
    "CREATE INDEX IF NOT EXISTS idx_wm_ip ON workstation_map(ip)",
    "CREATE INDEX IF NOT EXISTS idx_rc_date ON recent_connections(date)"
]

def init_db():
    """Инициализация БД с обработкой ошибок"""
    try:
        DB_PATH.parent.mkdir(exist_ok=True)
        with sqlite3.connect(DB_PATH, timeout=5) as conn:
            cursor = conn.cursor()

            # Создание таблиц
            for table in TABLES.values():
                cursor.execute(table)

            # Создание индексов
            for index in INDEXES:
                cursor.execute(index)

            # Триггер для ограничения истории (последние 50 записей)
            cursor.execute('''
                CREATE TRIGGER IF NOT EXISTS limit_recent_connections 
                AFTER INSERT ON recent_connections
                BEGIN
                    DELETE FROM recent_connections 
                    WHERE id NOT IN (
                        SELECT id 
                        FROM recent_connections 
                        ORDER BY date DESC 
                        LIMIT 50
                    );
                END
            ''')
    except Exception as e:
        logger.error(f"Database initialization failed: {str(e)}")
        raise

def add_recent_connection(ip: str):
    """Добавление в историю подключений с обработкой ошибок"""
    try:
        with sqlite3.connect(DB_PATH, timeout=5) as conn:
            cursor = conn.cursor()
            now = datetime.now().isoformat()  # Используем Python-время

            cursor.execute('''
                INSERT INTO recent_connections (ip, date)
                VALUES (?, ?)
            ''', (ip, now))
    except sqlite3.Error as e:
        logger.error(f"Error adding recent connection: {str(e)}")
        raise

def get_recent_connections(limit: int = 10):
    """Получение последних подключений с сортировкой"""
    try:
        with sqlite3.connect(DB_PATH, timeout=5) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute('''
                SELECT ip, date 
                FROM recent_connections 
                ORDER BY date DESC 
                LIMIT ?
            ''', (limit,))
            return cursor.fetchall()
    except sqlite3.Error as e:
        logger.error(f"Error getting recent connections: {str(e)}")
        return []

def clear_recent_connections():
    """Очистка истории подключений"""
    try:
        with sqlite3.connect(DB_PATH, timeout=5) as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM recent_connections")
    except sqlite3.Error as e:
        logger.error(f"Error clearing recent connections: {str(e)}")
        raise

def add_to_workstation_map(ip: str, os_name: str, rm_number: str = None):
    """
    Добавление или обновление записи о рабочей станции.
    Если rm_number не указан, старое значение сохраняется.
    """
    try:
        with sqlite3.connect(DB_PATH, timeout=5) as conn:
            cursor = conn.cursor()
            now = datetime.now().isoformat()

            if rm_number is not None:
                cursor.execute('''
                    INSERT INTO workstation_map (ip, os, rm_number, last_seen)
                    VALUES (?, ?, ?, ?)
                    ON CONFLICT(ip) DO UPDATE SET
                        os = excluded.os,
                        rm_number = excluded.rm_number,
                        last_seen = excluded.last_seen
                ''', (ip, os_name, rm_number, now))
            else:
                cursor.execute('''
                    INSERT INTO workstation_map (ip, os, last_seen)
                    VALUES (?, ?, ?)
                    ON CONFLICT(ip) DO UPDATE SET
                        os = excluded.os,
                        last_seen = excluded.last_seen
                ''', (ip, os_name, now))

    except sqlite3.Error as e:
        logger.error(f"Error updating workstation map: {str(e)}")
        raise

def update_workstation_rm(ip: str, new_rm_number: str):
    """Обновление номера РМ без изменения других данных"""
    try:
        with sqlite3.connect(DB_PATH, timeout=5) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE workstation_map
                SET rm_number = ?
                WHERE ip = ?
            ''', (new_rm_number, ip))
    except sqlite3.Error as e:
        logger.error(f"Error updating RM number: {str(e)}")
        raise

def get_workstation_map(sort_by: str = 'ip'):
    """Получение карты рабочих мест с сортировкой"""
    valid_sorts = ['ip', 'last_seen', 'rm_number']
    sort_by = sort_by if sort_by in valid_sorts else 'ip'

    try:
        with sqlite3.connect(DB_PATH, timeout=5) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute(f'''
                SELECT rm_number, ip, os, last_seen 
                FROM workstation_map 
                ORDER BY {sort_by}
            ''')
            return cursor.fetchall()
    except sqlite3.Error as e:
        logger.error(f"Error getting workstation map: {str(e)}")
        return []

def remove_from_workstation_map(ip: str):
    """Удаление рабочей станции"""
    try:
        with sqlite3.connect(DB_PATH, timeout=5) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                DELETE FROM workstation_map 
                WHERE ip = ?
            ''', (ip,))
    except sqlite3.Error as e:
        logger.error(f"Error removing from workstation map: {str(e)}")
        raise
