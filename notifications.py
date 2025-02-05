from PySide6.QtCore import Qt, QTimer, QPropertyAnimation, QPoint
from PySide6.QtWidgets import QWidget, QLabel, QVBoxLayout, QApplication, QHBoxLayout, QPushButton
from PySide6.QtGui import QCursor, QIcon

class Notification(QWidget):
    # Статический стек для хранения активных уведомлений
    _active_notifications = []

    def __init__(self, message: str, notif_type: str = "success", duration: int = 3000, parent=None):
        """
        :param message: Текст уведомления.
        :param notif_type: Тип уведомления ('success', 'error', 'warning').
        :param duration: Время отображения в мс.
        :param parent: Родительский виджет.
        """
        super().__init__(parent)
        # Флаги окна для отображения уведомления поверх остальных без рамки
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)

        # Основной layout и метка с текстом
        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 5, 10, 5)

        # Иконка в зависимости от типа уведомления
        self.icon_label = QLabel()
        self._set_icon(notif_type)
        layout.addWidget(self.icon_label)

        self.label = QLabel(message)
        layout.addWidget(self.label, 1)

        # Кнопка закрытия
        self.close_button = QPushButton()
        self.close_button.setIcon(QIcon.fromTheme("window-close"))
        self.close_button.setFlat(True)
        self.close_button.clicked.connect(self.hide_notification)
        layout.addWidget(self.close_button)

        # Применяем стиль в зависимости от типа уведомления
        self._apply_style(notif_type)
        self.adjustSize()

        # Таймер для автоматического скрытия
        self.timer = QTimer(self)
        self.timer.setInterval(duration)
        self.timer.setSingleShot(True)
        self.timer.timeout.connect(self.hide_notification)

        # При клике на уведомлении оно скрывается
        self.label.mousePressEvent = self._on_click

    def _set_icon(self, notif_type: str):
        """Устанавливает иконку в зависимости от типа уведомления."""
        if notif_type == "success":
            self.icon_label.setPixmap(QIcon.fromTheme("dialog-ok").pixmap(24, 24))
        elif notif_type == "error":
            self.icon_label.setPixmap(QIcon.fromTheme("dialog-error").pixmap(24, 24))
        else:
            self.icon_label.setPixmap(QIcon.fromTheme("dialog-warning").pixmap(24, 24))

    def _apply_style(self, notif_type: str):
        """Задает стили в зависимости от типа уведомления."""
        if notif_type == "success":
            bg_color = "#d4edda"  # светло-зеленый
            text_color = "#155724"
        elif notif_type == "error":
            bg_color = "#f8d7da"  # светло-красный
            text_color = "#721c24"
        else:
            # Например, предупреждение
            bg_color = "#fff3cd"  # светло-желтый
            text_color = "#856404"

        style = f"""
            background-color: {bg_color};
            color: {text_color};
            border: 1px solid {text_color};
            border-radius: 5px;
            padding: 10px;
        """
        self.setStyleSheet(style)

    def show_notification(self):
        """
        Отображает уведомление в правом нижнем углу окна приложения.
        Позиционирование осуществляется относительно глобальных координат главного окна.
        """
        Notification._active_notifications.append(self)
        self._update_position()
        self.show()

        # Анимация появления (fade in)
        self.setWindowOpacity(0.0)
        self.anim = QPropertyAnimation(self, b"windowOpacity")
        self.anim.setDuration(500)
        self.anim.setStartValue(0.0)
        self.anim.setEndValue(1.0)
        self.anim.start()

        self.timer.start()

    def _update_position(self):
        """
        Обновляет позицию уведомления с учетом других активных уведомлений.
        Если есть родительский виджет, позиционируем уведомление относительно главного окна.
        """
        if self.parent():
            # Используем главное окно (window) для получения глобальных координат
            main_window = self.parent().window()
            parent_rect = main_window.frameGeometry()
            x = parent_rect.x() + parent_rect.width() - self.width() - 20
            y = parent_rect.y() + parent_rect.height() - self.height() - 20
        else:
            # Если родителя нет, позиционируем относительно экрана
            screen_geometry = QApplication.primaryScreen().availableGeometry()
            x = screen_geometry.right() - self.width() - 20
            y = screen_geometry.bottom() - self.height() - 20

        # Смещение уведомлений, если их несколько
        for notif in Notification._active_notifications:
            if notif != self:
                y -= notif.height() + 10

        # Защита от выхода за границы экрана
        screen_geometry = QApplication.primaryScreen().availableGeometry()
        if y < screen_geometry.top():
            y = screen_geometry.top() + 20

        self.move(x, y)

    def hide_notification(self):
        """Скрывает уведомление с анимацией исчезновения."""
        self.anim = QPropertyAnimation(self, b"windowOpacity")
        self.anim.setDuration(500)
        self.anim.setStartValue(1.0)
        self.anim.setEndValue(0.0)
        self.anim.finished.connect(self._on_hide_finished)
        self.anim.start()

    def _on_hide_finished(self):
        """Удаляет уведомление из стека и закрывает его."""
        if self in Notification._active_notifications:
            Notification._active_notifications.remove(self)
        self.close()

        # Обновляем позиции оставшихся уведомлений
        for notif in Notification._active_notifications:
            notif._update_position()

    def _on_click(self, event):
        """Обработчик клика по уведомлению — скрывает его."""
        self.hide_notification()


# Пример использования (для тестирования уведомлений)
if __name__ == "__main__":
    import sys

    app = QApplication(sys.argv)

    # Уведомление об успешном действии
    notif_success = Notification("Операция выполнена успешно!", "success", duration=3000)
    notif_success.show_notification()

    # Уведомление об ошибке с задержкой
    QTimer.singleShot(4000, lambda: Notification("Произошла ошибка!", "error", duration=3000).show_notification())

    # Уведомление с предупреждением с задержкой
    QTimer.singleShot(8000, lambda: Notification("Внимание! Это предупреждение.", "warning", duration=3000).show_notification())

    sys.exit(app.exec())