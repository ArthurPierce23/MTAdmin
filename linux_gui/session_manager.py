import paramiko
import logging

logger = logging.getLogger(__name__)

class SessionManager:
    _instance = None

    def __init__(self, hostname: str, username: str, password: str):
        self.hostname = hostname
        self.username = username
        self.password = password
        self.client = None

    @classmethod
    def get_instance(cls, hostname: str, username: str, password: str):
        if cls._instance is None:
            cls._instance = cls(hostname, username, password)
        return cls._instance

    def connect(self):
        if self.client is not None:
            return self.client

        try:
            logger.info(f"Устанавливаем SSH-соединение с {self.hostname} (пользователь: {self.username})")
            self.client = paramiko.SSHClient()
            self.client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            self.client.connect(
                hostname=self.hostname,
                username=self.username,
                password=self.password,
                look_for_keys=False,
                allow_agent=False
            )
            logger.info("SSH-соединение установлено успешно.")
            return self.client
        except Exception as e:
            logger.error(f"Не удалось установить SSH-соединение: {e}")
            self.client = None
            raise e

    def get_client(self):
        if self.client is None:
            return self.connect()
        return self.client

    def close_session(self):
        """Закрывает SSH-сессию."""
        if self.client is not None:
            logger.info(f"Закрываем SSH-сессию для {self.hostname}")
            self.client.close()
            self.client = None
            SessionManager._instance = None  # Сбрасываем Singleton
