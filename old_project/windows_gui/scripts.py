import os
import shutil
from pathlib import Path

from pypsrp.powershell import PowerShell

class ScriptManager:
    def __init__(self, scripts_dir="windows_gui/scripts"):
        self.scripts_dir = Path(scripts_dir)
        self.scripts_dir.mkdir(parents=True, exist_ok=True)
        self.scripts = []
        self.load_scripts()

    def load_scripts(self):
        self.scripts = []
        for file in self.scripts_dir.glob("*.ps1"):
            self.scripts.append({
                "name": file.stem,
                "path": str(file.resolve())
            })

    def add_script(self, source_path, name):
        dest_path = self.scripts_dir / f"{name}.ps1"
        if dest_path.exists():
            raise FileExistsError(f"Скрипт '{name}' уже существует")
        shutil.copy(source_path, dest_path)
        self.load_scripts()

    def delete_script(self, name):
        script = next((s for s in self.scripts if s["name"] == name), None)
        if script:
            os.remove(script["path"])
            self.load_scripts()

    def get_scripts(self):
        return self.scripts

    def execute_script(self, name, session):
        """
        Выполняет скрипт с указанным именем на удалённом ПК с использованием
        переданной постоянной PowerShell-сессии.
        :param name: имя скрипта (без расширения .ps1)
        :param session: объект RunspacePool из PowerShellSessionManager
        """
        script = next((s for s in self.scripts if s["name"] == name), None)
        if script:
            self.run_powershell_script(script["path"], session)
        else:
            raise FileNotFoundError(f"Скрипт '{name}' не найден")

    def rename_script(self, old_name, new_name):
        old_path = self.scripts_dir / f"{old_name}.ps1"
        new_path = self.scripts_dir / f"{new_name}.ps1"

        if not old_path.exists():
            raise FileNotFoundError(f"Скрипт '{old_name}' не найден")

        if new_path.exists():
            raise FileExistsError(f"Скрипт '{new_name}' уже существует")

        os.rename(old_path, new_path)
        self.load_scripts()

    @staticmethod
    def run_powershell_script(script_path, session):
        """
        Выполняет PowerShell-скрипт, расположенный по script_path, через постоянную сессию.
        :param script_path: путь к файлу скрипта (.ps1)
        :param session: объект RunspacePool
        """
        try:
            # Читаем содержимое скрипта из файла
            with open(script_path, "r", encoding="utf-8") as f:
                script_content = f.read()

            # Создаем объект PowerShell, используя переданную сессию
            ps = PowerShell(runspace_pool=session)
            ps.add_script(script_content)
            ps.invoke()

            # Если были ошибки, собираем их в строку
            if ps.had_errors:
                # В зависимости от версии pypsrp может потребоваться корректное обращение к потоку ошибок.
                # Здесь используем ps.streams.error, если он доступен.
                try:
                    error_output = "\n".join(str(e) for e in ps.streams.error)
                except AttributeError:
                    error_output = "Не удалось получить подробности ошибок"
                raise Exception(f"Ошибка выполнения скрипта:\n{error_output}")

        except Exception as e:
            raise Exception(f"Ошибка запуска PowerShell: {str(e)}")
