from PySide6.QtCore import (QPropertyAnimation, QEasingCurve, QTimer,
                            QPoint, QObject, Signal, Qt)
from PySide6.QtGui import QColor, QPainter, QPainterPath, QMouseEvent
from PySide6.QtWidgets import (QWidget, QLabel, QVBoxLayout,
                               QGraphicsDropShadowEffect, QApplication)


class Notification(QWidget):
    closed = Signal(QWidget)
    heightChanged = Signal()

    def __init__(self, parent=None, message="", timeout=3000, style=None):
        super().__init__(parent)
        self.style = style or {}
        self.timeout = timeout
        self._init_ui(message)
        self._setup_animation()

    def _init_ui(self, message):
        self.setWindowFlags(Qt.ToolTip | Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_TranslucentBackground)

        # Основной контейнер без дополнительных отступов
        self.content = QWidget(self)
        self.content.setStyleSheet(f"""
            background: {self.style.get('background', '#ffffff')};
            border-radius: 8px;
            padding: 8px;
            border: 1px solid {self.style.get('border', '#e0e0e0')};
            color: {self.style.get('text', '#333333')};
            margin: 0px;
        """)

        # Тень
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(15)
        shadow.setColor(QColor(0, 0, 0, 60))
        shadow.setOffset(2, 2)
        self.content.setGraphicsEffect(shadow)

        # Layout содержимого
        layout = QVBoxLayout(self.content)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self.label = QLabel(message)
        self.label.setStyleSheet("font: 14px; margin: 0px;")
        self.label.setWordWrap(True)
        layout.addWidget(self.label)

        # Основной layout уведомления
        self.setLayout(QVBoxLayout())
        self.layout().setContentsMargins(0, 0, 0, 0)  # Убираем все внешние отступы
        self.layout().addWidget(self.content)

    def showEvent(self, event):
        self.raise_()
        self._update_position()
        super().showEvent(event)

    def _update_position(self):
        if self.parent():
            self.parent().notification_manager._update_positions()

    def _setup_animation(self):
        self.animation = QPropertyAnimation(self, b"pos")
        self.animation.setEasingCurve(QEasingCurve.OutCubic)
        self.animation.setDuration(300)

    def showEvent(self, event):
        QTimer.singleShot(self.timeout, self._start_hide_animation)

    def mousePressEvent(self, event: QMouseEvent):
        self._start_hide_animation()

    def _start_hide_animation(self):
        self.animation.setStartValue(self.pos())
        self.animation.setEndValue(self.pos() + QPoint(0, -self.height()))
        self.animation.finished.connect(lambda: self.closed.emit(self))
        self.animation.start()

    def update_position(self, y_pos):
        end_pos = QPoint(
            self.parent().width() - self.width() - 20,
            self.parent().height() - y_pos - 20
        )
        self.animation.setStartValue(self.pos())
        self.animation.setEndValue(end_pos)
        self.animation.start()


class NotificationManager(QObject):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.notifications = []
        self.spacing = 10
        self.margin = 10  # Отступ от краев окна

    def add_notification(self, notification):
        notification.closed.connect(self._remove_notification)
        self.notifications.append(notification)
        self._update_positions()
        notification.show()

    def _remove_notification(self, notification):
        if notification in self.notifications:
            self.notifications.remove(notification)
            notification.deleteLater()
            self._update_positions()

    def _update_positions(self):
        if not self.parent():
            return

        # Получаем актуальные координаты родительского окна
        parent_window = self.parent()
        if isinstance(parent_window, QWidget):
            global_pos = parent_window.mapToGlobal(QPoint(0, 0))
            width = parent_window.width()
            height = parent_window.height()

            y_offset = 0
            for notif in reversed(self.notifications):
                # Рассчитываем позицию относительно правого нижнего угла
                x = global_pos.x() + width - notif.width() - self.margin
                y = global_pos.y() + height - notif.height() - y_offset - self.margin

                # Корректировка позиции
                notif.move(int(x), int(y))
                y_offset += notif.height() + self.spacing