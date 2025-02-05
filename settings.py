import json
import os

SETTINGS_FILE = "settings.json"

def load_settings():
    """Загружает настройки из файла JSON."""
    if not os.path.exists(SETTINGS_FILE):
        return {"theme": "Светлая"}  # Значение по умолчанию

    with open(SETTINGS_FILE, "r", encoding="utf-8") as file:
        try:
            return json.load(file)
        except json.JSONDecodeError:
            return {"theme": "Светлая"}  # Фолбэк при ошибке

def save_settings(settings):
    """Сохраняет настройки в JSON файл."""
    with open(SETTINGS_FILE, "w", encoding="utf-8") as file:
        json.dump(settings, file, indent=4, ensure_ascii=False)
