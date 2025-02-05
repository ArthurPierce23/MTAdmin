import sys
import logging
from PySide6.QtWidgets import QApplication, QMainWindow, QTabWidget, QWidget, QVBoxLayout, QLabel, QMenu
from PySide6.QtGui import QAction
from main_gui.tab_widgets import DynamicTabs  # Динамические вкладки
from database import db_manager
from styles import THEMES, apply_theme  # Импорт тем
from notifications import Notification  # Импорт уведомлений
from settings import load_settings, save_settings
from functools import partial  # Для корректного связывания аргументов

# Инициализация БД
db_manager.init_db()

# Настройка логирования для отладки (DEBUG-уровень)
logging.basicConfig(
    level=logging.INFO,  # или level=logging.WARNING
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt="%H:%M:%S"
)

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("MTAdmin")
        self.setGeometry(100, 100, 700, 800)
        self.current_theme = load_settings().get("theme", "Светлая")
        self.init_ui()

    def init_ui(self):
        self.create_toolbar()

        self.tabs = QTabWidget()
        self.tabs.addTab(self.create_pc_management_tab(), "Управление ПК")
        self.tabs.addTab(self.create_placeholder_tab(), "В разработке")

        self.setCentralWidget(self.tabs)

        # Применяем начальную тему
        self.apply_theme(self.current_theme)

    def create_toolbar(self):
        menubar = self.menuBar()

        # Файл
        file_menu = menubar.addMenu("Файл")
        exit_action = QAction("Выход", self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        # Настройки
        settings_menu = menubar.addMenu("Настройки")

        # Подменю для выбора тем
        theme_menu = QMenu("Тема", self)
        for theme_name in THEMES.keys():
            # Используем partial для корректного связывания текущего значения theme_name
            theme_action = QAction(theme_name, self)
            theme_action.triggered.connect(partial(self.change_theme, theme_name))
            theme_menu.addAction(theme_action)

        settings_menu.addMenu(theme_menu)

        advanced_settings_action = QAction("Доп. настройки", self)
        settings_menu.addAction(advanced_settings_action)

        # Экспорт / Импорт
        export_import_menu = menubar.addMenu("Экспорт/Импорт")
        export_action = QAction("Экспорт данных", self)
        import_action = QAction("Импорт данных", self)
        export_import_menu.addAction(export_action)
        export_import_menu.addAction(import_action)

        # Справка
        help_menu = menubar.addMenu("Справка")
        about_action = QAction("О программе", self)
        help_menu.addAction(about_action)

    def create_pc_management_tab(self):
        widget = QWidget()
        layout = QVBoxLayout()
        self.dynamic_tabs = DynamicTabs()
        layout.addWidget(self.dynamic_tabs)
        widget.setLayout(layout)
        return widget

    def create_placeholder_tab(self):
        widget = QWidget()
        layout = QVBoxLayout()
        label = QLabel("Раздел находится в разработке.")
        layout.addWidget(label)
        widget.setLayout(layout)
        return widget

    def change_theme(self, theme_name: str):
        """Смена темы с сохранением в настройки и уведомлением."""
        self.current_theme = theme_name
        self.apply_theme(theme_name)

        # Сохраняем тему в settings.json
        save_settings({"theme": theme_name})

        # Показываем уведомление
        notification = Notification(f"Тема изменена на: {theme_name}", "success", duration=3000, parent=self)
        notification.show_notification()

    def apply_theme(self, theme_name: str):
        """Применяет тему ко всему приложению или сбрасывает стили."""
        if theme_name == "Без темы":
            self.setStyleSheet("")  # Сброс стилей
        else:
            style = apply_theme(theme_name)
            self.setStyleSheet(style)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
