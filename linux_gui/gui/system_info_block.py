import logging
from typing import Any, Dict

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QGroupBox, QProgressBar, QTableWidget,
    QTableWidgetItem, QPushButton, QHeaderView, QSpinBox, QHBoxLayout,
    QStyle, QSizePolicy, QFrame, QSpacerItem, QDialog
)
from PySide6.QtCore import QTimer, Qt, QThread, Signal, QSize
from PySide6.QtGui import QFont, QGuiApplication

from linux_gui.system_info import SystemInfo
from linux_gui.session_manager import SessionManager
from linux_gui.gui.auth_block import AuthDialog  # Окно авторизации
from notifications import Notification

logger = logging.getLogger(__name__)


def get_cores_text(cores: Any) -> str:
    """
    Возвращает строку с правильным окончанием для количества ядер.
    Примеры:
      1 -> "1 ядро", 2 -> "2 ядра", 5 -> "5 ядер".

    :param cores: Количество ядер (число или строка, которую можно привести к int).
    :return: Строка с количеством ядер и правильным окончанием.
    """
    try:
        cores_int = int(cores)
    except (ValueError, TypeError):
        return "N/A"
    if cores_int % 100 in (11, 12, 13, 14):
        ending = "ядер"
    else:
        last_digit = cores_int % 10
        if last_digit == 1:
            ending = "ядро"
        elif last_digit in (2, 3, 4):
            ending = "ядра"
        else:
            ending = "ядер"
    return f"{cores_int} {ending}"


class CopyableLabel(QLabel):
    """
    QLabel с возможностью выделения текста и копирования его по клику ЛКМ.
    При клике текст копируется в буфер обмена, выводится уведомление, а фон кратковременно меняется.
    """

    def __init__(self, text: str = "", parent: QWidget | None = None) -> None:
        super().__init__(text, parent)
        # Разрешаем выделение текста мышью
        self.setTextInteractionFlags(Qt.TextSelectableByMouse)

    def mousePressEvent(self, event) -> None:
        if event.button() == Qt.LeftButton:
            original_style = self.styleSheet()
            self.setStyleSheet("background-color: #e0e0e0;")  # Светло-серый фон для эффекта нажатия
            QTimer.singleShot(150, lambda: self.setStyleSheet(original_style))
            clipboard = QGuiApplication.clipboard()
            clipboard.setText(self.text())
            # Передаём уведомление без указания родителя (если требуется – можно добавить self.window())
            Notification("Скопировано", f"Скопировано: {self.text()}", "success").show_notification()
        super().mousePressEvent(event)


class SystemInfoThread(QThread):
    """
    Поток для получения данных о системе, чтобы не блокировать основной GUI.
    """
    data_ready = Signal(dict)

    def __init__(self, system_info: SystemInfo, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.system_info = system_info

    def run(self) -> None:
        """Фоновый поток для получения данных о системе."""
        logger.debug("🔄 SystemInfoThread запущен, запрашиваю данные...")
        try:
            info = self.system_info.get_system_info()
            logger.debug(f"✅ SystemInfoThread получил данные: {info}")
        except Exception as e:
            logger.exception("❌ Ошибка получения системной информации")
            info = {"error": str(e)}
        self.data_ready.emit(info)
        logger.debug("✅ SystemInfoThread завершил выполнение.")


class SystemInfoBlock(QWidget):
    """
    Виджет для отображения информации о системе удалённого Linux‑хоста.
    Содержит индикаторы загрузки CPU и RAM, таблицу по дискам,
    расширенную информацию (модель процессора, материнской платы, время работы, MAC-адрес)
    и кнопку обновления. При необходимости отображается кнопка для запроса root‑доступа.
    """

    def __init__(self, hostname: str, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.hostname: str = hostname
        # Изначально создаём SystemInfo без root-доступа
        self.system_info: SystemInfo = SystemInfo(hostname)
        self.timer: QTimer = QTimer(self)
        self.timer.timeout.connect(self.safe_update)
        self.thread: QThread | None = None

        # Базовые шрифты
        self.base_font: QFont = QFont("Arial", 10)
        self.header_font: QFont = QFont("Arial", 12, QFont.Bold)

        # Элементы для отображения CPU
        self.cpu_progress: QProgressBar = QProgressBar()
        self.cpu_label: QLabel = QLabel()
        self.cpu_progress.setFont(self.base_font)
        self.cpu_label.setFont(self.base_font)
        self.cpu_progress.setToolTip("Загрузка процессора")

        # Элементы для отображения RAM
        self.ram_progress: QProgressBar = QProgressBar()
        self.ram_label: QLabel = QLabel()
        self.ram_progress.setFont(self.base_font)
        self.ram_label.setFont(self.base_font)
        self.ram_progress.setToolTip("Использование оперативной памяти")

        # Таблица для отображения информации по дискам
        self.disk_table: QTableWidget = QTableWidget()
        self.disk_table.setFont(self.base_font)
        self.disk_table.setColumnCount(4)
        self.disk_table.setHorizontalHeaderLabels([
            "💽 Раздел", "📦 Всего", "🔓 Свободно", "📈 Использовано"
        ])
        header_obj = self.disk_table.horizontalHeader()
        header_obj.setSectionResizeMode(QHeaderView.Stretch)
        self.disk_table.verticalHeader().setVisible(False)
        self.disk_table.setSelectionMode(QTableWidget.NoSelection)
        self.disk_table.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.disk_table.setFixedHeight(130)

        # Элементы для отображения расширенной информации (используем CopyableLabel)
        self.cpu_model_label: CopyableLabel = CopyableLabel("Процессор: неизвестно")
        self.cpu_model_label.setFont(self.base_font)
        self.motherboard_label: CopyableLabel = CopyableLabel("Материнская плата: неизвестно")
        self.motherboard_label.setFont(self.base_font)
        self.uptime_label: CopyableLabel = CopyableLabel("Время работы: загрузка...")
        self.uptime_label.setFont(self.base_font)
        self.mac_address_label: CopyableLabel = CopyableLabel("MAC-адрес: неизвестно")
        self.mac_address_label.setFont(self.base_font)

        # Кнопка запроса root-доступа (скрыта по умолчанию)
        self.root_access_button: QPushButton = QPushButton("🔑 Получить root-доступ")
        self.root_access_button.setFont(self.base_font)
        self.root_access_button.setVisible(False)
        self.root_access_button.clicked.connect(self.request_root_access)

        # Кнопка обновления данных
        self.refresh_button: QPushButton = QPushButton("Обновить данные")
        self.refresh_button.setFont(self.base_font)
        self.refresh_button.setIcon(self.style().standardIcon(QStyle.SP_BrowserReload))
        self.refresh_button.setIconSize(QSize(20, 20))
        self.refresh_button.setToolTip("Нажмите для обновления данных о системе")
        self.refresh_button.clicked.connect(self.safe_update)

        # Интервал автообновления
        self.interval_label: QLabel = QLabel("⏱️ Интервал автообновления:")
        self.interval_label.setFont(self.base_font)
        self.interval_input: QSpinBox = QSpinBox()
        self.interval_input.setRange(0, 600)
        self.interval_input.setSuffix(" сек")
        self.interval_input.setSingleStep(10)
        self.interval_input.setValue(0)
        self.interval_input.setFixedWidth(120)
        self.interval_input.setAlignment(Qt.AlignRight)
        self.interval_input.setFont(self.base_font)
        self.interval_input.setToolTip("Задайте интервал автообновления (0 – автообновление отключено)")
        self.interval_input.valueChanged.connect(self.update_timer)

        self.init_ui()
        self.safe_update()

    def init_ui(self) -> None:
        """
        Инициализирует визуальные компоненты виджета с переработанным расположением элементов.
        """
        self.group_box: QGroupBox = QGroupBox("🖥️ Информация о системе")
        self.group_box.setFont(self.header_font)

        # Основной layout для группы
        group_layout = QVBoxLayout(self.group_box)
        group_layout.setSpacing(10)
        group_layout.setContentsMargins(12, 12, 12, 12)

        # 1. Блок с индикаторами CPU и RAM (один ряд)
        progress_layout = QHBoxLayout()
        cpu_box = self.create_progress_box("Процессор:", self.cpu_label, self.cpu_progress)
        ram_box = self.create_progress_box("ОЗУ:", self.ram_label, self.ram_progress)
        progress_layout.addWidget(cpu_box)
        progress_layout.addWidget(ram_box)
        progress_layout.addStretch()
        group_layout.addLayout(progress_layout)

        # 2. Таблица дисков
        group_layout.addWidget(self.disk_table)

        # 3. Блок управления: кнопка обновления и выбор интервала автообновления
        control_layout = QHBoxLayout()
        control_layout.addWidget(self.refresh_button)
        control_layout.addStretch()
        group_layout.addLayout(control_layout)

        interval_layout = QHBoxLayout()
        interval_layout.addWidget(self.interval_label)
        interval_layout.addWidget(self.interval_input)
        interval_layout.addStretch()
        group_layout.addLayout(interval_layout)

        # 4. Блок расширенной информации (два ряда по два элемента)
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
        group_layout.addLayout(details_layout)

        # 5. Кнопка запроса root-доступа (при необходимости)
        group_layout.addWidget(self.root_access_button)

        self.group_box.setLayout(group_layout)

        # Основной layout виджета
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

    def create_progress_box(self, title: str, label: QLabel, progress_bar: QProgressBar) -> QWidget:
        """
        Создает виджет для отображения заголовка и индикатора (прогрессбара).

        :param title: Текст заголовка.
        :param label: QLabel для отображения заголовка.
        :param progress_bar: QProgressBar для отображения прогресса.
        :return: Собранный виджет.
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

    def update_timer(self) -> None:
        """
        Обновляет интервал автообновления в соответствии со значением, заданным пользователем.
        """
        interval = self.interval_input.value() * 1000
        if interval > 0:
            self.timer.start(interval)
        else:
            self.timer.stop()

    def request_root_access(self) -> None:
        """
        Запрашивает root-доступ через диалог авторизации.
        Если аутентификация успешна, пересоздаёт SessionManager и обновляет SystemInfo.
        """
        dialog = AuthDialog(self.hostname, self.hostname)  # Показываем окно авторизации
        if dialog.exec() == QDialog.Accepted:
            credentials = dialog.get_credentials()  # Метод get_credentials() должен быть реализован в AuthDialog
            if not credentials:
                logger.error("❌ Ошибка: не удалось получить root-учётные данные.")
                return
            root_username, root_password = credentials
            # Пересоздаём менеджер с root-доступом
            session = SessionManager.get_instance(
                self.hostname,
                root_username,
                root_password,
                root_username=root_username,
                root_password=root_password
            )
            try:
                session.connect()
            except Exception as e:
                logger.exception("Ошибка подключения с root-доступом")
                Notification(
                    "🔑 Ошибка root-доступа",
                    f"Не удалось выполнить подключение с root-правами.\nОшибка: `{e}`",
                    "error",
                    parent=self.window()
                ).show_notification()

                return
            # Обновляем SystemInfo с новыми данными
            self.system_info = SystemInfo(self.hostname, root_username, root_password)
            logger.info("✅ Root-доступ успешно получен, обновляем данные...")
            self.safe_update()

    def safe_update(self) -> None:
        """
        Запускает обновление данных о системе в отдельном потоке.
        Если предыдущий поток ещё выполняется, новая задача не запускается.
        """
        if self.thread and self.thread.isRunning():
            logger.warning("⚠️ Предыдущий поток ещё выполняется, новое обновление не запущено.")
            return
        logger.debug("🚀 Запускаю новый поток SystemInfoThread...")
        self.refresh_button.setEnabled(False)
        self.thread = SystemInfoThread(self.system_info)
        self.thread.data_ready.connect(self.update_info)
        self.thread.start()

    def update_info(self, info: Dict[str, Any]) -> None:
        """
        Обновляет GUI на основе полученной информации.

        :param info: Словарь с данными о системе.
        """
        logger.debug(f"update_info() получил данные: {info}")

        if not isinstance(info, dict) or "error" in info:
            error_msg = info.get("error", "⚠️ Не удалось получить данные")
            logger.error(f"Ошибка в данных: {error_msg}")

            self.cpu_label.setText(f"Процессор: {error_msg}")
            self.cpu_progress.setValue(0)
            self.ram_label.setText("ОЗУ: данные недоступны")
            self.ram_progress.setValue(0)
            self.disk_table.setRowCount(0)
            self.cpu_model_label.setText("Процессор: неизвестно")
            self.motherboard_label.setText("Материнская плата: неизвестно")
            self.uptime_label.setText("Время работы: N/A")
            self.mac_address_label.setText("MAC-адрес: N/A")

            # Если ошибка связана с отсутствием root-доступа – отображаем кнопку
            if "требуется root-доступ" in error_msg or "не передан пароль root" in error_msg:
                self.root_access_button.setVisible(True)
                Notification(
                    "🔑 Требуется root-доступ",
                    "Для получения полной информации о системе необходимы root-права.",
                    "warning",
                    parent=self.window()
                ).show_notification()

            self.refresh_button.setEnabled(True)
            return

        # Обновляем данные по CPU
        cpu_data = info.get("CPU", {})
        cpu_load = cpu_data.get("Load", 0)
        cpu_cores = cpu_data.get("Cores")
        value_cpu = int(cpu_load) if cpu_load is not None else 0
        self.cpu_progress.setValue(value_cpu)
        cores_text = get_cores_text(cpu_cores)
        self.cpu_progress.setFormat(f"{value_cpu}% загрузки / {cores_text}")
        self.cpu_label.setText(f"Процессор: {value_cpu}%")

        # Обновляем данные по RAM
        ram_data = info.get("RAM", {})
        ram_used = ram_data.get("UsedPercent", 0)
        ram_total = ram_data.get("TotalGB")
        value_ram = int(ram_used) if ram_used is not None else 0
        self.ram_progress.setValue(value_ram)
        total_text = f"{ram_total:.1f} GB" if ram_total is not None else "N/A"
        self.ram_progress.setFormat(f"{value_ram}% использовано / {total_text} всего")
        self.ram_label.setText(f"ОЗУ: {value_ram}%")

        # Обновляем расширенную информацию
        cpu_model = info.get("CPU_Model", "Неизвестно")
        motherboard = info.get("Motherboard_Model", "Неизвестно")
        # Если данные содержат сообщение о необходимости root-доступа – показываем кнопку
        if ("требуется root-доступ" in cpu_model or
                "требуется root-доступ" in motherboard or
                "не передан пароль root" in cpu_model):
            self.root_access_button.setVisible(True)
        else:
            self.root_access_button.setVisible(False)

        self.cpu_model_label.setText(f"Процессор: {cpu_model}")
        self.motherboard_label.setText(f"Материнская плата: {motherboard}")
        self.uptime_label.setText(f"Время работы: {info.get('Uptime', 'N/A')}")
        self.mac_address_label.setText(f"MAC-адрес: {info.get('MAC_Address', 'N/A')}")

        # Обновляем таблицу дисков
        disks = info.get("Disks", [])
        self.disk_table.setRowCount(len(disks))
        for row, disk in enumerate(disks):
            self.add_disk_row(
                row,
                disk.get("Letter", "N/A"),
                disk.get("TotalGB", 0),
                disk.get("FreeGB", 0),
                disk.get("UsedPercent", 0)
            )

        logger.debug("update_info() завершил обновление GUI.")
        Notification(
            "🖥️ Обновление системы",
            "Системная информация успешно загружена.",
            "success",
            parent=self.window()
        ).show_notification()
        self.refresh_button.setEnabled(True)

    def add_disk_row(self, row: int, letter: Any, total: Any, free: Any, used_percent: Any) -> None:
        """
        Добавляет строку в таблицу дисков с выравниванием и форматированием.

        :param row: Номер строки.
        :param letter: Имя раздела.
        :param total: Общий объём.
        :param free: Свободное место.
        :param used_percent: Процент использования.
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
