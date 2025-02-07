from PySide6.QtWidgets import QWidget, QGridLayout, QPushButton, QGroupBox, QVBoxLayout, QSpacerItem, QSizePolicy, QFrame
from windows_gui.commands import run_powershell, open_compmgmt, open_rdp, open_shadow_rdp, open_c_drive, open_cmd
from notifications import Notification


class CommandsBlock(QWidget):
    """
    Виджет для запуска удалённых команд.
    """

    def __init__(self, hostname: str, ip: str, parent: QWidget = None):
        super().__init__(parent)
        self.hostname = hostname
        self.ip = ip
        self.init_ui()

    def init_ui(self):
        """Создаёт интерфейс с кнопками команд, оформленный через group_box."""
        self.group_box = QGroupBox("💻 Команды управления")
        self.group_box.setObjectName("groupBox")  # 🎯 Применяем стили из styles.py
        group_layout = QVBoxLayout()
        group_layout.setContentsMargins(10, 10, 10, 10)
        group_layout.setSpacing(10)

        buttons_layout = QGridLayout()
        buttons_layout.setContentsMargins(0, 0, 0, 0)
        buttons_layout.setVerticalSpacing(10)
        buttons_layout.setHorizontalSpacing(10)

        buttons = [
            ("🖥️ PowerShell", run_powershell, self.hostname),
            ("🛠️ Управление ПК", open_compmgmt, self.hostname),
            ("🌐 RDP", open_rdp, self.ip),
            ("👀 Shadow RDP", open_shadow_rdp, self.ip),
            ("📂 Открыть C$", open_c_drive, self.ip),
            ("🖤 CMD", open_cmd, self.hostname),
        ]

        for index, (title, command, arg) in enumerate(buttons):
            btn = QPushButton(title)
            btn.setObjectName("commandButton")  # 🎯 Стили кнопки из styles.py
            btn.setMinimumHeight(40)
            btn.clicked.connect(lambda _, cmd=command, a=arg: self.run_command(cmd, a))
            buttons_layout.addWidget(btn, index // 3, index % 3)

        group_layout.addLayout(buttons_layout)

        self.separator = QFrame()
        self.separator.setObjectName("separator")  # 🎯 Стили разделителя
        self.separator.setFrameShape(QFrame.HLine)
        self.separator.setFrameShadow(QFrame.Sunken)

        self.group_box.setLayout(group_layout)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(10)
        layout.addWidget(self.group_box)
        group_layout.addWidget(self.separator)

        self.setLayout(layout)

    def run_command(self, command, arg):
        """Запускает команду и показывает статус через Notification."""
        try:
            command(arg)
            Notification("Команда успешно отправлена.", "success").show_notification()
        except Exception as e:
            Notification(f"Ошибка выполнения: {str(e)}", "error").show_notification()
