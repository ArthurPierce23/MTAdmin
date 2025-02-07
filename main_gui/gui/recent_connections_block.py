from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QLineEdit, QPushButton, QTableWidget, QTableWidgetItem, QGroupBox, QHeaderView, QSizePolicy
)
from PySide6.QtCore import Qt
from notifications import Notification


class RecentConnectionsBlock(QWidget):
    def __init__(self, pc_connection_block=None):
        super().__init__()
        self.pc_connection_block = pc_connection_block
        self._last_filter = None  # Для контроля повторного уведомления при фильтрации (больше не используется)
        self.init_ui()
        self.clear_button.clicked.connect(self.clear_connections)
        self.connections_table.itemDoubleClicked.connect(self.on_item_double_clicked)
        self.refresh_table()  # Загружаем данные при старте

    def init_ui(self):
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
        self.search_input.setObjectName("inputField")  # Поле ввода стилизуем
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

        # ❌ Кнопка очистки
        self.clear_button = QPushButton("🗑 Очистить список")
        self.clear_button.setObjectName("dangerButton")  # Красная кнопка
        self.clear_button.setFixedHeight(36)
        group_layout.addWidget(self.clear_button, alignment=Qt.AlignRight)

        connections_group.setLayout(group_layout)
        main_layout.addWidget(connections_group)

        self.setLayout(main_layout)

    def filter_connections(self):
        filter_text = self.search_input.text().lower()
        found = False
        for row in range(self.connections_table.rowCount()):
            ip = self.connections_table.item(row, 0).text().lower()
            date = self.connections_table.item(row, 1).text().lower()
            is_visible = filter_text in ip or filter_text in date
            self.connections_table.setRowHidden(row, not is_visible)
            if is_visible:
                found = True

        # Уведём уведомления при поиске отключены,
        # чтобы не возникал спам уведомлений при каждом изменении текста.
        # Если требуется уведомлять о том, что ничего не найдено, можно добавить дополнительную логику,
        # например, показывать уведомление один раз по завершении ввода (debounce).
        self._last_filter = filter_text

    def clear_connections(self):
        self.connections_table.setRowCount(0)
        Notification("Список подключений очищен", "success", duration=3000, parent=self).show_notification()

    def add_connection(self, ip: str, date: str, notify: bool = True):
        """
        Добавляет новую запись в таблицу. Если notify=False, уведомление не показывается.
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
            Notification(f"Добавлено новое подключение: {ip}", "info", duration=3000, parent=self).show_notification()

    def on_item_double_clicked(self, item):
        if self.pc_connection_block is None:
            print("Ошибка: pc_connection_block is None")
            return

        row = item.row()
        ip_item = self.connections_table.item(row, 0)
        if ip_item:
            ip_text = ip_item.text()
            self.pc_connection_block.ip_input.setText(ip_text)
            Notification(f"Выбран IP: {ip_text}", "info", duration=3000, parent=self).show_notification()

    def refresh_table(self):
        """
        Загружает недавние подключения из базы данных и заполняет таблицу.
        При программном обновлении уведомления не показываются.
        """
        from database import db_manager  # Импортируем здесь, чтобы избежать циклических импортов

        records = db_manager.get_all_connections()
        self.connections_table.setRowCount(0)
        for row_data in records:
            ip, date = row_data[1], row_data[3]  # ip и last_connection
            self.add_connection(ip, date, notify=False)

    def moveEvent(self, event):
        """Обновляем позиции уведомлений при перемещении главного окна."""
        from notifications import Notification  # Если требуется, можно обновлять позиции уведомлений
        for notif in Notification.get_active_notifications():
            notif.update_position()
        super().moveEvent(event)
