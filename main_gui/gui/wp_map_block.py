from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QLineEdit, QTableWidget, QTableWidgetItem, QGroupBox, QHeaderView,
    QMenu, QMessageBox, QSizePolicy
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QAction
from notifications import Notification
from database import db_manager  # убедитесь, что путь импорта корректный


class WPMapBlock(QWidget):
    def __init__(self, pc_connection_block=None):
        """
        Инициализация блока «Карта рабочих мест».
        :param pc_connection_block: Ссылка на блок подключения к ПК (для передачи IP при двойном клике)
        """
        super().__init__()
        self.pc_connection_block = pc_connection_block
        # Словарь для контроля повторного уведомления при редактировании ячейки
        self._updating_cell = {}
        self.init_ui()
        self.refresh_table()
        self.wp_table.itemChanged.connect(self.update_rm_in_db)
        self.wp_table.itemDoubleClicked.connect(self.on_item_double_clicked)

    def init_ui(self):
        """Настраивает UI для блока: поле поиска и таблица рабочих мест."""
        main_layout = QVBoxLayout()

        # Группа "Карта рабочих мест"
        map_group = QGroupBox("📌 Карта рабочих мест")
        map_group.setObjectName("groupBox")
        group_layout = QVBoxLayout()
        group_layout.setContentsMargins(10, 10, 10, 10)
        group_layout.setSpacing(8)

        # Поле поиска
        search_layout = QHBoxLayout()
        search_label = QLabel("🔍 Поиск:")
        search_label.setObjectName("searchLabel")

        self.search_input = QLineEdit()
        self.search_input.setObjectName("inputField")
        self.search_input.setPlaceholderText("Введите РМ или IP")
        self.search_input.textChanged.connect(self.filter_connections)

        search_layout.addWidget(search_label)
        search_layout.addWidget(self.search_input)
        group_layout.addLayout(search_layout)

        # Таблица рабочих мест
        self.wp_table = QTableWidget(0, 4)
        self.wp_table.setObjectName("wpTable")
        self.wp_table.setHorizontalHeaderLabels(["🖥 РМ", "💻 IP", "🖥 ОС", "📅 Последнее подключение"])
        self.wp_table.setContextMenuPolicy(Qt.CustomContextMenu)
        self.wp_table.customContextMenuRequested.connect(self.open_context_menu)
        self.wp_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.wp_table.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        group_layout.addWidget(self.wp_table)
        map_group.setLayout(group_layout)
        main_layout.addWidget(map_group)
        self.setLayout(main_layout)

    def filter_connections(self):
        """
        Фильтрует строки таблицы по введённому значению в поле поиска.
        Строка показывается, если в ячейке с РМ или IP содержится искомый текст.
        """
        filter_text = self.search_input.text().lower()
        for row in range(self.wp_table.rowCount()):
            # Получаем ячейки, если они существуют
            rm_item = self.wp_table.item(row, 0)
            ip_item = self.wp_table.item(row, 1)
            rm_text = rm_item.text().lower() if rm_item else ""
            ip_text = ip_item.text().lower() if ip_item else ""
            is_visible = filter_text in rm_text or filter_text in ip_text
            self.wp_table.setRowHidden(row, not is_visible)

    def refresh_table(self):
        """
        Загружает данные карты рабочих мест из базы данных и заполняет таблицу.
        """
        records = db_manager.get_all_connections()
        self.wp_table.setRowCount(0)
        for row_data in records:
            row_index = self.wp_table.rowCount()
            self.wp_table.insertRow(row_index)
            # Заполняем 4 столбца (если данных меньше, оставляем пустую строку)
            for col_index in range(4):
                value = row_data[col_index] if col_index < len(row_data) and row_data[col_index] is not None else ""
                item = QTableWidgetItem(value)
                # Разрешаем редактирование только для первого столбца (РМ)
                if col_index == 0:
                    item.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEnabled | Qt.ItemIsEditable)
                else:
                    item.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEnabled)
                self.wp_table.setItem(row_index, col_index, item)

    def on_item_double_clicked(self, item):
        """
        При двойном клике по ячейке столбца IP передаёт значение в поле ввода IP
        в блоке подключения, если таковой имеется.
        """
        if item.column() == 1 and self.pc_connection_block:
            ip_text = item.text()
            self.pc_connection_block.ip_input.setText(ip_text)
            Notification(f"Выбран IP: {ip_text}", "info", duration=3000, parent=self).show_notification()

    def update_rm_in_db(self, item):
        """
        Сохраняет изменения в номере РМ (первый столбец) в базе данных при редактировании.
        Чтобы не создавать спам уведомлений, для каждой ячейки обновление уведомляется один раз.
        """
        # Обрабатываем только первый столбец
        if item.column() != 0:
            return

        row = item.row()
        new_rm = item.text().strip()
        ip_item = self.wp_table.item(row, 1)
        if not ip_item:
            return
        ip = ip_item.text()

        key = (row, item.column())
        if self._updating_cell.get(key) == new_rm:
            return

        db_manager.update_rm(ip, new_rm)
        self._updating_cell[key] = new_rm
        Notification(f"РМ для IP {ip} обновлён", "success", duration=3000, parent=self).show_notification()

    def open_context_menu(self, position):
        """
        Открывает контекстное меню для удаления записи.
        """
        menu = QMenu()
        delete_action = QAction("Удалить запись", self)

        selected_item = self.wp_table.itemAt(position)
        if selected_item is None:
            return

        delete_action.triggered.connect(lambda: self.delete_rm_entry(selected_item))
        menu.addAction(delete_action)
        menu.exec(self.wp_table.viewport().mapToGlobal(position))

    def delete_rm_entry(self, item):
        """
        Удаляет запись из базы данных и из таблицы после подтверждения.
        """
        row = item.row()
        ip_item = self.wp_table.item(row, 1)
        if ip_item is None:
            return
        ip = ip_item.text().strip()

        reply = QMessageBox.question(
            self,
            "Удаление записи",
            f"Вы уверены, что хотите удалить запись с IP {ip}?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            db_manager.delete_rm(ip)
            self.wp_table.removeRow(row)
            Notification(f"Запись с IP {ip} удалена", "success", duration=3000, parent=self).show_notification()
