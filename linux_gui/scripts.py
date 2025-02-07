# linux_gui/scripts.py

import json
import shutil
from pathlib import Path
import logging

from linux_gui.session_manager import SessionManager

logger = logging.getLogger(__name__)


class ScriptsManager:
    """
    Менеджер для работы с библиотекой .sh скриптов.

    Скрипты хранятся в папке 'scripts' в корне проекта.
    Метаданные (например, теги) хранятся в файле scripts_metadata.json.
    """

    def __init__(self, hostname: str):
        self.hostname = hostname
        # Определяем корневую директорию проекта как родительскую директорию текущего файла
        self.project_root = Path(__file__).resolve().parent.parent
        self.scripts_dir = self.project_root / "scripts"
        self.scripts_dir.mkdir(exist_ok=True)
        self.metadata_file = self.scripts_dir / "scripts_metadata.json"
        self.metadata = self._load_metadata()

    def _load_metadata(self) -> dict:
        if self.metadata_file.exists():
            try:
                with self.metadata_file.open("r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Ошибка загрузки метаданных скриптов: {e}")
                return {}
        else:
            return {}

    def _save_metadata(self):
        try:
            with self.metadata_file.open("w", encoding="utf-8") as f:
                json.dump(self.metadata, f, ensure_ascii=False, indent=4)
        except Exception as e:
            logger.error(f"Ошибка сохранения метаданных скриптов: {e}")

    def get_scripts(self) -> list:
        """
        Возвращает список скриптов в виде списка словарей.
        Каждый словарь содержит:
            - name: имя скрипта (без расширения)
            - full_name: имя файла (с расширением)
            - path: абсолютный путь к файлу
            - tags: список тегов (если есть)
        """
        scripts = []
        for file in self.scripts_dir.glob("*.sh"):
            script_info = {
                "full_name": file.name,
                "name": file.stem,
                "path": str(file.resolve()),
                "tags": self.metadata.get(file.name, {}).get("tags", [])
            }
            scripts.append(script_info)
        return scripts

    def add_script(self, file_path: str, tags: list):
        """
        Добавляет скрипт в библиотеку, копируя его в scripts_dir.
        Обновляет метаданные с тегами.
        """
        source = Path(file_path)
        if not source.exists() or source.suffix.lower() != ".sh":
            raise Exception("Выбранный файл не является .sh скриптом.")
        destination = self.scripts_dir / source.name
        if destination.exists():
            raise Exception("Скрипт с таким именем уже существует.")
        shutil.copy(source, destination)
        # Обновляем метаданные
        self.metadata[destination.name] = {"tags": tags}
        self._save_metadata()

    def rename_script(self, old_full_name: str, new_full_name: str) -> bool:
        """
        Переименовывает скрипт.
        """
        old_path = self.scripts_dir / old_full_name
        new_path = self.scripts_dir / new_full_name
        if not old_path.exists():
            raise Exception("Исходный скрипт не найден.")
        if new_path.exists():
            raise Exception("Файл с новым именем уже существует.")
        old_path.rename(new_path)
        # Обновляем метаданные
        if old_full_name in self.metadata:
            self.metadata[new_full_name] = self.metadata.pop(old_full_name)
            self._save_metadata()
        return True

    def update_tags(self, full_name: str, new_tags: list):
        """
        Обновляет теги для указанного скрипта.
        """
        if full_name not in self.metadata:
            self.metadata[full_name] = {}
        self.metadata[full_name]["tags"] = new_tags
        self._save_metadata()

    def delete_script(self, full_name: str):
        """
        Удаляет скрипт и его метаданные.
        """
        file_path = self.scripts_dir / full_name
        if file_path.exists():
            file_path.unlink()
        if full_name in self.metadata:
            del self.metadata[full_name]
            self._save_metadata()

    def execute_script(self, file_to_execute: str):
        """
        Выполняет скрипт на удалённом хосте в интерактивном режиме.

        Считывает содержимое файла, устанавливает интерактивный канал (shell)
        через SSH с запросом pty, отправляет содержимое скрипта и открывает
        окно-терминал с полноценной эмуляцией на базе xterm.js.
        """
        session = SessionManager.get_instance(self.hostname, "", "").get_client()
        script_path = Path(file_to_execute)
        if not script_path.exists():
            raise Exception("Скрипт не найден.")
        with script_path.open("r", encoding="utf-8") as f:
            script_content = f.read()

        # Запрашиваем интерактивный канал с pty.
        channel = session.invoke_shell(term='xterm')
        # Отправляем содержимое скрипта (и завершающий перевод строки).
        channel.send(script_content + "\n")

        # Импортируем окно-терминал (на базе xterm.js) и открываем его модально.
        from linux_gui.gui.terminal_window import TerminalWindow
        terminal = TerminalWindow(channel)
        terminal.exec()  # ждем закрытия окна

        # Можно, при необходимости, собрать остаточные данные.
        output = ""
        while channel.recv_ready():
            output += channel.recv(1024).decode("utf-8", errors="ignore")
        return output
