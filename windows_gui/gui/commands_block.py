from functools import partial
from typing import Callable

from PySide6.QtWidgets import (
    QWidget, QGridLayout, QPushButton, QGroupBox, QVBoxLayout,
    QSpacerItem, QSizePolicy, QFrame
)
from PySide6.QtCore import Qt
from windows_gui.commands import (
    run_powershell, open_compmgmt, open_rdp,
    open_shadow_rdp, open_c_drive, open_cmd
)
from notifications import Notification


class CommandsBlock(QWidget):
    """
    Виджет для запуска удалённых команд.
    """
    def __init__(self, hostname: str, ip: str, parent: QWidget = None) -> None:
        """
        Инициализация виджета с указанием имени хоста и IP.

        :param hostname: Имя хоста для команд, использующих hostname.
        :param ip: IP-адрес для команд, использующих IP.
        :param parent: Родительский виджет.
        """
        super().__init__(parent)
        self.hostname: str = hostname
        self.ip: str = ip
        self.init_ui()

    def init_ui(self) -> None:
        """
        Создаёт интерфейс с кнопками команд, оформленный через group box.
        """
        # Группа команд
        self.group_box = QGroupBox("💻 Команды управления", self)
        self.group_box.setObjectName("groupBox")  # Стили из styles.py
        group_layout = QVBoxLayout(self.group_box)
        group_layout.setContentsMargins(10, 10, 10, 10)
        group_layout.setSpacing(10)

        # Layout для кнопок
        buttons_layout = QGridLayout()
        buttons_layout.setContentsMargins(0, 0, 0, 0)
        buttons_layout.setVerticalSpacing(10)
        buttons_layout.setHorizontalSpacing(10)

        # Список команд: (текст кнопки, функция, аргумент, текст подсказки)
        buttons = [
            ("🖥️ PowerShell", run_powershell, self.hostname, "Запустить PowerShell"),
            ("🛠️ Управление ПК", open_compmgmt, self.hostname, "Открыть управление ПК"),
            ("🌐 RDP", open_rdp, self.ip, "Подключиться по RDP"),
            ("👀 Shadow RDP", open_shadow_rdp, self.ip, "Подключиться через Shadow RDP"),
            ("📂 Открыть C$", open_c_drive, self.ip, "Открыть диск C$"),
            ("🖤 CMD", open_cmd, self.hostname, "Запустить командную строку"),
        ]

        # Создаём кнопки с использованием partial для захвата параметров
        for index, (title, command, arg, tooltip) in enumerate(buttons):
            btn = QPushButton(title, self)
            btn.setObjectName("commandButton")  # Стили из styles.py
            btn.setMinimumHeight(40)
            btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
            btn.setCursor(Qt.PointingHandCursor)
            btn.setToolTip(tooltip)
            btn.clicked.connect(partial(self.run_command, command, arg))
            buttons_layout.addWidget(btn, index // 3, index % 3)

        group_layout.addLayout(buttons_layout)
        # Вертикальный spacer, чтобы содержимое было прижато к верху
        group_layout.addItem(QSpacerItem(20, 20, QSizePolicy.Minimum, QSizePolicy.Expanding))

        # Основной layout для виджета
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(12, 12, 12, 12)
        main_layout.setSpacing(10)
        main_layout.addWidget(self.group_box)

        # Разделительная линия под group box
        self.separator = QFrame(self)
        self.separator.setObjectName("separator")
        self.separator.setFrameShape(QFrame.HLine)
        self.separator.setFrameShadow(QFrame.Sunken)
        main_layout.addWidget(self.separator)

        self.setLayout(main_layout)

    def run_command(self, command: Callable[[str], None], arg: str) -> None:
        """
        Запускает команду и показывает уведомление о статусе.

        :param command: Функция команды, принимающая строковый аргумент.
        :param arg: Аргумент для команды.
        """
        try:
            command(arg)
            Notification(
                "✅ Команда успешно отправлена!",
                "Команда была выполнена без ошибок.",
                "success",
                duration=3000,
                parent=self.window()
            ).show_notification()
        except Exception as e:
            Notification(
                "❌ Ошибка выполнения команды!",
                f"Не удалось выполнить команду: {str(e)}. Пожалуйста, проверьте аргументы.",
                "error",
                duration=3000,
                parent=self.window()
            ).show_notification()

