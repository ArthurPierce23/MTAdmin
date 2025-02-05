# test_system_info_block.py

import sys
from PySide6.QtWidgets import QApplication
from windows_gui.gui.system_info_block import SystemInfoBlock

if __name__ == "__main__":
    app = QApplication(sys.argv)

    # Замените "MyPC" на нужное имя хоста
    hostname = "VLZ-RG-001"

    # Создаем экземпляр блока информации о системе
    system_info_block = SystemInfoBlock(hostname)
    system_info_block.setWindowTitle("Тестовый блок информации о системе")
    system_info_block.resize(400, 300)
    system_info_block.show()

    sys.exit(app.exec())
