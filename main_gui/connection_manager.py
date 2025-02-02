# connection_manager.py
import logging
from PySide6.QtCore import QThread, Signal
from database.db_manager import (
    add_recent_connection,
    get_recent_connections,
    add_to_workstation_map,
    get_workstation_map,
    remove_from_workstation_map,
    clear_recent_connections
)
from utils.network_utils import is_valid_ip, detect_os

logger = logging.getLogger(__name__)


class ConnectionWorker(QThread):
    finished = Signal(str, str, str)  # ip, os_name, error

    def __init__(self, ip):
        super().__init__()
        self.ip = ip

    def run(self):
        try:
            if not is_valid_ip(self.ip):
                self.finished.emit(self.ip, "", "Invalid IP format")
                return

            os_name = detect_os(self.ip)
            if os_name in ["Недоступен", "Ошибка проверки"]:
                self.finished.emit(self.ip, "", f"{self.ip} недоступен")
                return

            self.finished.emit(self.ip, os_name, "")
        except Exception as e:
            logger.error(f"Connection error: {str(e)}")
            self.finished.emit(self.ip, "", f"Ошибка: {str(e)}")


class ConnectionManager:
    def __init__(self):
        self.recent_limit = 10

    def get_recent_connections(self):
        return get_recent_connections(limit=self.recent_limit)

    def update_recent_connection(self, ip):
        add_recent_connection(ip)

    def update_workstation(self, ip, os_name, workstation=None):
        add_to_workstation_map(ip, os_name, workstation)

    def remove_workstation(self, ip):
        remove_from_workstation_map(ip)

    def clear_history(self):
        clear_recent_connections()

    def get_workstations(self):
        return get_workstation_map()