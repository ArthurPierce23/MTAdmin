import sys
from PySide6.QtWidgets import QApplication
from main_gui.gui.main_window import MainWindow  # Импортируйте ваш основной класс окна

if __name__ == "__main__":
    app = QApplication(sys.argv)  # Создаем экземпляр приложения
    window = MainWindow()          # Создаем экземпляр вашего главного окна
    window.show()                  # Показываем главное окно
    sys.exit(app.exec())           # Запускаем главный цикл приложения
