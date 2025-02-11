from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QApplication, QScrollArea,
    QMessageBox, QSpacerItem, QSizePolicy, QDialog, QFrame
)
from PySide6.QtCore import Qt
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

from settings import load_settings

logger = logging.getLogger(__name__)


class LinuxWindow(QWidget):
    """
    Главное окно для управления Linux/Unix-системой.
    Перед построением интерфейса запускается окно аутентификации.
    Если аутентификация не пройдена, выбрасывается исключение,
    чтобы не создавать пустой GUI.
    """

    def __init__(self, ip: str) -> None:
        super().__init__()
        self.hostname: str = ip  # В данном случае имя ПК совпадает с IP
        self.ip: str = ip  # IP для передачи в блоки (например, CommandsBlock)
        self.session_manager = None  # Здесь будет храниться SSH-сессия

        # Запускаем диалог аутентификации.
        # Если аутентификация не пройдена, генерируем исключение.
        if not self.perform_authentication():
            raise Exception("Аутентификация не пройдена")

        self.setObjectName("mainWindow")
        self.setWindowTitle(f"Linux: {self.hostname}")
        self.setGeometry(100, 100, 700, 800)

        # Основной макет окна
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(12, 12, 12, 12)
        main_layout.setSpacing(10)

        # Заголовок с информацией о подключении
        self.header = QLabel(f"Имя ПК: {self.hostname}   |   ОС: Linux/Unix")
        self.header.setObjectName("headerLabel")
        self.header.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(self.header)

        # Разделитель — горизонтальная линия
        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        separator.setFrameShadow(QFrame.Sunken)
        main_layout.addWidget(separator)

        # Область с прокруткой для размещения блоков
        self.scroll_area = QScrollArea()
        self.scroll_area.setObjectName("scrollArea")
        self.scroll_area.setWidgetResizable(True)

        # Контейнер для блоков
        self.content_widget = QWidget()
        self.content_widget.setObjectName("contentWidget")
        content_layout = QVBoxLayout(self.content_widget)
        content_layout.setSpacing(10)
        content_layout.setContentsMargins(0, 0, 0, 0)

        # Инициализация блоков с учетом сохранённой компоновки
        self.init_blocks(content_layout)

        self.scroll_area.setWidget(self.content_widget)
        main_layout.addWidget(self.scroll_area)

    def perform_authentication(self) -> bool:
        """
        Запускает диалог аутентификации и сохраняет SSH-сессию, если аутентификация пройдена.

        :return: True, если аутентификация успешна, иначе False.
        """
        auth_dialog = AuthDialog(self.hostname, self.ip, parent=self)
        result = auth_dialog.exec()
        if result == QDialog.DialogCode.Accepted:
            self.session_manager = auth_dialog.get_session_manager()
            return True
        return False

    def init_blocks(self, layout: QVBoxLayout) -> None:
        """
        Инициализирует и добавляет в макет GUI-блоки согласно сохранённой компоновке.
        Если в настройках присутствует ключ "layout_linux", используется порядок и видимость блоков из него.
        В противном случае используется порядок по умолчанию.
        """
        settings = load_settings()

        default_order = [
            ("SystemInfoBlock", SystemInfoBlock, [self.hostname]),
            ("CommandsBlock", CommandsBlock, [self.hostname, self.ip]),
            ("NetworkBlock", NetworkBlock, [self.hostname]),
            ("ProcessManagerBlock", ProcessManagerBlock, [self.hostname]),
            ("ScriptsBlock", ScriptsBlock, [self.hostname]),
        ]

        layout_config = settings.get("layout_linux")
        if layout_config:
            # Создаем словарь: имя блока -> (класс, аргументы)
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
                        QMessageBox.critical(self, "Ошибка", f"Ошибка в {block_name}: {e}")
        else:
            # Если настроек нет – используем порядок по умолчанию
            for block_name, block_class, args in default_order:
                try:
                    block_instance = block_class(*args)
                    layout.addWidget(block_instance)
                except Exception as e:
                    logger.exception(f"Ошибка в {block_name}: {e}")
                    QMessageBox.critical(self, "Ошибка", f"Ошибка в {block_name}: {e}")

    def update_layout(self) -> None:
        """
        Обновляет компоновку блоков согласно текущим настройкам.
        Метод очищает существующий layout контейнера и вызывает повторную инициализацию блоков.
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

    def close_session(self) -> None:
        """
        Закрывает SSH-сессию перед закрытием окна.
        """
        if self.session_manager:
            try:
                self.session_manager.close_session()
                logger.info(f"SSH-сессия с {self.ip} закрыта.")
            except Exception as e:
                logger.exception(f"Ошибка при закрытии SSH-сессии: {e}")

    def closeEvent(self, event) -> None:
        """
        При закрытии окна разрывается SSH-сессия, после чего окно закрывается.
        """
        self.close_session()
        event.accept()


# Тестовый запуск
if __name__ == "__main__":
    app = QApplication(sys.argv)
    ip = "10.254.45.64"
    try:
        window = LinuxWindow(ip)
        window.show()
        sys.exit(app.exec())
    except Exception as e:
        logger.exception(f"Не удалось запустить приложение: {e}")
