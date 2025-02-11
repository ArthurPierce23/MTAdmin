import sys
from PySide6.QtWidgets import QApplication
from main_gui.gui.main_window import MainWindow

# Устанавливаем фиксированную версию
__version__ = "0.2"

if __name__ == "__main__":
    print(f"Запуск MTAdmin, версия: {__version__}")  # Логируем версию
    app = QApplication(sys.argv)
    window = MainWindow()
    window.setWindowTitle(f"MTAdmin v{__version__}")  # Устанавливаем версию в заголовок окна
    window.show()
    sys.exit(app.exec())
