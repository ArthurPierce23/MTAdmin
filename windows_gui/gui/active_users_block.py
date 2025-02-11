import subprocess
import platform
import logging
from typing import List, Dict, Any

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QTableWidget, QTableWidgetItem,
    QGroupBox, QHeaderView, QFrame, QPushButton
)
from PySide6.QtCore import Qt, QTimer
from notifications import Notification

logger = logging.getLogger(__name__)


class ActiveUsers(QWidget):
    """
    Блок для отображения активных сессий пользователей.
    Принимает имя хоста (или IP), для которого запрашиваются сессии.
    """

    def __init__(self, hostname: str, parent: QWidget = None) -> None:
        super().__init__(parent)
        self.hostname: str = hostname
        self.EXCLUDED_USERNAMES: set[str] = {
            'SYSTEM', 'LOCAL SERVICE', 'pdqdeployment',
            'NETWORK SERVICE', 'СИСТЕМА', '', '65536'
        }
        self.STATUS_EMOJI: Dict[str, str] = {
            'Active': '🟢 Активно',
            'Active*': '🟡 Активно (подключение)',
            'Активно': '🟢 Активно',
            'Активно*': '🟡 Активно (подключение)',
            'Disc': '🔴 Отключено',
            'Disconnected': '⚫ Разъединено',
        }
        self._init_ui()
        # Первоначальное обновление через 100 мс, затем автообновление каждую минуту
        QTimer.singleShot(100, self.update_info)
        self.refresh_timer = QTimer(self)
        self.refresh_timer.timeout.connect(self.update_info)
        self.refresh_timer.start(60000)

    def _init_ui(self) -> None:
        """
        Инициализация графического интерфейса виджета.
        """
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(15)

        # Группа "Активные пользователи"
        self.group_box = QGroupBox("💻 Активные пользователи")
        self.group_box.setObjectName("groupBox")  # Стилизация из styles.py
        group_layout = QVBoxLayout()
        group_layout.setContentsMargins(10, 10, 10, 10)
        group_layout.setSpacing(10)

        self.info_label = QLabel("👥 Активные пользователи")
        self.info_label.setObjectName("title")  # Стиль заголовка
        group_layout.addWidget(self.info_label)

        # Таблица для отображения сессий
        self.table = QTableWidget(0, 3)
        self.table.setObjectName("usersTable")  # Стилизация из styles.py
        self.table.setHorizontalHeaderLabels(["👤 Пользователь", "🔑 Тип входа", "🔄 Статус"])
        self.table.verticalHeader().setVisible(False)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setFixedHeight(150)
        group_layout.addWidget(self.table)

        # Кнопка обновления
        self.refresh_button = QPushButton("🔄 Обновить данные")
        self.refresh_button.setObjectName("refreshButton")
        self.refresh_button.setToolTip("Обновить список активных сессий")
        self.refresh_button.clicked.connect(self._on_refresh_clicked)
        group_layout.addWidget(self.refresh_button)

        self.group_box.setLayout(group_layout)
        layout.addWidget(self.group_box)

        # Разделительная линия
        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        separator.setFrameShadow(QFrame.Sunken)
        separator.setObjectName("separator")  # Стилизация из styles.py
        layout.addWidget(separator)

    def _on_refresh_clicked(self) -> None:
        """
        Обработка нажатия кнопки обновления.
        При ручном обновлении показывается уведомление.
        """
        self.update_info(notify_on_update=True)

    def update_info(self, notify_on_update: bool = False) -> None:
        """
        Обновляет информацию о сессиях.

        :param notify_on_update: Если True, при ручном обновлении показывается уведомление.
                                  При автоматическом обновлении уведомления не выводятся.
        """
        result: Dict[str, Any] = self.get_active_sessions()
        if "error" in result:
            error_msg: str = result['error']
            # Обновляем текст статуса в виджете – уведомление не выводим автоматически
            self.info_label.setText(f"❌ Ошибка: {error_msg}")
            self.table.setRowCount(0)
            if notify_on_update:
                Notification(
                    "❌ Ошибка при обновлении",
                    f"Не удалось обновить информацию о сессиях: {error_msg}. Пожалуйста, проверьте соединение или настройки.",
                    "error",
                    duration=3000,
                    parent=self.window()
                ).show_notification()
        else:
            sessions: List[Dict[str, str]] = result.get("sessions", [])
            self._update_table(sessions)
            count: int = len(sessions)
            if count:
                sessions_text: str = self.declension_sessions(count)
                self.info_label.setText(f"✅ Активные пользователи ({count} {sessions_text})")
            else:
                self.info_label.setText("ℹ️ Нет активных пользователей")
            if notify_on_update:
                if count:
                    Notification(
                        "✅ Обновление завершено!",
                        f"Успешно обновлено: {count} {sessions_text}.",
                        'success',
                        duration=3000,
                        parent=self.window()
                    ).show_notification()

                else:
                    Notification(
                        "ℹ️ Обновление завершено!",
                        "Нет активных пользователей в данный момент.",
                        'info',
                        duration=3000,
                        parent=self.window()
                    ).show_notification()

    def _update_table(self, sessions: List[Dict[str, str]]) -> None:
        """
        Обновляет содержимое таблицы с активными сессиями.

        :param sessions: Список сессий, каждая из которых описывается словарём.
        """
        new_row_count: int = len(sessions)
        # Устанавливаем нужное количество строк
        self.table.setRowCount(new_row_count)
        for row, session in enumerate(sessions):
            # Создаём элементы таблицы и делаем их не редактируемыми
            user_item = QTableWidgetItem(f"👤 {session.get('user', '')}")
            user_item.setFlags(user_item.flags() & ~Qt.ItemIsEditable)

            logon_type: str = session.get("logon_type", "")
            type_icon: str = "💻" if logon_type == "Локальный" else "🌐"
            type_item = QTableWidgetItem(f"{type_icon} {logon_type}")
            type_item.setFlags(type_item.flags() & ~Qt.ItemIsEditable)

            status_text: str = session.get("status", "")
            status_item = QTableWidgetItem(self.STATUS_EMOJI.get(status_text, f"❔ {status_text}"))
            status_item.setToolTip(self._get_status_tooltip(status_text))
            status_item.setFlags(status_item.flags() & ~Qt.ItemIsEditable)

            self.table.setItem(row, 0, user_item)
            self.table.setItem(row, 1, type_item)
            self.table.setItem(row, 2, status_item)

    def _get_status_tooltip(self, status: str) -> str:
        """
        Возвращает подсказку для статуса сессии.

        :param status: Статус сессии.
        :return: Описание статуса.
        """
        tooltips: Dict[str, str] = {
            'Active': "Активная пользовательская сессия",
            'Disc': "Сессия была отключена",
            'Disconnected': "Соединение прервано",
        }
        return tooltips.get(status, "Неизвестный статус соединения")

    def get_active_sessions(self) -> Dict[str, Any]:
        """
        Получает активные сессии с использованием команд quser или qwinsta.
        Работает только на Windows.

        :return: Словарь с ключом "sessions" или "error".
        """
        try:
            if platform.system() != "Windows":
                return {"error": "Функция доступна только на Windows"}
            is_remote: bool = self.hostname.lower() not in ('localhost', '127.0.0.1')
            output: str = self._run_remote_command(is_remote)
            sessions: List[Dict[str, str]] = self._parse_output(output, is_remote)
            return {"sessions": sessions}
        except Exception as e:
            logger.exception("Ошибка получения активных сессий")
            return {"error": str(e)}

    def _run_remote_command(self, is_remote: bool) -> str:
        """
        Выполняет команду (quser или qwinsta) для получения активных сессий.

        :param is_remote: Если True, используется команда для удалённого сервера.
        :return: Вывод команды.
        :raises RuntimeError: Если команда завершается с ошибкой.
        """
        command: str = "qwinsta" if is_remote else "quser"
        args: List[str] = [command]
        if is_remote:
            args.append("/server:" + self.hostname)
        result = subprocess.run(
            args, capture_output=True, text=True, encoding='cp866',
            errors='replace', shell=True
        )
        if result.returncode != 0:
            raise RuntimeError(result.stderr or f"Command failed with code {result.returncode}")
        return result.stdout

    def _parse_output(self, output: str, is_remote: bool) -> List[Dict[str, str]]:
        """
        Разбивает вывод команды на строки и делегирует парсинг в зависимости от типа.

        :param output: Вывод команды.
        :param is_remote: Если True, используется парсинг для qwinsta.
        :return: Список сессий.
        """
        sessions: List[Dict[str, str]] = []
        lines: List[str] = [line.rstrip('\n') for line in output.split('\n') if line.strip()]
        if not lines:
            return sessions
        return self._parse_qwinsta(lines) if is_remote else self._parse_quser(lines)

    def _parse_quser(self, lines: List[str]) -> List[Dict[str, str]]:
        """
        Парсит вывод команды quser (локальная машина).

        :param lines: Строки вывода.
        :return: Список сессий.
        :raises ValueError: Если формат вывода не соответствует ожиданиям.
        """
        sessions: List[Dict[str, str]] = []
        header_line: str = lines[0].strip()
        col_positions: List[int] = self._get_column_positions(header_line)
        headers: List[str] = self._split_line_by_positions(header_line, col_positions)
        try:
            username_col: int = self._get_column_index(headers, ['USERNAME', 'ПОЛЬЗОВАТЕЛЬ'])
            session_col: int = self._get_column_index(headers, ['SESSIONNAME', 'СЕАНС'])
            state_col: int = self._get_column_index(headers, ['STATE', 'СТАТУС'])
        except ValueError as e:
            raise ValueError(f"Неизвестный формат вывода quser: {e}")
        for line in lines[1:]:
            parts: List[str] = self._split_line_by_positions(line, col_positions)
            username: str = parts[username_col] if username_col < len(parts) else ''
            session_type: str = parts[session_col] if session_col < len(parts) else ''
            state: str = parts[state_col] if state_col < len(parts) else ''
            if username and username not in self.EXCLUDED_USERNAMES:
                sessions.append({
                    "user": username,
                    "logon_type": self._get_session_type(session_type),
                    "status": state,
                })
        return sessions

    def _parse_qwinsta(self, lines: List[str]) -> List[Dict[str, str]]:
        """
        Парсит вывод команды qwinsta (удалённый хост).

        :param lines: Строки вывода.
        :return: Список сессий.
        :raises ValueError: Если формат вывода не соответствует ожиданиям.
        """
        sessions: List[Dict[str, str]] = []
        header_line: str = lines[0].strip()
        col_positions: List[int] = self._get_column_positions(header_line)
        headers: List[str] = self._split_line_by_positions(header_line, col_positions)
        try:
            session_col: int = self._get_column_index(headers, ['SESSIONNAME', 'СЕАНС'])
            user_col: int = self._get_column_index(headers, ['USERNAME', 'ПОЛЬЗОВАТЕЛЬ'])
            state_col: int = self._get_column_index(headers, ['STATE', 'СТАТУС'])
        except ValueError as e:
            raise ValueError(f"Неизвестный формат вывода qwinsta: {e}")
        for line in lines[1:]:
            parts: List[str] = self._split_line_by_positions(line, col_positions)
            session_type: str = parts[session_col] if session_col < len(parts) else ''
            username: str = parts[user_col] if user_col < len(parts) else ''
            state: str = parts[state_col] if state_col < len(parts) else ''
            if username and username not in self.EXCLUDED_USERNAMES and not username.isdigit():
                sessions.append({
                    "user": username,
                    "logon_type": self._get_session_type(session_type),
                    "status": state,
                })
        return sessions

    def _get_column_positions(self, header_line: str) -> List[int]:
        """
        Определяет начальные позиции столбцов на основе строки заголовка.

        :param header_line: Строка заголовка.
        :return: Список позиций начала каждого столбца.
        """
        col_positions: List[int] = []
        in_column = False
        for i, char in enumerate(header_line):
            if char != ' ':
                if not in_column:
                    col_positions.append(i)
                    in_column = True
            else:
                in_column = False
        col_positions.append(len(header_line) + 1)
        return col_positions

    def _split_line_by_positions(self, line: str, positions: List[int]) -> List[str]:
        """
        Разбивает строку на части по заданным позициям.

        :param line: Исходная строка.
        :param positions: Список позиций.
        :return: Список подстрок.
        """
        parts: List[str] = []
        for i in range(len(positions) - 1):
            start = positions[i]
            end = positions[i + 1]
            parts.append(line[start:end].strip())
        return parts

    def _get_column_index(self, headers: List[str], possible_names: List[str]) -> int:
        """
        Определяет индекс столбца по возможным именам.

        :param headers: Список заголовков.
        :param possible_names: Возможные варианты имени столбца.
        :return: Индекс найденного столбца.
        :raises ValueError: Если ни одно из имен не найдено.
        """
        for name in possible_names:
            if name in headers:
                return headers.index(name)
        raise ValueError(f"Не найдена колонка: {possible_names}")

    def _get_session_type(self, session_name: str) -> str:
        """
        Определяет тип сессии по имени.

        :param session_name: Имя сессии.
        :return: Тип сессии: "RDP", "Локальный" или "Удалённый".
        """
        session_name = session_name.lower()
        if 'rdp' in session_name or 'терминальная служба' in session_name:
            return "RDP"
        if 'console' in session_name or 'консоль' in session_name:
            return "Локальный"
        return "Удалённый"

    def declension_sessions(self, count: int) -> str:
        """
        Определяет правильное склонение для слова "сессия" в зависимости от числа.

        :param count: Количество сессий.
        :return: Строка с правильным склонением.
        """
        if 11 <= (count % 100) <= 14:
            return "сессий"
        remainder = count % 10
        if remainder == 1:
            return "сессия"
        elif 2 <= remainder <= 4:
            return "сессии"
        return "сессий"
