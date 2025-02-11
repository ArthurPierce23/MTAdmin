from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QLineEdit, QPushButton, QTableWidget, QTableWidgetItem, QGroupBox, QHeaderView, QSizePolicy
)
from PySide6.QtCore import Qt
from notifications import Notification


class RecentConnectionsBlock(QWidget):
    def __init__(self, pc_connection_block=None) -> None:
        super().__init__()
        self.pc_connection_block = pc_connection_block
        self.init_ui()
        self.clear_button.clicked.connect(self.clear_connections)
        self.connections_table.itemDoubleClicked.connect(self.on_item_double_clicked)
        self.refresh_table()  # Загружаем данные при старте

    def init_ui(self) -> None:
        main_layout = QVBoxLayout()

        connections_group = QGroupBox("📡 Недавние подключения")
        connections_group.setObjectName("groupBox")  # Применяем стилизацию

        group_layout = QVBoxLayout()
        group_layout.setContentsMargins(10, 10, 10, 10)
        group_layout.setSpacing(8)

        # 🔎 Поле поиска
        search_layout = QHBoxLayout()
        search_label = QLabel("🔍 Поиск:")
        search_label.setObjectName("searchLabel")

        self.search_input = QLineEdit()
        self.search_input.setObjectName("inputField")
        self.search_input.setPlaceholderText("Введите IP или дату")
        self.search_input.textChanged.connect(self.filter_connections)

        search_layout.addWidget(search_label)
        search_layout.addWidget(self.search_input)
        group_layout.addLayout(search_layout)

        # 📋 Таблица подключений
        self.connections_table = QTableWidget(0, 2)
        self.connections_table.setObjectName("connectionsTable")
        self.connections_table.setHorizontalHeaderLabels(["💻 IP", "📅 Дата"])
        self.connections_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.connections_table.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        group_layout.addWidget(self.connections_table)

        # ❌ Кнопка очистки в отдельном layout для корректной адаптации под текст
        clear_layout = QHBoxLayout()
        clear_layout.addStretch()  # Спейсер для прижатия кнопки вправо
        self.clear_button = QPushButton("🗑 Очистить список")
        self.clear_button.setObjectName("dangerButton")  # Для красной стилизации
        self.clear_button.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Fixed)
        self.clear_button.adjustSize()
        clear_layout.addWidget(self.clear_button)
        group_layout.addLayout(clear_layout)

        connections_group.setLayout(group_layout)
        main_layout.addWidget(connections_group)
        self.setLayout(main_layout)

    def filter_connections(self) -> None:
        filter_text = self.search_input.text().lower()
        for row in range(self.connections_table.rowCount()):
            ip_item = self.connections_table.item(row, 0)
            date_item = self.connections_table.item(row, 1)
            ip = ip_item.text().lower() if ip_item else ""
            date = date_item.text().lower() if date_item else ""
            is_visible = filter_text in ip or filter_text in date
            self.connections_table.setRowHidden(row, not is_visible)
        if not any(not self.connections_table.isRowHidden(row) for row in range(self.connections_table.rowCount())):
            Notification(
                "Нет совпадений",
                "Попробуйте изменить запрос.",
                "warning",
                duration=2500,
                parent=self
            ).show_notification()

    def clear_connections(self) -> None:
        self.connections_table.setRowCount(0)
        Notification(
            "Список подключений очищен",
            "Все недавние подключения удалены.",
            "error",
            duration=3500,
            parent=self
        ).show_notification()

    def add_connection(self, ip: str, date: str, notify: bool = True) -> None:
        """
        Добавляет новую запись в таблицу.
        Если notify=False, уведомление не показывается.
        """
        row = self.connections_table.rowCount()
        self.connections_table.insertRow(row)

        ip_item = QTableWidgetItem(ip)
        ip_item.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEnabled)

        date_item = QTableWidgetItem(date)
        date_item.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEnabled)

        self.connections_table.setItem(row, 0, ip_item)
        self.connections_table.setItem(row, 1, date_item)

        if notify:
            Notification(
                "Новое подключение",
                f"IP {ip} был добавлен в список подключений ({date}).",
                "success",
                duration=3500,
                parent=self
            ).show_notification()

    def on_item_double_clicked(self, item: QTableWidgetItem) -> None:
        if self.pc_connection_block is None:
            print("Ошибка: pc_connection_block is None")
            return

        row = item.row()
        ip_item = self.connections_table.item(row, 0)
        if ip_item:
            ip_text = ip_item.text()
            self.pc_connection_block.ip_input.setText(ip_text)
            Notification(
                "Выбран IP",
                f"{ip_text} теперь в поле ввода.",
                "info",
                duration=3000,
                parent=self
            ).show_notification()

    def refresh_table(self) -> None:
        """
        Загружает недавние подключения из базы данных и заполняет таблицу.
        При программном обновлении уведомления не показываются.
        """
        from database import db_manager  # Импорт внутри метода для избежания циклических импортов

        records = db_manager.get_all_connections()
        self.connections_table.setRowCount(0)
        for row_data in records:
            ip, date = row_data[1], row_data[3]  # ip и last_connection
            self.add_connection(ip, date, notify=False)

    def moveEvent(self, event) -> None:
        """
        Обновляет позиции уведомлений при перемещении главного окна.
        """
        from notifications import Notification
        for notif in Notification.get_active_notifications():
            notif.update_position()
        super().moveEvent(event)
