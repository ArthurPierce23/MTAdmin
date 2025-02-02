# settings.py
import json
from pathlib import Path

from PySide6.QtWidgets import (
    QLineEdit, QDialog
)
from PySide6.QtWidgets import QDialogButtonBox, QSpinBox
import logging

logger = logging.getLogger(__name__)
from PySide6.QtWidgets import QVBoxLayout, QLabel

SETTINGS_FILE = Path.home() / ".mtadmin" / "settings.json"
DEFAULT_THEME = "Темная"

DEFAULT_SETTINGS = {
    "theme": DEFAULT_THEME,
    "timeout": 5,
    "font_size": 12,
    "recent_limit": 10
}


def load_settings():
    """Загружает настройки из JSON"""
    try:
        SETTINGS_FILE.parent.mkdir(exist_ok=True)
        if not SETTINGS_FILE.exists():
            return DEFAULT_SETTINGS.copy()

        with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
            loaded = json.load(f)
            return {**DEFAULT_SETTINGS, **loaded}

    except Exception as e:
        print(f"Error loading settings: {e}")
        return DEFAULT_SETTINGS.copy()


def save_settings(settings):
    """Сохраняет настройки в JSON"""
    try:
        SETTINGS_FILE.parent.mkdir(exist_ok=True)
        with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
            json.dump({k: v for k, v in settings.items() if k in DEFAULT_SETTINGS},
                      f, indent=4, ensure_ascii=False)
    except Exception as e:
        print(f"Error saving settings: {e}")

class SettingsDialog(QDialog):
    def __init__(self, current_settings):
        super().__init__()
        self.setWindowTitle("Настройки приложения")
        layout = QVBoxLayout()

        # Таймаут подключения
        self.timeout_input = QSpinBox()
        self.timeout_input.setRange(1, 60)
        self.timeout_input.setValue(current_settings.get("timeout", 5))
        layout.addWidget(QLabel("Таймаут подключения (сек):"))
        layout.addWidget(self.timeout_input)

        # Размер шрифта
        self.font_size = QSpinBox()
        self.font_size.setRange(8, 20)
        self.font_size.setValue(current_settings.get("font_size", 12))
        layout.addWidget(QLabel("Размер шрифта:"))
        layout.addWidget(self.font_size)

        # Кнопки
        btn_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        btn_box.accepted.connect(self.accept)
        btn_box.rejected.connect(self.reject)
        layout.addWidget(btn_box)

        self.setLayout(layout)

        # Формат даты
        self.date_format = QLineEdit(current_settings.get("date_format", "dd.MM.yyyy HH:mm"))
        layout.addWidget(QLabel("Формат даты:"))
        layout.addWidget(self.date_format)