import subprocess
import platform
import logging
from typing import List, Dict, Union

logger = logging.getLogger(__name__)


class ActiveUsers:
    """
    Класс для получения активных сессий пользователей на Windows.
    Использует команды 'quser' для локальной машины и 'qwinsta' для удалённых серверов.
    """
    def __init__(self, hostname: str) -> None:
        """
        Инициализация с указанием имени хоста.

        :param hostname: Имя хоста или IP-адрес.
        """
        self.hostname: str = hostname
        self.EXCLUDED_USERNAMES = {
            'SYSTEM', 'LOCAL SERVICE', 'pdqdeployment',
            'NETWORK SERVICE', 'СИСТЕМА', '',
            '65536'  # Фильтрация по ID
        }

    def get_active_sessions(self) -> Dict[str, Union[List[Dict[str, str]], str]]:
        """
        Получает активные сессии пользователей.

        :return: Словарь с ключом 'sessions' и списком сессий или ключ 'error' с описанием ошибки.
        """
        try:
            if platform.system() != "Windows":
                return {"error": "Функция доступна только на Windows"}

            is_remote: bool = self.hostname.lower() not in ('localhost', '127.0.0.1')
            output: str = self._run_remote_command(is_remote)
            logger.debug(f"Raw command output: {output}")

            sessions: List[Dict[str, str]] = self._parse_output(output, is_remote)
            logger.debug(f"Parsed sessions: {sessions}")

            return {"sessions": sessions}
        except Exception as e:
            logger.error(f"Error: {str(e)}", exc_info=True)
            return {"error": str(e)}

    def _run_remote_command(self, is_remote: bool) -> str:
        """
        Выполняет команду для получения сессий.

        :param is_remote: True, если команда должна выполняться на удалённом хосте.
        :return: Вывод команды.
        :raises RuntimeError: При ошибке выполнения команды.
        """
        command: str = "qwinsta" if is_remote else "quser"
        args: List[str] = [command]

        if is_remote:
            args.append(f"/server:{self.hostname}")

        try:
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

    def _parse_output(self, output: str, is_remote: bool) -> List[Dict[str, str]]:
        """
        Парсит вывод команды и возвращает список сессий.

        :param output: Строка вывода команды.
        :param is_remote: Флаг, указывающий, используется ли удалённая команда.
        :return: Список сессий.
        """
        sessions: List[Dict[str, str]] = []
        lines: List[str] = [line.rstrip('\n') for line in output.split('\n') if line.strip()]

        if not lines:
            return sessions

        if is_remote:
            return self._parse_qwinsta(lines)
        else:
            return self._parse_quser(lines)

    def _parse_quser(self, lines: List[str]) -> List[Dict[str, str]]:
        """
        Парсит вывод команды 'quser' (локальная машина).

        :param lines: Список строк вывода.
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
            logon_time_col: int = self._get_column_index(headers, ['LOGON TIME', 'ВРЕМЯ ВХОДА'])
        except ValueError as e:
            raise ValueError(f"Неизвестный формат вывода quser: {str(e)}")

        for line in lines[1:]:
            parts: List[str] = self._split_line_by_positions(line, col_positions)
            username: str = parts[username_col] if username_col < len(parts) else ''
            session_type: str = parts[session_col] if session_col < len(parts) else ''
            state: str = parts[state_col] if state_col < len(parts) else ''
            logon_time: str = parts[logon_time_col] if logon_time_col < len(parts) else ''

            if username and username not in self.EXCLUDED_USERNAMES:
                sessions.append({
                    "user": username,
                    "logon_type": self._get_session_type(session_type),
                    "status": state,
                    "logon_time": logon_time
                })
        return sessions

    def _parse_qwinsta(self, lines: List[str]) -> List[Dict[str, str]]:
        """
        Парсит вывод команды 'qwinsta' (удалённый хост).

        :param lines: Список строк вывода.
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
            raise ValueError(f"Неизвестный формат вывода qwinsta: {str(e)}")

        for line in lines[1:]:
            parts: List[str] = self._split_line_by_positions(line, col_positions)
            session_type: str = parts[session_col] if session_col < len(parts) else ''
            username: str = parts[user_col] if user_col < len(parts) else ''
            state: str = parts[state_col] if state_col < len(parts) else ''

            # Фильтрация: пропускаем числовые идентификаторы и исключённые имена.
            if username and username not in self.EXCLUDED_USERNAMES:
                if username.isdigit():
                    continue
                sessions.append({
                    "user": username,
                    "logon_type": self._get_session_type(session_type),
                    "status": state,
                    "logon_time": ''
                })
        return sessions

    def _get_column_positions(self, header_line: str) -> List[int]:
        """
        Определяет начальные позиции столбцов на основе строки заголовка.

        :param header_line: Строка заголовка.
        :return: Список позиций, где начинается каждый столбец.
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
        Разбивает строку на части согласно указанным позициям.

        :param line: Строка для разбивки.
        :param positions: Список позиций начала столбцов.
        :return: Список частей строки.
        """
        parts: List[str] = []
        for i in range(len(positions) - 1):
            start = positions[i]
            end = positions[i + 1]
            part = line[start:end].strip()
            parts.append(part)
        return parts

    def _get_column_index(self, headers: List[str], possible_names: List[str]) -> int:
        """
        Находит индекс столбца среди заголовков, соответствующий одному из возможных имён.

        :param headers: Список заголовков.
        :param possible_names: Возможные имена столбца.
        :return: Индекс найденного столбца.
        :raises ValueError: Если ни одно из имён не найдено.
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
