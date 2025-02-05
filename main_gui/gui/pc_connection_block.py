# pc_connection_block.py
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton, QGroupBox
from PySide6.QtGui import QKeyEvent
from PySide6.QtCore import Qt, Signal
import socket
from datetime import datetime

from main_gui import utils
from database import db_manager
from notifications import Notification


class IPLineEdit(QLineEdit):
    """
    Поле для ввода IP-адреса или имени ПК с валидацией.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setPlaceholderText("Введите IP-адрес или имя ПК")
        self.valid = True
        self.textChanged.connect(self.validate_and_highlight)

    def keyPressEvent(self, event: QKeyEvent):
        key = event.key()
        key_text = event.text()
        cursor_pos = self.cursorPosition()
        text = self.text()

        # Разрешённые символы
        is_digit = key_text.isdigit()
        is_dot = key_text == '.'
        is_letter_or_hyphen = key_text.isalnum() or key_text == '-'

        # Разрешаем клавиши удаления
        if key in (Qt.Key_Backspace, Qt.Key_Delete):
            super().keyPressEvent(event)
            return

        # Если текст может быть IP-адресом, разрешаем только цифры и точки
        if utils.is_potential_ip(text):
            if not (is_digit or is_dot):
                event.ignore()
                return

            # Не допускаем точки в начале или двойные точки
            if is_dot and (cursor_pos == 0 or text[cursor_pos - 1] == '.'):
                event.ignore()
                return

            parts = text.split('.')
            part_index = text[:cursor_pos].count('.')
            if part_index < len(parts) and len(parts[part_index]) >= 3 and is_digit:
                event.ignore()
                return

            # Если в части уже 2 цифры – добавляем точку после ввода 3-й цифры (для облегчения ввода)
            if is_digit and len(parts[part_index]) == 2:
                next_text = text[:cursor_pos] + key_text + text[cursor_pos:]
                new_parts = next_text.split('.')
                if len(new_parts[part_index]) == 3 and part_index < 3:
                    super().keyPressEvent(event)
                    self.insert('.')
                    return

        else:
            # Если вводится имя ПК – разрешаем буквы, цифры и дефис
            if not is_letter_or_hyphen:
                event.ignore()
                return

            if key_text == '-' and (cursor_pos == 0 or (cursor_pos < len(text) and text[cursor_pos] == '-')):
                event.ignore()
                return

        super().keyPressEvent(event)

    def validate_and_highlight(self):
        """
        Валидирует введённый текст и подсвечивает поле красной рамкой при ошибке.
        """
        text = self.text().strip()
        if text == "" or utils.is_partial_ip(text):
            self.valid = True
        else:
            self.valid = utils.is_valid_input(text)
        self.setStyleSheet("border: 2px solid red;" if not self.valid else "")


class PCConnectionBlock(QWidget):
    """
    Блок подключения к ПК. Проверяет корректность введённых данных,
    пытается подключиться, логирует соединение в базу и обновляет связанные виджеты.
    """
    connection_successful = Signal(str, str, str)  # (OS, PC name, IP)

    def __init__(self, recent_connections_block=None, wp_map_block=None, parent=None):
        super().__init__(parent)
        self.recent_connections_block = recent_connections_block
        self.wp_map_block = wp_map_block  # Ссылка на блок "Карта РМ"
        self.init_ui()

    def init_ui(self):
        main_layout = QVBoxLayout()
        connection_group = QGroupBox("Подключение к ПК")
        group_layout = QVBoxLayout()

        ip_layout = QHBoxLayout()
        ip_label = QLabel("IP-адрес:")
        ip_layout.addWidget(ip_label)

        self.ip_input = IPLineEdit()
        ip_layout.addWidget(self.ip_input, 1)

        self.connect_button = QPushButton("Подключиться")
        ip_layout.addWidget(self.connect_button)
        self.connect_button.clicked.connect(self.connect_to_pc)

        group_layout.addLayout(ip_layout)
        connection_group.setLayout(group_layout)
        main_layout.addWidget(connection_group)
        self.setLayout(main_layout)

    def connect_to_pc(self):
        """
        Обрабатывает попытку подключения к ПК:
        - Валидирует ввод
        - Пытается получить IP-адрес (если введено имя)
        - Проверяет доступность устройства
        - Логирует подключение и обновляет связанные блоки
        - Показывает уведомления об ошибках или успехе
        """
        # Блокируем кнопку, чтобы избежать повторных попыток
        self.connect_button.setEnabled(False)
        input_text = self.ip_input.text().strip()

        if not utils.is_valid_input(input_text):
            self.ip_input.setStyleSheet("border: 2px solid red;")
            Notification("Некорректный IP-адрес или имя ПК.", "error", duration=3000, parent=self).show_notification()
            self.connect_button.setEnabled(True)
            return

        # Определяем, является ли введённое значение IP-адресом
        is_ip = utils.is_valid_ip(input_text)
        ip_address = input_text if is_ip else None

        # Если введено имя ПК, пытаемся получить его IP-адрес
        if not is_ip:
            try:
                ip_address = socket.gethostbyname(input_text)
            except socket.gaierror:
                Notification("Не удалось разрешить имя ПК.", "error", duration=3000, parent=self).show_notification()
                self.connect_button.setEnabled(True)
                return

        # Проверяем доступность устройства (пинг)
        reachable, _ = utils.ping_ip(ip_address)
        if not reachable:
            Notification("Устройство не отвечает.", "error", duration=3000, parent=self).show_notification()
            self.connect_button.setEnabled(True)
            return

        # Определяем операционную систему устройства
        os_name = utils.detect_os(ip_address) if is_ip else "Windows"

        current_time_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # Добавляем запись в блок "Недавние подключения"
        if self.recent_connections_block:
            self.recent_connections_block.add_connection(ip_address, current_time_str)

        # Записываем подключение в базу данных
        db_manager.add_connection(ip_address, os_name, datetime.now())

        # Обновляем данные в блоке "Карта РМ", если он присутствует
        if self.wp_map_block:
            # Можно заменить print() на вызов логгера, если он у вас настроен
            print("Обновляем таблицу 'Карта РМ' после подключения")
            self.wp_map_block.refresh_table()

        # Уведомление об успешном подключении
        Notification(f"Подключение к {ip_address} ({os_name}) успешно!", "success", duration=3000,
                     parent=self).show_notification()

        # Генерируем сигнал успешного подключения с данными:
        if os_name == "Windows" or not is_ip:
            pc_name = utils.get_pc_name(ip_address) if is_ip else input_text
            self.connection_successful.emit("Windows", pc_name or "Неизвестно", ip_address)
        elif os_name == "Linux/Unix":
            self.connection_successful.emit("Linux", "", ip_address)
        else:
            Notification("Не удалось определить операционную систему.", "error", duration=3000,
                         parent=self).show_notification()

        self.connect_button.setEnabled(True)
