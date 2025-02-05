from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel

class LinuxWindow(QWidget):
    def __init__(self, ip):
        super().__init__()
        self.setWindowTitle(f"Linux: {ip}")
        self.setGeometry(300, 300, 400, 300)

        layout = QVBoxLayout()
        layout.addWidget(QLabel(f"IP-адрес: {ip}"))
        layout.addWidget(QLabel("Операционная система: Linux/Unix"))

        self.setLayout(layout)
