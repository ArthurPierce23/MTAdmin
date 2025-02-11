import paramiko
import logging
from typing import Optional
import time

logger = logging.getLogger(__name__)


class SessionManager:
    _instance: Optional["SessionManager"] = None

    def __init__(self, hostname: str, username: str, password: str,
                 root_username: Optional[str] = None, root_password: Optional[str] = None) -> None:
        """
        Инициализирует SessionManager для работы с SSH-соединением.

        :param hostname: Имя или IP-адрес удалённого хоста.
        :param username: Имя пользователя для подключения.
        :param password: Пароль пользователя.
        :param root_username: (Опционально) Имя пользователя для получения root-доступа.
        :param root_password: (Опционально) Пароль для получения root-доступа.
        """
        self.hostname: str = hostname
        self.username: str = username
        self.password: str = password
        self.root_username: Optional[str] = root_username
        self.root_password: Optional[str] = root_password
        self.client: Optional[paramiko.SSHClient] = None
        self.root_session: Optional[paramiko.SSHClient] = None  # Будет хранить сессию с правами root

    @classmethod
    def get_instance(cls, hostname: str, username: str, password: str,
                     root_username: Optional[str] = None, root_password: Optional[str] = None) -> "SessionManager":
        """
        Возвращает синглтон-экземпляр SessionManager.
        Если экземпляр ещё не создан, создаёт новый.

        :return: Экземпляр SessionManager.
        """
        if cls._instance is None:
            cls._instance = cls(hostname, username, password, root_username, root_password)
        return cls._instance

    def connect(self) -> paramiko.SSHClient:
        """
        Устанавливает SSH-соединение с удалённым хостом, если оно ещё не установлено.
        При наличии root-учётных данных пытается получить root-доступ.

        :return: Экземпляр paramiko.SSHClient.
        :raises Exception: При ошибке подключения.
        """
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

            if self.root_username and self.root_password:
                logger.info("Обнаружены root-учётные данные, пробуем получить root-доступ...")
                self.enable_root_session()
            else:
                logger.warning("Root-учётные данные НЕ переданы, работаем без root-доступа.")

            return self.client
        except Exception as e:
            logger.error(f"Не удалось установить SSH-соединение: {e}")
            self.client = None
            raise e

    def enable_root_session(self) -> None:
        """
        Пытается получить root-доступ через `sudo -S` и сохраняет сессию в self.root_session.
        Если root-доступ получить не удалось, self.root_session устанавливается в None.
        """
        try:
            if not self.root_password:
                logger.error("❌ Root-пароль не передан, отменяем запрос root-доступа!")
                return

            # Проверяем, можно ли выполнить sudo без пароля
            stdin, stdout, stderr = self.client.exec_command("sudo -n id -u")
            output = stdout.read().decode().strip()
            error = stderr.read().decode().strip()

            if "0" in output:
                logger.info("✅ Root-доступ уже активен!")
                self.root_session = self.client
                return

            if "password is required" in error.lower():
                logger.info("🔑 Требуется ввод root-пароля...")

            # Пробуем передать root-пароль
            full_command = f"echo '{self.root_password}' | sudo -S id -u"
            stdin, stdout, stderr = self.client.exec_command(full_command)
            output = stdout.read().decode().strip()
            error = stderr.read().decode().strip()

            if "0" in output:
                logger.info("✅ Root-доступ успешно получен!")
                self.root_session = self.client
            else:
                logger.error(f"❌ Root-доступ не получен! Ответ: {output or error}")
                self.root_session = None
        except Exception as e:
            logger.error(f"❌ Ошибка при попытке получить root-доступ: {e}")
            self.root_session = None

    def has_root_access(self) -> bool:
        """
        Проверяет, есть ли у текущей сессии root-доступ.
        Выполняет команду для проверки прав с использованием sudo.

        :return: True, если root-доступ имеется, иначе False.
        """
        if not self.client or not self.root_password:
            logger.error("❌ Отсутствует SSH-сессия или root-пароль не передан!")
            return False

        try:
            # Выполняем команду для проверки root-доступа
            stdin, stdout, stderr = self.client.exec_command("sudo -n id -u")
            output = stdout.read().decode().strip()
            return "0" in output  # Если ID равен 0, значит есть root-доступ
        except Exception as e:
            logger.error(f"Ошибка проверки root-доступа: {e}")
            return False

    def execute(self, command: str, use_root: bool = False) -> str:
        """
        Выполняет указанную команду через SSH.
        Если use_root True и root-доступ имеется, команда выполняется через sudo.

        :param command: Команда для выполнения.
        :param use_root: Флаг, указывающий на необходимость выполнения с root-доступом.
        :return: Результат выполнения команды или сообщение об ошибке.
        """
        try:
            if use_root and self.root_session and self.has_root_access():
                full_command = f"echo '{self.root_password}' | sudo -S {command}"
            else:
                full_command = command

            stdin, stdout, stderr = self.client.exec_command(full_command)
            output = stdout.read().decode().strip()
            error = stderr.read().decode().strip()

            if error:
                logger.error(f"❌ Ошибка выполнения команды '{command}': {error}")
                return error
            return output if output else "Ошибка"
        except Exception as e:
            logger.error(f"❌ Ошибка выполнения команды '{command}': {e}")
            return "Ошибка"

    def get_client(self) -> paramiko.SSHClient:
        """
        Возвращает текущий SSH-клиент.
        Если соединение ещё не установлено, выполняет подключение.

        :return: Экземпляр paramiko.SSHClient.
        """
        if self.client is None:
            self.connect()
        return self.client

    def close_session(self) -> None:
        """
        Закрывает SSH-сессию и сбрасывает синглтон-экземпляр SessionManager.
        """
        if self.client:
            self.client.close()
            self.client = None
            self.root_session = None
            SessionManager._instance = None
