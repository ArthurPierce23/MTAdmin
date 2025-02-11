from PySide6.QtWidgets import QGroupBox, QVBoxLayout, QLabel, QPushButton, QInputDialog, QFrame
from PySide6.QtCore import Qt
import logging

from linux_gui.commands import start_ssh_session, start_vnc_session
from notifications import Notification

logger = logging.getLogger(__name__)


class CommandsBlock(QGroupBox):
    """
    Блок для выполнения команд (SSH, VNC).

    Интерфейс улучшен: уведомления отображаются с подробной информацией,
    добавлены эмодзи, а также визуальные разделители для более современного вида.
    Заголовок бокса теперь: "Управление хостом".
    """

    def __init__(self, unused_hostname: str, ip: str, parent=None) -> None:
        """
        Инициализирует блок управления для заданного IP-адреса.

        :param unused_hostname: Неиспользуемый параметр (оставлен для совместимости с фабричным вызовом).
        :param ip: IP-адрес хоста.
        :param parent: Родительский виджет (если имеется).
        """
        # Заголовок теперь фиксированный – "Управление хостом"
        super().__init__("Управление хостом", parent)
        self.ip: str = ip
        self.init_ui()

    def init_ui(self) -> None:
        """Настраивает визуальные компоненты блока команд."""
        self.setAlignment(Qt.AlignCenter)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        # Информационная метка с указанием IP-адреса хоста
        self.info_label = QLabel(f"Выберите действие для хоста:")
        self.info_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.info_label)

        # Кнопка для SSH-подключения
        self.ssh_button = QPushButton("🔐 SSH-подключение")
        self.ssh_button.setToolTip(
            "🚀 Запустить SSH-сессию.\nНажмите, чтобы ввести логин для подключения."
        )
        self.ssh_button.clicked.connect(self.connect_ssh)
        layout.addWidget(self.ssh_button)

        # Кнопка для VNC-подключения
        self.vnc_button = QPushButton("🖥️ VNC-подключение")
        self.vnc_button.setToolTip(
            "🌐 Запустить VNC-клиент для удалённого управления.\nНажмите для подключения к рабочему столу."
        )
        self.vnc_button.clicked.connect(self.connect_vnc)
        layout.addWidget(self.vnc_button)

        # Разделитель для визуального разделения элементов
        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        separator.setFrameShadow(QFrame.Sunken)
        layout.addWidget(separator)

        # Удалена статусная метка (нижняя часть бокса)

        self.setLayout(layout)

    def notify(self, title: str, message: str, notif_type: str) -> None:
        """
        Отображает уведомление через всплывающее окно.

        :param title: Заголовок уведомления.
        :param message: Текст уведомления.
        :param notif_type: Тип уведомления (например, "success", "error", "warning").
        """
        Notification(title, message, notif_type, parent=self.window()).show_notification()

    def connect_ssh(self) -> None:
        """
        Запрашивает логин для SSH-подключения, запускает сессию и отображает уведомления.
        """
        username, ok = QInputDialog.getText(
            self,
            "🔐 SSH Подключение",
            "Введите имя пользователя для SSH:",
            text="root"
        )
        if not ok:
            self.notify(
                "🔕 Подключение отменено",
                "Вы не ввели логин. Подключение по SSH отменено.",
                "warning"
            )
            return

        username = username.strip()
        if not username:
            self.notify(
                "⚠ Некорректный логин",
                "Поле логина не может быть пустым. Введите корректное имя пользователя.",
                "error"
            )
            return

        try:
            if start_ssh_session(self.ip, username):
                self.notify(
                    "🔐 SSH подключение установлено",
                    f"Вы успешно вошли под пользователем `{username}` на `{self.ip}`.",
                    "success"
                )
            else:
                self.notify(
                    "🚫 Ошибка SSH",
                    "Не удалось установить SSH-подключение.\nПроверьте сеть и учетные данные.",
                    "error"
                )
        except Exception as e:
            logger.exception("Ошибка SSH: %s", e)
            self.notify(
                "❗ Ошибка SSH",
                f"Произошла непредвиденная ошибка при подключении:\n`{e}`",
                "error"
            )
    def connect_vnc(self) -> None:
        """
        Запускает VNC-подключение и отображает соответствующие уведомления.
        """
        try:
            if start_vnc_session(self.ip):
                self.notify(
                    "🖥 Удалённый рабочий стол",
                    f"Вы успешно подключились к `{self.ip}` через VNC.",
                    "success"
                )
            else:
                self.notify(
                    "🚫 Ошибка VNC",
                    "Не удалось установить соединение.\nПроверьте настройки сервера VNC.",
                    "error"
                )
        except Exception as e:
            logger.exception("Ошибка VNC: %s", e)
            self.notify(
                "❗ Ошибка VNC",
                f"Произошла непредвиденная ошибка при подключении:\n`{e}`",
                "error"
            )