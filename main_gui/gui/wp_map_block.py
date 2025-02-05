from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QLineEdit, QTableWidget, QTableWidgetItem, QGroupBox, QHeaderView,
    QMenu, QMessageBox
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QAction
from notifications import Notification
from database import db_manager  # убедитесь, что путь импорта корректный


class WPMapBlock(QWidget):
    def __init__(self, pc_connection_block=None):
        super().__init__()
        self.pc_connection_block = pc_connection_block
        # Для контроля повторного уведомления при редактировании ячейки
        self._updating_cell = {}
        self.init_ui()
        self.refresh_table()
        self.wp_table.itemChanged.connect(self.update_rm_in_db)
        self.wp_table.itemDoubleClicked.connect(self.on_item_double_clicked)

    def init_ui(self):
        main_layout = QVBoxLayout()
        map_group = QGroupBox("Карта рабочих мест")
        group_layout = QVBoxLayout()

        search_layout = QHBoxLayout()
        search_label = QLabel("Поиск:")
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Введите РМ или IP")
        self.search_input.textChanged.connect(self.filter_connections)

        search_layout.addWidget(search_label)
        search_layout.addWidget(self.search_input)
        group_layout.addLayout(search_layout)

        self.wp_table = QTableWidget(0, 4)
        self.wp_table.setHorizontalHeaderLabels(["РМ", "IP", "ОС", "Последнее подключение"])
        self.wp_table.setContextMenuPolicy(Qt.CustomContextMenu)
        self.wp_table.customContextMenuRequested.connect(self.open_context_menu)
        group_layout.addWidget(self.wp_table)

        map_group.setLayout(group_layout)
        main_layout.addWidget(map_group)
        self.wp_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.setLayout(main_layout)

    def filter_connections(self):
        filter_text = self.search_input.text().lower()
        for row in range(self.wp_table.rowCount()):
            rm = self.wp_table.item(row, 0).text().lower()
            ip = self.wp_table.item(row, 1).text().lower()
            is_visible = filter_text in rm or filter_text in ip
            self.wp_table.setRowHidden(row, not is_visible)

    def refresh_table(self):
        """
        Загружает карту рабочих мест из базы данных.
        """
        records = db_manager.get_all_connections()
        self.wp_table.setRowCount(0)
        for row_data in records:
            row_index = self.wp_table.rowCount()
            self.wp_table.insertRow(row_index)
            # Предполагается, что row_data имеет как минимум 4 элемента
            for col_index in range(4):
                value = row_data[col_index] if col_index < len(row_data) else ""
                item = QTableWidgetItem(value if value is not None else "")
                # Разрешаем редактирование только для первого столбца (РМ)
                if col_index == 0:
                    item.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEnabled | Qt.ItemIsEditable)
                else:
                    item.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEnabled)
                self.wp_table.setItem(row_index, col_index, item)

    def on_item_double_clicked(self, item):
        column = item.column()
        # Если кликнули по колонке с IP (индекс 1) и pc_connection_block существует
        if column == 1 and self.pc_connection_block:
            ip_text = item.text()
            self.pc_connection_block.ip_input.setText(ip_text)
            Notification(f"Выбран IP: {ip_text}", "info", duration=3000, parent=self).show_notification()

    def update_rm_in_db(self, item):
        """
        Сохраняет изменения номера РМ (первый столбец) в базе данных при редактировании.
        Чтобы не спамить уведомления, для каждой ячейки обновление уведомляется один раз.
        """
        if item.column() != 0:
            return

        row = item.row()
        new_rm = item.text().strip()
        ip_item = self.wp_table.item(row, 1)
        if not ip_item:
            return
        ip = ip_item.text()

        # Если для данной ячейки уже было обновление с таким же значением, пропускаем уведомление
        key = (row, item.column())
        if self._updating_cell.get(key) == new_rm:
            return

        db_manager.update_rm(ip, new_rm)
        self._updating_cell[key] = new_rm
        Notification(f"РМ для IP {ip} обновлён", "success", duration=3000, parent=self).show_notification()

    def open_context_menu(self, position):
        menu = QMenu()
        delete_action = QAction("Удалить запись", self)

        selected_item = self.wp_table.itemAt(position)
        if selected_item is None:
            return

        delete_action.triggered.connect(lambda: self.delete_rm_entry(selected_item))
        menu.addAction(delete_action)
        menu.exec(self.wp_table.viewport().mapToGlobal(position))

    def delete_rm_entry(self, item):
        row = item.row()
        ip_item = self.wp_table.item(row, 1)
        if ip_item is None:
            return
        ip = ip_item.text().strip()
        reply = QMessageBox.question(self, "Удаление записи",
                                     f"Вы уверены, что хотите удалить запись с IP {ip}?",
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            db_manager.delete_rm(ip)
            self.wp_table.removeRow(row)
            Notification(f"Запись с IP {ip} удалена", "success", duration=3000, parent=self).show_notification()
