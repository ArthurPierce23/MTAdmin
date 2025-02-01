from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QTabWidget, QLabel, QPushButton,
    QTextEdit, QTableWidget, QTableWidgetItem, QHeaderView,
    QGroupBox, QDialog, QMessageBox, QListWidget, QInputDialog, QMenu
)
from PySide6.QtCore import Qt, QTimer
from linux_gui.auth import AuthDialog
from linux_gui.system_info import get_system_info
from linux_gui.commands import SSHConnection, connect_vnc, connect_ssh, connect_ftp, connect_telnet
from linux_gui.process_manager import get_process_list
from linux_gui.network import get_network_info
from linux_gui.logs import get_system_logs
from linux_gui.scripts import (
    list_scripts, add_script,
    delete_script, rename_script,
    execute_script
)
import subprocess
import platform
import logging
import paramiko
import shutil
from notification import Notification, NotificationManager
from styles import NOTIFICATION_STYLES


logger = logging.getLogger(__name__)


class LinuxWindow(QWidget):
    """GUI для работы с Linux-системами"""

    def __init__(self, ip, os_name):
        super().__init__()
        self.setAttribute(Qt.WA_DeleteOnClose)
        self.ip = ip
        self.os_name = os_name
        self.username = None
        self.password = None
        self.ssh_connection = None

        self.setWindowTitle(f"Linux: {ip}")
        self.resize(800, 600)

        # Окно авторизации
        self._request_auth()

        # Основной layout
        layout = QVBoxLayout(self)
        self.tabs = QTabWidget()
        layout.addWidget(self.tabs)

        # Вкладки
        self._init_system_info_tab()
        self._init_process_tab()
        self._init_network_tab()
        self._init_logs_tab()
        self._init_actions_tab()  # ✅ Добавляем вкладку "Действия"
        self.tabs.currentChanged.connect(self._on_tab_change)
        self._init_scripts_context_menu()
        self.notification_manager = NotificationManager(self)

    def show_notification(self, message, style_type="default"):
        style = NOTIFICATION_STYLES.get(style_type, {})
        notification = Notification(self, message, style=style)
        self.notification_manager.add_notification(notification)

    def resizeEvent(self, event):
        self.notification_manager._update_positions()
        super().resizeEvent(event)

    def moveEvent(self, event):
        self.notification_manager._update_positions()
        super().moveEvent(event)

    def showEvent(self, event):
        self.notification_manager._update_positions()
        super().showEvent(event)

    def _on_tab_change(self, index):
        """Автоматическое обновление данных при переключении вкладок"""
        tab_name = self.tabs.tabText(index)

        if tab_name == "Система":
            self._update_system_info()
        elif tab_name == "Процессы":
            self._update_process_list()
        elif tab_name == "Сеть":
            self._update_network_info()
        elif tab_name == "Журналы":
            self._update_logs()
        elif tab_name == "Действия":
            self._update_scripts_list()

    def _request_auth(self):
        dialog = AuthDialog(self.ip)
        if dialog.exec() != QDialog.DialogCode.Accepted:
            self.close()
            return

        self.username, self.password = dialog.get_credentials()

        try:
            self.ssh_connection = SSHConnection(self.ip, self.username, self.password)
            self.ssh_connection.connect()
            output, _ = self.ssh_connection.execute_command("echo 'Auth check'")
            if "Auth check" not in output:
                raise paramiko.AuthenticationException()
        except paramiko.AuthenticationException:
            self.show_notification("Неверные логин или пароль", "error")
            self.close()
        except Exception as e:
            self.show_notification(f"Ошибка подключения: {str(e)}", "error")
            self.close()

    def _init_system_info_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)

        self.system_info_table = QTableWidget(0, 2)
        self.system_info_table.setHorizontalHeaderLabels(["Параметр", "Значение"])
        self.system_info_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.system_info_table.setEditTriggers(QTableWidget.NoEditTriggers)

        btn_refresh = QPushButton("Обновить информацию")
        btn_refresh.clicked.connect(self._update_system_info)

        layout.addWidget(self.system_info_table)
        layout.addWidget(btn_refresh)
        self.tabs.addTab(tab, "Система")

        self._update_system_info()
        btn_refresh.clicked.connect(lambda: self._update_system_info(manual=True))  # Обновлено


    def _update_system_info(self, manual=False):
        try:
            info = get_system_info(self.ssh_connection)
            self.system_info_table.setRowCount(0)
            for key, value in info.items():
                self._add_table_row(self.system_info_table, [key, value])
            if manual:
                self.show_notification("Системная информация обновлена", "success")  # Добавлено
        except Exception as e:
            self.show_notification(f"Ошибка загрузки данных: {str(e)}", "error")

    def _create_table(self, headers, stretch_mode=QHeaderView.Stretch):
        """Создает таблицу с заданными заголовками и настройками."""
        table = QTableWidget(0, len(headers))
        table.setHorizontalHeaderLabels(headers)
        table.horizontalHeader().setSectionResizeMode(stretch_mode)
        table.setEditTriggers(QTableWidget.NoEditTriggers)
        return table

    def handle_errors(func):
        """Декоратор для обработки ошибок в методах обновления."""

        def wrapper(self, *args, **kwargs):
            try:
                return func(self, *args, **kwargs)
            except Exception as e:
                logger.exception(f"Ошибка в {func.__name__}: {e}")
                QMessageBox.critical(self, "Ошибка", f"Ошибка загрузки данных: {str(e)}")

        return wrapper

    def _update_logs(self, manual=False):
        """Обновляет системные журналы"""
        try:
            logs = get_system_logs(self.ssh_connection)
            self.logs_text.setText(logs)
            if manual:
                self.show_notification("Логи успешно обновлены", "success")  # Добавлено
        except Exception as e:
            self.show_notification(f"Ошибка загрузки журналов: {str(e)}", "error")  # Исправлено

    def closeEvent(self, event):
        """Закрытие окна и завершение SSH-сессии"""
        logger.info(f"Закрытие окна для {self.ip}")

        if hasattr(self, 'process_timer'):
            self.process_timer.stop()
            logger.info("Таймер обновления процессов остановлен.")

        if self.ssh_connection:
            self.ssh_connection.close()
            logger.info(f"SSH-сессия с {self.ip} закрыта.")

        super().closeEvent(event)

    def _init_process_tab(self):
        """Инициализирует вкладку с процессами и настраивает автообновление."""
        self.process_table = self._create_table(["PID", "Имя", "CPU %"])
        self.process_timer = QTimer(self)
        self.process_timer.timeout.connect(self._update_process_list)
        self.process_timer.start(5000)  # Обновление каждые 5 секунд

    def _update_process_list(self):
        """Обновляет список процессов"""
        try:
            logger.info(f"Обновление списка процессов для {self.ip}")
            process_list = get_process_list(self.ssh_connection)
            self.process_table.setRowCount(0)

            for row in process_list:
                row_position = self.process_table.rowCount()
                self.process_table.insertRow(row_position)
                for col, value in enumerate(row):
                    self.process_table.setItem(row_position, col, QTableWidgetItem(str(value)))

            logger.info(f"Список процессов успешно обновлён для {self.ip}")

        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка загрузки процессов: {str(e)}")
            logger.exception(f"Ошибка при обновлении списка процессов для {self.ip}: {e}")

    def _init_network_tab(self):
        """Вкладка: Сетевые настройки"""
        tab = QWidget()
        layout = QVBoxLayout(tab)

        # Таблица для IP-адресов и интерфейсов
        self.network_table = QTableWidget(0, 2)
        self.network_table.setHorizontalHeaderLabels(["Интерфейс", "IP-адрес"])
        self.network_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.network_table.setEditTriggers(QTableWidget.NoEditTriggers)

        # Текстовое поле для активных соединений
        self.connections_text = QTextEdit()
        self.connections_text.setReadOnly(True)

        btn_refresh = QPushButton("Обновить информацию о сети")
        btn_refresh.clicked.connect(self._update_network_info)

        layout.addWidget(self.network_table)
        layout.addWidget(QLabel("Активные подключения:"))
        layout.addWidget(self.connections_text)
        layout.addWidget(btn_refresh)
        self.tabs.addTab(tab, "Сеть")

        self._update_network_info()
        btn_refresh.clicked.connect(lambda: self._update_network_info(manual=True))  # Обновлено

    def _update_network_info(self, manual=False):
        try:
            network_info = get_network_info(self.ssh_connection)
            self.network_table.setRowCount(0)
            max_len = max(len(network_info["Interfaces"]), len(network_info["IP Addresses"]))
            for i in range(max_len):
                iface = network_info["Interfaces"][i] if i < len(network_info["Interfaces"]) else "N/A"
                ip = network_info["IP Addresses"][i] if i < len(network_info["IP Addresses"]) else "N/A"
                self._add_table_row(self.network_table, [iface, ip])
            if manual:
                self.show_notification("Сетевая информация обновлена", "success")  # Добавлено
        except Exception as e:
            self.show_notification(f"Ошибка сетевых данных: {str(e)}", "error")

    def _add_table_row(self, table, items):
        """Добавляет строку с данными в таблицу."""
        row = table.rowCount()
        table.insertRow(row)
        for col, text in enumerate(items):
            table.setItem(row, col, QTableWidgetItem(str(text)))

    def _init_logs_tab(self):
        """Вкладка: Журналы системы"""
        tab = QWidget()
        layout = QVBoxLayout(tab)

        self.logs_text = QTextEdit()
        self.logs_text.setReadOnly(True)
        self.logs_text.setText("Загрузка журналов...")

        btn_refresh = QPushButton("Обновить логи")
        btn_refresh.clicked.connect(lambda: self._update_logs(manual=True))  # Исправлено

        layout.addWidget(self.logs_text)
        layout.addWidget(btn_refresh)
        self.tabs.addTab(tab, "Журналы")

    def _show_stub(self, feature_name):
        """Показывает заглушку для функций"""
        stub_text = QTextEdit()
        stub_text.setText(f"Функция {feature_name} пока не реализована.")
        self.tabs.addTab(stub_text, feature_name)

    def _init_actions_tab(self):
        """Инициализирует вкладку с действиями (команды + скрипты)"""
        tab = QWidget()
        layout = QVBoxLayout(tab)

        # === Команды ===
        commands_box = QGroupBox("Команды")
        commands_layout = QVBoxLayout()

        connection_buttons = [
            ("ssh", connect_ssh, [self.ip, self.username]),  # command_name в нижнем регистре
            ("ftp", connect_ftp, [self.ip]),
            ("telnet", connect_telnet, [self.ip]),
            ("vnc", connect_vnc, [self.ip]),
        ]

        for label, func, args in connection_buttons:
            btn = QPushButton(f"Подключиться по {label.upper()}")
            # Передаем все три аргумента в правильном порядке:
            btn.clicked.connect(lambda _, f=func, cmd=label, a=args: self._handle_connection(f, cmd, a))
            commands_layout.addWidget(btn)

        commands_box.setLayout(commands_layout)

        # === Скрипты ===
        scripts_box = QGroupBox("Управление скриптами")
        scripts_layout = QVBoxLayout()

        # Список скриптов
        self.scripts_list = QListWidget()
        self.scripts_list.itemDoubleClicked.connect(self._execute_selected_script)
        self._update_scripts_list()

        # Контекстное меню
        self.scripts_list.setContextMenuPolicy(Qt.CustomContextMenu)
        self.scripts_list.customContextMenuRequested.connect(self._show_scripts_context_menu)

        # Кнопки управления
        btn_add = QPushButton("Добавить скрипт")
        btn_add.clicked.connect(self._add_new_script)

        btn_delete = QPushButton("Удалить скрипт")
        btn_delete.clicked.connect(self._delete_selected_script)

        scripts_layout.addWidget(self.scripts_list)
        scripts_layout.addWidget(btn_add)
        scripts_layout.addWidget(btn_delete)

        scripts_box.setLayout(scripts_layout)

        layout.addWidget(commands_box)
        layout.addWidget(scripts_box)
        self.tabs.addTab(tab, "Действия")

    def _handle_connection(self, connection_func, command_name, args):
        # Логика метода остается без изменений
        if command_name and not shutil.which(command_name):
            self.show_notification(
                f"Утилита '{command_name}' не найдена. Установите её",
                "error"
            )
            return

        if command_name == "vnc" and platform.system() != "Windows":
            if not shutil.which("vncviewer"):
                self.show_notification(
                    "Утилита vncviewer не найдена. Установите tightvnc или аналогичный пакет",
                    "error"
                )
                return

        try:
            connection_func(*args)
            self.show_notification(f"Подключение {command_name} установлено", "success")
        except Exception as e:
            self.show_notification(f"Ошибка подключения: {str(e)}", "error")

    # === Методы для команд ===
    def _run_command(self, command):
        output, error = self.ssh_connection.execute_command(command)
        QMessageBox.information(self, "Результат", output if output else error)

    def _run_custom_command(self):
        command, ok = QInputDialog.getText(self, "Пользовательская команда", "Введите команду:")
        if ok and command:
            self._run_command(command)

    # === Методы для скриптов ===
    def _update_scripts_list(self):
        """Обновляет список доступных скриптов"""
        self.scripts_list.clear()
        self.scripts_list.addItems(list_scripts())

    def _add_new_script(self):
        """Диалог добавления нового скрипта"""
        name, ok = QInputDialog.getText(self, "Новый скрипт", "Имя скрипта:")
        if not ok or not name:
            return

        content, ok = QInputDialog.getMultiLineText(
            self,
            "Содержимое скрипта",
            "Введите bash-команды:",
            "#!/bin/bash\n\n"
        )
        if ok and content:
            add_script(name, content)
            self._update_scripts_list()

    def _delete_selected_script(self):
        if item := self.scripts_list.currentItem():
            reply = QMessageBox.question(
                self,
                "Подтверждение",
                f"Удалить скрипт '{item.text()}'?",
                QMessageBox.Yes | QMessageBox.No
            )
            if reply == QMessageBox.Yes:
                delete_script(item.text())
                self.show_notification(f"Скрипт '{item.text()}' удален", "success")
                self._update_scripts_list()

    def _rename_selected_script(self, item):
        """Переименование скрипта через контекстное меню"""
        old_name = item.text()
        new_name, ok = QInputDialog.getText(
            self,
            "Переименовать скрипт",
            "Новое имя:",
            text=old_name
        )
        if ok and new_name:
            rename_script(old_name, new_name)
            self._update_scripts_list()

    def _execute_selected_script(self, item):
        script_name = item.text()
        try:
            output, error = execute_script(self.ssh_connection, script_name)
            result = output if output else error
            self.show_notification(
                f"Скрипт '{script_name}' выполнен: {result[:100]}...",
                "success" if output else "error"
            )
        except Exception as e:
            self.show_notification(f"Ошибка выполнения: {str(e)}", "error")

    def _init_scripts_context_menu(self):
        self.scripts_list.setContextMenuPolicy(Qt.CustomContextMenu)
        self.scripts_list.customContextMenuRequested.connect(self._show_scripts_context_menu)

    def _show_scripts_context_menu(self, pos):
        """Контекстное меню для скриптов"""
        menu = QMenu()
        rename_action = menu.addAction("✏️ Переименовать")
        delete_action = menu.addAction("🗑️ Удалить")

        if item := self.scripts_list.itemAt(pos):
            action = menu.exec_(self.scripts_list.mapToGlobal(pos))
            if action == rename_action:
                self._rename_selected_script(item)
            elif action == delete_action:
                self._delete_selected_script()

