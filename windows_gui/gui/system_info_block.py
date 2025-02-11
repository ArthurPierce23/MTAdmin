import logging
import json

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QGroupBox, QProgressBar,
    QTableWidget, QTableWidgetItem, QPushButton, QHeaderView,
    QSpinBox, QHBoxLayout, QStyle, QSizePolicy,
    QStyledItemDelegate, QFrame, QSpacerItem
)
from PySide6.QtCore import QTimer, Qt, QThread, Signal, QSize, QUrl
from PySide6.QtGui import (
    QDesktopServices, QIcon, QFontMetrics, QColor, QPainter,
    QAction, QFont, QGuiApplication
)

from windows_gui.system_info import SystemInfo
from notifications import Notification

logger = logging.getLogger(__name__)


def get_cores_text(cores) -> str:
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


class CopyableLabel(QLabel):
    """
    QLabel, позволяющий выделять и копировать текст по клику ЛКМ.
    При клике текст копируется в буфер обмена, а также показывается уведомление.
    """

    def __init__(self, text: str = '', parent=None) -> None:
        super().__init__(text, parent)
        self.setTextInteractionFlags(Qt.TextSelectableByMouse)

    def mousePressEvent(self, event) -> None:
        if event.button() == Qt.LeftButton:
            original_style = self.styleSheet()
            self.setStyleSheet("background-color: #e0e0e0;")  # светло-серый фон
            QTimer.singleShot(150, lambda: self.setStyleSheet(original_style))
            clipboard = QGuiApplication.clipboard()
            clipboard.setText(self.text())
            Notification("Скопировано",
                         f"Скопировано: {self.text()}",
                         "success",
                         parent=self.window()).show_notification()
        super().mousePressEvent(event)


class SystemInfoThread(QThread):
    """
    Поток для получения данных о системе, чтобы не блокировать основной GUI.
    """
    data_ready = Signal(dict)

    def __init__(self, system_info: SystemInfo) -> None:
        super().__init__()
        self.system_info = system_info

    def run(self) -> None:
        info = self.system_info.get_system_info()
        self.data_ready.emit(info)


class ScriptItemDelegate(QStyledItemDelegate):
    """
    Делегат для отрисовки элемента списка скриптов с тегами (на будущее расширение функционала).
    """

    def paint(self, painter: QPainter, option, index) -> None:
        super().paint(painter, option, index)
        script = index.data(Qt.UserRole)
        if script and script.get('tags'):
            painter.save()
            tag_spacing = 5
            tag_height = 20
            tag_radius = 8
            font_metrics = QFontMetrics(option.font)
            x_pos = option.rect.right() - 10
            for tag in reversed(script['tags']):
                text_width = font_metrics.horizontalAdvance(tag) + 20
                tag_rect = option.rect.adjusted(
                    x_pos - text_width,
                    (option.rect.height() - tag_height) // 2,
                    -10,
                    0
                )
                if tag_rect.left() < option.rect.left():
                    break
                painter.setBrush(QColor(230, 240, 255))
                painter.setPen(Qt.NoPen)
                painter.drawRoundedRect(tag_rect, tag_radius, tag_radius)
                painter.setPen(QColor(50, 100, 200))
                painter.drawText(tag_rect.adjusted(5, 0, -5, 0), Qt.AlignCenter, tag)
                x_pos -= text_width + tag_spacing
            painter.restore()


class SystemInfoBlock(QWidget):
    """
    Виджет для отображения информации о системе:
    - индикаторы загрузки CPU и ОЗУ,
    - таблица с информацией по дискам,
    - поля для модели процессора, материнской платы, времени работы и MAC-адреса.

    Уведомления о результате обновления показываются только при ручном обновлении.
    """

    def __init__(self, hostname: str, parent=None) -> None:
        super().__init__(parent)
        self.hostname = hostname
        self.system_info = SystemInfo(hostname)
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.safe_update)
        self.thread = None
        self.manual_update = False  # Флаг: True, если обновление вызвано пользователем

        self.base_font = QFont("Arial", 10)
        self.header_font = QFont("Arial", 12, QFont.Bold)

        self.cpu_progress = QProgressBar()
        self.ram_progress = QProgressBar()
        self.cpu_label = QLabel()
        self.ram_label = QLabel()

        for widget in (self.cpu_label, self.ram_label, self.cpu_progress, self.ram_progress):
            widget.setFont(self.base_font)

        self.cpu_progress.setStyleSheet("color: black;")
        self.ram_progress.setStyleSheet("color: black;")

        self.init_ui()
        self.safe_update()  # Первичное обновление данных

    def init_ui(self) -> None:
        """Инициализирует визуальные компоненты виджета."""
        self.group_box = QGroupBox("🖥️ Информация о системе")
        self.group_box.setObjectName("groupBox")
        self.group_box.setFont(self.header_font)

        main_layout = QVBoxLayout(self.group_box)
        main_layout.setSpacing(10)
        main_layout.setContentsMargins(12, 12, 12, 12)

        # Блок для CPU и RAM (расположены горизонтально)
        info_layout = QHBoxLayout()
        cpu_box = self.create_progress_box("💻 Процессор:", self.cpu_label, self.cpu_progress)
        ram_box = self.create_progress_box("📀 Оперативная память:", self.ram_label, self.ram_progress)
        info_layout.addWidget(cpu_box)
        info_layout.addWidget(ram_box)
        info_layout.addStretch()
        main_layout.addLayout(info_layout)

        # Таблица для информации по дискам
        self.disk_table = QTableWidget()
        self.disk_table.setObjectName("diskTable")
        self.disk_table.setFont(self.base_font)
        self.disk_table.setColumnCount(4)
        self.disk_table.setHorizontalHeaderLabels([
            "💽 Диск", "📏 Всего", "📂 Свободно", "📊 Использовано"
        ])
        header = self.disk_table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.Stretch)
        self.disk_table.verticalHeader().setVisible(False)
        self.disk_table.setSelectionMode(QTableWidget.NoSelection)
        self.disk_table.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.disk_table.setFixedHeight(130)
        main_layout.addWidget(self.disk_table)

        # Блок управления: кнопка обновления и выбор интервала автообновления
        control_layout = QHBoxLayout()
        control_layout.setSpacing(10)
        self.refresh_button = QPushButton("Обновить данные")
        self.refresh_button.setObjectName("refreshButton")
        self.refresh_button.setIcon(self.style().standardIcon(QStyle.SP_BrowserReload))
        self.refresh_button.setIconSize(QSize(20, 20))
        self.refresh_button.setToolTip("Обновить данные о системе в реальном времени")
        self.refresh_button.setFont(self.base_font)
        # При нажатии на кнопку устанавливаем флаг ручного обновления
        self.refresh_button.clicked.connect(self.on_refresh_button_clicked)
        control_layout.addWidget(self.refresh_button)
        control_layout.addStretch()

        # Интервал автообновления
        interval_layout = QHBoxLayout()
        interval_layout.setSpacing(5)
        self.interval_label = QLabel("⏱️ Интервал обновления:")
        self.interval_label.setFont(self.base_font)
        self.interval_input = QSpinBox()
        self.interval_input.setObjectName("intervalInput")
        self.interval_input.setRange(0, 600)
        self.interval_input.setSuffix(" сек")
        self.interval_input.setSingleStep(10)
        self.interval_input.setValue(0)
        self.interval_input.setFixedWidth(120)
        self.interval_input.setAlignment(Qt.AlignRight)
        self.interval_input.setFont(self.base_font)
        self.interval_input.setToolTip("Задайте интервал автообновления (0 = автообновление отключено)")
        self.interval_input.valueChanged.connect(self.update_timer)
        interval_layout.addWidget(self.interval_label)
        interval_layout.addWidget(self.interval_input)
        interval_layout.addStretch()

        main_layout.addLayout(control_layout)
        main_layout.addLayout(interval_layout)

        # Блок расширенной информации (два ряда по два поля)
        self.cpu_model_label = CopyableLabel()
        self.motherboard_label = CopyableLabel()
        self.uptime_label = CopyableLabel()
        self.mac_address_label = CopyableLabel()

        for label in (self.cpu_model_label, self.motherboard_label,
                      self.uptime_label, self.mac_address_label):
            label.setFont(self.base_font)

        details_layout = QVBoxLayout()

        row1_layout = QHBoxLayout()
        row1_layout.addWidget(self.cpu_model_label)
        row1_layout.addWidget(self.motherboard_label)
        row1_layout.addStretch()

        row2_layout = QHBoxLayout()
        row2_layout.addWidget(self.uptime_label)
        row2_layout.addWidget(self.mac_address_label)
        row2_layout.addStretch()

        details_layout.addLayout(row1_layout)
        details_layout.addSpacing(10)
        details_layout.addLayout(row2_layout)

        main_layout.addLayout(details_layout)

        self.group_box.setLayout(main_layout)

        # Основной компоновщик с разделителем
        outer_layout = QVBoxLayout(self)
        outer_layout.setContentsMargins(12, 12, 12, 12)
        outer_layout.setSpacing(10)
        outer_layout.addWidget(self.group_box)

        spacer = QSpacerItem(20, 20, QSizePolicy.Minimum, QSizePolicy.Expanding)
        outer_layout.addItem(spacer)

        separator = QFrame()
        separator.setObjectName("separator")
        separator.setFrameShape(QFrame.HLine)
        separator.setFrameShadow(QFrame.Sunken)
        outer_layout.addWidget(separator)

        self.setLayout(outer_layout)

    def create_progress_box(self, title: str, label: QLabel, progress_bar: QProgressBar) -> QWidget:
        """
        Создает виджет с заголовком и индикатором (прогресс-баром).
        """
        box = QWidget()
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        label.setText(title)
        label.setFont(self.base_font)
        label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        progress_bar.setTextVisible(True)
        progress_bar.setAlignment(Qt.AlignCenter)
        progress_bar.setFont(self.base_font)
        layout.addWidget(label)
        layout.addWidget(progress_bar)
        box.setLayout(layout)
        return box

    def update_timer(self) -> None:
        """
        Обновляет интервал автообновления согласно значению, заданному пользователем.
        """
        interval = self.interval_input.value() * 1000
        if interval > 0:
            self.timer.start(interval)
        else:
            self.timer.stop()

    def on_refresh_button_clicked(self) -> None:
        """
        Обработчик нажатия кнопки обновления.
        Устанавливает флаг ручного обновления и запускает обновление.
        """
        self.manual_update = True
        self.safe_update()

    def safe_update(self) -> None:
        """
        Запускает обновление данных о системе в отдельном потоке.
        Если предыдущий поток ещё не завершился, новая задача не запускается.
        При запуске обновления кнопка обновления блокируется.
        """
        if self.thread and self.thread.isRunning():
            return
        self.refresh_button.setEnabled(False)
        self.thread = SystemInfoThread(self.system_info)
        self.thread.data_ready.connect(self.update_info)
        self.thread.start()

    def update_info(self, info: dict) -> None:
        """
        Обновляет элементы интерфейса на основе полученной информации.
        При возникновении ошибки уведомление об ошибке показывается только при ручном обновлении.
        """
        self.refresh_button.setEnabled(True)

        if not isinstance(info, dict) or "error" in info:
            error_msg = info["error"] if isinstance(info, dict) and "error" in info else "⚠️ Не удалось получить данные"
            self.cpu_label.setText(f"💻 {error_msg}")
            self.cpu_progress.setValue(0)
            self.cpu_progress.setFormat("")
            self.ram_label.setText("📀 Данные ОЗУ недоступны")
            self.ram_progress.setValue(0)
            self.ram_progress.setFormat("")
            self.disk_table.setRowCount(0)
            if self.manual_update:
                Notification("Ошибка получения данных",
                             error_msg,
                             "error",
                             parent=self.window()).show_notification()
            return

        # Обновляем поля с расширенной информацией
        cpu_data = info.get("CPU", {})
        cpu_model = cpu_data.get("Model", "Неизвестно")
        motherboard = info.get("Motherboard", "Неизвестно")
        uptime = info.get("Uptime", "Неизвестно")
        mac = info.get("MAC_Address", "Неизвестно")

        self.cpu_model_label.setText(f"🖥️ Процессор: {cpu_model}")
        self.motherboard_label.setText(f"📡 Материнская плата: {motherboard}")
        self.uptime_label.setText(f"⏳ Время работы: {uptime}")
        self.mac_address_label.setText(f"🔌 MAC-адрес: {mac}")

        # Обновляем индикатор загрузки CPU
        cpu_load = cpu_data.get("Load")
        cpu_cores = cpu_data.get("Cores")
        value_cpu = int(cpu_load) if cpu_load is not None else 0
        self.cpu_progress.setValue(value_cpu)
        cores_text = get_cores_text(cpu_cores)
        self.cpu_progress.setFormat(f"{value_cpu}% загрузки / {cores_text}")

        # Обновляем индикатор загрузки RAM
        ram_data = info.get("RAM", {})
        ram_used = ram_data.get("UsedPercent")
        ram_total = ram_data.get("TotalGB")
        value_ram = int(ram_used) if ram_used is not None else 0
        self.ram_progress.setValue(value_ram)
        total_text = f"{ram_total} GB" if ram_total is not None else "N/A"
        self.ram_progress.setFormat(f"{value_ram}% использовано / {total_text} всего")

        # Обновляем таблицу дисков
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

        if self.manual_update:
            Notification("Данные обновлены",
                         "Информация успешно обновлена",
                         "success",
                         parent=self.window()).show_notification()

        self.manual_update = False

    def add_disk_row(self, row: int, letter, total, free, used_percent) -> None:
        """
        Добавляет строку в таблицу дисков с выравниванием и форматированием.
        """
        items = [
            QTableWidgetItem(letter),
            QTableWidgetItem(f"{total:.1f} GB"),
            QTableWidgetItem(f"{free:.1f} GB"),
            QTableWidgetItem(f"{used_percent:.1f}%")
        ]
        for col, item in enumerate(items):
            item.setTextAlignment(Qt.AlignCenter)
            item.setFlags(item.flags() & ~Qt.ItemIsEditable)
            self.disk_table.setItem(row, col, item)
