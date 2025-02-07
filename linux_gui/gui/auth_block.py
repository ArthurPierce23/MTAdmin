from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QLabel, QLineEdit, QPushButton, QMessageBox
)
import logging

from linux_gui.session_manager import SessionManager

logger = logging.getLogger(__name__)

class AuthDialog(QDialog):
    """
    Окно аутентификации для удалённого Linux-хоста.
    Запрашивает логин и пароль, пытается установить SSH-сессию через SessionManager.
    """
    def __init__(self, hostname: str, ip: str, parent=None):
        super().__init__(parent)
        self.hostname = hostname
        self.ip = ip
        self.setWindowTitle("Аутентификация для Linux")
        self.setModal(True)
        self.session_manager = None
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)

        layout.addWidget(QLabel(f"Подключение к {self.hostname} ({self.ip})"))

        # Поле ввода логина
        layout.addWidget(QLabel("Логин:"))
        self.login_edit = QLineEdit()
        layout.addWidget(self.login_edit)

        # Поле ввода пароля
        layout.addWidget(QLabel("Пароль:"))
        self.password_edit = QLineEdit()
        self.password_edit.setEchoMode(QLineEdit.Password)
        layout.addWidget(self.password_edit)

        # Кнопка подтверждения
        self.auth_button = QPushButton("Войти")
        self.auth_button.clicked.connect(self.authenticate)
        layout.addWidget(self.auth_button)

    def authenticate(self):
        username = self.login_edit.text().strip()
        password = self.password_edit.text().strip()

        if not username or not password:
            QMessageBox.warning(self, "Ошибка", "Введите логин и пароль.")
            return

        try:
            # Пытаемся установить SSH-сессию через SessionManager
            self.session_manager = SessionManager.get_instance(self.hostname, username, password)
            self.session_manager.connect()  # Если не удаётся установить соединение – исключение
            self.accept()  # Если соединение успешно, закрываем диалог с Accepted
        except Exception as e:
            logger.error(f"Ошибка аутентификации: {e}")
            QMessageBox.critical(self, "Ошибка", f"Не удалось установить SSH-соединение:\n{e}")

    def get_session_manager(self):
        """Возвращает установленную SSH-сессию."""
        return self.session_manager  # ✅ Теперь этот метод есть!
