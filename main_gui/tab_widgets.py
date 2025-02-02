from PySide6.QtWidgets import QApplication, QMainWindow, QTabWidget, QTabBar, QWidget, QMenu, QPushButton, QVBoxLayout
from PySide6.QtGui import QDrag, QAction
from PySide6.QtCore import Qt, QPoint, QMimeData, QEvent, Signal


class DetachableTabWidget(QTabWidget):
    tabAdded = Signal(QWidget)  # Новый сигнал
    tabPinned = Signal(int)
    tabUnpinned = Signal(int)
    lastTabClosed = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMovable(True)
        self.setTabsClosable(True)
        self.setTabBar(DetachableTabBar(self))

        # Контекстное меню
        self.tabBar().setContextMenuPolicy(Qt.CustomContextMenu)
        self.tabBar().customContextMenuRequested.connect(self._show_tab_context_menu)

        # Кнопка добавления вкладок
        self.add_btn = QPushButton("+")
        self.add_btn.clicked.connect(self.add_session_tab)
        self.setCornerWidget(self.add_btn, Qt.TopRightCorner)

        self.tabCloseRequested.connect(self.close_tab)

    def _show_tab_context_menu(self, pos):
        """Показ контекстного меню для вкладки"""
        index = self.tabBar().tabAt(pos)
        if index == -1:
            return

        menu = QMenu()
        widget = self.widget(index)
        pinned = widget.property('pinned') if widget else False

        # Опция закрепления
        pin_action = QAction('Открепить' if pinned else 'Закрепить', self)
        pin_action.triggered.connect(lambda: self.toggle_pin_tab(index))
        menu.addAction(pin_action)

        # Опции закрытия
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
        """Переключение состояния закрепления вкладки"""
        widget = self.widget(index)
        if widget:
            pinned = not widget.property('pinned')
            widget.setProperty('pinned', pinned)
            self._update_tab_style(index)

            if pinned:
                self.tabPinned.emit(index)
            else:
                self.tabUnpinned.emit(index)

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

    def close_other_tabs(self, index):
        """Закрыть все вкладки кроме текущей"""
        for i in range(self.count() - 1, -1, -1):
            if i != index and not self.widget(i).property('pinned'):
                self.close_tab(i)

    def close_tab(self, index):
        """Закрытие вкладки с проверкой на закрепление"""
        if index < 0 or index >= self.count():
            return

        widget = self.widget(index)
        if widget and widget.property('pinned'):
            return

        super().removeTab(index)
        widget.deleteLater()

        if self.count() == 0:
            self.lastTabClosed.emit()

    def add_session_tab(self, content_widget=None, title="Новая сессия"):
        """Добавление новой вкладки с возможностью кастомизации"""
        tab = content_widget or QWidget()
        tab.setProperty('pinned', False)
        index = self.addTab(tab, title)
        self.setCurrentIndex(index)
        self.tabAdded.emit(tab)  # Испускаем сигнал
        return tab

class DetachableTabBar(QTabBar):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAcceptDrops(True)
        self.drag_start_pos = QPoint()
        self.dragged_index = -1

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.drag_start_pos = event.pos()
            self.dragged_index = self.tabAt(event.pos())
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if event.buttons() & Qt.LeftButton and self.dragged_index >= 0:
            drag_distance = (event.pos() - self.drag_start_pos).manhattanLength()
            if drag_distance >= QApplication.startDragDistance():
                self.start_drag(event)

    def start_drag(self, event):
        """Запускаем перетаскивание"""
        parent_tab_widget = self.parent()
        if not isinstance(parent_tab_widget, DetachableTabWidget) or self.dragged_index < 0:
            return

        widget = parent_tab_widget.widget(self.dragged_index)
        if not widget:
            return

        drag = QDrag(self)
        mime_data = QMimeData()
        mime_data.setData("application/x-tabwidget", str(self.dragged_index).encode())
        drag.setMimeData(mime_data)

        pixmap = widget.grab()
        drag.setPixmap(pixmap)
        drag.setHotSpot(event.pos() - self.tabRect(self.dragged_index).topLeft())

        result = drag.exec(Qt.MoveAction)
        if result != Qt.MoveAction:
            parent_tab_widget.detach_tab(self.dragged_index, event.globalPosition().toPoint())
        self.dragged_index = -1

    def dragEnterEvent(self, event):
        if event.mimeData().hasFormat("application/x-tabwidget"):
            event.acceptProposedAction()

    def dropEvent(self, event):
        if event.mimeData().hasFormat("application/x-tabwidget"):
            from_index = int(event.mimeData().data("application/x-tabwidget").data().decode())
            source_tab_widget = event.source().parent()

            if not isinstance(source_tab_widget, DetachableTabWidget) or source_tab_widget == self.parent():
                event.ignore()
                return

            if from_index >= source_tab_widget.count():
                return

            widget = source_tab_widget.widget(from_index)
            title = source_tab_widget.tabText(from_index)

            if widget:
                source_tab_widget.removeTab(from_index)
                self.addTab(widget, title)
                self.setCurrentIndex(self.count() - 1)

            event.acceptProposedAction()