from PySide6.QtWidgets import QDialog, QVBoxLayout, QLabel, QLineEdit, QPushButton, QCheckBox, QMessageBox
from PySide6.QtCore import Qt
import paramiko
import logging

logger = logging.getLogger(__name__)

class AuthDialog(QDialog):
    """Диалоговое окно авторизации для подключения к Linux"""

    _password_cache = {}  # Кэш учетных данных (IP: (логин, пароль))

    def __init__(self, ip: str):
        super().__init__()
        self.ip = ip
        self.setWindowTitle(f"Авторизация ({ip})")
        self.setMinimumWidth(300)
        self.setWindowFlag(Qt.WindowCloseButtonHint, False)  # Запрет закрытия через крестик
        self._init_ui()

    def _init_ui(self):
        """Инициализация интерфейса"""
        layout = QVBoxLayout(self)

        # Поля ввода
        self.input_login = QLineEdit()
        self.input_password = QLineEdit()
        self.input_password.setEchoMode(QLineEdit.Password)

        # Кнопка показа пароля
        self.show_password = QCheckBox("Показать пароль")
        self.show_password.toggled.connect(
            lambda checked: self.input_password.setEchoMode(
                QLineEdit.Normal if checked else QLineEdit.Password
            )
        )

        # Кнопка подключения
        self.btn_ok = QPushButton("Подключиться")
        self.btn_ok.clicked.connect(self._on_accept)

        # Добавление элементов в layout
        layout.addWidget(QLabel("Логин:"))
        layout.addWidget(self.input_login)
        layout.addWidget(QLabel("Пароль:"))
        layout.addWidget(self.input_password)
        layout.addWidget(self.show_password)
        layout.addWidget(self.btn_ok)

        # Загрузка сохраненных данных
        self._load_cached_credentials()

    def _load_cached_credentials(self):
        """Загружает сохраненные учетные данные для текущего IP"""
        login, password = self._password_cache.get(self.ip, (None, None))
        if login:
            self.input_login.setText(login)
        if password:
            self.input_password.setText(password)

    def _on_accept(self):
        """Обработка попытки авторизации"""
        login = self.input_login.text().strip()
        password = self.input_password.text().strip()

        if not self._validate_input(login, password):
            return

        if self._test_ssh_connection(login, password):
            self._password_cache[self.ip] = (login, password)  # Сохраняем в кэш
            self.accept()
        else:
            QMessageBox.critical(self, "Ошибка", "Неверные учетные данные или недоступен SSH")

    def _validate_input(self, login: str, password: str) -> bool:
        """Проверка заполнения полей"""
        if not login or not password:
            QMessageBox.warning(self, "Ошибка", "Логин и пароль не могут быть пустыми!")
            return False
        return True

    def _test_ssh_connection(self, login: str, password: str) -> bool:
        """Проверка SSH-подключения"""
        try:
            with paramiko.SSHClient() as client:
                client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                client.connect(
                    hostname=self.ip,
                    username=login,
                    password=password,
                    timeout=5
                )
            return True
        except Exception as e:
            logger.error(f"SSH connection error: {str(e)}")
            return False

    @staticmethod
    def get_credentials(ip: str) -> tuple[str, str] | tuple[None, None]:
        """Возвращает (логин, пароль) или (None, None) при отмене"""
        dialog = AuthDialog(ip)
        if dialog.exec() == QDialog.Accepted:
            return dialog.input_login.text().strip(), dialog.input_password.text().strip()
        return None, None  # Явное возвращение None при отмене