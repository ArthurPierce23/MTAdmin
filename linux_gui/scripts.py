import json
import shutil
import sys
import logging
from pathlib import Path
from typing import List, Dict, Any

import pyperclip  # Для копирования в буфер обмена

logger = logging.getLogger(__name__)


def get_project_root() -> Path:
    """
    Определяет корневую папку проекта.

    Если приложение скомпилировано (sys.frozen True), то корневая папка — это папка, где находится .exe.
    Иначе — родительская папка относительно этого файла.
    """
    if getattr(sys, 'frozen', False):
        return Path(sys.executable).parent
    else:
        # Предполагается, что этот файл находится в подпапке (например, /some_folder/),
        # а корень проекта — на один уровень выше.
        return Path(__file__).resolve().parent.parent


class ScriptsManager:
    """
    Менеджер для работы с библиотекой .sh скриптов.

    Скрипты и файл метаданных (scripts_metadata.json) хранятся в папке 'scripts',
    которая находится в корне проекта (как в режиме разработки, так и в скомпилированном .exe).
    """

    def __init__(self, hostname: str):
        self.hostname = hostname
        self.project_root: Path = get_project_root()
        # Папка scripts всегда находится в корне проекта.
        self.scripts_dir: Path = self.project_root / "scripts"
        self.scripts_dir.mkdir(exist_ok=True)
        self.metadata_file: Path = self.scripts_dir / "scripts_metadata.json"
        self.metadata: Dict[str, Any] = self._load_metadata()

    def _load_metadata(self) -> Dict[str, Any]:
        if self.metadata_file.exists():
            try:
                with self.metadata_file.open("r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Ошибка загрузки метаданных скриптов: {e}")
                return {}
        else:
            return {}

    def _save_metadata(self) -> None:
        try:
            with self.metadata_file.open("w", encoding="utf-8") as f:
                json.dump(self.metadata, f, ensure_ascii=False, indent=4)
        except Exception as e:
            logger.error(f"Ошибка сохранения метаданных скриптов: {e}")

    def get_scripts(self) -> List[Dict[str, Any]]:
        """
        Возвращает список скриптов в виде списка словарей.
        Каждый словарь содержит:
            - full_name: имя файла (с расширением)
            - name: имя файла без расширения
            - path: полный путь к файлу
            - tags: список тегов (из метаданных)
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

    def add_script(self, file_path: str, tags: List[str]) -> None:
        """
        Добавляет скрипт в библиотеку, копируя его в scripts_dir.
        Если файл не является .sh или с таким именем уже существует — выбрасывается исключение.
        """
        source = Path(file_path)
        if not source.exists() or source.suffix.lower() != ".sh":
            raise Exception("Выбранный файл не является .sh скриптом.")
        destination = self.scripts_dir / source.name
        if destination.exists():
            raise Exception("Скрипт с таким именем уже существует.")
        shutil.copy(source, destination)
        self.metadata[destination.name] = {"tags": tags}
        self._save_metadata()

    def rename_script(self, old_full_name: str, new_full_name: str) -> bool:
        """
        Переименовывает скрипт.
        Если исходный файл не найден или файл с новым именем уже существует — выбрасывается исключение.
        """
        old_path = self.scripts_dir / old_full_name
        new_path = self.scripts_dir / new_full_name
        if not old_path.exists():
            raise Exception("Исходный скрипт не найден.")
        if new_path.exists():
            raise Exception("Файл с новым именем уже существует.")
        old_path.rename(new_path)
        if old_full_name in self.metadata:
            self.metadata[new_full_name] = self.metadata.pop(old_full_name)
            self._save_metadata()
        return True

    def update_tags(self, full_name: str, new_tags: List[str]) -> None:
        """
        Обновляет теги для указанного скрипта.
        """
        if full_name not in self.metadata:
            self.metadata[full_name] = {}
        self.metadata[full_name]["tags"] = new_tags
        self._save_metadata()

    def delete_script(self, full_name: str) -> None:
        """
        Удаляет скрипт и его метаданные.
        """
        file_path = self.scripts_dir / full_name
        if file_path.exists():
            file_path.unlink()
        if full_name in self.metadata:
            del self.metadata[full_name]
            self._save_metadata()

    def copy_script_content(self, full_name: str) -> None:
        """
        Копирует содержимое указанного скрипта в буфер обмена.
        """
        script_path = self.scripts_dir / full_name
        if not script_path.exists():
            raise Exception("Скрипт не найден.")
        with script_path.open("r", encoding="utf-8") as f:
            script_content = f.read()
        pyperclip.copy(script_content)
        logger.info(f"Скрипт '{full_name}' скопирован в буфер обмена.")

    def edit_script(self, full_name: str) -> None:
        """
        Открывает скрипт в редакторе по умолчанию.

        Для Windows используется os.startfile, для macOS – команда 'open',
        для Linux – 'xdg-open'. Ошибки логируются и пробрасываются.
        """
        script_path = self.scripts_dir / full_name
        if not script_path.exists():
            raise Exception("Скрипт не найден.")
        try:
            if sys.platform.startswith("win"):
                import os
                os.startfile(str(script_path))
            elif sys.platform.startswith("darwin"):
                from subprocess import Popen
                Popen(["open", str(script_path)])
            else:
                # Предполагаем, что на Linux доступна команда xdg-open
                from subprocess import Popen
                Popen(["xdg-open", str(script_path)])
            logger.info(f"Скрипт '{full_name}' открыт в редакторе по умолчанию.")
        except Exception as e:
            logger.error(f"Ошибка при открытии скрипта: {e}")
            raise e
