from PySide6.QtWidgets import (QApplication, QMainWindow, QTabWidget, QTabBar,
                              QWidget, QMenu, QPushButton, QVBoxLayout, QProxyStyle, QStyle, QStyleOptionTab, QStyleFactory)
from PySide6.QtGui import QDrag, QAction, QPainter, QColor, QCursor, QPixmap, QPainterPath, QPen, QBrush, QMouseEvent
from PySide6.QtCore import Qt, QPoint, QMimeData, QEvent, Signal, QByteArray, QDataStream, QIODevice, QPropertyAnimation, QTimer, QEasingCurve, QParallelAnimationGroup, QAbstractAnimation

class TabBarStyle(QProxyStyle):
    def drawControl(self, element, option, painter, widget=None):
        super().drawControl(element, option, painter, widget)


class DetachableTabWidget(QTabWidget):
    tabAdded = Signal(QWidget)
    tabPinned = Signal(int)
    tabUnpinned = Signal(int)
    lastTabClosed = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setTabBar(DetachableTabBar(self))
        self.setTabsClosable(True)
        self.setMovable(False)
        self.tabBar().tabMoved.connect(self._handle_tab_move)

        self.tabBar().setContextMenuPolicy(Qt.CustomContextMenu)
        self.tabBar().customContextMenuRequested.connect(self._show_tab_context_menu)

        self.add_btn = QPushButton("+")
        self.add_btn.clicked.connect(self.add_session_tab)
        self.setCornerWidget(self.add_btn, Qt.TopRightCorner)
        self.lastTabClosed.connect(self._close_window_if_needed)
        self.tabCloseRequested.connect(self.close_tab)

    def _handle_tab_move(self, from_idx, to_idx):
        """Обработчик перемещения вкладки"""
        pass  # Добавьте свою логику при необходимости

    def update_insert_pos(self, pos):
        self.tabBar().insert_pos = pos
        self.tabBar().update()

    def start_drag(self, index):
        # Оставлено для совместимости, но не используется
        pass

    def tabBar(self):
        return super().tabBar()

    def _create_new_window(self, widget, title, pos):
        new_window = QMainWindow()
        new_tab_widget = DetachableTabWidget()
        new_window.setCentralWidget(new_tab_widget)
        new_window.setWindowTitle(title)
        new_tab_widget.addTab(widget, title)
        new_window.setGeometry(pos.x(), pos.y(), 400, 300)

        # Гарантируем, что окно будет поверх других
        new_window.setWindowFlag(Qt.WindowStaysOnTopHint, True)
        new_window.show()
        new_window.setWindowFlag(Qt.WindowStaysOnTopHint, False)
        new_window.show()

    def _close_window_if_needed(self):
        window = self.window()
        if window.isWindow() and self.count() == 0:
            window.close()

    def detach_tab(self, index, global_pos):
        widget = self.widget(index)
        title = self.tabText(index)
        if widget and index >= 0:
            try:
                # Получаем текущие размеры окна
                window_size = self.window().size()

                # Создаем новое окно
                new_window = QMainWindow()
                new_tab_widget = DetachableTabWidget()
                new_window.setCentralWidget(new_tab_widget)

                # Переносим виджет
                self.removeTab(index)
                new_tab_widget.addTab(widget, title)

                # Настраиваем размеры и позицию
                new_window.resize(window_size)
                new_window.move(global_pos - QPoint(50, 30))  # Смещение от курсора
                new_window.setWindowTitle(title)
                new_window.show()

            except Exception as e:
                print(f"Ошибка при создании окна: {str(e)}")
                # Возвращаем вкладку обратно при ошибке
                self.insertTab(index, widget, title)

    def _show_tab_context_menu(self, pos):
        index = self.tabBar().tabAt(pos)
        if index == -1:
            return

        menu = QMenu()
        widget = self.widget(index)
        pinned = widget.property('pinned') if widget else False

        # Пункт "В отдельном окне"
        detach_action = QAction('В отдельном окне', self)
        detach_action.triggered.connect(lambda: self.detach_tab(index, QCursor.pos()))
        menu.addAction(detach_action)

        pin_action = QAction('Открепить' if pinned else 'Закрепить', self)
        pin_action.triggered.connect(lambda: self.toggle_pin_tab(index))
        menu.addAction(pin_action)

        close_action = QAction('Закрыть', self)
        close_action.triggered.connect(lambda: self.close_tab(index))
        menu.addAction(close_action)

        close_right_action = QAction('Закрыть вкладки справа', self)
        close_right_action.triggered.connect(lambda: self.close_tabs_to_right(index))
        menu.addAction(close_right_action)

        close_others_action = QAction('Закрыть другие вкладки', self)
        close_others_action.triggered.connect(lambda: self.close_other_tabs(index))
        menu.addAction(close_others_action)

        menu.exec(self.tabBar().mapToGlobal(pos))

    def toggle_pin_tab(self, index):
        """Переключение состояния закрепления с автоматической сортировкой"""
        widget = self.widget(index)
        if not widget:
            return

        pinned = not widget.property('pinned')
        widget.setProperty('pinned', pinned)
        self._update_tab_style(index)

        # Перемещаем вкладку при изменении статуса
        if pinned:
            self._move_to_pinned_position(index)
        else:
            self._move_to_unpinned_position(index)

    def _move_to_pinned_position(self, index):
        """Перемещает вкладку в конец закрепленных"""
        pinned_count = sum(1 for i in range(self.count()) if self.widget(i).property('pinned'))
        if index > pinned_count:
            self.tabBar().moveTab(index, pinned_count)
            self.setCurrentIndex(pinned_count)

    def _move_to_unpinned_position(self, index):
        """Перемещает вкладку в начало незакрепленных"""
        pinned_count = sum(1 for i in range(self.count()) if self.widget(i).property('pinned'))
        if index < pinned_count:
            self.tabBar().moveTab(index, pinned_count - 1)
            self.setCurrentIndex(pinned_count - 1)

    def _update_tab_style(self, index):
        """Обновление стиля закрепленной вкладки"""
        pinned = self.widget(index).property('pinned')
        tab_text = self.tabText(index).replace("📌 ", "")

        if pinned:
            self.setTabText(index, f"📌 {tab_text}")
        else:
            self.setTabText(index, tab_text)

    def close_tabs_to_right(self, index):
        """Закрыть все вкладки справа от текущей"""
        for i in range(self.count() - 1, index, -1):
            if not self.widget(i).property('pinned'):
                self.close_tab(i)
        self.tabBar().update()  # Добавить принудительное обновление

    def close_other_tabs(self, index):
        """Закрыть все вкладки кроме текущей"""
        for i in range(self.count() - 1, -1, -1):
            if i != index and not self.widget(i).property('pinned'):
                self.close_tab(i)
        self.tabBar().update()  # Добавить принудительное обновление

    def close_tab(self, index):
        """Закрытие вкладки с проверкой на закрепление"""
        if index < 0 or index >= self.count():
            return

        widget = self.widget(index)
        if widget and widget.property('pinned'):
            return

        # Упрощенная версия без лишних проверок
        super().removeTab(index)
        if widget:
            widget.deleteLater()

        if self.count() == 0:
            self.lastTabClosed.emit()

    def add_session_tab(self, content_widget=None, title="Новая сессия"):
        """Добавление новой вкладки с возможностью кастомизации"""
        tab = content_widget or QWidget()
        tab.setProperty('pinned', False)
        index = self.addTab(tab, title)
        self.setCurrentIndex(index)
        self.tabBar().update()  # Форсируем обновление
        self.tabAdded.emit(tab)
        return tab


class DetachableTabBar(QTabBar):
    tabMoved = Signal(int, int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._drag_start_pos = QPoint()
        self._dragged_index = -1
        self._current_ghost_pos = QPoint()
        self._animation = QPropertyAnimation(self, b"")
        self._animation.setDuration(200)
        self._animation.setEasingCurve(QEasingCurve.OutQuad)

    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.LeftButton:
            self._dragged_index = self.tabAt(event.pos())
            if self._dragged_index != -1:
                if self.parent().widget(self._dragged_index).property('pinned'):
                    self._dragged_index = -1
                    return

                self._drag_start_pos = event.pos()

                # Вызов базового метода, чтобы вкладка становилась активной при клике
                super().mousePressEvent(event)

                event.accept()
                return

        super().mousePressEvent(event)

    def mouseMoveEvent(self, event: QMouseEvent):
        if self._dragged_index != -1:
            if (event.pos() - self._drag_start_pos).manhattanLength() < QApplication.startDragDistance():
                return

            self._current_ghost_pos = event.pos()
            new_index = self._calculate_new_position(event.pos().x())

            if new_index != self._dragged_index and new_index != -1:
                self._animate_tab_move(self._dragged_index, new_index)
                self._dragged_index = new_index
                self.tabMoved.emit(self._dragged_index, new_index)

            self.update()
            event.accept()
            return

        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event: QMouseEvent):
        if self._dragged_index != -1:
            self._dragged_index = -1
            self.update()
            event.accept()
            return

        super().mouseReleaseEvent(event)

    def _calculate_new_position(self, x_pos):
        pinned_count = sum(1 for i in range(self.count())
                           if self.parent().widget(i).property('pinned'))
        for i in range(pinned_count, self.count()):
            tab_rect = self.tabRect(i)
            if x_pos < tab_rect.center().x():
                return i
        return self.count() - 1

    def _animate_tab_move(self, from_idx, to_idx):
        if from_idx == to_idx:
            return

        self._animation.stop()
        super().moveTab(from_idx, to_idx)
        self.setCurrentIndex(to_idx)

    def paintEvent(self, event):
        # Рисуем стандартные вкладки
        super().paintEvent(event)

        # Рисуем призрак перетаскиваемой вкладки
        if self._dragged_index != -1:
            painter = QPainter(self)
            option = QStyleOptionTab()
            self.initStyleOption(option, self._dragged_index)

            # Вычисляем позицию призрака
            ghost_rect = self.tabRect(self._dragged_index)
            offset = self._current_ghost_pos - self._drag_start_pos
            ghost_rect.moveTopLeft(ghost_rect.topLeft() + offset)

            painter.setOpacity(0.7)
            self.style().drawControl(QStyle.CE_TabBarTab, option, painter, self)