# linux_gui/gui/process_manager_block.py

from PySide6.QtWidgets import (
    QGroupBox, QVBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QLineEdit, QHBoxLayout
)
from PySide6.QtCore import Qt
import logging

from linux_gui.session_manager import SessionManager
from linux_gui.process_manager import ProcessManager
from notifications import Notification

logger = logging.getLogger(__name__)


class ProcessManagerBlock(QGroupBox):
    """
    Виджет для отображения информации о процессах на удалённом Linux-хосте.

    Отображает список процессов в виде таблицы, аналогичной htop, с возможностью сортировки
    по столбцам и поиска по строкам.
    """
    def __init__(self, hostname, parent=None):
        """
        :param hostname: имя или IP-адрес удалённого хоста.
        """
        # Заголовок группы дополнен эмодзи
        super().__init__("🛠️ Процессы", parent)
        self.hostname = hostname
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)

        # Информационная метка с эмодзи и поясняющим текстом
        self.info_label = QLabel("💡 Нажмите «Обновить процессы», чтобы загрузить список процессов.")
        self.info_label.setWordWrap(True)
        layout.addWidget(self.info_label)

        # Горизонтальный блок для поля поиска с эмодзи
        search_layout = QHBoxLayout()
        search_label = QLabel("🔎 Поиск:")
        self.search_field = QLineEdit()
        self.search_field.setPlaceholderText("Введите текст для поиска...")
        self.search_field.textChanged.connect(self.filter_table)
        search_layout.addWidget(search_label)
        search_layout.addWidget(self.search_field)
        layout.addLayout(search_layout)

        # Таблица для отображения процессов.
        # Заголовки столбцов дополнены эмодзи для лучшего восприятия.
        self.process_table = QTableWidget()
        self.process_table.setColumnCount(6)
        self.process_table.setHorizontalHeaderLabels([
            "🔢 PID", "👤 USER", "⚙️ CPU%", "💾 MEM%", "⏱️ TIME", "💻 COMMAND"
        ])
        header = self.process_table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.Stretch)
        self.process_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.process_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.process_table.setSortingEnabled(True)  # Включаем сортировку по столбцам
        layout.addWidget(self.process_table)

        # Кнопка обновления процессов, дополненная эмодзи
        self.refresh_button = QPushButton("🔄 Обновить процессы")
        self.refresh_button.setToolTip("Нажмите для обновления списка процессов")
        self.refresh_button.clicked.connect(self.refresh_processes)
        layout.addWidget(self.refresh_button)

        self.setLayout(layout)

    def refresh_processes(self):
        """
        Обновляет информацию о процессах.

        Получает SSH-сессию через SessionManager, вызывает ProcessManager для получения данных,
        и заполняет таблицу полученными данными.
        """
        try:
            # Предполагается, что аутентификация уже выполнена.
            session = SessionManager.get_instance(self.hostname, "", "").get_client()
            proc_manager = ProcessManager(session)
            data = proc_manager.get_processes_info()
            processes = data.get("processes", [])
            self.populate_table(processes)
            Notification("Процессы", "✅ Информация о процессах успешно обновлена.", "success").show_notification()
        except Exception as e:
            logger.error(f"Ошибка обновления процессов: {e}")
            Notification("Ошибка", f"❌ Не удалось обновить информацию о процессах:\n{e}", "error").show_notification()

    def populate_table(self, processes):
        """
        Заполняет таблицу данными о процессах.
        Отображаются выбранные столбцы: PID, USER, CPU%, MEM%, TIME, COMMAND.
        """
        self.process_table.setRowCount(0)
        for process in processes:
            row_position = self.process_table.rowCount()
            self.process_table.insertRow(row_position)

            pid_item = QTableWidgetItem(process.get("PID", ""))
            user_item = QTableWidgetItem(process.get("USER", ""))
            cpu_item = QTableWidgetItem(process.get("%CPU", ""))
            mem_item = QTableWidgetItem(process.get("%MEM", ""))
            time_item = QTableWidgetItem(process.get("TIME", ""))
            cmd_item = QTableWidgetItem(process.get("COMMAND", ""))

            for item in [pid_item, user_item, cpu_item, mem_item, time_item, cmd_item]:
                item.setTextAlignment(Qt.AlignCenter)
            self.process_table.setItem(row_position, 0, pid_item)
            self.process_table.setItem(row_position, 1, user_item)
            self.process_table.setItem(row_position, 2, cpu_item)
            self.process_table.setItem(row_position, 3, mem_item)
            self.process_table.setItem(row_position, 4, time_item)
            self.process_table.setItem(row_position, 5, cmd_item)

        # Применяем фильтрацию, если в поиске уже что-то введено
        self.filter_table(self.search_field.text())

    def filter_table(self, text):
        """
        Фильтрует строки таблицы по введённому тексту.

        :param text: Строка для поиска (без учёта регистра).
        """
        filter_text = text.strip().lower()
        row_count = self.process_table.rowCount()
        col_count = self.process_table.columnCount()

        for row in range(row_count):
            row_visible = False
            for col in range(col_count):
                item = self.process_table.item(row, col)
                if item is not None and filter_text in item.text().lower():
                    row_visible = True
                    break
            self.process_table.setRowHidden(row, not row_visible)
