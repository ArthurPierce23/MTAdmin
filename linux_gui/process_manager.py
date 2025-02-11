import logging
from typing import List, Dict, Any

logger = logging.getLogger(__name__)


class ProcessManager:
    """
    Класс для получения информации о процессах на удалённом Linux-хосте через SSH.
    Использует команду "ps aux --sort=-%cpu" для получения списка процессов,
    аналогичного выводу htop.
    """

    def __init__(self, client: Any) -> None:
        """
        Инициализирует объект ProcessManager.

        :param client: SSHClient, полученный через SessionManager.
        """
        self.client = client

    def get_processes_info(self) -> Dict[str, Any]:
        """
        Получает информацию о процессах с удалённого хоста.
        Используется команда "ps aux --sort=-%cpu".

        :return: Словарь вида:
            {
                "raw": <полный вывод команды>,
                "processes": [
                    {
                        "USER": ...,
                        "PID": ...,
                        "%CPU": ...,
                        "%MEM": ...,
                        "VSZ": ...,
                        "RSS": ...,
                        "TTY": ...,
                        "STAT": ...,
                        "START": ...,
                        "TIME": ...,
                        "COMMAND": ...
                    },
                    ...
                ]
            }
        :raises Exception: При возникновении ошибок выполнения команды.
        """
        try:
            stdin, stdout, stderr = self.client.exec_command("ps aux --sort=-%cpu")
            output = stdout.read().decode()
            error_output = stderr.read().decode()
            if error_output.strip():
                raise Exception(f"Ошибка при выполнении команды ps aux: {error_output}")
            processes = self._parse_ps_output(output)
            return {"raw": output, "processes": processes}
        except Exception as e:
            logger.exception("Ошибка получения информации о процессах: %s", e)
            raise

    def _parse_ps_output(self, output: str) -> List[Dict[str, str]]:
        """
        Парсит вывод команды ps aux и возвращает список процессов в виде словарей.

        Предполагается, что первая строка – заголовок со столбцами:
          USER, PID, %CPU, %MEM, VSZ, RSS, TTY, STAT, START, TIME, COMMAND

        :param output: Вывод команды ps aux.
        :return: Список словарей с данными о процессах.
        """
        lines = output.strip().splitlines()
        if not lines:
            return []

        processes: List[Dict[str, str]] = []
        # Первая строка – заголовок, пропускаем её
        for line in lines[1:]:
            # Разбиваем строку на 11 частей: первые 10 столбцов фиксированы, оставшееся – команда.
            parts = line.split(None, 10)
            if len(parts) < 11:
                logger.debug("Пропущена строка с недостаточным количеством столбцов: %s", line)
                continue
            process = {
                "USER": parts[0],
                "PID": parts[1],
                "%CPU": parts[2],
                "%MEM": parts[3],
                "VSZ": parts[4],
                "RSS": parts[5],
                "TTY": parts[6],
                "STAT": parts[7],
                "START": parts[8],
                "TIME": parts[9],
                "COMMAND": parts[10]
            }
            processes.append(process)
        return processes
