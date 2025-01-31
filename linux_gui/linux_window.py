from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel

class LinuxWindow(QWidget):
    def __init__(self, ip, os_name):
        super().__init__()
        self.ip = ip
        self.os_name = os_name
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        title = QLabel(f"Linux Management - {self.ip}")
        layout.addWidget(title)
        # Дополнительные элементы управления для Linux