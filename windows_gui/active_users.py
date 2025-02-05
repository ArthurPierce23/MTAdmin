import subprocess
import re
import platform
import logging

logger = logging.getLogger(__name__)


class ActiveUsers:
    def __init__(self, hostname):
        self.hostname = hostname
        self.EXCLUDED_USERNAMES = {
            'SYSTEM', 'LOCAL SERVICE', 'pdqdeployment',
            'NETWORK SERVICE', 'СИСТЕМА', '',
            '65536'  # Добавляем фильтрацию по ID
        }
    def get_active_sessions(self):
        try:
            if platform.system() != "Windows":
                return {"error": "Функция доступна только на Windows"}

            is_remote = self.hostname.lower() not in ('localhost', '127.0.0.1')
            output = self._run_remote_command(is_remote)
            logger.debug(f"Raw command output: {output}")

            sessions = self._parse_output(output, is_remote)
            logger.debug(f"Parsed sessions: {sessions}")

            return {"sessions": sessions}

        except Exception as e:
            logger.error(f"Error: {str(e)}", exc_info=True)
            return {"error": str(e)}

    def _run_remote_command(self, is_remote):
        try:
            command = "qwinsta" if is_remote else "quser"
            args = [command]

            if is_remote:
                args.extend(["/server:" + self.hostname])

            result = subprocess.run(
                args,
                capture_output=True,
                text=True,
                encoding='cp866',
                errors='replace',
                shell=True
            )

            if result.returncode != 0:
                error_msg = result.stderr or f"Command failed with code {result.returncode}"
                raise RuntimeError(error_msg)

            return result.stdout

        except Exception as e:
            raise RuntimeError(f"Ошибка выполнения {command}: {str(e)}")

    def _parse_output(self, output, is_remote):
        sessions = []
        lines = [line.rstrip('\n') for line in output.split('\n') if line.strip()]

        if not lines:
            return sessions

        if is_remote:
            return self._parse_qwinsta(lines)
        return self._parse_quser(lines)

    def _parse_quser(self, lines):
        sessions = []
        header_line = lines[0].strip()
        col_positions = self._get_column_positions(header_line)
        headers = self._split_line_by_positions(header_line, col_positions)

        try:
            username_col = self._get_column_index(headers, ['USERNAME', 'ПОЛЬЗОВАТЕЛЬ'])
            session_col = self._get_column_index(headers, ['SESSIONNAME', 'СЕАНС'])
            state_col = self._get_column_index(headers, ['STATE', 'СТАТУС'])
            logon_time_col = self._get_column_index(headers, ['LOGON TIME', 'ВРЕМЯ ВХОДА'])
        except ValueError as e:
            raise ValueError(f"Неизвестный формат вывода quser: {str(e)}")

        for line in lines[1:]:
            parts = self._split_line_by_positions(line, col_positions)
            username = parts[username_col] if username_col < len(parts) else ''
            session_type = parts[session_col] if session_col < len(parts) else ''
            state = parts[state_col] if state_col < len(parts) else ''
            logon_time = parts[logon_time_col] if logon_time_col < len(parts) else ''

            if username and username not in self.EXCLUDED_USERNAMES:
                sessions.append({
                    "user": username,
                    "logon_type": self._get_session_type(session_type),
                    "status": state,
                    "logon_time": logon_time
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
            raise ValueError(f"Неизвестный формат вывода qwinsta: {str(e)}")

        for line in lines[1:]:
            parts = self._split_line_by_positions(line, col_positions)
            session_type = parts[session_col] if session_col < len(parts) else ''
            username = parts[user_col] if user_col < len(parts) else ''
            state = parts[state_col] if state_col < len(parts) else ''

            # Добавляем фильтрацию числовых значений
            if username and username not in self.EXCLUDED_USERNAMES:
                if username.isdigit():  # Пропускаем числовые идентификаторы
                    continue

                sessions.append({
                    "user": username,
                    "logon_type": self._get_session_type(session_type),
                    "status": state,
                    "logon_time": ''
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
            end = positions[i+1]
            part = line[start:end].strip()
            parts.append(part)
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