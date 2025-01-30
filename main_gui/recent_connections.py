import json
import os

HISTORY_FILE = "recent_connections.json"

def load_recent_connections():
    """Загружает последние подключения."""
    if not os.path.exists(HISTORY_FILE):
        return []
    with open(HISTORY_FILE, "r", encoding="utf-8") as file:
        return json.load(file)

def save_recent_connection(ip):
    """Добавляет новое подключение в историю."""
    history = load_recent_connections()
    from datetime import datetime
    history.append({"ip": ip, "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S")})
    with open(HISTORY_FILE, "w", encoding="utf-8") as file:
        json.dump(history[-10:], file, indent=4, ensure_ascii=False)  # Храним последние 10
