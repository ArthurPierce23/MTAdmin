from PySide6.QtWidgets import QWidget, QGridLayout, QPushButton, QGroupBox, QVBoxLayout

class CommandsBlock(QWidget):
    def __init__(self, hostname: str, parent: QWidget = None):
        super().__init__(parent)
        self.hostname = hostname
        group_box = QGroupBox("Команды")
        grid_layout = QGridLayout()

        # Пример набора кнопок – измените или добавьте кнопки по необходимости.
        buttons = [
            ("winrs", self.dummy_action),
            ("Shadow RDP", self.dummy_action),
            ("C:\\", self.dummy_action),
            ("Команда 4", self.dummy_action),
            ("Команда 5", self.dummy_action),
            ("Команда 6", self.dummy_action),
            ("Команда 7", self.dummy_action),
            ("Команда 8", self.dummy_action),
        ]

        cols = 4  # Количество кнопок в ряду
        for index, (title, callback) in enumerate(buttons):
            row = index // cols
            col = index % cols
            btn = QPushButton(title)
            btn.clicked.connect(callback)
            grid_layout.addWidget(btn, row, col)

        group_box.setLayout(grid_layout)

        layout = QVBoxLayout()
        layout.addWidget(group_box)
        self.setLayout(layout)

    def dummy_action(self):
        print("Команда вызвана")
