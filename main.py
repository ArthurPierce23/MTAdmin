import sys
from PySide6.QtWidgets import QApplication
from main_gui.main_window import MainWindow
from database.db_manager import init_db

def main():
    """Запуск приложения."""
    init_db()  # Инициализация базы данных
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
