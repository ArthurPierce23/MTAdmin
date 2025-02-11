import time
import logging
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QLabel, QLineEdit, QDialogButtonBox, QMessageBox,
    QFormLayout, QCheckBox
)
from PySide6.QtCore import Qt, QSettings
from linux_gui.session_manager import SessionManager

logger = logging.getLogger(__name__)

# Время жизни кэша в секундах (15 минут)
CACHE_EXPIRATION: int = 15 * 60  # 900 секунд


class AuthDialog(QDialog):
    """
    Окно аутентификации для удалённого Linux-хоста.
    Запрашивает логин и пароль, а также root-доступ (по желанию).
    Реализовано кэширование данных на 15 минут.
    """

    def __init__(self, hostname: str, ip: str, parent=None) -> None:
        super().__init__(parent)
        self.setObjectName("authDialog")
        self.hostname: str = hostname
        self.ip: str = ip
        self.setWindowTitle("Аутентификация для Linux")
        self.setModal(True)
        self.session_manager: SessionManager | None = None

        # Настройка QSettings: ключи будут сохраняться в системном реестре или INI-файле.
        # Имя организации и приложения можно задавать глобально (например, в главном модуле).
        self.settings: QSettings = QSettings("MyCompany", "MTAdmin")

        self.setup_ui()
        self.load_cached_credentials()

    def setup_ui(self) -> None:
        """Создает и настраивает визуальные компоненты окна аутентификации."""
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(10)
        main_layout.setContentsMargins(12, 12, 12, 12)

        # Информационная метка с эмодзи
        info_label = QLabel(f"🔑 Подключение к <b>{self.hostname}</b>")
        info_label.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(info_label)

        # Форма для ввода логина и пароля
        form_layout = QFormLayout()
        form_layout.setSpacing(8)

        self.login_edit = QLineEdit()
        self.login_edit.setPlaceholderText("Введите логин")
        form_layout.addRow("👤 Логин:", self.login_edit)

        self.password_edit = QLineEdit()
        self.password_edit.setPlaceholderText("Введите пароль")
        self.password_edit.setEchoMode(QLineEdit.Password)
        form_layout.addRow("🔒 Пароль:", self.password_edit)

        # Чекбокс для использования root-доступа
        self.root_checkbox = QCheckBox("Использовать root-доступ")
        self.root_checkbox.stateChanged.connect(self.toggle_root_fields)
        form_layout.addRow(self.root_checkbox)

        # Поля для ввода root-логина и root-пароля (по умолчанию отключены)
        self.root_login_edit = QLineEdit()
        self.root_login_edit.setPlaceholderText("Введите root-логин")
        self.root_login_edit.setEnabled(False)
        form_layout.addRow("👑 Root-логин:", self.root_login_edit)

        self.root_password_edit = QLineEdit()
        self.root_password_edit.setPlaceholderText("Введите root-пароль")
        self.root_password_edit.setEchoMode(QLineEdit.Password)
        self.root_password_edit.setEnabled(False)
        form_layout.addRow("🛡️ Root-пароль:", self.root_password_edit)

        main_layout.addLayout(form_layout)

        # Чекбокс "Запомнить пароль"
        self.remember_checkbox = QCheckBox("💾 Запомнить пароль на 15 минут")
        main_layout.addWidget(self.remember_checkbox)

        # Кнопки "Войти" и "Отмена"
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.button(QDialogButtonBox.Ok).setText("Войти")
        button_box.button(QDialogButtonBox.Cancel).setText("Отмена")
        button_box.accepted.connect(self.authenticate)
        button_box.rejected.connect(self.reject)
        main_layout.addWidget(button_box)

    def toggle_root_fields(self) -> None:
        """Включает или отключает поля для ввода root-данных в зависимости от состояния чекбокса."""
        enabled: bool = self.root_checkbox.isChecked()
        self.root_login_edit.setEnabled(enabled)
        self.root_password_edit.setEnabled(enabled)

    def load_cached_credentials(self) -> None:
        """
        Загружает сохранённые учётные данные, если они актуальны (меньше CACHE_EXPIRATION секунд).
        Если данные устарели, производится очистка кэша.
        """
        cached_time: float = self.settings.value("auth/timestamp", 0, type=float)
        now: float = time.time()
        if now - cached_time < CACHE_EXPIRATION:
            # Если кэш актуален, подставляем сохранённые данные
            self.login_edit.setText(self.settings.value("auth/username", ""))
            self.password_edit.setText(self.settings.value("auth/password", ""))
            root_username: str = self.settings.value("auth/root_username", "")
            root_password: str = self.settings.value("auth/root_password", "")
            if root_username or root_password:
                self.root_checkbox.setChecked(True)
                self.root_login_edit.setText(root_username)
                self.root_password_edit.setText(root_password)
        else:
            # Если данные устарели – очищаем кэш
            self.settings.remove("auth")

    def save_cached_credentials(self) -> None:
        """
        Сохраняет учётные данные в QSettings с текущей временной меткой.
        """
        self.settings.setValue("auth/username", self.login_edit.text().strip())
        self.settings.setValue("auth/password", self.password_edit.text().strip())
        if self.root_checkbox.isChecked():
            self.settings.setValue("auth/root_username", self.root_login_edit.text().strip())
            self.settings.setValue("auth/root_password", self.root_password_edit.text().strip())
        else:
            self.settings.remove("auth/root_username")
            self.settings.remove("auth/root_password")
        self.settings.setValue("auth/timestamp", time.time())

    def clear_cached_credentials(self) -> None:
        """Очищает сохранённые учётные данные."""
        self.settings.remove("auth")

    def authenticate(self) -> None:
        """
        Пытается установить SSH-сессию через SessionManager.
        Если аутентификация проходит успешно, данные кэшируются (если выбрано сохранение) и окно закрывается.
        В случае ошибки выводится соответствующее сообщение.
        """
        username: str = self.login_edit.text().strip()
        password: str = self.password_edit.text().strip()
        use_root: bool = self.root_checkbox.isChecked()
        root_username: str | None = self.root_login_edit.text().strip() if use_root else None
        root_password: str | None = self.root_password_edit.text().strip() if use_root else None

        if not username or not password:
            QMessageBox.warning(self, "Ошибка", "Введите логин и пароль.")
            return

        try:
            self.session_manager = SessionManager.get_instance(
                self.hostname, username, password, root_username, root_password
            )
            self.session_manager.connect()
            # Сохраняем данные в кэш, если выбрано
            if self.remember_checkbox.isChecked():
                self.save_cached_credentials()
            else:
                self.clear_cached_credentials()
            self.accept()  # Аутентификация успешна – закрываем диалог
        except Exception as e:
            logger.error(f"Ошибка аутентификации: {e}")
            QMessageBox.critical(self, "Ошибка", f"Не удалось подключиться:\n{e}")

    def get_credentials(self) -> tuple[str, str]:
        """
        Возвращает кортеж (username, password) в зависимости от выбранного способа аутентификации.
        Если используется root-доступ, возвращаются root-учётные данные.
        """
        if self.root_checkbox.isChecked():
            return self.root_login_edit.text().strip(), self.root_password_edit.text().strip()
        return self.login_edit.text().strip(), self.password_edit.text().strip()

    def get_session_manager(self) -> SessionManager | None:
        """Возвращает установленную SSH-сессию."""
        return self.session_manager
