from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QLineEdit, QLabel,
    QCheckBox, QListWidget, QAbstractItemView, QMenu, QMessageBox
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QContextMenuEvent


class WindowsWindow(QWidget):
    refresh_requested = Signal()
    close_requested = Signal()

    def __init__(self, ip, os_name):
        super().__init__()
        self.ip = ip
        self.os_name = os_name
        self._init_ui()

    def _init_ui(self):
        main_layout = QHBoxLayout(self)

        # Левая панель с командами и скриптами
        left_panel = QVBoxLayout()
        left_panel.addWidget(self._create_commands_group())
        left_panel.addWidget(self._create_scripts_group())
        left_panel.addStretch()

        # Правая панель с информацией
        right_panel = QVBoxLayout()
        right_panel.addWidget(self._create_active_users_group())
        right_panel.addWidget(self._create_rdp_management_group())
        right_panel.addWidget(self._create_system_info_group())
        right_panel.addLayout(self._create_control_buttons())

        main_layout.addLayout(left_panel, stretch=1)
        main_layout.addLayout(right_panel, stretch=3)

    def _create_commands_group(self):
        group = QGroupBox("Команды")
        layout = QVBoxLayout()

        self.psexec_btn = QPushButton("PSExec")
        self.winrs_btn = QPushButton("WinRS")
        self.compmgmt_btn = QPushButton("compmgmt.msc")
        self.rdp_btn = QPushButton("RDP")
        self.c_drive_btn = QPushButton("C:\\")
        self.shadow_rdp_btn = QPushButton("Shadow RDP")

        buttons = [
            self.psexec_btn, self.winrs_btn, self.compmgmt_btn,
            self.rdp_btn, self.c_drive_btn, self.shadow_rdp_btn
        ]

        for btn in buttons:
            btn.setFixedHeight(30)
            layout.addWidget(btn)

        group.setLayout(layout)
        return group

    def _create_scripts_group(self):
        group = QGroupBox("Скрипты")
        layout = QVBoxLayout()

        self.script_library_btn = QPushButton("Библиотека скриптов")
        self.script_list = QListWidget()

        # Заглушка для демонстрации
        self.script_list.addItems(["Скрипт 1", "Скрипт 2", "Скрипт 3"])

        layout.addWidget(self.script_library_btn)
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

        # Заглушка данных
        self._update_users_table()

        layout.addWidget(self.users_table)
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
        return group

    def _create_system_info_group(self):
        group = QGroupBox("Состояние системы")
        layout = QVBoxLayout()

        # CPU и RAM
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
        # Заглушка данных
        self.users_table.setRowCount(2)
        self.users_table.setItem(0, 0, QTableWidgetItem("1"))
        self.users_table.setItem(0, 1, QTableWidgetItem("user1"))
        self.users_table.setItem(0, 2, QTableWidgetItem("RDP-TCP#1"))
        self.users_table.setItem(1, 0, QTableWidgetItem("2"))
        self.users_table.setItem(1, 1, QTableWidgetItem("user2"))
        self.users_table.setItem(1, 2, QTableWidgetItem("Console"))

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