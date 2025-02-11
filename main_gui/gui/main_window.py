import sys
import os
import logging
import zipfile
import shutil
import base64
from functools import partial
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QTabWidget, QWidget, QVBoxLayout, QHBoxLayout,
    QMenu, QMessageBox, QSystemTrayIcon, QDialog, QDialogButtonBox, QCheckBox,
    QSizePolicy, QFileDialog, QListWidget, QListWidgetItem, QAbstractItemView,
    QLabel, QGroupBox, QPushButton
)
from PySide6.QtGui import QAction, QIcon, QPixmap
from PySide6.QtCore import Qt
from main_gui.tab_widgets import DynamicTabs
from database import db_manager
from styles import THEMES, apply_theme
from notifications import Notification, set_notifications_enabled
from settings import load_settings, save_settings

# Функция для определения корневой папки проекта (учитываем, что приложение может быть скомпилировано в .exe)
def get_project_root():
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    else:
        return os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

PROJECT_ROOT = get_project_root()
SETTINGS_FILE = os.path.join(PROJECT_ROOT, "settings.json")
SCRIPTS_FOLDER = os.path.join(PROJECT_ROOT, "scripts")
LOGO_FILE = os.path.join(PROJECT_ROOT, "mtadmin.jpg")

# Инициализируем базу данных
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

        # Если найден логотип – устанавливаем его как иконку окна
        if os.path.exists(LOGO_FILE):
            self.setWindowIcon(QIcon(LOGO_FILE))

        settings = load_settings()
        self.current_theme = settings.get("theme", "Светлая")
        self.auto_start = settings.get("auto_start", False)
        set_notifications_enabled(settings.get("show_notifications", True))
        self.tray_icon = None
        self.init_ui()

    def init_ui(self):
        self.apply_theme()
        self.create_toolbar()
        self.create_tray_icon()
        self.tabs = QTabWidget()
        self.tabs.setMovable(True)
        self.tabs.setTabsClosable(True)
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
        export_action.triggered.connect(self.export_data)
        import_action.triggered.connect(self.import_data)
        export_import_menu.addAction(export_action)
        export_import_menu.addAction(import_action)

        # Справка
        help_menu = menubar.addMenu("Справка")
        about_action = QAction("О программе", self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)

    def open_advanced_settings(self):
        """
        Открывает диалоговое окно расширенных настроек с разделением на группы:
        — Уведомления;
        — Настройка компоновки блоков для Windows и Linux с кнопками для изменения порядка.
        """
        dialog = QDialog(self)
        dialog.setWindowTitle("Расширенные настройки")
        dialog.resize(500, 450)
        main_layout = QVBoxLayout(dialog)

        settings = load_settings()
        show_notifications = settings.get("show_notifications", True)

        # Группа уведомлений
        notif_group = QGroupBox("Уведомления", dialog)
        notif_layout = QVBoxLayout(notif_group)
        notifications_checkbox = QCheckBox("Показывать уведомления", dialog)
        notifications_checkbox.setChecked(show_notifications)
        notif_layout.addWidget(notifications_checkbox)
        main_layout.addWidget(notif_group)

        # Группа настройки блоков
        blocks_group = QGroupBox("Настройка блоков", dialog)
        blocks_layout = QVBoxLayout(blocks_group)

        layout_label = QLabel("Настройка компоновки блоков:", dialog)
        blocks_layout.addWidget(layout_label)

        tab_widget = QTabWidget(dialog)

        # Функции для перемещения выбранного элемента вверх/вниз в QListWidget
        def move_item_up(list_widget):
            current_row = list_widget.currentRow()
            if current_row > 0:
                current_item = list_widget.takeItem(current_row)
                list_widget.insertItem(current_row - 1, current_item)
                list_widget.setCurrentRow(current_row - 1)  # <-- фиксируем выделение

        def move_item_down(list_widget):
            current_row = list_widget.currentRow()
            if current_row < list_widget.count() - 1 and current_row != -1:
                current_item = list_widget.takeItem(current_row)
                list_widget.insertItem(current_row + 1, current_item)
                list_widget.setCurrentRow(current_row + 1)  # <-- фиксируем выделение

        # --- Вкладка для Windows ---
        # Создаём контейнер с горизонтальным лэйаутом для списка и кнопок
        windows_tab = QWidget()
        windows_tab_layout = QHBoxLayout(windows_tab)

        windows_list_widget = QListWidget(dialog)
        windows_list_widget.setDragDropMode(QAbstractItemView.InternalMove)
        # Значения по умолчанию для Windows
        default_windows = [
            {"id": "SystemInfoBlock", "name": "Информация о системе"},
            {"id": "CommandsBlock", "name": "Команды управления"},
            {"id": "RDPBlock", "name": "Управление RDP"},
            {"id": "ActiveUsers", "name": "Активные пользователи"},
            {"id": "ScriptsBlock", "name": "Библиотека скриптов"}
        ]
        if "layout_windows" in settings:
            for block in settings["layout_windows"]:
                item = QListWidgetItem(block["name"])
                item.setFlags(item.flags() | Qt.ItemIsUserCheckable | Qt.ItemIsEnabled |
                              Qt.ItemIsSelectable | Qt.ItemIsDragEnabled)
                item.setCheckState(Qt.Checked if block.get("visible", True) else Qt.Unchecked)
                windows_list_widget.addItem(item)
        else:
            for block in default_windows:
                item = QListWidgetItem(block["name"])
                item.setFlags(item.flags() | Qt.ItemIsUserCheckable | Qt.ItemIsEnabled |
                              Qt.ItemIsSelectable | Qt.ItemIsDragEnabled)
                item.setCheckState(Qt.Checked)
                windows_list_widget.addItem(item)

        # Вертикальный лэйаут для стрелок
        windows_arrows_layout = QVBoxLayout()
        up_button_win = QPushButton("↑", dialog)
        down_button_win = QPushButton("↓", dialog)

        button_style = """
            QPushButton {
                font-size: 14px;
                min-width: 30px;
                min-height: 30px;
            }
        """

        up_button_win.setStyleSheet(button_style)
        down_button_win.setStyleSheet(button_style)

        up_button_win.setToolTip("Переместить вверх")
        down_button_win.setToolTip("Переместить вниз")
        up_button_win.clicked.connect(lambda: move_item_up(windows_list_widget))
        down_button_win.clicked.connect(lambda: move_item_down(windows_list_widget))
        windows_arrows_layout.addWidget(up_button_win)
        windows_arrows_layout.addWidget(down_button_win)
        windows_arrows_layout.addStretch()

        windows_tab_layout.addWidget(windows_list_widget)
        windows_tab_layout.addLayout(windows_arrows_layout)
        tab_widget.addTab(windows_tab, "Windows")  # название вкладки: Windows

        # --- Вкладка для Linux ---
        linux_tab = QWidget()
        linux_tab_layout = QHBoxLayout(linux_tab)

        linux_list_widget = QListWidget(dialog)
        linux_list_widget.setDragDropMode(QAbstractItemView.InternalMove)
        default_linux = [
            {"id": "SystemInfoBlock", "name": "Информация о системе"},
            {"id": "CommandsBlock", "name": "Управление хостом"},
            {"id": "NetworkBlock", "name": "Сетевые настройки"},
            {"id": "ProcessManagerBlock", "name": "Процессы"},
            {"id": "ScriptsBlock", "name": "Библиотека скриптов"}
        ]
        if "layout_linux" in settings:
            for block in settings["layout_linux"]:
                item = QListWidgetItem(block["name"])
                item.setFlags(item.flags() | Qt.ItemIsUserCheckable | Qt.ItemIsEnabled |
                              Qt.ItemIsSelectable | Qt.ItemIsDragEnabled)
                item.setCheckState(Qt.Checked if block.get("visible", True) else Qt.Unchecked)
                linux_list_widget.addItem(item)
        else:
            for block in default_linux:
                item = QListWidgetItem(block["name"])
                item.setFlags(item.flags() | Qt.ItemIsUserCheckable | Qt.ItemIsEnabled |
                              Qt.ItemIsSelectable | Qt.ItemIsDragEnabled)
                item.setCheckState(Qt.Checked)
                linux_list_widget.addItem(item)

        linux_arrows_layout = QVBoxLayout()
        up_button_lin = QPushButton("▲", dialog)
        down_button_lin = QPushButton("▼", dialog)
        up_button_lin.setToolTip("Переместить вверх")
        down_button_lin.setToolTip("Переместить вниз")
        up_button_lin.clicked.connect(lambda: move_item_up(linux_list_widget))
        down_button_lin.clicked.connect(lambda: move_item_down(linux_list_widget))
        linux_arrows_layout.addWidget(up_button_lin)
        linux_arrows_layout.addWidget(down_button_lin)
        linux_arrows_layout.addStretch()

        linux_tab_layout.addWidget(linux_list_widget)
        linux_tab_layout.addLayout(linux_arrows_layout)
        tab_widget.addTab(linux_tab, "Linux")  # название вкладки: Linux

        blocks_layout.addWidget(tab_widget)
        main_layout.addWidget(blocks_group)

        # Кнопки OK/Cancel
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel, dialog)
        main_layout.addWidget(button_box)
        button_box.accepted.connect(dialog.accept)
        button_box.rejected.connect(dialog.reject)

        if dialog.exec() == QDialog.Accepted:
            # Сохраняем настройку уведомлений
            settings["show_notifications"] = notifications_checkbox.isChecked()

            # Формируем новую компоновку для Windows
            layout_windows = []
            for i in range(windows_list_widget.count()):
                item = windows_list_widget.item(i)
                layout_windows.append({
                    "name": item.text(),
                    "visible": item.checkState() == Qt.Checked
                })
            settings["layout_windows"] = layout_windows

            # Формируем новую компоновку для Linux
            layout_linux = []
            for i in range(linux_list_widget.count()):
                item = linux_list_widget.item(i)
                layout_linux.append({
                    "name": item.text(),
                    "visible": item.checkState() == Qt.Checked
                })
            settings["layout_linux"] = layout_linux

            save_settings(settings)
            set_notifications_enabled(notifications_checkbox.isChecked())
            Notification(
                "Настройки сохранены",
                "Новые настройки успешно применены.",
                "success",
                duration=3000,
                parent=self
            ).show_notification()

            # Обновляем компоновку во всех открытых вкладках, если метод update_layout() реализован
            for i in range(self.tabs.count()):
                widget = self.tabs.widget(i)
                if hasattr(widget, "update_layout"):
                    widget.update_layout()
            if hasattr(self, "dynamic_tabs"):
                for i in range(self.dynamic_tabs.count()):
                    tab = self.dynamic_tabs.widget(i)
                    if hasattr(tab, "update_layout"):
                        tab.update_layout()

    def export_data(self):
        """Экспортирует settings.json, базу данных и папку scripts в единый ZIP-архив."""
        export_path, _ = QFileDialog.getSaveFileName(
            self,
            "Экспорт данных",
            PROJECT_ROOT,
            "Zip Archive (*.zip)"
        )
        if not export_path:
            return

        try:
            exported_count = 0
            with zipfile.ZipFile(export_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                if os.path.exists(SETTINGS_FILE):
                    zipf.write(SETTINGS_FILE, arcname="settings.json")
                    exported_count += 1

                if getattr(sys, 'frozen', False):
                    db_path = os.path.join(PROJECT_ROOT, "mtadmin.sqlite")
                else:
                    db_path = os.path.join(PROJECT_ROOT, "database", "mtadmin.sqlite")
                if os.path.exists(db_path):
                    arcname = os.path.relpath(db_path, PROJECT_ROOT)
                    zipf.write(db_path, arcname=arcname)
                    exported_count += 1

                if os.path.exists(SCRIPTS_FOLDER):
                    for root, dirs, files in os.walk(SCRIPTS_FOLDER):
                        for file in files:
                            file_path = os.path.join(root, file)
                            arcname = os.path.relpath(file_path, PROJECT_ROOT)
                            zipf.write(file_path, arcname=arcname)
                            exported_count += 1

            if exported_count == 0:
                QMessageBox.warning(self, "Экспорт данных", "Нет данных для экспорта.")
            else:
                QMessageBox.information(self, "Экспорт данных", "Экспорт данных успешно завершён.")
        except Exception as e:
            QMessageBox.critical(self, "Ошибка экспорта", f"Ошибка при экспорте данных:\n{str(e)}")

    def import_data(self):
        """Импортирует настройки, базу данных и папку scripts из ZIP-архива."""
        import_path, _ = QFileDialog.getOpenFileName(
            self,
            "Импорт данных",
            PROJECT_ROOT,
            "Zip Archive (*.zip)"
        )
        if not import_path:
            return

        reply = QMessageBox.question(
            self,
            "Импорт данных",
            "Импорт данных перезапишет текущие настройки, базу данных и скрипты. Продолжить?",
            QMessageBox.Yes | QMessageBox.No
        )
        if reply != QMessageBox.Yes:
            return

        try:
            with zipfile.ZipFile(import_path, 'r') as zipf:
                if os.path.exists(SCRIPTS_FOLDER):
                    shutil.rmtree(SCRIPTS_FOLDER)
                zipf.extractall(PROJECT_ROOT)
            QMessageBox.information(self, "Импорт данных",
                                    "Импорт данных успешно завершён.\nДля применения изменений перезапустите программу.")
        except Exception as e:
            QMessageBox.critical(self, "Ошибка импорта", f"Ошибка при импорте данных:\n{str(e)}")

    def resizeEvent(self, event):
        """Обновляем позиции уведомлений при изменении размера окна."""
        for notif in Notification.get_active_notifications():
            notif.update_position()
        super().resizeEvent(event)

    def create_tray_icon(self):
        """Создание и настройка иконки для системного трея."""
        if os.path.exists(LOGO_FILE):
            tray_icon = QIcon(LOGO_FILE)
        else:
            tray_icon = QIcon()

        self.tray_icon = QSystemTrayIcon(tray_icon, self)
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
        Notification(
            f"Тема изменена на: {theme_name}",
            f"Тема {theme_name} применена.",
            "success",
            duration=3000,
            parent=self
        ).show_notification()

    def apply_theme(self):
        if self.current_theme == "Без темы":
            self.setStyleSheet("")
        else:
            self.setStyleSheet(apply_theme(self.current_theme))

    def moveEvent(self, event):
        for notif in Notification.get_active_notifications():
            notif.update_position()
        super().moveEvent(event)

    def show_about(self):
        # Подготавливаем логотип для отображения в About-диалоге.
        logo_html = ""
        if os.path.exists(LOGO_FILE):
            try:
                with open(LOGO_FILE, "rb") as img_file:
                    img_data = img_file.read()
                img_base64 = base64.b64encode(img_data).decode("utf-8")
                logo_html = f'<div align="center"><img src="data:image/jpeg;base64,{img_base64}" width="150" height="150"></div>'
            except Exception as e:
                print("Ошибка загрузки логотипа:", e)
        version = "0.2"
        about_text = f"""
        {logo_html}
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

        # Создаём динамические вкладки (здесь внутри уже создаётся логика подключения ПК)
        self.dynamic_tabs = DynamicTabs(theme_name=self.current_theme)
        self.dynamic_tabs.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        layout.addWidget(self.dynamic_tabs)
        widget.setLayout(layout)
        return widget

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
