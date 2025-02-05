import os
import json
import shutil
import subprocess
import platform
from pathlib import Path
from typing import List, Dict, Optional
from PySide6.QtWidgets import QMessageBox, QWidget

class ScriptsManager:
    def __init__(self, hostname: str):
        # Папка для скриптов: project_root/scripts
        self.scripts_dir = Path(__file__).parent.parent / "scripts"
        self.meta_path = self.scripts_dir / ".metadata"
        self.supported_ext = {'.ps1', '.bat', '.cmd', '.vbs', '.sh'}
        self._init_structure()

    def _init_structure(self):
        self.scripts_dir.mkdir(exist_ok=True, parents=True)
        if not self.meta_path.exists():
            self.meta_path.write_text("{}", encoding='utf-8')

    def _get_metadata(self) -> Dict:
        try:
            return json.loads(self.meta_path.read_text(encoding='utf-8')) if self.meta_path.exists() else {}
        except json.JSONDecodeError:
            return {}

    def _save_metadata(self, data: Dict):
        self.meta_path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding='utf-8')

    def get_scripts(self) -> List[Dict]:
        """
        Возвращает список скриптов из папки и объединяет их с метаданными (например, тегами).
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

    def update_tags(self, filename: str, tags: list):
        """
        Обновляет или задаёт теги для скрипта с именем filename.
        """
        metadata = self._get_metadata()
        cleaned_tags = [t.strip().lower() for t in tags if t.strip()]
        metadata.setdefault(filename, {})["tags"] = cleaned_tags
        self._save_metadata(metadata)

    def add_script(self, source_path: str, tags: list = None) -> Optional[str]:
        """
        Копирует выбранный скрипт в папку /scripts, устанавливает метаданные (теги)
        и возвращает путь к скопированному файлу.
        """
        try:
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
            print(f"Копируем файл из {src.resolve()} в {dest.resolve()}")
            return str(dest)

        except Exception as e:
            QMessageBox.critical(QWidget(), "Ошибка", f"Ошибка добавления: {str(e)}")
            return None

    def rename_script(self, old_filename: str, new_filename: str) -> bool:
        """
        Переименовывает скрипт и обновляет метаданные.
        """
        try:
            old_path = self.scripts_dir / old_filename
            new_path = self.scripts_dir / new_filename

            if not old_path.exists():
                raise FileNotFoundError("Исходный файл не найден")
            if new_path.exists():
                raise FileExistsError("Файл с новым именем уже существует")

            old_path.rename(new_path)

            metadata = self._get_metadata()
            if old_filename in metadata:
                metadata[new_filename] = metadata.pop(old_filename)
                self._save_metadata(metadata)

            return True
        except Exception as e:
            QMessageBox.critical(QWidget(), "Ошибка", f"Ошибка переименования: {str(e)}")
            return False

    def delete_script(self, filename: str):
        """
        Удаляет скрипт и его метаданные.
        """
        try:
            script_path = self.scripts_dir / filename
            if script_path.exists():
                script_path.unlink()
                metadata = self._get_metadata()
                if filename in metadata:
                    del metadata[filename]
                    self._save_metadata(metadata)
                return True
            return False
        except Exception as e:
            QMessageBox.critical(QWidget(), "Ошибка", f"Ошибка удаления: {str(e)}")
            return False

    def execute_script(self, script_path: str):
        """
        Выполняет скрипт в зависимости от его расширения.
        На Windows скрипты запускаются с повышенными привилегиями (от имени администратора)
        с помощью PowerShell и параметра -Verb runas.
        Для Linux/Unix – bash (если это .sh).
        """
        try:
            script_file = Path(script_path)
            if not script_file.exists():
                raise FileNotFoundError("Скрипт не найден")

            ext = script_file.suffix.lower()
            if platform.system() != 'Windows' and ext in ('.ps1', '.bat', '.cmd', '.vbs'):
                raise RuntimeError("Данный тип скриптов поддерживается только в Windows")

            if platform.system() == 'Windows':
                # Формируем команду через PowerShell для запуска от имени администратора
                # Обратите внимание: если это PowerShell-скрипт, можно добавить параметр -File
                if ext == '.ps1':
                    # Запуск PowerShell-скрипта с параметром -File
                    cmd = f'powershell -Command "Start-Process powershell -ArgumentList \'-ExecutionPolicy Bypass -File \"{script_path}\"\' -Verb runas"'
                else:
                    # Для .bat, .cmd, .vbs, .sh и прочих – запускаем сам файл
                    cmd = f'powershell -Command "Start-Process \'{script_path}\' -Verb runas"'
                subprocess.Popen(cmd, shell=True)
            else:
                # Для Linux/Unix – если это .sh, запускаем через bash
                if ext == '.sh':
                    cmd = ["bash", script_path]
                    subprocess.Popen(cmd, start_new_session=True)
                else:
                    # Для других типов скриптов на Unix, можно добавить свою логику
                    subprocess.Popen([script_path], start_new_session=True)

        except Exception as e:
            from PySide6.QtWidgets import QMessageBox, QWidget
            QMessageBox.critical(QWidget(), "Ошибка", f"Ошибка выполнения: {str(e)}")
            raise
