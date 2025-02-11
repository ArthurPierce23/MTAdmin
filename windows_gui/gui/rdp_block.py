import logging
import subprocess
from typing import Any, Callable, Dict, List

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QCheckBox, QLabel, QLineEdit,
    QPushButton, QListWidget, QGroupBox, QMessageBox, QListWidgetItem,
    QMenu, QProgressBar, QFrame, QSizePolicy, QSpacerItem
)
from PySide6.QtCore import Qt, QTimer, QThreadPool, QRunnable, Signal, QObject
from PySide6.QtGui import QIntValidator, QFont

from windows_gui.rdp_management import RDPManagerSync  # Обновленный RDPManagerSync с pypsexec
from notifications import Notification

logger = logging.getLogger(__name__)


class BlockSignals:
    """
    Контекстный менеджер для временной блокировки сигналов у виджетов.
    При входе блокирует сигналы, а при выходе – восстанавливает их исходное состояние.
    """

    def __init__(self, widgets: List[QObject]) -> None:
        self.widgets = widgets

    def __enter__(self) -> None:
        for w in self.widgets:
            w.blockSignals(True)

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        for w in self.widgets:
            w.blockSignals(False)


class RDPWorker(QRunnable, QObject):
    """
    Потоковый класс для выполнения RDP-команд без зависания UI.

    Вызывает переданную функцию с заданными параметрами, а по завершении отправляет результат или сообщение об ошибке через сигналы.
    """
    finished = Signal(dict)  # Сигнал, передающий результат (словарь)
    error = Signal(str)  # Сигнал, передающий сообщение об ошибке

    def __init__(self, func: Callable[..., Dict[str, Any]], **kwargs: Any) -> None:
        QRunnable.__init__(self)
        QObject.__init__(self)
        self.func = func
        self.kwargs = kwargs

    def run(self) -> None:
        """
        Запускает выполнение переданной функции и посылает результат через сигнал finished.
        В случае исключения отправляет текст ошибки через сигнал error.
        """
        try:
            logger.debug(f"Запуск потока для функции: {self.func.__name__} с параметрами: {self.kwargs}")
            result = self.func(**self.kwargs)
            logger.debug(f"Поток для {self.func.__name__} завершён. Результат: {result}")
            self.finished.emit(result)
        except Exception as e:
            logger.error(f"Ошибка в потоке {self.func.__name__}: {e}")
            self.error.emit(str(e))


class RDPBlock(QWidget):
    """
    Виджет для управления RDP на удалённом ПК.

    Позволяет включать/выключать RDP, менять порт, редактировать список пользователей и получать обновлённые настройки.
    """

    def __init__(self, hostname: str, parent: QWidget = None) -> None:
        """
        Инициализирует виджет управления RDP.

        :param hostname: Имя хоста (или IP), к которому осуществляется доступ.
        :param parent: Родительский виджет.
        """
        super().__init__(parent)
        self.hostname: str = hostname
        self.manager = RDPManagerSync(hostname)
        self.threadpool = QThreadPool.globalInstance()

        # Флаги для автообновления
        self.auto_refresh: bool = False
        self.refresh_scheduled: bool = False

        logger.info(f"Инициализация RDPBlock для {hostname}")
        self._init_ui()
        self._init_connections()
        self._load_initial_data()

    def _init_ui(self) -> None:
        """Создаёт интерфейс управления RDP."""
        self.group_box = QGroupBox("🖥️ Управление RDP", self)
        self.group_box.setObjectName("groupBox")  # Стилизация из styles.py

        main_layout = QVBoxLayout(self.group_box)
        main_layout.setContentsMargins(12, 12, 12, 12)
        main_layout.setSpacing(10)

        # Индикатор загрузки
        self.progress = QProgressBar(self)
        self.progress.setVisible(False)
        self.progress.setTextVisible(False)
        self.progress.setFixedHeight(20)
        main_layout.addWidget(self.progress)

        # Чекбокс "Включить RDP"
        self.checkbox_rdp = QCheckBox("✅ Включить RDP", self)
        self.checkbox_rdp.setToolTip("Включить/отключить удаленный RDP")
        self.checkbox_rdp.setCursor(Qt.PointingHandCursor)
        main_layout.addWidget(self.checkbox_rdp)

        # Блок ввода порта
        port_layout = QHBoxLayout()
        port_layout.setSpacing(5)
        port_label = QLabel("🔌 Порт:", self)
        port_layout.addWidget(port_label)
        self.port_input = QLineEdit(self)
        self.port_input.setValidator(QIntValidator(1, 65535, self))
        self.port_input.setFixedWidth(80)
        self.port_input.setPlaceholderText("Порт")
        port_layout.addWidget(self.port_input)
        self.change_port_btn = QPushButton("Изменить", self)
        self.change_port_btn.setCursor(Qt.PointingHandCursor)
        self.change_port_btn.setToolTip("Изменить порт RDP")
        port_layout.addWidget(self.change_port_btn)
        port_layout.addStretch()  # Spacer для разделения элементов
        main_layout.addLayout(port_layout)

        # Список пользователей
        users_label = QLabel("👥 Пользователи RDP:", self)
        main_layout.addWidget(users_label)
        self.users_list = QListWidget(self)
        self.users_list.setContextMenuPolicy(Qt.CustomContextMenu)
        self.users_list.setMinimumHeight(100)
        main_layout.addWidget(self.users_list)

        # Блок добавления пользователя
        user_layout = QHBoxLayout()
        user_layout.setSpacing(5)
        self.user_input = QLineEdit(self)
        self.user_input.setPlaceholderText("Имя пользователя")
        user_layout.addWidget(self.user_input)
        self.add_user_btn = QPushButton("Добавить", self)
        self.add_user_btn.setCursor(Qt.PointingHandCursor)
        self.add_user_btn.setToolTip("Добавить пользователя в RDP")
        user_layout.addWidget(self.add_user_btn)
        main_layout.addLayout(user_layout)

        # Блок кнопок "Обновить" и "Применить"
        button_layout = QHBoxLayout()
        button_layout.setSpacing(10)
        self.refresh_btn = QPushButton("Обновить", self)
        self.refresh_btn.setCursor(Qt.PointingHandCursor)
        self.refresh_btn.setToolTip("Обновить данные RDP")
        self.apply_btn = QPushButton("Применить", self)
        self.apply_btn.setCursor(Qt.PointingHandCursor)
        self.apply_btn.setToolTip("Применить изменения настроек RDP")
        button_layout.addStretch()
        button_layout.addWidget(self.refresh_btn)
        button_layout.addWidget(self.apply_btn)
        button_layout.addStretch()
        main_layout.addLayout(button_layout)

        # Строка состояния
        self.status_label = QLabel("", self)
        self.status_label.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(self.status_label)

        self.group_box.setLayout(main_layout)

        # Основной Layout виджета
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(10)
        layout.addWidget(self.group_box)

        # Разделитель под GroupBox
        self.separator = QFrame(self)
        self.separator.setObjectName("separator")  # Стилизация из styles.py
        self.separator.setFrameShape(QFrame.HLine)
        self.separator.setFrameShadow(QFrame.Sunken)
        layout.addWidget(self.separator)

        self.setLayout(layout)

    def _init_connections(self) -> None:
        """Привязывает элементы интерфейса к обработчикам событий."""
        self.checkbox_rdp.toggled.connect(self._toggle_rdp)
        self.change_port_btn.clicked.connect(self._change_port)
        self.add_user_btn.clicked.connect(self._add_user)
        self.refresh_btn.clicked.connect(self._load_initial_data)
        self.apply_btn.clicked.connect(self._apply_changes)
        self.users_list.customContextMenuRequested.connect(self._show_context_menu)

    def _load_initial_data(self) -> None:
        """Загружает данные RDP в фоновом режиме."""
        logger.info(f"Старт загрузки данных RDP для {self.hostname}")
        self._execute_operation(self.manager.refresh)

    def _execute_operation(self, func: Callable[..., Dict[str, Any]], **kwargs: Any) -> RDPWorker:
        """
        Запускает операцию в фоне, отображает индикатор загрузки и возвращает worker для дальнейшей обработки.

        :param func: Функция, которую необходимо выполнить в фоне.
        :param kwargs: Аргументы для функции.
        :return: Объект worker.
        """
        logger.debug(f"Запуск операции {func.__name__} с параметрами: {kwargs}")
        self._show_loading(True)

        worker = RDPWorker(func, **kwargs)
        worker.finished.connect(self._update_ui)
        worker.error.connect(self._handle_error)
        # Скрываем индикатор загрузки после завершения операции
        worker.finished.connect(lambda _: self._show_loading(False))
        worker.error.connect(lambda _: self._show_loading(False))
        self.threadpool.start(worker)
        return worker

    def _show_notification(self, message: str, notif_type: str = "success", duration: int = 3000,
                           manual: bool = True) -> None:
        """
        Отображает уведомление.

        Если manual=False, уведомление выводится в статусной строке, а не как всплывающее окно.
        """
        if not manual:
            # Обновляем строку состояния (status_label) вместо показа всплывающего уведомления
            self.status_label.setText(message)
            # Скрываем сообщение через duration миллисекунд
            QTimer.singleShot(duration, lambda: self.status_label.setText(""))
        else:
            notif = Notification(message, notif_type, duration, parent=self.window())
            notif.show_notification()

    def _auto_refresh(self) -> None:
        """Запускает автообновление данных RDP."""
        self.auto_refresh = True
        self.refresh_scheduled = False
        self._execute_operation(self.manager.refresh)

    def _toggle_rdp(self, checked: bool) -> None:
        """
        Обрабатывает изменение состояния чекбокса RDP.
        Запрашивает подтверждение, затем обновляет настройки.

        :param checked: True, если RDP должен быть включён.
        """
        reply = QMessageBox.question(
            self, "Подтверждение", "Изменить статус RDP?",
            QMessageBox.Yes | QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            worker = self._execute_operation(self.manager.update_settings, enabled=checked)
            if not self.refresh_scheduled:
                self.refresh_scheduled = True
                worker.finished.connect(lambda _: QTimer.singleShot(1000, self._auto_refresh))
            Notification(
                "✅ Статус RDP изменён",
                "Статус RDP успешно обновлён.",
                "success",
                duration=3000,
                parent=self.window()
            ).show_notification()
        else:
            with BlockSignals([self.checkbox_rdp]):
                self.checkbox_rdp.setChecked(not checked)
            Notification(
                "⚠️ Операция отменена",
                "Вы отменили выполнение операции.",
                "warning",
                duration=3000,
                parent=self.window()
            ).show_notification()

    def _change_port(self) -> None:
        """Изменяет порт RDP после проверки корректности ввода."""
        port_str = self.port_input.text()
        if port_str.isdigit() and 1 <= int(port_str) <= 65535:
            self._execute_operation(self.manager.update_settings, port=int(port_str))
            Notification(
                "✅ Порт изменён",
                "Порт RDP успешно обновлён.",
                "success",
                duration=3000,
                parent=self.window()
            ).show_notification()
        else:
            Notification(
                "❌ Некорректный порт",
                "Пожалуйста, введите значение порта от 1 до 65535.",
                "error",
                duration=3000,
                parent=self.window()
            ).show_notification()

    def _validate_user(self, user: str) -> bool:
        """
        Проверяет существование доменного пользователя с помощью команды:
        net user "<user>" /domain.

        :param user: Имя пользователя для проверки.
        :return: True, если пользователь найден, иначе False.
        """
        command = f'net user "{user}" /domain'
        result = subprocess.run(
            command, capture_output=True, text=True, shell=True, encoding='cp866'
        )
        logger.debug(f"_validate_user: Команда = {command}")
        logger.debug(f"_validate_user: stdout = {repr(result.stdout)}")
        logger.debug(f"_validate_user: stderr = {repr(result.stderr)}")

        if "Не найдено имя пользователя" in result.stderr or "NET HELPMSG 2221" in result.stderr:
            logger.warning(f"Пользователь {user} НЕ найден в домене!")
            return False

        logger.info(f"Пользователь {user} найден в домене.")
        return True

    def _add_user(self) -> None:
        """Добавляет пользователя в группу RDP без удаления существующих пользователей."""
        user = self.user_input.text().strip()
        if not user:
            Notification(
                "❌ Ввод имени пользователя",
                "Введите имя пользователя.",
                "error",
                duration=3000,
                parent=self.window()
            ).show_notification()
            return

        if not self._validate_user(user):
            Notification(
                "❌ Пользователь не найден",
                "Пользователь не найден в домене!",
                "error",
                duration=3000,
                parent=self.window()
            ).show_notification()
            return

        current_users = [
            self.users_list.item(i).text().lower().replace("ncc\\", "")
            for i in range(self.users_list.count())
        ]
        if user.lower() in current_users:
            Notification(
                "⚠️ Пользователь уже добавлен",
                "Пользователь уже находится в списке.",
                "warning",
                duration=3000,
                parent=self.window()
            ).show_notification()
            return

        self._execute_operation(self.manager.add_user, username=user)
        self.user_input.clear()
        Notification(
            "✅ Пользователь добавлен",
            f"Пользователь {user} успешно добавлен!",
            "success",
            duration=3000,
            parent=self.window()
        ).show_notification()
        QTimer.singleShot(1000, self._load_initial_data)

    def _apply_changes(self) -> None:
        """
        Применяет изменения настроек RDP (чекбокс, порт и список пользователей)
        и обновляет UI после завершения операции.
        """
        current_users = [self.users_list.item(i).text() for i in range(self.users_list.count())]
        port = self.port_input.text()

        def on_update_complete(_: dict) -> None:
            if not self.refresh_scheduled:
                self.refresh_scheduled = True
                QTimer.singleShot(1000, self._auto_refresh)
            Notification(
                "✅ Настройки применены",
                "Настройки RDP успешно обновлены.",
                "success",
                duration=3000,
                parent=self.window()
            ).show_notification()

        worker = self._execute_operation(
            self.manager.update_settings,
            enabled=self.checkbox_rdp.isChecked(),
            port=int(port) if port else None,
            users=current_users
        )
        worker.finished.connect(on_update_complete)

    def _show_context_menu(self, pos) -> None:
        """Показывает контекстное меню для удаления выбранного пользователя."""
        menu = QMenu()
        delete_action = menu.addAction("Удалить")
        delete_action.triggered.connect(self._delete_selected_user)
        menu.exec_(self.users_list.mapToGlobal(pos))

    def _delete_selected_user(self) -> None:
        """Удаляет выбранного пользователя и обновляет UI после завершения операции."""
        item = self.users_list.currentItem()
        if not item:
            Notification(
                "❌ Пользователь не выбран",
                "Пожалуйста, выберите пользователя для удаления.",
                "error",
                duration=3000,
                parent=self.window()
            ).show_notification()
            return

        current_users = [self.users_list.item(i).text() for i in range(self.users_list.count())]
        current_users.remove(item.text())
        logger.debug(f"Удаляем пользователя {item.text()} из RDP")

        def on_update_complete(_: dict) -> None:
            if not self.refresh_scheduled:
                self.refresh_scheduled = True
                QTimer.singleShot(100, self._auto_refresh)
            Notification(
                "✅ Пользователь удалён",
                "Пользователь успешно удалён из списка.",
                "success",
                duration=3000,
                parent=self.window()
            ).show_notification()

        worker = self._execute_operation(self.manager.update_settings, users=current_users)
        worker.finished.connect(on_update_complete)

    def _update_ui(self, data: Dict[str, Any]) -> None:
        """Обновляет UI на основе полученных данных."""
        logger.debug(f"Обновление UI с данными: {data}")
        self._show_loading(False)

        with BlockSignals([self.checkbox_rdp, self.port_input, self.users_list]):
            self.checkbox_rdp.setChecked(data.get('enabled', False))
            self.port_input.setText(str(data.get('port', 3389)))
            self.users_list.clear()
            for user in data.get('users', []):
                item = QListWidgetItem(user)
                font = QFont("Arial", 10)
                font.setBold(False)
                item.setFont(font)
                item.setFlags(item.flags() & ~Qt.ItemIsEditable)
                self.users_list.addItem(item)

        self.status_label.setText("")

        # Если обновление не было авто (т.е. вызвано вручную), показываем всплывающее уведомление.
        if not self.auto_refresh:
            Notification(
                "✅ Данные обновлены",
                "Информация успешно обновлена.",
                "success",
                duration=3000,
                parent=self.window()
            ).show_notification()
        # Если обновление произошло автоматически, можно обновить только status_label.
        else:
            self.info_label.setText("Данные обновлены.")  # Обновляем статусную строку
        self.auto_refresh = False
        self.refresh_scheduled = False

    def _show_loading(self, visible: bool) -> None:
        """
        Отображает или скрывает индикатор загрузки и блокирует элементы управления.

        :param visible: True – показывать индикатор и блокировать элементы, False – скрывать.
        """
        self.progress.setVisible(visible)
        # Если индикатор виден – задаём бесконечный режим
        self.progress.setRange(0, 0 if visible else 1)
        for widget in [self.checkbox_rdp, self.change_port_btn, self.add_user_btn,
                       self.refresh_btn, self.apply_btn]:
            widget.setEnabled(not visible)

    def _handle_error(self, message: str) -> None:
        """
        Обрабатывает ошибки, снимает блокировку с интерфейса и выводит уведомление.

        Здесь можно выбрать менее навязчивый способ отображения ошибки.
        """
        logger.error(f"Ошибка: {message}")
        self._show_loading(False)

        error_mapping = {
            "ERROR_ACCESS_DENIED": (
                "Ошибка доступа.\nПроверьте, что у вас есть административные права на удалённом компьютере.\n"
                "Возможно, учетные данные неверны или настройки UAC ограничивают выполнение операций."
            ),
            "unsupported operand type(s) for +=: 'NoneType' and 'bytes'": (
                "Ошибка при обработке данных службы.\nВозможно, служба не была создана из-за недостатка прав.\n"
                "Проверьте учетные данные и обновите библиотеку pypsexec."
            )
        }

        friendly_message = next((msg for key, msg in error_mapping.items() if key in message), message)
        self.status_label.setText(f"❌ Ошибка: {friendly_message}")

        # Вместо блокирующего модального окна можно показать уведомление в status_label:
        Notification(
            "❌ Ошибка",
            friendly_message,
            "error",
            duration=3000,
            parent=self.window()
        ).show_notification()

        # Если всё же нужно показать модальное окно, можно сделать это по выбору пользователя:
        # msg_box = QMessageBox(self)
        # msg_box.setIcon(QMessageBox.Critical)
        # msg_box.setWindowTitle("Ошибка")
        # msg_box.setText("Произошла ошибка при выполнении операции:")
        # msg_box.setInformativeText(friendly_message)
        # msg_box.exec_()

