from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QLineEdit, QLabel,
    QCheckBox, QListWidget, QAbstractItemView, QMenu, QMessageBox,
    QFileDialog, QInputDialog, QSizePolicy, QListWidgetItem
)
from PySide6.QtCore import Qt, Signal, QObject, QThread
from old_project.windows_gui.commands import run_psexec, run_winrs, run_compmgmt, run_rdp, open_c_drive, run_shadow_rdp, get_shadow_session_id
from old_project.windows_gui.scripts import ScriptManager
from old_project.windows_gui.active_users import get_active_users
from old_project.windows_gui.system_info import get_system_info
from old_project.notification import NotificationManager, Notification
from old_project.styles import NOTIFICATION_STYLES
import logging
from old_project.windows_gui.rdp_management import (
    is_rdp_enabled, enable_rdp,
    get_rdp_port, set_rdp_port,
    get_rdp_users, add_rdp_user, remove_rdp_user
)
from .session_manager import PowerShellSessionManager

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class Worker(QObject):
    finished = Signal(object)
    error = Signal(str)

    def __init__(self, func, *args, **kwargs):
        super().__init__()
        self.func = func
        self.args = args
        self.kwargs = kwargs

    def run(self):
        try:
            result = self.func(*self.args, **self.kwargs)
            self.finished.emit(result)
        except Exception as e:
            self.error.emit(str(e))


class WindowsWindow(QWidget):
    refresh_requested = Signal()
    close_requested = Signal()

    def __init__(self, ip, os_name):
        super().__init__()
        self.ip = ip
        self.os_name = os_name
        self.session_manager = PowerShellSessionManager(ip)
        if not self.session_manager.connect():
            raise ConnectionError(f"Не удалось подключиться к {ip}")
        self.notification_manager = NotificationManager(self)
        self.script_manager = ScriptManager()
        self.is_refreshing = False

        self._init_ui()
        self._connect_signals()
        self._init_session()
        self._initial_data_load()

    def _init_ui(self):
        main_layout = QHBoxLayout(self)

        # Left Panel
        left_panel = QVBoxLayout()
        left_panel.addWidget(self._create_commands_group())
        left_panel.addWidget(self._create_scripts_group())

        # Right Panel
        right_panel = QVBoxLayout()
        right_panel.addWidget(self._create_active_users_group())
        right_panel.addWidget(self._create_rdp_management_group())
        right_panel.addWidget(self._create_system_info_group())
        right_panel.addLayout(self._create_control_buttons())

        main_layout.addLayout(left_panel, stretch=1)
        main_layout.addLayout(right_panel, stretch=1)

    def _connect_signals(self):
        self.refresh_requested.connect(self._refresh_all_data)
        self.refresh_btn.clicked.connect(self.refresh_requested.emit)
        self.close_btn.clicked.connect(self.close_requested.emit)

    def _init_session(self):
        if not self.session_manager.connect():
            self._show_error("Не удалось установить соединение с сервером")

    def _initial_data_load(self):
        self._start_worker(
            self._load_initial_data,
            success_callback=lambda: self.refresh_requested.emit()
        )

    def _load_initial_data(self):
        return {
            'system_info': get_system_info(self.session_manager.session),
            'rdp_status': is_rdp_enabled(self.session_manager.session),
            'users': get_active_users(self.ip)
        }

    def _start_worker(self, func, success_callback=None, error_callback=None):
        thread = QThread()
        worker = Worker(func)
        worker.moveToThread(thread)

        worker.finished.connect(lambda res: self._handle_worker_result(res, success_callback))
        worker.error.connect(lambda err: self._handle_worker_error(err, error_callback))
        thread.started.connect(worker.run)
        thread.finished.connect(thread.deleteLater)
        thread.start()

    def _handle_worker_result(self, result, callback):
        if callback:
            callback(result)
        self.is_refreshing = False

    def _handle_worker_error(self, error, callback):
        self._show_error(error)
        if callback:
            callback()
        self.is_refreshing = False

    def _refresh_all_data(self):
        if self.is_refreshing:
            return
        self.is_refreshing = True

        self._start_worker(
            self._fetch_all_data,
            success_callback=self._update_all_ui
        )

    def _fetch_all_data(self):
        return {
            'system_info': get_system_info(self.session_manager.session),
            'rdp_users': get_rdp_users(self.session_manager.session),
            'active_users': get_active_users(self.ip),
            'rdp_port': get_rdp_port(self.session_manager.session)
        }

    def _update_all_ui(self, data):
        try:
            self._update_system_info(data['system_info'])
            self._update_rdp_users_list(data['rdp_users'])
            self._update_active_users(data['active_users'])
            self._update_rdp_port(data['rdp_port'])
        except Exception as e:
            self._show_error(str(e))

    def _update_system_info(self, system_info):
        try:
            if 'error' in system_info:
                raise Exception(system_info['error'])

            self.cpu_label.setText(f"CPU: {system_info.get('cpu_usage', 0)}%")
            mem_info = system_info.get('memory', {})
            self.ram_label.setText(
                f"RAM: {mem_info.get('used_mb', 0):.2f}/{mem_info.get('total_mb', 0):.2f} MB "
                f"({mem_info.get('percent_used', 0)}%)"
            )

            # Clear existing disk labels
            for label in self.disk_labels.values():
                self.disks_layout.removeWidget(label)
                label.deleteLater()
            self.disk_labels.clear()

            # Add new disk info
            for disk in system_info.get('disks', []):
                label = QLabel(
                    f"{disk['mount']}: Свободно {disk['free']:.2f} GB, Всего {disk['total']:.2f} GB "
                    f"({disk['percent_used']}%)"
                )
                self.disks_layout.addWidget(label)
                self.disk_labels[disk['mount']] = label

        except Exception as e:
            logger.error(f"Ошибка обновления информации о системе: {str(e)}")
            self.show_notification(f"Ошибка обновления системы: {str(e)}", "error")

    def _update_rdp_users_list(self, users):
        self.rdp_users_list.clear()
        for user in users:
            item = QListWidgetItem(user)
            item.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable)
            self.rdp_users_list.addItem(item)

    def _update_active_users(self, users_data):
        self.users_table.setRowCount(len(users_data))
        for row, user in enumerate(users_data):
            self.users_table.setItem(row, 0, QTableWidgetItem(str(row + 1)))
            self.users_table.setItem(row, 1, QTableWidgetItem(user.get("username", "N/A")))
            self.users_table.setItem(row, 2, QTableWidgetItem(user.get("state", "N/A")))

    def _update_rdp_port(self, port):
        self.rdp_port_input.setText(str(port))

    def _create_commands_group(self):
        group = QGroupBox("Команды")
        layout = QVBoxLayout()

        commands = [
            ("PSExec", self._on_psexec_clicked),
            ("WinRS", self._on_winrs_clicked),
            ("compmgmt.msc", self._on_compmgmt_clicked),
            ("RDP", self._on_rdp_clicked),
            ("C:\\", self._on_c_drive_clicked),
            ("Shadow RDP", self._on_shadow_rdp_clicked)
        ]

        for text, callback in commands:
            btn = QPushButton(text)
            btn.clicked.connect(callback)
            btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
            layout.addWidget(btn)

        group.setLayout(layout)
        return group

    def _create_scripts_group(self):
        group = QGroupBox("Скрипты")
        layout = QVBoxLayout()

        # Кнопки управления
        btn_layout = QHBoxLayout()
        self.add_script_btn = QPushButton("Добавить")
        self.remove_script_btn = QPushButton("Удалить")
        btn_layout.addWidget(self.add_script_btn)
        btn_layout.addWidget(self.remove_script_btn)

        self.script_list = QListWidget()
        self.script_list.setContextMenuPolicy(Qt.CustomContextMenu)
        self.script_list.customContextMenuRequested.connect(self._show_script_context_menu)
        self._update_script_list()

        self.add_script_btn.clicked.connect(self._add_script)
        self.remove_script_btn.clicked.connect(self._remove_script)
        self.script_list.itemDoubleClicked.connect(self._execute_script)

        layout.addLayout(btn_layout)
        layout.addWidget(self.script_list)
        group.setLayout(layout)
        return group

    def _create_active_users_group(self):
        group = QGroupBox("Активные пользователи")
        layout = QVBoxLayout()

        self.users_table = QTableWidget(0, 3)
        self.users_table.setHorizontalHeaderLabels(["№", "Логин", "Тип подключения"])
        self.users_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.users_table.setEditTriggers(QAbstractItemView.NoEditTriggers)

        layout.addWidget(self.users_table)
        group.setLayout(layout)
        return group

    def _create_rdp_management_group(self):
        group = QGroupBox("Управление RDP")
        layout = QVBoxLayout()

        # RDP Toggle
        self.rdp_checkbox = QCheckBox("RDP Включен")
        self.rdp_checkbox.stateChanged.connect(self._on_rdp_toggle)

        # Port Management
        port_layout = QHBoxLayout()
        self.rdp_port_input = QLineEdit()
        self.rdp_port_input.setPlaceholderText("Порт RDP")
        change_port_btn = QPushButton("Изменить")
        change_port_btn.clicked.connect(self._change_rdp_port)
        port_layout.addWidget(self.rdp_port_input)
        port_layout.addWidget(change_port_btn)

        # Users List
        self.rdp_users_list = QListWidget()
        self.rdp_users_list.setContextMenuPolicy(Qt.CustomContextMenu)
        self.rdp_users_list.customContextMenuRequested.connect(self._show_rdp_users_context_menu)

        # Add User
        add_user_layout = QHBoxLayout()
        self.new_user_input = QLineEdit()
        self.new_user_input.setPlaceholderText("Новый пользователь")
        add_user_btn = QPushButton("Добавить")
        add_user_btn.clicked.connect(self._add_rdp_user)
        add_user_layout.addWidget(self.new_user_input)
        add_user_layout.addWidget(add_user_btn)

        layout.addWidget(self.rdp_checkbox)
        layout.addLayout(port_layout)
        layout.addWidget(self.rdp_users_list)
        layout.addLayout(add_user_layout)
        return group

    def _create_system_info_group(self):
        group = QGroupBox("Состояние системы")
        layout = QVBoxLayout()

        self.cpu_label = QLabel("CPU: Н/Д")
        self.ram_label = QLabel("RAM: Н/Д")
        self.disks_layout = QVBoxLayout()
        self.disk_labels = {}

        layout.addWidget(self.cpu_label)
        layout.addWidget(self.ram_label)
        layout.addLayout(self.disks_layout)
        group.setLayout(layout)
        return group

    def _create_control_buttons(self):
        layout = QHBoxLayout()
        self.refresh_btn = QPushButton("Обновить")
        self.close_btn = QPushButton("Закрыть")
        layout.addWidget(self.refresh_btn)
        layout.addWidget(self.close_btn)
        return layout

    def closeEvent(self, event):
        self.session_manager.close()
        super().closeEvent(event)

    def show_notification(self, message, style_type="default"):
        style = NOTIFICATION_STYLES.get(style_type, {})
        notification = Notification(self, message, style=style)
        self.notification_manager.add_notification(notification)

    def resizeEvent(self, event):
        self.notification_manager._update_positions()
        super().resizeEvent(event)

    def _update_script_list(self):
        self.script_list.clear()
        for script in self.script_manager.get_scripts():
            self.script_list.addItem(script["name"])

    def _add_script(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Выберите скрипт",
            "",
            "PowerShell Scripts (*.ps1)"
        )

        if file_path:
            name, ok = QInputDialog.getText(
                self,
                "Имя скрипта",
                "Введите отображаемое имя:"
            )

            if ok and name:
                try:
                    self.script_manager.add_script(file_path, name)
                    self._update_script_list()
                except Exception as e:
                    self._show_error_message(str(e))

    def _remove_script(self):
        selected = self.script_list.currentItem()
        if selected:
            name = selected.text()
            reply = QMessageBox.question(
                self,
                "Подтверждение",
                f"Удалить скрипт '{name}'?",
                QMessageBox.Yes | QMessageBox.No
            )

            if reply == QMessageBox.Yes:
                try:
                    self.script_manager.delete_script(name)
                    self._update_script_list()
                except Exception as e:
                    self._show_error_message(str(e))

    def _execute_script(self, item):
        script_name = item.text()
        try:
            # Передаем объект сессии, а не IP-адрес.
            self.script_manager.execute_script(script_name, self.session_manager.session)
            self.show_notification(f"Скрипт '{script_name}' успешно выполнен", "success")
        except Exception as e:
            self.show_notification(f"Ошибка выполнения: {str(e)}", "error")

    def _show_script_context_menu(self, pos):
        menu = QMenu()

        rename_action = menu.addAction("Переименовать")
        remove_action = menu.addAction("Удалить")

        action = menu.exec(self.script_list.mapToGlobal(pos))

        selected_item = self.script_list.currentItem()
        if selected_item:
            script_name = selected_item.text()
            if action == rename_action:
                self._rename_script(script_name)
            elif action == remove_action:
                self._remove_script()

    def _rename_script(self, old_name):
        new_name, ok = QInputDialog.getText(self, "Переименование", "Введите новое имя:")

        if ok and new_name:
            try:
                self.script_manager.rename_script(old_name, new_name)
                self._update_script_list()
            except Exception as e:
                self._show_error_message(str(e))

    def _update_rdp_status(self):
        try:
            # Получаем актуальный статус с сервера
            current_state = is_rdp_enabled(self.session_manager.session)
            logger.debug(f"Actual RDP state from server: {current_state}")

            self.rdp_checkbox.blockSignals(True)
            self.rdp_checkbox.setChecked(current_state)
            self.rdp_checkbox.blockSignals(False)

            # Обновляем список пользователей
            self._update_rdp_users_list()

        except Exception as e:
            logger.error(f"RDP status update failed: {str(e)}")

    def _on_rdp_toggle(self, state):
        target_state = self.rdp_checkbox.isChecked()

        def rdp_operation():
            enable_rdp(self.session_manager.session, target_state)
            return target_state

        def success_callback(result):
            self.refresh_requested.emit()
            self.show_notification("Состояние RDP успешно изменено", "success")

        def error_callback(error):
            self.rdp_checkbox.setChecked(not target_state)
            self.show_notification(f"Ошибка: {error}", "error")

        self._start_worker(
            rdp_operation,
            success_callback=success_callback,
            error_callback=error_callback
        )

    def _change_rdp_port(self):
        port_text = self.rdp_port_input.text()
        if not port_text.isdigit():
            self.show_notification("Порт должен быть числом", "error")
            return

        port = int(port_text)
        if not (1 <= port <= 65535):
            self.show_notification("Порт должен быть в диапазоне 1-65535", "error")
            return

        self._start_worker(
            lambda: set_rdp_port(self.session_manager.session, port),
            success_callback=lambda: self.refresh_requested.emit(),
            error_callback=lambda e: self.show_notification(f"Ошибка: {e}", "error")
        )

    def _add_rdp_user(self):
        username = self.new_user_input.text().strip()
        if not username:
            return

        def add_operation():
            add_rdp_user(self.session_manager.session, username)
            return username

        def success_callback(username):
            self.new_user_input.clear()
            self.refresh_requested.emit()
            self.show_notification(f"Пользователь {username} добавлен", "success")

        self._start_worker(
            add_operation,
            success_callback=success_callback,
            error_callback=lambda e: self.show_notification(str(e), "error")
        )

    def _show_rdp_users_context_menu(self, pos):
        menu = QMenu()
        remove_action = menu.addAction("Удалить")
        action = menu.exec(self.rdp_users_list.mapToGlobal(pos))

        if action == remove_action:
            selected_item = self.rdp_users_list.currentItem()
            if selected_item:
                username = selected_item.text()
                self._start_worker(
                    lambda: remove_rdp_user(self.session_manager.session, f"NCC\\{username}"),
                    success_callback=lambda: self.refresh_requested.emit(),
                    error_callback=lambda e: self.show_notification(f"Ошибка удаления: {e}", "error")
                )

    def _on_psexec_clicked(self):
        try:
            run_psexec(self.ip)
            self.show_notification("PSExec успешно запущен", "success")
        except Exception as e:
            self.show_notification(f"Ошибка при запуске PSExec: {str(e)}", "error")

    def _on_winrs_clicked(self):
        try:
            run_winrs(self.ip)
            self.show_notification("WinRS успешно запущен", "success")
        except Exception as e:
            self.show_notification(f"Ошибка при запуске WinRS: {str(e)}", "error")

    def _on_compmgmt_clicked(self):
        try:
            run_compmgmt(self.ip)
            self.show_notification("compmgmt.msc успешно запущен", "success")
        except Exception as e:
            self.show_notification(f"Ошибка при запуске compmgmt.msc: {str(e)}", "error")

    def _on_rdp_clicked(self):
        try:
            run_rdp(self.ip)
            self.show_notification("RDP подключение запущено", "success")
        except Exception as e:
            self.show_notification(f"Ошибка при запуске RDP: {str(e)}", "error")

    def _on_c_drive_clicked(self):
        try:
            open_c_drive(self.ip)
            self.show_notification("Диск C: успешно открыт", "success")
        except Exception as e:
            self.show_notification(f"Ошибка при открытии диска C:: {str(e)}", "error")

    def _on_shadow_rdp_clicked(self):
        try:
            session_id = get_shadow_session_id(self.ip)
            run_shadow_rdp(self.ip, session_id)
            self.show_notification("Shadow RDP подключение установлено", "success")
        except Exception as e:
            self.show_notification(f"Ошибка при подключении через Shadow RDP: {str(e)}", "error")

    def _show_error(self, message):
        QMessageBox.critical(self, "Ошибка", message)
        logger.error(message)