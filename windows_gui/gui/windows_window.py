from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QApplication, QScrollArea,
    QSpacerItem, QSizePolicy
)
from windows_gui.gui.system_info_block import SystemInfoBlock
from windows_gui.gui.commands_block import CommandsBlock
from windows_gui.gui.rdp_block import RDPBlock
from windows_gui.gui.active_users_block import ActiveUsers
from windows_gui.gui.scripts_block import ScriptsBlock
from notifications import Notification

import sys
import logging

# Инициализация логгера
logger = logging.getLogger(__name__)


class WindowsWindow(QWidget):
    """
    Главное окно для управления Windows-компьютером.
    Объединяет блоки для мониторинга системы, выполнения команд, RDP и управления скриптами.
    """
    def __init__(self, hostname: str, ip: str) -> None:
        super().__init__()
        self.hostname = hostname
        self.ip = ip

        self.setObjectName("mainWindow")
        self.setWindowTitle(f"Windows: {hostname}")
        self.setGeometry(100, 100, 700, 800)

        # Основной вертикальный макет окна
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(12, 12, 12, 12)
        main_layout.setSpacing(10)

        # Заголовок с информацией о подключении
        self.header = QLabel(f"Имя ПК: {hostname}   |   IP: {ip}   |   ОС: Windows")
        self.header.setObjectName("headerLabel")
        main_layout.addWidget(self.header)

        # Разделитель (Spacer) между заголовком и основным содержимым
        spacer = QSpacerItem(20, 10, QSizePolicy.Minimum, QSizePolicy.Fixed)
        main_layout.addItem(spacer)

        # Область прокрутки для основного содержимого
        self.scroll_area = QScrollArea()
        self.scroll_area.setObjectName("scrollArea")
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setFrameShape(QScrollArea.NoFrame)

        # Контейнер для блоков внутри области прокрутки
        self.content_widget = QWidget()
        self.content_widget.setObjectName("contentWidget")
        content_layout = QVBoxLayout()
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(10)

        # Инициализация блоков с учетом сохраненной компоновки
        self.init_blocks(content_layout)

        self.content_widget.setLayout(content_layout)
        self.scroll_area.setWidget(self.content_widget)
        main_layout.addWidget(self.scroll_area)

    def init_blocks(self, layout: QVBoxLayout) -> None:
        """
        Инициализирует блоки согласно сохранённой компоновке из settings.json.
        Если настройки отсутствуют, используется порядок по умолчанию.
        """
        from settings import load_settings
        settings = load_settings()

        # Порядок блоков по умолчанию
        default_order = [
            ("SystemInfoBlock", SystemInfoBlock, [self.hostname]),
            ("CommandsBlock", CommandsBlock, [self.hostname, self.ip]),
            ("RDPBlock", RDPBlock, [self.hostname]),
            ("ActiveUsers", ActiveUsers, [self.hostname]),
            ("ScriptsBlock", ScriptsBlock, [self.hostname]),
        ]

        # Пытаемся загрузить сохранённую компоновку для Windows
        layout_config = settings.get("layout_windows")
        if layout_config:
            # Создаем словарь соответствия: имя блока -> (класс, аргументы)
            block_mapping = {name: (cls, args) for name, cls, args in default_order}
            for block in layout_config:
                block_name = block.get("name")
                visible = block.get("visible", True)
                if visible and block_name in block_mapping:
                    cls, args = block_mapping[block_name]
                    try:
                        block_instance = cls(*args)
                        layout.addWidget(block_instance)
                    except Exception as e:
                        logger.exception(f"Ошибка в {block_name}: {e}")
                        Notification(f"Ошибка в {block_name}: {e}", "error", duration=3000, parent=self).show_notification()
        else:
            # Если настроек нет – создаем блоки в порядке по умолчанию
            for block_name, block_class, args in default_order:
                try:
                    block_instance = block_class(*args)
                    layout.addWidget(block_instance)
                except Exception as e:
                    error_msg = f"Ошибка в {block_name}: {e}"
                    logger.exception(error_msg)
                    Notification(error_msg, "error", duration=3000, parent=self).show_notification()

    def update_layout(self) -> None:
        """
        Обновляет компоновку блоков согласно текущим настройкам.
        Метод очищает текущий layout контейнера и повторно вызывает init_blocks().
        """
        layout = self.content_widget.layout()
        if layout is None:
            layout = QVBoxLayout(self.content_widget)
            self.content_widget.setLayout(layout)
        # Удаляем все элементы из layout
        while layout.count():
            item = layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.setParent(None)
                widget.deleteLater()
        # Пересоздаем блоки по новым настройкам
        self.init_blocks(layout)

    def closeEvent(self, event) -> None:
        """
        Обработка события закрытия окна.
        """
        event.accept()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    hostname = "VLG-STP-012"
    ip = "10.254.44.36"
    window = WindowsWindow(hostname, ip)
    window.show()
    sys.exit(app.exec())
