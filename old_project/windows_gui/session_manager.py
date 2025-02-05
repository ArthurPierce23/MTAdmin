from pypsrp.powershell import RunspacePool
from pypsrp.wsman import WSMan
import logging

logger = logging.getLogger(__name__)

class PowerShellSessionManager:
    def __init__(self, ip, username=None, password=None):
        self.ip = ip
        self.username = username
        self.password = password
        self.session = None

    def connect(self):
        try:
            # Если логин и пароль не заданы, они не будут переданы в WSMan,
            # что позволит использовать текущие учетные данные Windows.
            wsman_params = {
                'server': self.ip,
                'ssl': False,
                'auth': 'negotiate',  # Используем negotiate для использования текущей сессии
                'connection_timeout': 10
            }
            if self.username and self.password:
                wsman_params['username'] = self.username
                wsman_params['password'] = self.password

            wsman = WSMan(**wsman_params)
            self.session = RunspacePool(wsman)
            self.session.open()
            return True
        except Exception as e:
            logger.error(f"Connection error: {str(e)}")
            self.session = None
            return False

    def is_connected(self):
        return self.session is not None

    def close(self):
        if self.session:
            self.session.close()
            self.session = None
