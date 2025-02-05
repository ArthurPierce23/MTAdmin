import winrm
import os
import logging

# Настройка логирования
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

class PSSessionManager:
    def __init__(self, hostname, use_ssl=True, port=5986):
        self.hostname = hostname
        self.port = port
        self.use_ssl = use_ssl
        self.username = None  # CredSSP будет использовать текущего пользователя
        self.session = None

    def connect(self):
        """Устанавливает соединение с удалённым компьютером через CredSSP."""
        try:
            endpoint = f'{"https" if self.use_ssl else "http"}://{self.hostname}:{self.port}/wsman'

            self.session = winrm.Session(
                endpoint,
                auth=(self.username, ''),  # Используем текущего пользователя
                transport='credssp',  # CredSSP
                server_cert_validation='ignore'  # Отключаем проверку сертификата
            )

            logger.info(f"Connected to {self.hostname} on port {self.port} using CredSSP.")
        except Exception as e:
            logger.error(f"Failed to connect to {self.hostname}: {e}")
            raise

    def execute_script(self, script: str):
        """Выполняет PowerShell-скрипт на удалённом компьютере."""
        if not self.session:
            self.connect()

        try:
            result = self.session.run_ps(script)
            if result.status_code != 0:
                error_msgs = result.std_err.decode('utf-8')
                logger.error(f"Errors occurred while executing script: {error_msgs}")
            else:
                logger.info("Script executed successfully")
            return result.std_out.decode('utf-8')
        except Exception as e:
            logger.error(f"Failed to execute script: {e}")
            raise

    def close(self):
        """Закрывает соединение с удалённым компьютером."""
        if self.session:
            self.session = None
            logger.info(f"Connection to {self.hostname} closed")

    def __enter__(self):
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
