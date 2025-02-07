from PySide6.QtCore import Qt, QTimer, QPropertyAnimation, QEvent, QPoint
from PySide6.QtWidgets import QWidget, QLabel, QVBoxLayout, QHBoxLayout, QApplication, QPushButton
from PySide6.QtGui import QIcon, QFont

# Глобальный флаг для включения/выключения уведомлений
notifications_enabled = True

def set_notifications_enabled(enabled: bool):
    """Функция для управления глобальным флагом уведомлений."""
    global notifications_enabled
    notifications_enabled = enabled

class Notification(QWidget):
    _active_notifications = []

    def __init__(self, title: str, message: str, notif_type: str = "info",
                 duration: int = 3000, parent=None, action_text=None, on_action=None):
        super().__init__(parent)
        self.title = title
        self.message = message
        self.notif_type = notif_type
        self.duration = duration
        self.action_text = action_text
        self.on_action = on_action  # Функция, вызываемая при клике на кнопку действия

        if parent:
            parent.installEventFilter(self)

        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 5, 10, 5)

        self.icon_label = QLabel()
        self._set_icon()
        layout.addWidget(self.icon_label)

        text_layout = QVBoxLayout()
        self.title_label = QLabel(self.title)
        bold_font = QFont()
        bold_font.setBold(True)
        self.title_label.setFont(bold_font)
        self.message_label = QLabel(self.message)
        self.message_label.setWordWrap(True)
        text_layout.addWidget(self.title_label)
        text_layout.addWidget(self.message_label)

        if self.action_text:
            self.action_button = QPushButton(self.action_text)
            self.action_button.clicked.connect(self._on_action_click)
            text_layout.addWidget(self.action_button)

        layout.addLayout(text_layout, 1)

        self._apply_style()
        self.adjustSize()

        self.timer = QTimer(self)
        self.timer.setInterval(self.duration)
        self.timer.setSingleShot(True)
        self.timer.timeout.connect(self.hide_notification)

        self.message_label.mousePressEvent = self._on_click
        self.title_label.mousePressEvent = self._on_click
        self.icon_label.mousePressEvent = self._on_click

    def _set_icon(self):
        icon_map = {
            "success": QIcon.fromTheme("dialog-ok"),
            "error": QIcon.fromTheme("dialog-error"),
            "warning": QIcon.fromTheme("dialog-warning"),
            "info": QIcon.fromTheme("dialog-information")
        }
        fallback_emoji = {
            "success": "✅",
            "error": "❌",
            "warning": "⚠️",
            "info": "ℹ️"
        }
        icon = icon_map.get(self.notif_type, QIcon.fromTheme("dialog-information"))
        pixmap = icon.pixmap(24, 24)
        if pixmap.isNull():
            self.icon_label.setText(fallback_emoji.get(self.notif_type, "ℹ️"))
        else:
            self.icon_label.setPixmap(pixmap)

    def _apply_style(self):
        if self.notif_type == "success":
            bg_color = "#d4edda"
            text_color = "#155724"
        elif self.notif_type == "error":
            bg_color = "#f8d7da"
            text_color = "#721c24"
        elif self.notif_type == "warning":
            bg_color = "#fff3cd"
            text_color = "#856404"
        else:
            bg_color = "#d1ecf1"
            text_color = "#0c5460"

        style = f"""
            background-color: {bg_color};
            color: {text_color};
            border: 1px solid {text_color};
            border-radius: 5px;
            padding: 10px;
        """
        self.setStyleSheet(style)

    def show_notification(self, parent_pos=None):
        if not notifications_enabled:
            return  # Если уведомления отключены, ничего не делаем

        Notification._active_notifications.append(self)

        if parent_pos:
            self.move(*parent_pos)
        else:
            self.update_position()

        self.show()
        self.setWindowOpacity(0.0)
        self.anim = QPropertyAnimation(self, b"windowOpacity")
        self.anim.setDuration(500)
        self.anim.setStartValue(0.0)
        self.anim.setEndValue(1.0)
        self.anim.start()

        self.timer.start()

    def update_position(self):
        """Обновляет позицию уведомления относительно родительского окна (если есть) или экрана."""
        margin = 20
        if self.parent():
            # Получаем глобальные координаты родительского виджета
            parent_top_left = self.parent().mapToGlobal(self.parent().rect().topLeft())
            parent_geometry = self.parent().geometry()
            parent_geometry.moveTopLeft(parent_top_left)
        else:
            parent_geometry = QApplication.primaryScreen().availableGeometry()

        x = parent_geometry.right() - self.width() - margin
        y = parent_geometry.bottom() - self.height() - margin

        # Если есть другие активные уведомления, смещаем их вверх
        offset = 0
        for notif in Notification.get_active_notifications():
            if notif is self:
                break
            offset += notif.height() + 10

        y -= offset

        if x < 0: x = 0
        if y < 0: y = 0

        self.move(x, y)

    def hide_notification(self):
        self.anim = QPropertyAnimation(self, b"windowOpacity")
        self.anim.setDuration(500)
        self.anim.setStartValue(1.0)
        self.anim.setEndValue(0.0)
        self.anim.finished.connect(self._on_hide_finished)
        self.anim.start()

    def _on_hide_finished(self):
        if self in Notification._active_notifications:
            Notification._active_notifications.remove(self)
        self.close()
        self._update_positions_of_remaining_notifications()

    def _on_click(self, event):
        self.hide_notification()

    def _on_action_click(self):
        if self.on_action:
            self.on_action()
        self.hide_notification()

    def eventFilter(self, obj, event):
        if event.type() in (QEvent.Move, QEvent.Resize):
            QTimer.singleShot(0, self.update_position)
        return super().eventFilter(obj, event)

    @staticmethod
    def get_active_notifications():
        return Notification._active_notifications

    @staticmethod
    def _update_positions_of_remaining_notifications():
        for notif in Notification.get_active_notifications():
            notif.update_position()
