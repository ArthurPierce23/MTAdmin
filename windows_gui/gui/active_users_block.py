from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QFrame, QGroupBox
)
from PySide6.QtCore import QTimer
import subprocess
import platform
import logging
from notifications import Notification
from PySide6.QtCore import Qt

logger = logging.getLogger(__name__)


class ActiveUsers(QWidget):
    def __init__(self, hostname, parent=None):
        super().__init__(parent)
        self.hostname = hostname
        self.EXCLUDED_USERNAMES = {
            'SYSTEM', 'LOCAL SERVICE', 'pdqdeployment',
            'NETWORK SERVICE', 'СИСТЕМА', '', '65536'
        }
        self.STATUS_EMOJI = {
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

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(15)

        self.group_box = QGroupBox("💻 Активные пользователи")
        self.group_box.setObjectName("groupBox")  # Применяем стилизацию из styles.py
        group_layout = QVBoxLayout()
        group_layout.setContentsMargins(10, 10, 10, 10)
        group_layout.setSpacing(10)

        self.info_label = QLabel("👥 Активные пользователи")
        self.info_label.setObjectName("title")  # Применяем стиль заголовка
        group_layout.addWidget(self.info_label)

        self.table = QTableWidget(0, 3)
        self.table.setObjectName("usersTable")  # Применяем стилизацию из styles.py
        self.table.setHorizontalHeaderLabels(["👤 Пользователь", "🔑 Тип входа", "🔄 Статус"])
        self.table.verticalHeader().setVisible(False)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setFixedHeight(150)
        group_layout.addWidget(self.table)

        self.refresh_button = QPushButton("🔄 Обновить данные")
        self.refresh_button.setObjectName("refreshButton")  # Применяем стилизацию из styles.py
        self.refresh_button.setToolTip("Обновить список активных сессий")
        self.refresh_button.clicked.connect(self._on_refresh_clicked)
        group_layout.addWidget(self.refresh_button)

        self.group_box.setLayout(group_layout)
        layout.addWidget(self.group_box)

        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        separator.setFrameShadow(QFrame.Sunken)
        separator.setObjectName("separator")  # Применяем стилизацию из styles.py
        layout.addWidget(separator)

    def _on_refresh_clicked(self):
        self.update_info()
        Notification('Обновление завершено!', 'success').show_notification()

    def update_info(self):
        result = self.get_active_sessions()
        if "error" in result:
            Notification(result['error'], "error").show_notification()
            self.info_label.setText(f"❌ Ошибка: {result['error']}")
            self.table.setRowCount(0)
        else:
            sessions = result.get("sessions", [])
            self._update_table(sessions)
            count = len(sessions)
            if count:
                sessions_text = self.declension_sessions(count)
                self.info_label.setText(f"✅ Активные пользователи ({count} {sessions_text})")
            else:
                self.info_label.setText("ℹ️ Нет активных пользователей")

    def _update_table(self, sessions):
        self.table.setRowCount(len(sessions))
        for row, session in enumerate(sessions):
            user_item = QTableWidgetItem(f"👤 {session['user']}")
            user_item.setFlags(user_item.flags() & ~Qt.ItemIsEditable)

            logon_type = session["logon_type"]
            type_icon = "💻" if logon_type == "Локальный" else "🌐"
            type_item = QTableWidgetItem(f"{type_icon} {logon_type}")
            type_item.setFlags(type_item.flags() & ~Qt.ItemIsEditable)

            status_text = session["status"]
            status_item = QTableWidgetItem(self.STATUS_EMOJI.get(status_text, f"❔ {status_text}"))
            status_item.setToolTip(self._get_status_tooltip(status_text))
            status_item.setFlags(status_item.flags() & ~Qt.ItemIsEditable)

            self.table.setItem(row, 0, user_item)
            self.table.setItem(row, 1, type_item)
            self.table.setItem(row, 2, status_item)


    def _get_status_tooltip(self, status):
        tooltips = {
            'Active': "Активная пользовательская сессия",
            'Disc': "Сессия была отключена",
            'Disconnected': "Соединение прервано",
        }
        return tooltips.get(status, "Неизвестный статус соединения")

    def get_active_sessions(self):
        try:
            if platform.system() != "Windows":
                return {"error": "Функция доступна только на Windows"}
            is_remote = self.hostname.lower() not in ('localhost', '127.0.0.1')
            output = self._run_remote_command(is_remote)
            sessions = self._parse_output(output, is_remote)
            return {"sessions": sessions}
        except Exception as e:
            logger.exception("Ошибка получения активных сессий")
            return {"error": str(e)}

    def _run_remote_command(self, is_remote):
        command = "qwinsta" if is_remote else "quser"
        args = [command]
        if is_remote:
            args.append("/server:" + self.hostname)
        result = subprocess.run(
            args, capture_output=True, text=True, encoding='cp866', errors='replace', shell=True
        )
        if result.returncode != 0:
            raise RuntimeError(result.stderr or f"Command failed with code {result.returncode}")
        return result.stdout

    def _parse_output(self, output, is_remote):
        sessions = []
        lines = [line.rstrip('\n') for line in output.split('\n') if line.strip()]
        if not lines:
            return sessions
        return self._parse_qwinsta(lines) if is_remote else self._parse_quser(lines)

    def _parse_quser(self, lines):
        sessions = []
        header_line = lines[0].strip()
        col_positions = self._get_column_positions(header_line)
        headers = self._split_line_by_positions(header_line, col_positions)
        try:
            username_col = self._get_column_index(headers, ['USERNAME', 'ПОЛЬЗОВАТЕЛЬ'])
            session_col = self._get_column_index(headers, ['SESSIONNAME', 'СЕАНС'])
            state_col = self._get_column_index(headers, ['STATE', 'СТАТУС'])
        except ValueError as e:
            raise ValueError(f"Неизвестный формат вывода quser: {e}")
        for line in lines[1:]:
            parts = self._split_line_by_positions(line, col_positions)
            username = parts[username_col] if username_col < len(parts) else ''
            session_type = parts[session_col] if session_col < len(parts) else ''
            state = parts[state_col] if state_col < len(parts) else ''
            if username and username not in self.EXCLUDED_USERNAMES:
                sessions.append({
                    "user": username,
                    "logon_type": self._get_session_type(session_type),
                    "status": state,
                })
        return sessions

    def _parse_qwinsta(self, lines):
        sessions = []
        header_line = lines[0].strip()
        col_positions = self._get_column_positions(header_line)
        headers = self._split_line_by_positions(header_line, col_positions)
        try:
            session_col = self._get_column_index(headers, ['SESSIONNAME', 'СЕАНС'])
            user_col = self._get_column_index(headers, ['USERNAME', 'ПОЛЬЗОВАТЕЛЬ'])
            state_col = self._get_column_index(headers, ['STATE', 'СТАТУС'])
        except ValueError as e:
            raise ValueError(f"Неизвестный формат вывода qwinsta: {e}")
        for line in lines[1:]:
            parts = self._split_line_by_positions(line, col_positions)
            session_type = parts[session_col] if session_col < len(parts) else ''
            username = parts[user_col] if user_col < len(parts) else ''
            state = parts[state_col] if state_col < len(parts) else ''
            if username and username not in self.EXCLUDED_USERNAMES and not username.isdigit():
                sessions.append({
                    "user": username,
                    "logon_type": self._get_session_type(session_type),
                    "status": state,
                })
        return sessions

    def _get_column_positions(self, header_line):
        col_positions = []
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

    def _split_line_by_positions(self, line, positions):
        parts = []
        for i in range(len(positions) - 1):
            start = positions[i]
            end = positions[i + 1]
            parts.append(line[start:end].strip())
        return parts

    def _get_column_index(self, headers, possible_names):
        for name in possible_names:
            if name in headers:
                return headers.index(name)
        raise ValueError(f"Не найдена колонка: {possible_names}")

    def _get_session_type(self, session_name):
        session_name = session_name.lower()
        if 'rdp' in session_name or 'терминальная служба' in session_name:
            return "RDP"
        if 'console' in session_name or 'консоль' in session_name:
            return "Локальный"
        return "Удалённый"

    def declension_sessions(self, count: int) -> str:
        if 11 <= (count % 100) <= 14:
            return "сессий"
        remainder = count % 10
        if remainder == 1:
            return "сессия"
        elif 2 <= remainder <= 4:
            return "сессии"
        return "сессий"
