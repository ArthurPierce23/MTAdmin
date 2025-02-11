import re
import logging
from typing import Any, Dict

logger = logging.getLogger(__name__)


class NetworkInfo:
    """
    Класс для получения сетевой информации удалённого Linux-хоста через SSH.

    Использует команду 'ip addr show' для получения сведений об интерфейсах и IP-адресах.

    Метод get_network_info() возвращает словарь с двумя ключами:
      - "raw": полный вывод команды.
      - "interfaces": словарь, где ключ — имя интерфейса, а значение — список найденных IP-адресов.
    """

    def __init__(self, client: Any) -> None:
        """
        Инициализирует объект для получения сетевой информации.

        :param client: SSHClient, полученный через SessionManager.
        """
        self.client = client

    def get_network_info(self) -> Dict[str, Any]:
        """
        Получает сетевую информацию с удалённого хоста.

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
                logger.error("Ошибка при выполнении команды 'ip addr show': %s", error)
                raise Exception(error)

            interfaces: Dict[str, Dict[str, Any]] = {}
            current_interface: str | None = None

            # Компилируем регулярные выражения для поиска интерфейсных строк и строк с IP-адресом
            interface_pattern = re.compile(r'^\d+:\s+(\S+):')
            ip_pattern = re.compile(r'inet\s+([\d\.]+)/\d+')

            for line in output.splitlines():
                line = line.strip()

                # Если строка соответствует описанию интерфейса (например, "2: enp0s3: <BROADCAST,...")
                interface_match = interface_pattern.match(line)
                if interface_match:
                    current_interface = interface_match.group(1)
                    interfaces[current_interface] = {"ips": []}
                    continue

                # Если уже найден текущий интерфейс и строка содержит IP-адрес
                if current_interface and line.startswith("inet "):
                    ip_match = ip_pattern.search(line)
                    if ip_match:
                        ip_address = ip_match.group(1)
                        interfaces[current_interface]["ips"].append(ip_address)

            return {"raw": output, "interfaces": interfaces}

        except Exception as e:
            logger.error("Ошибка получения сетевой информации: %s", e)
            raise e
