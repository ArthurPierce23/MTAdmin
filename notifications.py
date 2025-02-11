from PySide6.QtCore import Qt, QTimer, QPropertyAnimation, QEvent, QPoint
from PySide6.QtWidgets import QWidget, QLabel, QVBoxLayout, QHBoxLayout, QApplication, QPushButton
from PySide6.QtGui import QIcon, QFont, QColor, QPalette

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
        layout.setContentsMargins(15, 10, 15, 10)
        layout.setSpacing(10)

        self.icon_label = QLabel()
        self._set_icon()
        layout.addWidget(self.icon_label)

        text_layout = QVBoxLayout()
        self.title_label = QLabel(self.title)
        self.title_label.setFont(QFont("Arial", 10, QFont.Bold))
        self.message_label = QLabel(self.message)
        self.message_label.setWordWrap(True)
        self.message_label.setFont(QFont("Arial", 9))
        text_layout.addWidget(self.title_label)
        text_layout.addWidget(self.message_label)

        if self.action_text:
            self.action_button = QPushButton(self.action_text)
            self.action_button.setStyleSheet("""
                QPushButton {
                    background-color: #007BFF;
                    color: white;
                    border-radius: 5px;
                    padding: 5px 10px;
                }
                QPushButton:hover {
                    background-color: #0056b3;
                }
            """)
            self.action_button.clicked.connect(self._on_action_click)
            text_layout.addWidget(self.action_button)

        layout.addLayout(text_layout, 1)
        self._apply_style()
        self.adjustSize()

        self.timer = QTimer(self)
        self.timer.setInterval(self.duration)
        self.timer.setSingleShot(True)
        self.timer.timeout.connect(self.hide_notification)

        # Закрытие по клику
        self.message_label.mousePressEvent = self._on_click
        self.title_label.mousePressEvent = self._on_click
        self.icon_label.mousePressEvent = self._on_click

    def _set_icon(self):
        """Устанавливает иконку уведомления."""
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
        """Применяет стилизацию уведомления."""
        color_map = {
            "success": ("#28a745", "#d4edda"),
            "error": ("#dc3545", "#f8d7da"),
            "warning": ("#ffc107", "#fff3cd"),
            "info": ("#17a2b8", "#d1ecf1")
        }

        text_color, bg_color = color_map.get(self.notif_type, ("#0c5460", "#d1ecf1"))

        style = f"""
            background-color: {bg_color};
            color: {text_color};
            border-radius: 8px;
            border: 1px solid {text_color};
            padding: 12px;
            box-shadow: 0px 5px 15px rgba(0, 0, 0, 0.2);
        """
        self.setStyleSheet(style)

    def show_notification(self, parent_pos=None):
        """Показывает уведомление с анимацией."""
        if not notifications_enabled:
            return  # Если уведомления отключены, ничего не делаем

        Notification._active_notifications.append(self)

        if parent_pos:
            self.move(*parent_pos)
        else:
            self.update_position()

        self.show()
        self.setWindowOpacity(0.0)

        # Анимация появления
        self.anim = QPropertyAnimation(self, b"windowOpacity")
        self.anim.setDuration(400)
        self.anim.setStartValue(0.0)
        self.anim.setEndValue(1.0)
        self.anim.start()

        self.timer.start()

    def update_position(self):
        """Обновляет позицию уведомления на экране."""
        margin = 20
        main_window = self.parent().window() if self.parent() else QApplication.activeWindow()
        parent_geometry = main_window.frameGeometry() if main_window else QApplication.primaryScreen().availableGeometry()

        x = parent_geometry.right() - self.width() - margin
        y = parent_geometry.bottom() - self.height() - margin

        # Смещаем, если уже есть другие уведомления
        offset = sum(notif.height() + 10 for notif in Notification.get_active_notifications() if notif is not self)
        y -= offset

        self.move(max(0, x), max(0, y))

    def hide_notification(self):
        """Анимация исчезновения."""
        self.anim = QPropertyAnimation(self, b"windowOpacity")
        self.anim.setDuration(400)
        self.anim.setStartValue(1.0)
        self.anim.setEndValue(0.0)
        self.anim.finished.connect(self._on_hide_finished)
        self.anim.start()

    def _on_hide_finished(self):
        """Удаляет уведомление из активных и обновляет расположение остальных."""
        if self in Notification._active_notifications:
            Notification._active_notifications.remove(self)
        self.close()
        self._update_positions_of_remaining_notifications()

    def _on_click(self, event):
        """Закрывает уведомление при клике."""
        self.hide_notification()

    def _on_action_click(self):
        """Обрабатывает нажатие на кнопку действия."""
        if self.on_action:
            self.on_action()
        self.hide_notification()

    def eventFilter(self, obj, event):
        """Следит за изменением размера главного окна."""
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
