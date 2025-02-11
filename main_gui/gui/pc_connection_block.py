from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLineEdit,
    QPushButton, QGroupBox, QSizePolicy, QApplication
)
from PySide6.QtGui import QKeyEvent, QFont
from PySide6.QtCore import Qt, Signal
import socket
from datetime import datetime

from main_gui import utils
from database import db_manager
from notifications import Notification  # и функцию set_notifications_enabled, если потребуется


class IPLineEdit(QLineEdit):
    """
    Поле для ввода IP-адреса или имени ПК с валидацией.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setPlaceholderText("Введите IP-адрес или имя ПК")
        self.valid = True
        self.textChanged.connect(self.validate_and_highlight)

    def keyPressEvent(self, event: QKeyEvent) -> None:
        key = event.key()
        key_text = event.text()
        cursor_pos = self.cursorPosition()
        text = self.text()
        modifiers = event.modifiers()

        # 1️⃣ Разрешаем стандартные комбинации клавиш (Ctrl+C, Ctrl+V, Ctrl+X, Ctrl+A)
        if modifiers & Qt.ControlModifier:
            if key in (Qt.Key_C, Qt.Key_V, Qt.Key_X, Qt.Key_A):
                super().keyPressEvent(event)
                return

        # 2️⃣ Разрешаем клавиши удаления и навигации
        if key in (Qt.Key_Backspace, Qt.Key_Delete, Qt.Key_Left, Qt.Key_Right, Qt.Key_Home, Qt.Key_End):
            super().keyPressEvent(event)
            return

        # 3️⃣ Определяем допустимые символы
        is_digit = key_text.isdigit()
        is_dot = key_text == '.'
        is_letter_or_hyphen = key_text.isalnum() or key_text == '-'

        # 4️⃣ Проверяем, вводится ли IP-адрес
        if utils.is_potential_ip(text):
            if not (is_digit or is_dot):  # Только цифры и точки
                event.ignore()
                return

            # Не допускаем две точки подряд или точку в начале
            if is_dot and (cursor_pos == 0 or text[cursor_pos - 1] == '.'):
                event.ignore()
                return

            # Разбиваем IP на октеты
            parts = text.split('.')
            part_index = text[:cursor_pos].count('.')

            # Ограничиваем длину каждого октета до 3 цифр
            if part_index < len(parts) and len(parts[part_index]) >= 3 and is_digit:
                event.ignore()
                return

            # Автоматически вставляем точку после 3 цифр, если это не последний октет
            if is_digit and len(parts[part_index]) == 2:
                next_text = text[:cursor_pos] + key_text + text[cursor_pos:]
                new_parts = next_text.split('.')
                if len(new_parts[part_index]) == 3 and part_index < 3:
                    super().keyPressEvent(event)
                    self.insert('.')
                    return

        else:  # 5️⃣ Если вводится имя ПК
            if not is_letter_or_hyphen:  # Разрешаем только буквы, цифры и дефис
                event.ignore()
                return

            # Не допускаем дефис в начале или подряд
            if key_text == '-' and (cursor_pos == 0 or (cursor_pos < len(text) and text[cursor_pos] == '-')):
                event.ignore()
                return

        # 6️⃣ Если все проверки пройдены, передаем обработку стандартному методу
        super().keyPressEvent(event)

    def validate_and_highlight(self) -> None:
        """
        Валидирует введённый текст и подсвечивает поле красной рамкой при ошибке.
        """
        text = self.text().strip()
        # Если поле пустое или содержит неполный IP, оставляем его валидным для продолжения ввода
        if text == "" or (utils.is_partial_ip(text) and not utils.is_valid_ip(text)):
            self.valid = True
        else:
            # Для завершённого ввода требуем, чтобы текст был корректным IP или именем ПК
            self.valid = utils.is_valid_ip(text) or utils.is_valid_hostname(text)

        if not self.valid:
            self.setStyleSheet("""
                border: 2px solid #ff4d4d;
                background: #ffe6e6;
                border-radius: 6px;
                color: #b30000;
            """)
        else:
            self.setStyleSheet("")


class PCConnectionBlock(QWidget):
    """
    Блок подключения к ПК. Проверяет корректность введённых данных,
    пытается подключиться, логирует соединение в базу и обновляет связанные виджеты.
    """
    connection_successful = Signal(str, str, str)  # (OS, PC name, IP)

    def __init__(self, recent_connections_block=None, wp_map_block=None, parent=None) -> None:
        super().__init__(parent)
        self.recent_connections_block = recent_connections_block
        self.wp_map_block = wp_map_block  # Ссылка на блок "Карта РМ"

        # Явно объявляем атрибуты для корректного анализа типов
        self.ip_input: IPLineEdit | None = None
        self.connect_button: QPushButton | None = None

        self.init_ui()

    def init_ui(self) -> None:
        main_layout = QVBoxLayout()
        connection_group = QGroupBox("🔗 Подключение к ПК")
        connection_group.setObjectName("groupBox")  # Применяем стили

        group_layout = QHBoxLayout()
        group_layout.setContentsMargins(0, 0, 0, 0)
        group_layout.setSpacing(8)

        self.ip_input = IPLineEdit()
        self.ip_input.setObjectName("inputField")
        self.ip_input.setPlaceholderText("💻 Введите IP или имя ПК")
        self.ip_input.setFixedHeight(36)
        # Нажатие Enter инициирует попытку подключения
        self.ip_input.returnPressed.connect(self.connect_to_pc)

        self.connect_button = QPushButton("🚀 Подключиться")
        self.connect_button.setObjectName("actionButton")
        self.connect_button.setMinimumHeight(36)
        self.connect_button.setMinimumWidth(120)
        self.connect_button.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Fixed)
        self.connect_button.setFont(QFont("Arial", 11, QFont.Bold))
        self.connect_button.setToolTip("Нажмите для подключения к ПК")
        self.connect_button.clicked.connect(self.connect_to_pc)

        group_layout.addWidget(self.ip_input)
        group_layout.addWidget(self.connect_button, alignment=Qt.AlignVCenter)

        connection_group.setLayout(group_layout)
        main_layout.addWidget(connection_group)
        self.setLayout(main_layout)

    def connect_to_pc(self) -> None:
        """
        Обрабатывает попытку подключения к ПК и показывает уведомления об успехе или ошибке.
        """
        if self.connect_button is None or self.ip_input is None:
            return  # защита от ошибок, если интерфейс не инициализирован

        self.connect_button.setEnabled(False)
        input_text = self.ip_input.text().strip()
        parent_window = self.window()

        # Проверка на пустой ввод
        if not input_text:
            Notification(
                "🔍 Введите адрес",
                "Поле ввода пустое. Введите IP-адрес или имя ПК для подключения.",
                "warning",
                duration=3000,
                parent=parent_window
            ).show_notification()

            self.connect_button.setEnabled(True)
            return

        # Различаем корректный IP и корректное имя ПК.
        if utils.is_valid_ip(input_text):
            ip_address = input_text
        elif utils.is_valid_hostname(input_text):
            try:
                ip_address = socket.gethostbyname(input_text)
            except socket.gaierror:
                Notification(
                    "🌍 Ошибка DNS",
                    "Система не смогла определить IP-адрес по имени ПК.\nПроверьте корректность имени.",
                    "error",
                    duration=3500,
                    parent=parent_window
                ).show_notification()

                self.connect_button.setEnabled(True)
                return
        else:
            # Если ввод не является полным IP и не корректным именем ПК – возможно, это неполный ввод.
            Notification(
                "⚠ Неверный формат",
                "Проверьте, что IP-адрес или имя ПК указаны правильно.",
                "error",
                duration=3500,
                parent=parent_window
            ).show_notification()

            self.connect_button.setEnabled(True)
            return

        # Устанавливаем курсор ожидания, так как операция может занять некоторое время
        QApplication.setOverrideCursor(Qt.WaitCursor)
        try:
            reachable, _ = utils.ping_ip(ip_address)
            if not reachable:
                Notification(
                    "🚫 Нет ответа",
                    "Удалённое устройство не отвечает.\nПроверьте его подключение к сети.",
                    "error",
                    duration=4000,
                    parent=parent_window
                ).show_notification()

                return

            now = datetime.now()
            current_time_str = now.strftime("%Y-%m-%d %H:%M:%S")
            # Если определить ОС не удалось, возвращаем "Неизвестно"
            os_name = utils.detect_os(ip_address) or "Неизвестно"

            if self.recent_connections_block:
                self.recent_connections_block.add_connection(ip_address, current_time_str)

            db_manager.add_connection(ip_address, os_name, now)

            if self.wp_map_block:
                print("Обновляем таблицу 'Карта РМ' после подключения")
                self.wp_map_block.refresh_table()

            Notification(
                "🔗 Подключение установлено",
                f"Вы успешно подключились к `{ip_address}`.\nОС: `{os_name}`",
                "success",
                duration=3500,
                parent=parent_window
            ).show_notification()

            pc_name = utils.get_pc_name(ip_address) or input_text
            self.connection_successful.emit(os_name, pc_name, ip_address)
        finally:
            QApplication.restoreOverrideCursor()
            self.connect_button.setEnabled(True)
