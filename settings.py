import json
import os

SETTINGS_FILE = "settings.json"  # Должно быть определено

DEFAULT_SETTINGS = {
    "theme": "Без темы",
    "timeout": 5,
    "font_size": 12
}

def load_settings():
    """Загружает настройки из JSON, если файла нет — создает с дефолтными значениями."""
    if not os.path.exists(SETTINGS_FILE):
        save_settings(DEFAULT_SETTINGS)
    with open(SETTINGS_FILE, "r", encoding="utf-8") as file:
        return json.load(file)

def save_settings(settings):
    """Сохраняет настройки в JSON."""
    with open(SETTINGS_FILE, "w", encoding="utf-8") as file:
        json.dump(settings, file, indent=4, ensure_ascii=False)
