# linux_gui/network.py

import re
import logging

logger = logging.getLogger(__name__)


class NetworkInfo:
    """
    Класс для получения сетевой информации удалённого Linux-хоста через SSH.

    Использует команду 'ip addr show' для получения сведений об интерфейсах и IP-адресах.

    Метод get_network_info() возвращает словарь с двумя ключами:
      - "raw": полный вывод команды.
      - "interfaces": словарь, где ключ — имя интерфейса, а значение — список найденных IP-адресов.
    """

    def __init__(self, client):
        """
        :param client: SSHClient, полученный через SessionManager.
        """
        self.client = client

    def get_network_info(self) -> dict:
        """
        Получает сетевую информацию.

        :return: Словарь вида:
          {
              "raw": <полный вывод команды>,
              "interfaces": {
                  "eth0": {"ips": ["192.168.1.100", ...]},
                  "lo": {"ips": ["127.0.0.1"]},
                  ...
              }
          }
        :raises Exception: при возникновении ошибок выполнения команды.
        """
        try:
            # Выполняем команду для получения информации об интерфейсах
            stdin, stdout, stderr = self.client.exec_command("ip addr show")
            output = stdout.read().decode()
            error = stderr.read().decode()
            if error:
                raise Exception(error)

            # Простой парсинг вывода: ищем строки с именем интерфейса и строки с 'inet'
            interfaces = {}
            current_if = None
            for line in output.splitlines():
                line = line.strip()
                # Интерфейсная строка начинается с "число:" (например, "2: enp0s3: <BROADCAST,...")
                if re.match(r'^\d+:\s+\S+:', line):
                    # Разбиваем по двоеточию: первый элемент — порядковый номер, второй — имя
                    parts = line.split(":")
                    if len(parts) >= 2:
                        current_if = parts[1].strip()
                        interfaces[current_if] = {"ips": []}
                elif current_if and line.startswith("inet "):
                    # Строка с IP-адресом: формат "inet 192.168.1.100/24 ..."
                    match = re.search(r'inet\s+([\d\.]+)/\d+', line)
                    if match:
                        ip_addr = match.group(1)
                        interfaces[current_if]["ips"].append(ip_addr)

            return {"raw": output, "interfaces": interfaces}
        except Exception as e:
            logger.error(f"Ошибка получения сетевой информации: {e}")
            raise e
