from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QLineEdit, QLabel,
    QCheckBox, QListWidget, QAbstractItemView, QMenu, QMessageBox,
    QFileDialog, QInputDialog, QSizePolicy
)
from PySide6.QtCore import Qt, Signal, QTimer, QMetaObject
from PySide6.QtGui import QContextMenuEvent
from windows_gui.commands import run_psexec, run_winrs, run_compmgmt, run_rdp, open_c_drive, run_shadow_rdp, get_shadow_session_id
from windows_gui.scripts import ScriptManager
from windows_gui.active_users import get_active_users

class WindowsWindow(QWidget):
    refresh_requested = Signal()
    close_requested = Signal()

    def __init__(self, ip, os_name):
        super().__init__()
        self.ip = ip
        self.os_name = os_name
        self.script_manager = ScriptManager()

        # Создаём UI до вызова обновления таблицы
        self._init_ui()

        # Убедимся, что таблица создана
        if hasattr(self, 'users_table'):
            self._update_users_table()
            self.refresh_requested.connect(self._update_users_table)

            # Настройка таблицы
            self.users_table.resizeColumnsToContents()
            self.users_table.resizeRowsToContents()
        else:
            print("Ошибка: users_table не была создана!")

    def _init_ui(self):
        """Инициализация UI"""
        main_layout = QHBoxLayout(self)

        # Левая панель с командами и скриптами
        left_panel = QVBoxLayout()
        left_panel.addWidget(self._create_commands_group())
        left_panel.addWidget(self._create_scripts_group())
        left_panel.setSpacing(10)  # Отступы между элементами

        # Правая панель с информацией
        right_panel = QVBoxLayout()
        right_panel.addWidget(self._create_active_users_group(), stretch=1)
        right_panel.addWidget(self._create_rdp_management_group(), stretch=1)
        right_panel.addWidget(self._create_system_info_group(), stretch=1)
        right_panel.addLayout(self._create_control_buttons(), stretch=0)

        # Добавляем в основной макет
        main_layout.addLayout(left_panel, stretch=1)
        main_layout.addLayout(right_panel, stretch=1)

        self.setLayout(main_layout)

    def _create_scripts_group(self):
        group = QGroupBox("Скрипты")
        layout = QVBoxLayout()

        # Кнопки управления
        btn_layout = QHBoxLayout()
        self.add_script_btn = QPushButton("Добавить")
        self.remove_script_btn = QPushButton("Удалить")
        btn_layout.addWidget(self.add_script_btn)
        btn_layout.addWidget(self.remove_script_btn)

        # Список скриптов
        self.script_list = QListWidget()
        self.script_list.setContextMenuPolicy(Qt.CustomContextMenu)
        self.script_list.customContextMenuRequested.connect(self._show_script_context_menu)

        self._update_script_list()

        # Сигналы
        self.add_script_btn.clicked.connect(self._add_script)
        self.remove_script_btn.clicked.connect(self._remove_script)
        self.script_list.itemDoubleClicked.connect(self._execute_script)

        layout.addLayout(btn_layout)
        layout.addWidget(self.script_list)
        group.setLayout(layout)

        return group

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
            self.script_manager.execute_script(script_name, self.ip)
            # Удалили плашку с сообщением об успешном выполнении
        except Exception as e:
            self._show_error_message(str(e))

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

    def _create_commands_group(self):
        group = QGroupBox("Команды")
        layout = QVBoxLayout()

        # Создаем кнопки команд
        self.psexec_btn = QPushButton("PSExec")
        self.winrs_btn = QPushButton("WinRS")
        self.compmgmt_btn = QPushButton("compmgmt.msc")
        self.rdp_btn = QPushButton("RDP")
        self.c_drive_btn = QPushButton("C:\\")
        self.shadow_rdp_btn = QPushButton("Shadow RDP")

        # Список кнопок
        buttons = [
            self.psexec_btn, self.winrs_btn, self.compmgmt_btn,
            self.rdp_btn, self.c_drive_btn, self.shadow_rdp_btn
        ]

        # Добавляем кнопки в layout
        for btn in buttons:
            btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)  # Кнопки растягиваются по ширине
            layout.addWidget(btn)

        # Подключаем обработчики событий
        self.psexec_btn.clicked.connect(self._on_psexec_clicked)
        self.winrs_btn.clicked.connect(self._on_winrs_clicked)
        self.compmgmt_btn.clicked.connect(self._on_compmgmt_clicked)
        self.rdp_btn.clicked.connect(self._on_rdp_clicked)
        self.c_drive_btn.clicked.connect(self._on_c_drive_clicked)
        self.shadow_rdp_btn.clicked.connect(self._on_shadow_rdp_clicked)

        group.setLayout(layout)
        return group

    def _create_active_users_group(self):
        """Создаёт группу с активными пользователями"""

        group = QGroupBox("Активные пользователи")
        layout = QVBoxLayout()

        self.users_table = QTableWidget(0, 3)
        self.users_table.setHorizontalHeaderLabels(
            ["№", "Логин", "Тип подключения"])
        self.users_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.users_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.users_table.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        layout.setContentsMargins(0, 0, 0, 0)  # Убираем отступы
        layout.addWidget(self.users_table)
        group.setLayout(layout)

        return group

    def _create_rdp_management_group(self):
        group = QGroupBox("Управление RDP")
        layout = QVBoxLayout()

        # Чекбокс RDP
        self.rdp_checkbox = QCheckBox("RDP Включен")
        self.rdp_checkbox.stateChanged.connect(self._on_rdp_toggle)

        # Порт RDP
        port_layout = QHBoxLayout()
        self.rdp_port_input = QLineEdit()
        self.rdp_port_input.setPlaceholderText("Порт RDP")
        change_port_btn = QPushButton("Изменить")
        change_port_btn.clicked.connect(self._change_rdp_port)
        port_layout.addWidget(self.rdp_port_input)
        port_layout.addWidget(change_port_btn)

        # Список пользователей RDP
        self.rdp_users_list = QListWidget()
        self.rdp_users_list.setContextMenuPolicy(Qt.CustomContextMenu)
        self.rdp_users_list.customContextMenuRequested.connect(self._show_rdp_users_context_menu)

        # Добавление пользователей
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
        group.setLayout(layout)

        return group

    def _create_system_info_group(self):
        group = QGroupBox("Состояние системы")
        layout = QVBoxLayout()

        self.cpu_label = QLabel("CPU: 15%")
        self.ram_label = QLabel("RAM: 4.2/8.0 GB (52%)")

        # Диски
        disks_layout = QVBoxLayout()
        self.disk_c_label = QLabel("C: Свободно 45.2 GB, Всего 120 GB")
        self.disk_d_label = QLabel("D: Свободно 112.5 GB, Всего 256 GB")
        disks_layout.addWidget(self.disk_c_label)
        disks_layout.addWidget(self.disk_d_label)

        layout.addWidget(self.cpu_label)
        layout.addWidget(self.ram_label)
        layout.addLayout(disks_layout)
        group.setLayout(layout)

        return group

    def _create_control_buttons(self):
        layout = QHBoxLayout()
        self.refresh_btn = QPushButton("Обновить")
        self.close_btn = QPushButton("Закрыть")

        self.refresh_btn.clicked.connect(self.refresh_requested.emit)
        self.close_btn.clicked.connect(self.close_requested.emit)

        layout.addWidget(self.refresh_btn)
        layout.addWidget(self.close_btn)

        return layout

    def _update_users_table(self):
        try:
            users_data = get_active_users(self.ip)

            if isinstance(users_data, str):
                QMessageBox.critical(self, "Ошибка", users_data)
                return

            if not users_data:
                self.users_table.setRowCount(0)
                return

            self._populate_table(users_data)

        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка обновления: {str(e)}")

    def _populate_table(self, users_data):
        try:
            self.users_table.setRowCount(len(users_data))

            for row, user in enumerate(users_data):
                self.users_table.setItem(row, 0, QTableWidgetItem(str(row + 1)))
                self.users_table.setItem(row, 1, QTableWidgetItem(user.get("username", "N/A")))
                self.users_table.setItem(row, 2, QTableWidgetItem(user.get("state", "N/A")))

            self.users_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
            self.users_table.horizontalHeader().setStretchLastSection(True)
            self.users_table.viewport().update()

        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка отображения данных: {str(e)}")

    def _on_rdp_toggle(self, state):
        # Заглушка для обработки изменения состояния RDP
        pass

    def _change_rdp_port(self):
        new_port = self.rdp_port_input.text()
        # Заглушка для изменения порта
        QMessageBox.information(self, "Информация", f"Порт RDP изменен на {new_port}")

    def _show_rdp_users_context_menu(self, pos):
        menu = QMenu()
        remove_action = menu.addAction("Удалить")
        action = menu.exec(self.rdp_users_list.mapToGlobal(pos))

        if action == remove_action:
            selected_item = self.rdp_users_list.currentItem()
            if selected_item:
                # Заглушка для удаления пользователя
                QMessageBox.information(self, "Удаление",
                                        f"Пользователь {selected_item.text()} удален")

    def _add_rdp_user(self):
        new_user = self.new_user_input.text()
        if new_user:
            self.rdp_users_list.addItem(new_user)
            self.new_user_input.clear()

    def contextMenuEvent(self, event: QContextMenuEvent):
        # Общая реализация контекстного меню при необходимости
        pass

    def _on_psexec_clicked(self):
        try:
            run_psexec(self.ip)
        except Exception as e:
            self._show_error_message(f"Ошибка при запуске PSExec: {str(e)}")

    def _on_winrs_clicked(self):
        try:
            run_winrs(self.ip)
        except Exception as e:
            self._show_error_message(f"Ошибка при запуске WinRS: {str(e)}")

    def _on_compmgmt_clicked(self):
        try:
            run_compmgmt(self.ip)
        except Exception as e:
            self._show_error_message(f"Ошибка при запуске compmgmt.msc: {str(e)}")

    def _on_rdp_clicked(self):
        try:
            run_rdp(self.ip)
        except Exception as e:
            self._show_error_message(f"Ошибка при запуске RDP: {str(e)}")

    def _on_c_drive_clicked(self):
        try:
            open_c_drive(self.ip)
        except Exception as e:
            self._show_error_message(f"Ошибка при открытии диска C: {str(e)}")

    def _on_shadow_rdp_clicked(self):
        try:
            session_id = get_shadow_session_id(self.ip)
            run_shadow_rdp(self.ip, session_id)
        except Exception as e:
            self._show_error_message(f"Ошибка при подключении через Shadow RDP: {str(e)}")

    def _show_error_message(self, message):
        QMessageBox.critical(self, "Ошибка", message)