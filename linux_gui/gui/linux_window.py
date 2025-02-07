from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QApplication, QScrollArea,
    QMessageBox, QSpacerItem, QSizePolicy, QDialog
)
import sys
import logging

# Импорт диалога аутентификации
from linux_gui.gui.auth_block import AuthDialog

# Импорт блоков
from linux_gui.gui.system_info_block import SystemInfoBlock
from linux_gui.gui.commands_block import CommandsBlock
from linux_gui.gui.network_block import NetworkBlock
from linux_gui.gui.process_manager_block import ProcessManagerBlock
from linux_gui.gui.scripts_block import ScriptsBlock
logger = logging.getLogger(__name__)

class LinuxWindow(QWidget):
    """
    Главное окно для управления Linux/Unix-системой.
    Перед построением интерфейса запускается окно аутентификации.
    """
    def __init__(self, ip):
        super().__init__()
        self.hostname = ip
        self.ip = ip
        self.session_manager = None  # Храним SSH-сессию

        # Запускаем диалог аутентификации
        if not self.perform_authentication():
            self.close()
            return

        self.setObjectName("mainWindow")
        self.setWindowTitle(f"Linux: {self.hostname}")
        self.setGeometry(100, 100, 700, 800)

        # Основной макет
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(12, 12, 12, 12)
        main_layout.setSpacing(10)

        # Заголовок с информацией о подключении
        self.header = QLabel(f"Имя ПК: {self.hostname}   |   IP: {self.ip}   |   ОС: Linux/Unix")
        self.header.setObjectName("headerLabel")
        main_layout.addWidget(self.header)

        # Разделитель
        spacer = QSpacerItem(20, 10, QSizePolicy.Minimum, QSizePolicy.Fixed)
        main_layout.addItem(spacer)

        # Создаём область с прокруткой
        self.scroll_area = QScrollArea()
        self.scroll_area.setObjectName("scrollArea")
        self.scroll_area.setWidgetResizable(True)

        self.content_widget = QWidget()
        self.content_widget.setObjectName("contentWidget")
        content_layout = QVBoxLayout(self.content_widget)

        # Инициализация блоков
        self.init_blocks(content_layout)

        self.content_widget.setLayout(content_layout)
        self.scroll_area.setWidget(self.content_widget)
        main_layout.addWidget(self.scroll_area)

    def perform_authentication(self):
        """
        Запускает диалог аутентификации и сохраняет SSH-сессию.
        """
        auth_dialog = AuthDialog(self.hostname, self.ip, parent=self)
        result = auth_dialog.exec()
        if result == QDialog.DialogCode.Accepted:
            self.session_manager = auth_dialog.get_session_manager()
            return True
        return False

    def init_blocks(self, layout):
        """
        Инициализирует и добавляет в макет GUI-блоки.
        """
        blocks = [
            ("SystemInfoBlock", SystemInfoBlock, [self.hostname]),
            ("CommandsBlock",    CommandsBlock,    [self.hostname, self.ip]),
            ("NetworkBlock",     NetworkBlock,     [self.hostname]),
            ("ProcessManagerBlock", ProcessManagerBlock, [self.hostname]),
            ("ScriptsBlock",     ScriptsBlock,     [self.hostname]),
        ]

        for block_name, block_class, args in blocks:
            try:
                logger.info(f"Инициализация {block_name}")
                block = block_class(*args)
                layout.addWidget(block)
            except Exception as e:
                error_msg = f"Ошибка в {block_name}: {str(e)}"
                logger.error(error_msg)
                QMessageBox.critical(self, "Ошибка", error_msg)

    def close_session(self):
        """Закрывает SSH-сессию перед закрытием окна."""
        if self.session_manager:
            try:
                self.session_manager.close_session()
                logger.info(f"SSH-сессия с {self.ip} закрыта.")
            except Exception as e:
                logger.error(f"Ошибка при закрытии SSH-сессии: {e}")

    def closeEvent(self, event):
        """Разрыв SSH-сессии при закрытии окна."""
        self.close_session()
        event.accept()

# Тестовый запуск
if __name__ == "__main__":
    app = QApplication(sys.argv)
    ip = "10.254.45.204"
    # Передаём только IP-адрес, который используется и как hostname
    window = LinuxWindow(ip)
    if window.isVisible():
        window.show()
        sys.exit(app.exec())
