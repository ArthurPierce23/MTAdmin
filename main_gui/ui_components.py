# ui_components.py
from PySide6.QtWidgets import (
    QLineEdit,
    QDialog,
    QListWidget,
    QPushButton,
    QVBoxLayout,
    QLabel
)
from PySide6.QtGui import QRegularExpressionValidator, QKeyEvent
from PySide6.QtCore import Qt, QRegularExpression
from styles import apply_theme


class IPLineEdit(QLineEdit):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setPlaceholderText("Введите IP (например: 192.168.1.1)")
        self.setValidator(QRegularExpressionValidator(
            QRegularExpression(r"^((\d{1,3}\.){0,3}\d{0,3})$"),
            self
        ))
        self.setInputMethodHints(Qt.ImhFormattedNumbersOnly)
        # Проверяем корректность ввода сразу при каждом изменении текста
        self.textChanged.connect(self._check_range)
        # Окончательное форматирование при завершении ввода (например, при потере фокуса)
        self.editingFinished.connect(self._finalize_text)


    def keyPressEvent(self, event: QKeyEvent):
        # Разрешённые клавиши редактирования – просто передаём их базовому методу
        if event.key() in (Qt.Key_Backspace, Qt.Key_Delete, Qt.Key_Left, Qt.Key_Right, Qt.Key_Home, Qt.Key_End):
            super().keyPressEvent(event)
            return

        # Обработка ввода точки или пробела (используем пробел как дополнительный разделитель, если нужно)
        if event.key() in (Qt.Key_Period, Qt.Key_Comma, Qt.Key_Space):
            # Если в строке меньше 3 точек, вставляем разделитель
            if self.text().count('.') < 3:
                self._insert_dot()
            return

        # Если вводится цифра
        if event.text().isdigit():
            cursor = self.cursorPosition()
            current_text = self.text()
            # Определяем границы текущего октета:
            start = current_text.rfind('.', 0, cursor) + 1
            end = current_text.find('.', cursor)
            if end == -1:
                end = len(current_text)
            current_octet = current_text[start:end]

            # Если курсор находится в конце строки и длина текущего октета уже 3 цифры,
            # а октетов меньше 4, автоматически вставляем точку
            if (cursor == len(current_text)) and (len(current_octet) >= 3) and (self.text().count('.') < 3):
                self._insert_dot()

            super().keyPressEvent(event)
            return

        # Для всех остальных символов – базовая обработка
        super().keyPressEvent(event)

    def _insert_dot(self):
        pos = self.cursorPosition()
        self.insert(".")
        self.setCursorPosition(pos + 1)

    def _check_range(self):
        """
        Проверяем, что все октеты находятся в диапазоне 0-255.
        Если хотя бы один октет неверный – устанавливаем красную рамку.
        Это происходит сразу при изменении текста.
        """
        text = self.text()
        parts = text.split('.')
        style_error = False

        for part in parts:
            if part.isdigit() and part != "":
                if int(part) > 255:
                    style_error = True
                    break

        if style_error:
            self.setStyleSheet("border: 1px solid red;")
        else:
            self.setStyleSheet("")

    def _finalize_text(self):
        """
        Окончательное форматирование:
         - Для каждого октета, если он не пустой и состоит из цифр, убираем ведущие нули.
         - Также повторно проверяем диапазон октетов.
        """
        text = self.text()
        parts = text.split('.')
        new_parts = []
        style_error = False

        for part in parts:
            if part == "":
                new_parts.append("")
            elif part.isdigit():
                num = int(part)
                if num > 255:
                    style_error = True
                new_parts.append(str(num))
            else:
                new_parts.append(part)

        new_text = ".".join(new_parts)
        self.blockSignals(True)
        self.setText(new_text)
        self.blockSignals(False)

        if style_error:
            self.setStyleSheet("border: 1px solid red;")
        else:
            self.setStyleSheet("")

class ThemeDialog(QDialog):
    """Диалоговое окно для выбора темы"""

    def __init__(self, theme_list):
        super().__init__()
        self.setWindowTitle("Выбор темы")
        self.setMinimumWidth(300)
        self.setMinimumHeight(200)


        layout = QVBoxLayout(self)
        self.theme_list = QListWidget()
        self.theme_list.addItems(["Без темы"] + theme_list)

        self.ok_button = QPushButton("OK")
        self.ok_button.clicked.connect(self.accept)

        layout.addWidget(self.theme_list)
        layout.addWidget(self.ok_button)
        self.setStyleSheet(apply_theme("Темная"))

    @property
    def selected_theme(self):
        return self.theme_list.currentItem().text() if self.theme_list.currentItem() else None
