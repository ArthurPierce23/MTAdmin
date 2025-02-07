import json
import os

# Определяем корневую папку проекта (на один уровень выше, чем этот файл)
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
SETTINGS_FILE = os.path.join(PROJECT_ROOT, "settings.json")

def load_settings():
    """Загружает настройки из файла JSON."""
    if not os.path.exists(SETTINGS_FILE):
        return {"theme": "Светлая", "auto_start": False, "font_size": 10, "show_notifications": True}

    with open(SETTINGS_FILE, "r", encoding="utf-8") as file:
        try:
            return json.load(file)
        except json.JSONDecodeError:
            return {"theme": "Светлая", "auto_start": False, "font_size": 10, "show_notifications": True}

def save_settings(settings):
    """Сохраняет настройки в JSON файл."""
    with open(SETTINGS_FILE, "w", encoding="utf-8") as file:
        json.dump(settings, file, indent=4, ensure_ascii=False)
