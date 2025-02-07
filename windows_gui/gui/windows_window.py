from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QApplication, QScrollArea, QMessageBox, QSpacerItem, QSizePolicy
)
from windows_gui.gui.system_info_block import SystemInfoBlock
from windows_gui.gui.commands_block import CommandsBlock
from windows_gui.gui.rdp_block import RDPBlock
from windows_gui.gui.active_users_block import ActiveUsers
from windows_gui.gui.scripts_block import ScriptsBlock
import sys
import logging

logger = logging.getLogger(__name__)

class WindowsWindow(QWidget):
    """
    Главное окно-контейнер для управления Windows-компьютером.
    Включает блоки для мониторинга системы, выполнения команд, RDP и управления скриптами.
    """
    def __init__(self, hostname, ip):
        super().__init__()

        self.hostname = hostname
        self.ip = ip
        self.setObjectName("mainWindow")  # 🎯 Теперь можно стилизовать через styles.py
        self.setWindowTitle(f"Windows: {hostname}")
        self.setGeometry(100, 100, 700, 800)

        # Основной вертикальный макет
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(12, 12, 12, 12)
        main_layout.setSpacing(10)

        # Заголовок с информацией о подключении
        self.header = QLabel(f"Имя ПК: {hostname}   |   IP: {ip}   |   ОС: Windows")
        self.header.setObjectName("headerLabel")  # 🎯 Теперь можно стилизовать через styles.py
        main_layout.addWidget(self.header)

        # Разделитель (Spacer), чтобы заголовок не прилипал к контенту
        spacer = QSpacerItem(20, 10, QSizePolicy.Minimum, QSizePolicy.Fixed)
        main_layout.addItem(spacer)

        # Используем QScrollArea для прокрутки контента
        self.scroll_area = QScrollArea()
        self.scroll_area.setObjectName("scrollArea")  # 🎯 Стилизация через styles.py
        self.scroll_area.setWidgetResizable(True)

        self.content_widget = QWidget()
        self.content_widget.setObjectName("contentWidget")  # 🎯 Стилизация через styles.py
        content_layout = QVBoxLayout(self.content_widget)

        # Инициализация блоков
        self.init_blocks(content_layout)

        self.content_widget.setLayout(content_layout)
        self.scroll_area.setWidget(self.content_widget)
        main_layout.addWidget(self.scroll_area)

    def init_blocks(self, layout):
        """
        Инициализирует блоки интерфейса и добавляет их в макет.
        Если блок не инициализируется, логирует ошибку и показывает уведомление.
        """
        blocks = [
            ("SystemInfoBlock", SystemInfoBlock, [self.hostname]),
            ("CommandsBlock", CommandsBlock, [self.hostname, self.ip]),  # Передаём ip
            ("RDPBlock", RDPBlock, [self.hostname]),
            ("ActiveUsers", ActiveUsers, [self.hostname]),
            ("ScriptsBlock", ScriptsBlock, [self.hostname]),
        ]

        for block_name, block_class, args in blocks:
            try:
                logger.info(f"Инициализация {block_name}")
                block = block_class(*args)  # Передаём аргументы как список
                layout.addWidget(block)
            except Exception as e:
                error_msg = f"Ошибка в {block_name}: {str(e)}"
                logger.error(error_msg)
                QMessageBox.critical(self, "Ошибка", error_msg)

    def closeEvent(self, event):
        """
        Закрытие окна без дополнительных действий.
        """
        event.accept()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    hostname = "VLG-STP-012"
    ip = "10.254.44.36"
    window = WindowsWindow(hostname, ip)
    window.show()
    sys.exit(app.exec())
