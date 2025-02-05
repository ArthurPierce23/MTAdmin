from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QGroupBox, QProgressBar,
    QTableWidget, QTableWidgetItem, QPushButton, QHeaderView,
    QSpinBox, QHBoxLayout, QStyle, QSizePolicy, QStyledItemDelegate
)
from PySide6.QtCore import QTimer, Qt, QThread, Signal, QSize, QUrl
from PySide6.QtGui import QDesktopServices, QIcon, QFontMetrics, QColor, QPainter, QAction
from windows_gui.system_info import SystemInfo
from notifications import Notification


def get_cores_text(cores):
    """
    Возвращает строку с правильным окончанием для количества ядер.
    Например: 1 -> "1 ядро", 2 -> "2 ядра", 5 -> "5 ядер".
    """
    try:
        cores = int(cores)
    except (ValueError, TypeError):
        return "N/A"
    # Определяем окончание
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

    def __init__(self, system_info):
        super().__init__()
        self.system_info = system_info

    def run(self):
        info = self.system_info.get_system_info()
        self.data_ready.emit(info)


class ScriptItemDelegate(QStyledItemDelegate):
    """
    Делегат для отрисовки элемента списка скриптов с тегами.
    (Если понадобится для будущего расширения функционала.)
    """
    def paint(self, painter, option, index):
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
    загрузка CPU, использование ОЗУ, данные по дискам и возможность автообновления.
    При возникновении ошибок отображаются уведомления.
    """
    def __init__(self, hostname, parent=None):
        super().__init__(parent)
        self.hostname = hostname
        self.system_info = SystemInfo(hostname)
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.safe_update)
        self.thread = None

        # Элементы для отображения CPU и RAM
        self.cpu_progress = QProgressBar()
        self.ram_progress = QProgressBar()
        self.cpu_label = QLabel()
        self.ram_label = QLabel()

        # Устанавливаем стиль прогрессбаров (чёрный цвет текста)
        self.cpu_progress.setStyleSheet("color: black;")
        self.ram_progress.setStyleSheet("color: black;")

        self.init_ui()
        self.safe_update()

    def init_ui(self):
        """Инициализирует визуальные компоненты виджета."""
        group_box = QGroupBox("🖥️ Информация о системе")
        group_box.setStyleSheet("font-size: 16px; font-weight: 600;")
        layout = QVBoxLayout()

        # Блоки для CPU и RAM с соответствующими эмодзи
        cpu_box = self.create_progress_box("💻 Процессор:", self.cpu_label, self.cpu_progress)
        ram_box = self.create_progress_box("📀 Оперативная память:", self.ram_label, self.ram_progress)

        # Кнопка для ручного обновления данных
        self.refresh_button = QPushButton(" Обновить данные")
        self.refresh_button.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_BrowserReload))
        self.refresh_button.setIconSize(QSize(20, 20))
        self.refresh_button.setToolTip("Обновить данные о системе в реальном времени")
        self.refresh_button.clicked.connect(self.safe_update)

        control_layout = QHBoxLayout()
        control_layout.addWidget(self.refresh_button)
        control_layout.addStretch()

        # Блок для выбора интервала автообновления
        interval_layout = QHBoxLayout()
        self.interval_label = QLabel("⏱️ Интервал обновления:")
        self.interval_input = QSpinBox()
        self.interval_input.setRange(0, 600)
        self.interval_input.setSuffix(" сек")
        self.interval_input.setSingleStep(10)
        self.interval_input.setValue(0)
        self.interval_input.setFixedWidth(120)
        self.interval_input.setAlignment(Qt.AlignRight)
        self.interval_input.valueChanged.connect(self.update_timer)

        interval_layout.addWidget(self.interval_label)
        interval_layout.addWidget(self.interval_input)
        interval_layout.addStretch()
        interval_layout.setContentsMargins(0, 0, 0, 0)

        # Таблица для отображения информации по дискам
        self.disk_table = QTableWidget()
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

        # Компонуем все элементы
        layout.addWidget(cpu_box)
        layout.addWidget(ram_box)
        layout.addWidget(self.disk_table)
        layout.addLayout(control_layout)
        layout.addLayout(interval_layout)

        group_box.setLayout(layout)
        main_layout = QVBoxLayout()
        main_layout.addWidget(group_box)
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

    def update_info(self, info):
        """
        Обновляет данные в индикаторах и таблице на основе полученной информации.
        В случае ошибки отображается уведомление.
        """
        if not isinstance(info, dict) or "error" in info:
            error_msg = "⚠️ Не удалось получить данные" if not isinstance(info, dict) else info["error"]
            self.cpu_label.setText(f"💻 {error_msg}")
            self.cpu_progress.setValue(0)
            self.cpu_progress.setFormat("")
            self.ram_label.setText("📀 Данные ОЗУ недоступны")
            self.ram_progress.setValue(0)
            self.ram_progress.setFormat("")
            self.disk_table.setRowCount(0)
            Notification("Ошибка получения данных о системе", "error").show_notification()
            return

        # Обновляем индикатор загрузки CPU
        cpu_data = info.get("CPU", {})
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
        Notification("Данные обновлены", "success").show_notification()

    def add_disk_row(self, row, letter, total, free, used_percent):
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
