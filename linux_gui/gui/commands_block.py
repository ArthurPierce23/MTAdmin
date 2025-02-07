from PySide6.QtWidgets import QGroupBox, QVBoxLayout, QLabel, QPushButton, QInputDialog, QFrame
from PySide6.QtCore import Qt
import logging

from linux_gui.commands import start_ssh_session, start_vnc_session
from notifications import Notification

logger = logging.getLogger(__name__)


class CommandsBlock(QGroupBox):
    """
    Блок для выполнения команд (SSH, VNC).
    Интерфейс улучшен: уведомления и статус отображаются с подробной информацией,
    добавлены эмодзи, а также визуальные разделители для более современного вида.
    """
    def __init__(self, unused_hostname, ip, parent=None):
        # Заголовок блока дополнен эмодзи и информацией об IP-адресе
        super().__init__(f"💻 Управление хостом: {ip}", parent)
        self.ip = ip
        self.init_ui()

    def init_ui(self):
        self.setAlignment(Qt.AlignCenter)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        # Информационная метка с указанием назначния блока
        self.info_label = QLabel(f"Выберите действие для хоста {self.ip}:")
        self.info_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.info_label)

        # Кнопка для SSH с эмодзи в заголовке и подробным tooltip
        self.ssh_button = QPushButton("🔐 SSH-подключение")
        self.ssh_button.setToolTip("🚀 Запустить SSH-сессию.\nНажмите, чтобы ввести логин для подключения.")
        self.ssh_button.clicked.connect(self.connect_ssh)
        layout.addWidget(self.ssh_button)

        # Кнопка для VNC с эмодзи в заголовке и подробным tooltip
        self.vnc_button = QPushButton("🖥️ VNC-подключение")
        self.vnc_button.setToolTip("🌐 Запустить VNC-клиент для удалённого управления.\nНажмите для подключения к рабочему столу.")
        self.vnc_button.clicked.connect(self.connect_vnc)
        layout.addWidget(self.vnc_button)

        # Разделитель для визуального разделения
        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        separator.setFrameShadow(QFrame.Sunken)
        layout.addWidget(separator)

        # Метка для отображения текущего статуса действий
        self.status_label = QLabel("ℹ️ Ожидание выбора действия...")
        self.status_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.status_label)

        self.setLayout(layout)

    def connect_ssh(self):
        """
        Запрашивает логин для SSH-подключения и запускает сессию.
        Отображает подробные уведомления и обновляет статус в интерфейсе.
        """
        username, ok = QInputDialog.getText(self, "🔐 SSH Подключение", "Введите имя пользователя для SSH:", text="root")
        # Если пользователь нажал "Отмена" – просто обновляем статус и выходим.
        if not ok:
            self.status_label.setText("ℹ️ SSH-подключение отменено пользователем.")
            return

        # Если поле ввода пустое – выдаём предупреждение и обновляем статус
        if not username.strip():
            Notification(
                "Внимание",
                "⚠️ Имя пользователя для SSH не может быть пустым.\nПожалуйста, введите корректное имя.",
                "warning"
            ).show_notification()
            self.status_label.setText("⚠️ Ожидание корректного ввода логина для SSH.")
            return

        self.status_label.setText("⏳ Идёт попытка подключения по SSH...")
        try:
            if start_ssh_session(self.ip, username):
                Notification(
                    "SSH Успех",
                    f"✅ SSH-сессия для {username}@{self.ip} успешно запущена.\nПодключение устанавливается...",
                    "success"
                ).show_notification()
                self.status_label.setText("✅ SSH-сессия запущена.")
            else:
                Notification(
                    "Ошибка SSH",
                    "❌ Не удалось запустить SSH-сессию.\nПроверьте настройки сети и данные подключения.",
                    "error"
                ).show_notification()
                self.status_label.setText("❌ Ошибка запуска SSH-сессии.")
        except Exception as e:
            logger.error(f"Ошибка запуска SSH: {e}")
            Notification(
                "Ошибка SSH",
                f"❌ Произошла ошибка при запуске SSH:\n{e}\nПроверьте корректность введённых данных и настройки хоста.",
                "error"
            ).show_notification()
            self.status_label.setText("❌ Ошибка при запуске SSH.")

    def connect_vnc(self):
        """
        Запускает VNC-подключение и отображает подробные уведомления о результате.
        """
        self.status_label.setText("⏳ Идёт попытка подключения по VNC...")
        try:
            if start_vnc_session(self.ip):
                Notification(
                    "VNC Успех",
                    "🖥️ VNC-клиент успешно запущен.\nПодключение к удалённому рабочему столу устанавливается...",
                    "success"
                ).show_notification()
                self.status_label.setText("✅ VNC-подключение установлено.")
            else:
                Notification(
                    "Ошибка VNC",
                    "❌ Не удалось запустить VNC-клиент.\nПроверьте настройки подключения и доступность хоста.",
                    "error"
                ).show_notification()
                self.status_label.setText("❌ Ошибка запуска VNC.")
        except Exception as e:
            logger.error(f"Ошибка запуска VNC: {e}")
            Notification(
                "Ошибка VNC",
                f"❌ Ошибка при запуске VNC:\n{e}\nУбедитесь, что все необходимые компоненты установлены.",
                "error"
            ).show_notification()
            self.status_label.setText("❌ Ошибка при запуске VNC.")
