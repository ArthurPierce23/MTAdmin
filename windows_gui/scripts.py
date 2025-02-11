import os
import json
import shutil
import subprocess
import platform
import sys
import logging
from pathlib import Path
from typing import List, Dict, Optional
# Убираем привязку к GUI – ошибки будем сообщать через исключения,
# а GUI уже сможет отобразить их как нужно.
# Если нужно, импорт можно добавить в GUI-слое.
# from PySide6.QtWidgets import QMessageBox, QWidget

logger = logging.getLogger(__name__)


def get_project_root() -> Path:
    """
    Определяет корневую папку проекта.

    Если приложение скомпилировано (sys.frozen True), то корневая папка — это папка,
    где находится исполняемый файл (.exe). Иначе — родительская папка относительно этого файла.
    """
    if getattr(sys, 'frozen', False):
        return Path(sys.executable).parent
    else:
        return Path(__file__).resolve().parent.parent


class ScriptsManager:
    def __init__(self, hostname: str):
        # Папка для скриптов: project_root/scripts
        self.project_root = get_project_root()
        self.scripts_dir = self.project_root / "scripts"
        self.meta_path = self.scripts_dir / ".metadata"
        self.supported_ext = {'.ps1', '.bat', '.cmd', '.vbs', '.sh'}
        self._init_structure()

    def _init_structure(self):
        self.scripts_dir.mkdir(exist_ok=True, parents=True)
        if not self.meta_path.exists():
            self.meta_path.write_text("{}", encoding='utf-8')

    def _get_metadata(self) -> Dict:
        try:
            if self.meta_path.exists():
                return json.loads(self.meta_path.read_text(encoding='utf-8'))
            return {}
        except json.JSONDecodeError:
            logger.error("Ошибка чтения метаданных – повреждён JSON. Восстанавливаем пустую структуру.")
            return {}

    def _save_metadata(self, data: Dict):
        self.meta_path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding='utf-8')

    def get_scripts(self) -> List[Dict]:
        """
        Возвращает список скриптов из папки и объединяет их с метаданными (например, тегами).
        Каждый элемент списка — словарь с информацией:
            - "name": имя файла без расширения,
            - "full_name": имя файла с расширением,
            - "path": абсолютный путь к файлу,
            - "type": тип скрипта (расширение без точки, верхним регистром),
            - "tags": список тегов (если заданы),
            - "created": время создания файла (timestamp).
        """
        metadata = self._get_metadata()
        scripts = []

        for f in self.scripts_dir.glob("*"):
            if f.suffix.lower() in self.supported_ext and f.is_file():
                script_name = f.stem
                scripts.append({
                    "name": script_name,
                    "full_name": f.name,
                    "path": str(f.resolve()),
                    "type": f.suffix[1:].upper(),
                    "tags": metadata.get(f.name, {}).get("tags", []),
                    "created": f.stat().st_ctime
                })
        return sorted(scripts, key=lambda x: x['name'].lower())

    def update_tags(self, filename: str, tags: List[str]):
        """
        Обновляет или задаёт теги для скрипта с именем filename.
        """
        metadata = self._get_metadata()
        cleaned_tags = [t.strip().lower() for t in tags if t.strip()]
        metadata.setdefault(filename, {})["tags"] = cleaned_tags
        self._save_metadata(metadata)
        logger.info(f"Теги для {filename} обновлены: {cleaned_tags}")

    def add_script(self, source_path: str, tags: Optional[List[str]] = None) -> str:
        """
        Копирует выбранный скрипт в папку /scripts, устанавливает метаданные (теги)
        и возвращает путь к скопированному файлу.

        :raises FileNotFoundError: если исходный файл не найден.
        :raises ValueError: если тип файла не поддерживается.
        :raises FileExistsError: если файл с таким именем уже существует.
        """
        src = Path(source_path)
        if not src.is_file():
            raise FileNotFoundError("Файл не найден")

        if src.suffix.lower() not in self.supported_ext:
            raise ValueError("Неподдерживаемый тип файла")

        dest = self.scripts_dir / src.name
        if dest.exists():
            raise FileExistsError("Файл уже существует")

        # Копирование файла
        shutil.copy(src, dest)
        # Обновление метаданных (тегов)
        self.update_tags(dest.name, tags or [])
        logger.info(f"Скрипт скопирован из {src.resolve()} в {dest.resolve()}")
        return str(dest)

    def rename_script(self, old_filename: str, new_filename: str) -> bool:
        """
        Переименовывает скрипт и обновляет метаданные.

        :raises FileNotFoundError: если исходный файл не найден.
        :raises FileExistsError: если файл с новым именем уже существует.
        """
        old_path = self.scripts_dir / old_filename
        new_path = self.scripts_dir / new_filename

        if not old_path.exists():
            raise FileNotFoundError("Исходный файл не найден")
        if new_path.exists():
            raise FileExistsError("Файл с новым именем уже существует")

        old_path.rename(new_path)
        logger.info(f"Файл {old_filename} переименован в {new_filename}")

        metadata = self._get_metadata()
        if old_filename in metadata:
            metadata[new_filename] = metadata.pop(old_filename)
            self._save_metadata(metadata)
        return True

    def delete_script(self, filename: str) -> bool:
        """
        Удаляет скрипт и его метаданные.

        :raises Exception: если удаление не удалось.
        """
        script_path = self.scripts_dir / filename
        if script_path.exists():
            script_path.unlink()
            logger.info(f"Файл {filename} удалён")
            metadata = self._get_metadata()
            if filename in metadata:
                del metadata[filename]
                self._save_metadata(metadata)
            return True
        else:
            raise FileNotFoundError("Файл для удаления не найден")

    def execute_script(self, script_path: str) -> None:
        """
        Выполняет скрипт в зависимости от его расширения.
        На Windows скрипты запускаются с повышенными привилегиями (от имени администратора)
        с помощью PowerShell и параметра -Verb runas.
        Для Linux/Unix – bash (если это .sh) или прямая попытка выполнения, если файл исполняемый.

        :raises FileNotFoundError: если скрипт не найден.
        :raises RuntimeError: если выполнение скрипта невозможно.
        """
        script_file = Path(script_path)
        if not script_file.exists():
            raise FileNotFoundError("Скрипт не найден")

        ext = script_file.suffix.lower()
        system = platform.system()

        try:
            if system == 'Windows':
                if ext == '.ps1':
                    cmd = (
                        f'powershell -Command "Start-Process powershell '
                        f'-ArgumentList \'-ExecutionPolicy Bypass -File \"{script_path}\"\' '
                        f'-Verb runas"'
                    )
                else:
                    cmd = f'powershell -Command "Start-Process \'{script_path}\' -Verb runas"'
                logger.info(f"Запуск скрипта Windows: {cmd}")
                subprocess.Popen(cmd, shell=True)
            else:
                # Для Linux/Unix
                if ext == '.sh':
                    cmd = ["bash", script_path]
                else:
                    # Проверяем, что файл является исполняемым
                    if os.access(script_path, os.X_OK):
                        cmd = [script_path]
                    else:
                        raise RuntimeError("Файл не является исполняемым")
                logger.info(f"Запуск скрипта Unix: {' '.join(cmd)}")
                subprocess.Popen(cmd, start_new_session=True)
        except Exception as e:
            logger.error(f"Ошибка выполнения скрипта: {e}")
            raise RuntimeError(f"Ошибка выполнения скрипта: {e}") from e
