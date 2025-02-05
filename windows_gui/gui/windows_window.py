from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QApplication, QScrollArea, QMessageBox
)
from windows_gui.gui.system_info_block import SystemInfoBlock
from windows_gui.gui.commands_block import CommandsBlock
from windows_gui.gui.rdp_block import RDPBlock
from windows_gui.gui.active_users_block import ActiveUsers
from windows_gui.gui.scripts_block import ScriptsBlock
import sys


class WindowsWindow(QWidget):
    """
    Главное окно-контейнер для управления Windows-компьютером.
    Включает блоки для мониторинга системы, выполнения команд, RDP и управления скриптами.
    """
    def __init__(self, hostname, ip):
        super().__init__()

        self.hostname = hostname
        self.ip = ip
        self.setWindowTitle(f"Windows: {hostname}")
        self.setGeometry(100, 100, 700, 800)

        # Основной вертикальный макет
        main_layout = QVBoxLayout()

        # Заголовок с информацией о подключении
        header = QLabel(f"Имя ПК: {hostname}   |   IP: {ip}   |   ОС: Windows")
        header.setStyleSheet("font-size: 14pt; padding: 5px;")
        main_layout.addWidget(header)

        # Используем QScrollArea для прокрутки контента
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        content_widget = QWidget()
        content_layout = QVBoxLayout()

        # Инициализация блоков с безопасной обработкой ошибок
        self.init_blocks(content_layout)

        content_widget.setLayout(content_layout)
        scroll_area.setWidget(content_widget)
        main_layout.addWidget(scroll_area)

        self.setLayout(main_layout)

    def init_blocks(self, layout):
        """
        Инициализирует блоки интерфейса и добавляет их в макет.
        Если блок не инициализируется, логирует ошибку и показывает уведомление.
        """
        blocks = [
            ("SystemInfoBlock", SystemInfoBlock),
            ("CommandsBlock", CommandsBlock),
            ("RDPBlock", RDPBlock),
            ("ActiveUsers", ActiveUsers),
            ("ScriptsBlock", ScriptsBlock),
        ]

        for block_name, block_class in blocks:
            try:
                print(f"Инициализация {block_name}")
                block = block_class(hostname=self.hostname)
                layout.addWidget(block)
            except Exception as e:
                error_msg = f"Ошибка в {block_name}: {str(e)}"
                print(error_msg)
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
