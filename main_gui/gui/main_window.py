import sys
import logging
import os
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QTabWidget, QWidget, QVBoxLayout, QMenu, QMessageBox, QSystemTrayIcon, QMenu,
    QDialog, QDialogButtonBox, QCheckBox, QSizePolicy
)
from PySide6.QtGui import QAction, QIcon
from functools import partial
from main_gui.tab_widgets import DynamicTabs
from database import db_manager
from styles import THEMES, apply_theme
from notifications import Notification, set_notifications_enabled
from settings import load_settings, save_settings
from pc_connection_block import PCConnectionBlock

# Инициализация БД
db_manager.init_db()

# Настройка логирования
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt="%H:%M:%S"
)

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("MTAdmin")
        self.setGeometry(100, 100, 700, 800)
        settings = load_settings()
        self.current_theme = settings.get("theme", "Светлая")
        self.auto_start = settings.get("auto_start", False)
        # Устанавливаем глобальный флаг уведомлений согласно сохранённым настройкам
        set_notifications_enabled(settings.get("show_notifications", True))
        self.tray_icon = None
        self.init_ui()

    def init_ui(self):
        self.apply_theme()
        self.create_toolbar()
        self.create_tray_icon()
        self.tabs = QTabWidget()
        self.tabs.setMovable(True)  # Делаем вкладки подвижными
        self.tabs.setTabsClosable(True)  # Разрешаем закрывать вкладки
        self.tabs.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.tabs.addTab(self.create_pc_management_tab(), "Управление ПК")
        self.setCentralWidget(self.tabs)
        self.apply_theme()

    def create_toolbar(self):
        menubar = self.menuBar()

        # Файл
        file_menu = menubar.addMenu("Файл")
        exit_action = QAction("Выход", self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        # Настройки
        settings_menu = menubar.addMenu("Настройки")
        theme_menu = QMenu("Тема", self)
        for theme_name in THEMES.keys():
            theme_action = QAction(theme_name, self)
            theme_action.triggered.connect(partial(self.change_theme, theme_name))
            theme_menu.addAction(theme_action)
        settings_menu.addMenu(theme_menu)

        advanced_settings_action = QAction("Доп. настройки", self)
        advanced_settings_action.triggered.connect(self.open_advanced_settings)
        settings_menu.addAction(advanced_settings_action)

        # Экспорт/Импорт
        export_import_menu = menubar.addMenu("Экспорт/Импорт")
        export_action = QAction("Экспорт данных", self)
        import_action = QAction("Импорт данных", self)
        export_import_menu.addAction(export_action)
        export_import_menu.addAction(import_action)

        # Справка
        help_menu = menubar.addMenu("Справка")
        about_action = QAction("О программе", self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)

    def open_advanced_settings(self):
        """Открытие окна дополнительных настроек с сохранением параметров."""
        dialog = QDialog(self)
        dialog.setWindowTitle("Дополнительные настройки")
        layout = QVBoxLayout(dialog)

        # Загружаем текущие настройки
        settings = load_settings()
        show_notifications = settings.get("show_notifications", True)

        # Чекбокс для показа уведомлений
        self.notifications_checkbox = QCheckBox("Показывать уведомления", dialog)
        self.notifications_checkbox.setChecked(show_notifications)
        layout.addWidget(self.notifications_checkbox)

        # Добавляем кнопки ОК/Отмена
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        layout.addWidget(button_box)

        button_box.accepted.connect(dialog.accept)
        button_box.rejected.connect(dialog.reject)

        if dialog.exec() == QDialog.Accepted:
            new_value = self.notifications_checkbox.isChecked()
            settings["show_notifications"] = new_value
            save_settings(settings)
            set_notifications_enabled(new_value)

    def resizeEvent(self, event):
        """Обновляем позиции уведомлений при изменении размера окна."""
        for notif in Notification.get_active_notifications():
            notif.update_position()
        super().resizeEvent(event)

    def create_tray_icon(self):
        """Создание и настройка иконки для системного трея"""
        self.tray_icon = QSystemTrayIcon(QIcon("path_to_icon.png"), self)
        self.tray_menu = QMenu(self)

        restore_action = QAction("Восстановить", self)
        restore_action.triggered.connect(self.restore_from_tray)
        self.tray_menu.addAction(restore_action)

        exit_action = QAction("Выход", self)
        exit_action.triggered.connect(self.close)
        self.tray_menu.addAction(exit_action)

        self.tray_icon.setContextMenu(self.tray_menu)
        self.tray_icon.activated.connect(self.tray_activated)
        self.tray_icon.show()

        if self.current_theme != "Без темы":
            self.tray_menu.setStyleSheet(apply_theme(self.current_theme))

    def tray_activated(self, reason):
        if reason == QSystemTrayIcon.Trigger:
            self.restore_from_tray()

    def restore_from_tray(self):
        self.showNormal()
        self.activateWindow()

    def change_theme(self, theme_name: str):
        self.current_theme = theme_name
        self.setStyleSheet(apply_theme(self.current_theme))
        self.apply_theme()
        save_settings({"theme": theme_name})
        if hasattr(self, "dynamic_tabs"):
            self.dynamic_tabs.set_theme(theme_name)
        Notification(f"Тема изменена на: {theme_name}",
                     f"Тема {theme_name} применена.",
                     "success",
                     duration=3000,
                     parent=self).show_notification()

    def apply_theme(self):
        theme_name = self.current_theme
        if theme_name == "Без темы":
            self.setStyleSheet("")
        else:
            self.setStyleSheet(apply_theme(theme_name))

    def moveEvent(self, event):
        for notif in Notification.get_active_notifications():
            notif.update_position()
        super().moveEvent(event)

    def show_about(self):
        version = get_version()
        about_text = f"""
        <h2 style="color:{THEMES[self.current_theme]['foreground']};">MTAdmin — это приложение для упрощения работы с ОС Windows и Linux.</h2>
        <h3>Версия: <span style="font-weight: bold; color:{THEMES[self.current_theme]['highlight']};">{version}</span></h3>
        <h3>Автор: <span style="font-weight: bold;">ArthurPierce</span></h3>
        <h3>Контакты: <a href="https://t.me/ArthurPierce" style="color:{THEMES[self.current_theme]['highlight']};">https://t.me/ArthurPierce</a></h3>
        <h4>Используемые технологии:</h4>
        <ul>
            <li><strong>Python</strong></li>
            <li><strong>PySide6</strong></li>
            <li><strong>SQLite</strong></li>
        </ul>
        <h4>Возможности программы:</h4>
        <ul>
            <li>Просмотр нагрузки на ПК с ОС Linux и Windows.</li>
            <li>Быстрое подключение, выполнение команд и скриптов.</li>
            <li>Библиотека скриптов для Bash, Batch, PowerShell и других.</li>
            <li>Работа во вкладках (каждое подключение — отдельная вкладка, которую можно выносить за пределы основного окна).</li>
        </ul>
        <h4>Благодарности:</h4>
        <p style="font-style:italic; color:{THEMES[self.current_theme]['foreground']};">
        Спасибо моей лени, которая заставила меня создать эту программу вместо того, чтобы просто складывать скрипты в одну папку.
        </p>
        """
        msg_box = QMessageBox(self)
        msg_box.setWindowTitle("О программе")
        msg_box.setText(about_text)
        msg_box.setStyleSheet(apply_theme(self.current_theme))
        msg_box.exec()

    def create_pc_management_tab(self):
        widget = QWidget()
        layout = QVBoxLayout()

        # Удаляем создание и добавление блока PCConnectionBlock
        # self.pc_connection_block = PCConnectionBlock()
        # self.pc_connection_block.setMaximumHeight(100)
        # layout.addWidget(self.pc_connection_block)

        # Создаём динамические вкладки, в которых внутри своей логики уже создаётся PCConnectionBlock
        self.dynamic_tabs = DynamicTabs(theme_name=self.current_theme)
        self.dynamic_tabs.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        layout.addWidget(self.dynamic_tabs)  # Вкладки займут всё пространство

        widget.setLayout(layout)
        return widget


def get_version():
    try:
        with open("version.txt", "r") as f:
            return f.read().strip()
    except FileNotFoundError:
        return "Неизвестно"

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())