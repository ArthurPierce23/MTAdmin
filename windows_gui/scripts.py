import os
import shutil
from pathlib import Path
import subprocess

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

    def execute_script(self, name, ip=None):  # ip теперь необязателен
        script = next((s for s in self.scripts if s["name"] == name), None)
        if script:
            self.run_powershell_script(script["path"])

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
    def run_powershell_script(script_path):
        try:
            command = f'powershell -ExecutionPolicy Bypass -NoProfile -File "{script_path}"'
            result = subprocess.run(
                ["powershell", "-ExecutionPolicy", "Bypass", "-NoProfile", "-File", script_path],
                shell=True,
                capture_output=True,
                text=True
            )

            if result.returncode != 0:
                raise Exception(f"Ошибка выполнения скрипта:\n{result.stderr}")

        except Exception as e:
            raise Exception(f"Ошибка запуска PowerShell: {str(e)}")