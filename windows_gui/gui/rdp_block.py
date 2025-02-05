import logging
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QCheckBox, QLabel, QLineEdit,
    QPushButton, QListWidget, QGroupBox, QMessageBox, QListWidgetItem,
    QMenu, QProgressBar
)
from PySide6.QtCore import Qt, QTimer, QThreadPool, QRunnable, Signal, QObject
from PySide6.QtGui import QIntValidator
from windows_gui.rdp_management import RDPManagerSync  # Обновленный RDPManagerSync с pypsexec
from notifications import Notification  # Импортируем уведомления из отдельного файла
import subprocess

logger = logging.getLogger(__name__)


# =============================================================================
# Класс для блокировки сигналов у виджетов
# =============================================================================
class BlockSignals:
    """Контекстный менеджер для временной блокировки сигналов у виджетов."""
    def __init__(self, widgets):
        self.widgets = widgets

    def __enter__(self):
        for w in self.widgets:
            w.blockSignals(True)

    def __exit__(self, exc_type, exc_val, exc_tb):
        for w in self.widgets:
            w.blockSignals(False)


# =============================================================================
# Класс для выполнения фоновых операций RDP (без зависания UI)
# =============================================================================
class RDPWorker(QRunnable, QObject):
    """Потоковый класс для выполнения RDP-команд без зависания UI."""
    finished = Signal(dict)  # Передача результата в UI
    error = Signal(str)      # Передача сообщения об ошибке

    def __init__(self, func, **kwargs):
        super().__init__()
        QObject.__init__(self)  # Инициализируем QObject
        self.func = func
        self.kwargs = kwargs

    def run(self):
        """Запускает удалённую команду и отправляет результат в UI."""
        try:
            logger.debug(f"Запуск потока для: {self.func.__name__}")
            result = self.func(**self.kwargs)
            logger.debug(f"Поток завершён: {result}")
            self.finished.emit(result)
        except Exception as e:
            logger.error(f"Ошибка в потоке {self.func.__name__}: {e}")
            self.error.emit(str(e))


# =============================================================================
# Основной виджет управления RDP
# =============================================================================
class RDPBlock(QWidget):
    def __init__(self, hostname: str, parent: QWidget = None):
        super().__init__(parent)
        self.hostname = hostname
        self.manager = RDPManagerSync(hostname)
        self.threadpool = QThreadPool.globalInstance()

        # Флаги для автообновления
        self.auto_refresh = False
        self.refresh_scheduled = False

        logger.info(f"Инициализация RDPBlock для {hostname}")
        self._init_ui()
        self._init_connections()
        self._load_initial_data()

    def _init_ui(self):
        """Создает GUI-интерфейс для управления RDP."""
        group_box = QGroupBox("🖥️ Управление RDP")
        main_layout = QVBoxLayout()

        # Индикатор загрузки
        self.progress = QProgressBar()
        self.progress.setVisible(False)
        main_layout.addWidget(self.progress)

        # Чекбокс включения RDP
        self.checkbox_rdp = QCheckBox("✅ Включить RDP")
        main_layout.addWidget(self.checkbox_rdp)

        # Изменение порта
        port_layout = QHBoxLayout()
        port_layout.addWidget(QLabel("🔌 Порт:"))
        self.port_input = QLineEdit()
        self.port_input.setValidator(QIntValidator(1, 65535))
        port_layout.addWidget(self.port_input)
        self.change_port_btn = QPushButton("Изменить")
        port_layout.addWidget(self.change_port_btn)
        main_layout.addLayout(port_layout)

        # Список пользователей
        main_layout.addWidget(QLabel("👥 Пользователи RDP:"))
        self.users_list = QListWidget()
        self.users_list.setContextMenuPolicy(Qt.CustomContextMenu)
        main_layout.addWidget(self.users_list)

        # Добавление пользователя
        user_layout = QHBoxLayout()
        self.user_input = QLineEdit()
        user_layout.addWidget(self.user_input)
        self.add_user_btn = QPushButton("Добавить")
        user_layout.addWidget(self.add_user_btn)
        main_layout.addLayout(user_layout)

        # Кнопки обновления и применения настроек
        button_layout = QHBoxLayout()
        self.refresh_btn = QPushButton("Обновить")
        self.apply_btn = QPushButton("Применить")
        button_layout.addWidget(self.refresh_btn)
        button_layout.addWidget(self.apply_btn)
        main_layout.addLayout(button_layout)

        # Строка состояния
        self.status_label = QLabel()
        main_layout.addWidget(self.status_label)

        group_box.setLayout(main_layout)
        layout = QVBoxLayout(self)
        layout.addWidget(group_box)

    def _init_connections(self):
        """Привязывает элементы интерфейса к обработчикам событий."""
        self.checkbox_rdp.toggled.connect(self._toggle_rdp)
        self.change_port_btn.clicked.connect(self._change_port)
        self.add_user_btn.clicked.connect(self._add_user)
        self.refresh_btn.clicked.connect(self._load_initial_data)
        self.apply_btn.clicked.connect(self._apply_changes)
        self.users_list.customContextMenuRequested.connect(self._show_context_menu)

    def _load_initial_data(self):
        """Загружает данные RDP в фоновом режиме."""
        logger.info(f"Старт загрузки данных RDP для {self.hostname}")
        self._execute_operation(self.manager.refresh)

    def _execute_operation(self, func, **kwargs) -> RDPWorker:
        """
        Запускает операцию в фоне, обновляет UI и возвращает worker для дальнейшей цепочки.
        """
        logger.debug(f"Запуск операции {func.__name__}")
        self._show_loading(True)

        worker = RDPWorker(func, **kwargs)
        worker.finished.connect(self._update_ui)
        worker.error.connect(self._handle_error)
        worker.finished.connect(lambda _: self._show_loading(False))
        worker.error.connect(lambda _: self._show_loading(False))
        self.threadpool.start(worker)
        return worker

    def _show_notification(self, message: str, notif_type: str = "success", duration: int = 3000):
        """Упрощенный метод для отображения уведомления через модуль notifications."""
        notif = Notification(message, notif_type, duration, parent=self)
        notif.show_notification()

    def _auto_refresh(self):
        """Устанавливает флаг автообновления и запускает обновление."""
        self.auto_refresh = True
        self.refresh_scheduled = False
        self._execute_operation(self.manager.refresh)

    def _toggle_rdp(self, checked: bool):
        """
        Обрабатывает изменение статуса RDP.
        Запрашивает подтверждение действия и запускает обновление настроек.
        """
        reply = QMessageBox.question(
            self, "Подтверждение", "Изменить статус RDP?",
            QMessageBox.Yes | QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            worker = self._execute_operation(
                self.manager.update_settings,
                enabled=checked
            )
            if not self.refresh_scheduled:
                self.refresh_scheduled = True
                worker.finished.connect(lambda _: QTimer.singleShot(1000, self._auto_refresh))
            self._show_notification("Статус RDP изменён", "success")
        else:
            with BlockSignals([self.checkbox_rdp]):
                self.checkbox_rdp.setChecked(not checked)
            self._show_notification("Операция отменена", "warning")

    def _change_port(self):
        """Изменяет порт RDP после проверки корректности ввода."""
        port = self.port_input.text()
        if port.isdigit() and 1 <= int(port) <= 65535:
            self._execute_operation(self.manager.update_settings, port=int(port))
            self._show_notification("Порт изменён", "success")
        else:
            self._show_notification("Некорректный порт", "error")

    def _validate_user(self, user: str) -> bool:
        """
        Проверяет существование доменного пользователя с помощью `net user "<user>" /domain`.
        Если в stderr содержится "Не найдено имя пользователя", считаем, что пользователь не существует.
        """
        command = f'net user "{user}" /domain'
        result = subprocess.run(command, capture_output=True, text=True, shell=True, encoding='cp866')

        logger.debug(f"_validate_user: Команда = {command}")
        logger.debug(f"_validate_user: stdout = {repr(result.stdout)}")
        logger.debug(f"_validate_user: stderr = {repr(result.stderr)}")

        # Если stderr содержит "Не найдено имя пользователя", значит юзер НЕ существует
        if "Не найдено имя пользователя" in result.stderr or "NET HELPMSG 2221" in result.stderr:
            logger.warning(f"❌ Пользователь {user} НЕ найден в домене!")
            return False

        logger.info(f"✅ Пользователь {user} найден в домене.")
        return True

    def _add_user(self):
        """Добавляет пользователя в группу RDP без удаления существующих пользователей."""
        user = self.user_input.text().strip()
        if not user:
            self._show_notification("Введите имя пользователя", "error")
            return

        # Проверяем, существует ли пользователь в домене
        if not self._validate_user(user):
            self._show_notification("❌ Пользователь не найден в домене!", "error")
            return

        # Получаем текущих пользователей
        current_users = [self.users_list.item(i).text().lower().replace("ncc\\", "") for i in
                         range(self.users_list.count())]

        if user.lower() in current_users:
            self._show_notification("⚠️ Пользователь уже добавлен!", "warning")
            return

        # Добавляем пользователя БЕЗ ПЕРЕЗАПИСИ ВСЕГО СПИСКА!
        self._execute_operation(self.manager.add_user, username=user)

        self.user_input.clear()
        self._show_notification(f"✅ Пользователь {user} добавлен!", "success")

        # Запрашиваем обновление списка пользователей после добавления
        QTimer.singleShot(1000, self._load_initial_data)

    def _apply_changes(self):
        """
        Применяет изменения настроек RDP (чекбокс, порт и список пользователей)
        и обновляет UI после завершения операции.
        """
        current_users = [self.users_list.item(i).text() for i in range(self.users_list.count())]
        port = self.port_input.text()

        def on_update_complete(_):
            if not self.refresh_scheduled:
                self.refresh_scheduled = True
                QTimer.singleShot(1000, self._auto_refresh)
            self._show_notification("Настройки успешно применены", "success")

        self._execute_operation(
            self.manager.update_settings,
            enabled=self.checkbox_rdp.isChecked(),
            port=int(port) if port else None,
            users=current_users
        ).finished.connect(on_update_complete)

    def _show_context_menu(self, pos):
        """Показывает контекстное меню для удаления выбранного пользователя."""
        menu = QMenu()
        delete_action = menu.addAction("Удалить")
        delete_action.triggered.connect(self._delete_selected_user)
        menu.exec_(self.users_list.mapToGlobal(pos))

    def _delete_selected_user(self):
        """Удаляет выбранного пользователя и обновляет UI после завершения операции."""
        item = self.users_list.currentItem()
        if not item:
            self._show_notification("Пользователь не выбран", "error")
            return

        current_users = [self.users_list.item(i).text() for i in range(self.users_list.count())]
        current_users.remove(item.text())
        logger.debug(f"Удаляем пользователя {item.text()} из RDP")

        def on_update_complete(_):
            if not self.refresh_scheduled:
                self.refresh_scheduled = True
                QTimer.singleShot(100, self._auto_refresh)
            self._show_notification("Пользователь удалён", "success")

        worker = self._execute_operation(self.manager.update_settings, users=current_users)
        worker.finished.connect(on_update_complete)

    def _update_ui(self, data: dict):
        """Обновляет элементы интерфейса на основе полученных данных."""
        logger.debug(f"Обновление UI с данными: {data}")
        self._show_loading(False)

        with BlockSignals([self.checkbox_rdp, self.port_input, self.users_list]):
            self.checkbox_rdp.setChecked(data.get('enabled', False))
            self.port_input.setText(str(data.get('port', 3389)))
            self.users_list.clear()
            for user in data.get('users', []):
                item = QListWidgetItem(user)
                item.setFlags(item.flags() | Qt.ItemIsEditable)
                self.users_list.addItem(item)

        self.status_label.setText("✅ Данные обновлены")
        if not self.auto_refresh:
            self._show_notification("Данные обновлены", "success")
        self.auto_refresh = False
        self.refresh_scheduled = False

    def _show_loading(self, visible: bool):
        """Отображает или скрывает индикатор загрузки и блокирует элементы управления."""
        self.progress.setVisible(visible)
        self.progress.setRange(0, 0 if visible else 1)
        for widget in [self.checkbox_rdp, self.change_port_btn, self.add_user_btn, self.refresh_btn, self.apply_btn]:
            widget.setEnabled(not visible)

    def _handle_error(self, message: str):
        """Обрабатывает ошибки, снимает блокировку с интерфейса и выводит уведомление."""
        logger.error(f"Ошибка: {message}")
        self._show_loading(False)
        self._show_notification(message, "error")
        self.status_label.setText(f"❌ Ошибка: {message}")
