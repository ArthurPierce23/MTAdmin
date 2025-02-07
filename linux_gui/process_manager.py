# linux_gui/process_manager.py

import logging

logger = logging.getLogger(__name__)

class ProcessManager:
    """
    Класс для получения информации о процессах на удалённом Linux-хосте через SSH.
    Использует команду "ps aux --sort=-%cpu" для получения списка процессов, аналогичного выводу htop.
    """

    def __init__(self, client):
        """
        :param client: SSHClient, полученный через SessionManager.
        """
        self.client = client

    def get_processes_info(self) -> dict:
        """
        Получает информацию о процессах.
        Используется команда "ps aux --sort=-%cpu".

        :return: Словарь вида:
            {
                "raw": <полный вывод команды>,
                "processes": [ { "USER": ..., "PID": ..., "%CPU": ..., "%MEM": ..., "VSZ": ..., "RSS": ..., "TTY": ..., "STAT": ..., "START": ..., "TIME": ..., "COMMAND": ... }, ... ]
            }
        :raises Exception: При возникновении ошибок выполнения команды.
        """
        try:
            stdin, stdout, stderr = self.client.exec_command("ps aux --sort=-%cpu")
            output = stdout.read().decode()
            error = stderr.read().decode()
            if error:
                raise Exception(error)
            processes = self._parse_ps_output(output)
            return {"raw": output, "processes": processes}
        except Exception as e:
            logger.error(f"Ошибка получения информации о процессах: {e}")
            raise e

    def _parse_ps_output(self, output: str) -> list:
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
        # Первая строка – заголовок, пропускаем её
        processes = []
        for line in lines[1:]:
            # Разбиваем строку на 11 частей: первые 10 столбцов фиксированные, оставшееся – команда.
            parts = line.split(None, 10)
            if len(parts) < 11:
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
