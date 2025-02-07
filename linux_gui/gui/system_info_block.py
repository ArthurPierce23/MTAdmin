# linux_gui/gui/system_info_block.py

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QGroupBox, QProgressBar, QTableWidget,
    QTableWidgetItem, QPushButton, QHeaderView, QSpinBox, QHBoxLayout,
    QStyle, QSizePolicy, QFrame, QSpacerItem
)
from PySide6.QtCore import QTimer, Qt, QThread, Signal, QSize
from PySide6.QtGui import QFont, QColor
import logging

from linux_gui.system_info import SystemInfo  # Логика получения данных о системе
from notifications import Notification

logger = logging.getLogger(__name__)


def get_cores_text(cores):
    """
    Возвращает строку с правильным окончанием для количества ядер.
    Например: 1 -> "1 ядро", 2 -> "2 ядра", 5 -> "5 ядер".
    """
    try:
        cores = int(cores)
    except (ValueError, TypeError):
        return "N/A"
    if cores % 100 in (11, 12, 13, 14):
        ending = "ядер"
    else:
        last_digit = cores % 10
        if last_digit == 1:
            ending = "ядро"
        elif last_digit in (2, 3, 4):
            ending = "ядра"
        else:
            ending = "ядер"
    return f"{cores} {ending}"


class SystemInfoThread(QThread):
    """
    Поток для получения данных о системе, чтобы не блокировать основной GUI.
    """
    data_ready = Signal(dict)

    def __init__(self, system_info: SystemInfo, parent=None):
        super().__init__(parent)
        self.system_info = system_info

    def run(self):
        try:
            info = self.system_info.get_system_info()
        except Exception as e:
            logger.error(f"Ошибка получения системной информации: {e}")
            info = {"error": str(e)}
        self.data_ready.emit(info)


class SystemInfoBlock(QWidget):
    """
    Виджет для отображения информации о системе удалённого Linux-хоста.
    Содержит индикаторы загрузки CPU, RAM, таблицу по дискам, кнопку ручного обновления
    и возможность автообновления по заданному интервалу.
    """
    def __init__(self, hostname, parent=None):
        super().__init__(parent)
        self.hostname = hostname
        self.system_info = SystemInfo(hostname)
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.safe_update)
        self.thread = None

        # Базовые шрифты
        self.base_font = QFont("Arial", 10)
        self.header_font = QFont("Arial", 12, QFont.Bold)

        # Элементы для отображения CPU
        self.cpu_progress = QProgressBar()
        self.cpu_label = QLabel()
        self.cpu_progress.setFont(self.base_font)
        self.cpu_label.setFont(self.base_font)
        self.cpu_progress.setToolTip("Загрузка процессора")

        # Элементы для отображения RAM
        self.ram_progress = QProgressBar()
        self.ram_label = QLabel()
        self.ram_progress.setFont(self.base_font)
        self.ram_label.setFont(self.base_font)
        self.ram_progress.setToolTip("Использование оперативной памяти")

        # Таблица для отображения информации по дискам
        self.disk_table = QTableWidget()
        self.disk_table.setFont(self.base_font)
        self.disk_table.setColumnCount(4)
        self.disk_table.setHorizontalHeaderLabels([
            "💽 Диск", "📦 Всего", "🔓 Свободно", "📈 Использовано"
        ])
        header = self.disk_table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.Stretch)
        self.disk_table.verticalHeader().setVisible(False)
        self.disk_table.setSelectionMode(QTableWidget.NoSelection)
        self.disk_table.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.disk_table.setFixedHeight(130)

        self.init_ui()
        self.safe_update()

    def init_ui(self):
        """Инициализирует визуальные компоненты виджета."""
        self.group_box = QGroupBox("🖥️ Информация о системе")
        self.group_box.setFont(self.header_font)

        layout = QVBoxLayout(self.group_box)

        # Блок для CPU
        cpu_box = self.create_progress_box("Процессор:", self.cpu_label, self.cpu_progress)
        # Блок для RAM
        ram_box = self.create_progress_box("Оперативная память:", self.ram_label, self.ram_progress)

        # Кнопка для ручного обновления данных
        self.refresh_button = QPushButton("Обновить данные")
        self.refresh_button.setFont(self.base_font)
        self.refresh_button.setIcon(self.style().standardIcon(QStyle.SP_BrowserReload))
        self.refresh_button.setIconSize(QSize(20, 20))
        self.refresh_button.setToolTip("Нажмите для обновления данных о системе")
        self.refresh_button.clicked.connect(self.safe_update)

        control_layout = QHBoxLayout()
        control_layout.addWidget(self.refresh_button)
        control_layout.addStretch()

        # Блок для выбора интервала автообновления
        interval_layout = QHBoxLayout()
        self.interval_label = QLabel("⏱️ Интервал автообновления:")
        self.interval_label.setFont(self.base_font)
        self.interval_input = QSpinBox()
        self.interval_input.setRange(0, 600)
        self.interval_input.setSuffix(" сек")
        self.interval_input.setSingleStep(10)
        self.interval_input.setValue(0)
        self.interval_input.setFixedWidth(120)
        self.interval_input.setAlignment(Qt.AlignRight)
        self.interval_input.setFont(self.base_font)
        self.interval_input.setToolTip("Задайте интервал автообновления (0 – автообновление отключено)")
        self.interval_input.valueChanged.connect(self.update_timer)
        interval_layout.addWidget(self.interval_label)
        interval_layout.addWidget(self.interval_input)
        interval_layout.addStretch()

        # Компоновка элементов внутри группы
        layout.addWidget(cpu_box)
        layout.addWidget(ram_box)
        layout.addWidget(self.disk_table)
        layout.addLayout(control_layout)
        layout.addLayout(interval_layout)
        self.group_box.setLayout(layout)

        # Основной компоновщик
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(12, 12, 12, 12)
        main_layout.setSpacing(10)
        main_layout.addWidget(self.group_box)

        spacer = QSpacerItem(20, 20, QSizePolicy.Minimum, QSizePolicy.Expanding)
        main_layout.addItem(spacer)

        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        separator.setFrameShadow(QFrame.Sunken)
        main_layout.addWidget(separator)

        self.setLayout(main_layout)

    def create_progress_box(self, title, label, progress_bar):
        """
        Создает виджет для отображения заголовка и индикатора (прогрессбара).
        """
        box = QWidget()
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        label.setText(title)
        label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        progress_bar.setTextVisible(True)
        progress_bar.setAlignment(Qt.AlignCenter)
        layout.addWidget(label)
        layout.addWidget(progress_bar)
        box.setLayout(layout)
        return box

    def update_timer(self):
        """
        Обновляет интервал автообновления в соответствии со значением, заданным пользователем.
        """
        interval = self.interval_input.value() * 1000
        if interval > 0:
            self.timer.start(interval)
        else:
            self.timer.stop()

    def safe_update(self):
        """
        Запускает обновление данных о системе в отдельном потоке.
        Если предыдущий поток ещё не завершился, новая задача не запускается.
        """
        if self.thread and self.thread.isRunning():
            return
        self.thread = SystemInfoThread(self.system_info)
        self.thread.data_ready.connect(self.update_info)
        self.thread.start()

    def update_info(self, info: dict):
        """
        Обновляет данные индикаторов и таблицы на основе полученной информации.
        При возникновении ошибок отображается уведомление.
        """
        if not isinstance(info, dict) or "error" in info:
            error_msg = "⚠️ Не удалось получить данные" if not isinstance(info, dict) else info.get("error", "Ошибка")
            self.cpu_label.setText(f"Процессор: {error_msg}")
            self.cpu_progress.setValue(0)
            self.cpu_progress.setFormat("")
            self.ram_label.setText("ОЗУ: данные недоступны")
            self.ram_progress.setValue(0)
            self.ram_progress.setFormat("")
            self.disk_table.setRowCount(0)
            Notification("Ошибка системной информации", f"❌ {error_msg}", "error").show_notification()
            return

        # Обновление данных по CPU
        cpu_data = info.get("CPU", {})
        cpu_load = cpu_data.get("Load", 0)
        cpu_cores = cpu_data.get("Cores", 0)
        value_cpu = int(cpu_load) if cpu_load is not None else 0
        self.cpu_progress.setValue(value_cpu)
        cores_text = get_cores_text(cpu_cores)
        self.cpu_progress.setFormat(f"{value_cpu}% / {cores_text}")

        # Обновление данных по RAM
        ram_data = info.get("RAM", {})
        ram_used = ram_data.get("UsedPercent", 0)
        ram_total = ram_data.get("TotalGB", "N/A")
        value_ram = int(ram_used) if ram_used is not None else 0
        self.ram_progress.setValue(value_ram)
        total_text = f"{ram_total} GB" if ram_total != "N/A" else "N/A"
        self.ram_progress.setFormat(f"{value_ram}% / {total_text}")

        # Обновление таблицы с информацией по дискам
        disks = info.get("Disks", [])
        if isinstance(disks, dict):
            disks = [disks]
        self.disk_table.setRowCount(len(disks))
        for row, disk in enumerate(disks):
            self.add_disk_row(
                row,
                disk.get("Letter", "N/A"),
                disk.get("TotalGB", 0),
                disk.get("FreeGB", 0),
                disk.get("UsedPercent", 0)
            )

        Notification("Система", "✅ Данные о системе обновлены", "success").show_notification()

    def add_disk_row(self, row, letter, total, free, used_percent):
        """
        Добавляет строку в таблицу дисков с выравниванием и форматированием.
        """
        items = [
            QTableWidgetItem(str(letter)),
            QTableWidgetItem(f"{total:.1f} GB"),
            QTableWidgetItem(f"{free:.1f} GB"),
            QTableWidgetItem(f"{used_percent:.1f}%")
        ]
        for col, item in enumerate(items):
            item.setTextAlignment(Qt.AlignCenter)
            item.setFlags(item.flags() & ~Qt.ItemIsEditable)
            self.disk_table.setItem(row, col, item)
