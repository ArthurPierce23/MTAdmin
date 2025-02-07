# tab_widgets.py
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QTabWidget, QMenu, QMainWindow, QMessageBox, QInputDialog, QSpacerItem
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QAction, QIcon

# Импортируем модифицированный PCConnectionBlock
from main_gui.gui.pc_connection_block import PCConnectionBlock
# Импортируем другие виджеты (например, RecentConnectionsBlock, WPMapBlock)
from main_gui.gui.recent_connections_block import RecentConnectionsBlock
from main_gui.gui.wp_map_block import WPMapBlock
# Импорт окон для подключения
from windows_gui.gui.windows_window import WindowsWindow
from linux_gui.gui.linux_window import LinuxWindow
from styles import apply_theme
from linux_gui.session_manager import SessionManager


class DetachedWindow(QMainWindow):
    def __init__(self, tabs_widget: 'DynamicTabs', parent: 'DynamicTabs', title: str, theme_name: str):
        """
        Отсоединённое окно, куда переносится вкладка.
        """
        super().__init__()
        self.setWindowTitle(title)
        self.setGeometry(200, 200, 500, 600)
        self.setCentralWidget(tabs_widget)
        self.tabs_widget = tabs_widget
        self.parent_tabs = parent
        self.theme_name = theme_name
        self.setStyleSheet(apply_theme(self.theme_name))

    def closeEvent(self, event):
        """
        При закрытии окна все вкладки из отсоединённого окна возвращаются в родительский DynamicTabs.
        """
        for i in reversed(range(self.tabs_widget.count())):
            widget = self.tabs_widget.widget(i)
            title = self.tabs_widget.tabText(i)
            if isinstance(self.parent_tabs, DynamicTabs):
                self.parent_tabs.add_existing_tab(widget, title)
                if self in self.parent_tabs.detached_windows:
                    self.parent_tabs.detached_windows.remove(self)
        super().closeEvent(event)


class DynamicTabs(QTabWidget):
    def __init__(self, with_initial_tab=True, theme_name="Светлая"):
        """
        Основной виджет вкладок с поддержкой отсоединения, переименования, закрепления и т.д.
        """
        super().__init__()
        self.current_theme = theme_name
        self.setObjectName("dynamicTabs")
        self.setTabsClosable(True)
        self.tabCloseRequested.connect(self.close_tab)
        self.setMovable(True)
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self.open_context_menu)
        self.detached_windows = []
        self.pinned_tabs = set()

        # Устанавливаем фиксированную высоту таббара
        self.tabBar().setFixedHeight(40)

        # Создание кнопки "Добавить вкладку"
        self.addTabButton = QPushButton("➕")
        self.addTabButton.setObjectName("addTabButton")
        self.addTabButton.clicked.connect(self.add_new_tab)

        # Контейнер для кнопки, выравненный по правому верхнему углу таббара
        corner_container = QWidget()
        corner_layout = QHBoxLayout(corner_container)
        # Отступы: левый = 0, верх = 0, правый = 5, нижний = 0
        corner_layout.setContentsMargins(0, 0, 5, -5)
        corner_layout.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        corner_layout.addWidget(self.addTabButton)
        corner_container.setLayout(corner_layout)

        # Сохраним ссылку на контейнер для возможности управлять z-порядком
        self.corner_widget = corner_container

        # Устанавливаем контейнер как corner widget в верхнем правом углу
        self.setCornerWidget(self.corner_widget, Qt.TopRightCorner)
        # Сразу поднимаем его над остальными
        self.corner_widget.raise_()

        # Применяем тему (без дополнительных правил для QTabWidget::pane, чтобы сохранить границу)
        self.setStyleSheet(apply_theme(self.current_theme))

        if with_initial_tab:
            self.add_new_tab()

    def resizeEvent(self, event):
        """
        При изменении размеров гарантируем, что corner widget (кнопка "+") остается поверх.
        """
        super().resizeEvent(event)
        if hasattr(self, 'corner_widget'):
            self.corner_widget.raise_()

    @staticmethod
    def create_tab_content(self, parent_tabs: 'DynamicTabs', is_pc_connection_needed: bool = True) -> QWidget:
        """
        Создает содержимое новой вкладки.
        Добавлен верхний отступ для предотвращения наложения на область таббара.
        """
        new_tab = QWidget()
        main_layout = QVBoxLayout()
        # Добавляем небольшой отступ сверху (например, 10px)
        main_layout.setContentsMargins(0, 10, 0, 0)

        # Создаем блоки для отображения подключения, списка недавних подключений и карты рабочих мест.
        recent_connections_block = RecentConnectionsBlock()

        if is_pc_connection_needed:
            connection_block = PCConnectionBlock(recent_connections_block=recent_connections_block, wp_map_block=None)
            main_layout.addWidget(connection_block)
        else:
            connection_block = None

        wp_map_block = WPMapBlock(pc_connection_block=connection_block)

        if connection_block:
            connection_block.wp_map_block = wp_map_block
        recent_connections_block.pc_connection_block = connection_block

        bottom_widget = QWidget()
        bottom_layout = QHBoxLayout()
        bottom_layout.addWidget(recent_connections_block)
        bottom_layout.addWidget(wp_map_block)
        bottom_widget.setLayout(bottom_layout)

        main_layout.addWidget(bottom_widget)
        new_tab.setLayout(main_layout)

        return new_tab

    def add_new_tab(self, _checked=False, title="Новая сессия", is_pc_connection_needed=True):
        """
        Добавляет новую вкладку с содержимым, созданным методом create_tab_content.
        """
        content = self.create_tab_content(self, is_pc_connection_needed)
        index = self.addTab(content, title)
        self.setCurrentIndex(index)
        content.setStyleSheet(apply_theme(self.current_theme))

    def add_existing_tab(self, widget: QWidget, title="Новая сессия"):
        index = self.addTab(widget, title)
        self.setCurrentIndex(index)

    def handle_connection(self, os_name: str, pc_name: str, ip: str):
        if os_name == "Windows":
            self.open_windows_gui(pc_name, ip)
        elif os_name == "Linux":
            self.open_linux_gui(ip)
        else:
            QMessageBox.warning(self, "Ошибка", "Не удалось определить операционную систему.")

    def set_theme(self, theme_name: str):
        self.current_theme = theme_name
        self.setStyleSheet(apply_theme(theme_name))
        for i in range(self.count()):
            widget = self.widget(i)
            if isinstance(widget, QWidget):
                widget.setStyleSheet(apply_theme(theme_name))
        for window in self.detached_windows:
            window.setStyleSheet(apply_theme(theme_name))
            if hasattr(window, 'tabs_widget'):
                window.tabs_widget.set_theme(theme_name)

    def open_windows_gui(self, hostname: str, ip: str):
        try:
            windows_widget = WindowsWindow(hostname, ip)
            self.add_existing_tab(windows_widget, f"Windows: {hostname}")
        except Exception as e:
            QMessageBox.critical(self, "Ошибка подключения", f"Не удалось подключиться к {hostname}: {str(e)}")

    def open_linux_gui(self, ip: str):
        try:
            linux_widget = LinuxWindow(ip)
            self.add_existing_tab(linux_widget, f"Linux: {ip}")
        except Exception as e:
            QMessageBox.critical(self, "Ошибка подключения", f"Не удалось подключиться к {ip}: {str(e)}")

    def detach_tab(self, index: int):
        if index in self.pinned_tabs or self.count() == 1:
            return

        title = self.tabText(index)
        widget = self.widget(index)
        self.removeTab(index)

        detached_tabs = DynamicTabs(with_initial_tab=False, theme_name=self.current_theme)
        detached_tabs.add_existing_tab(widget, title)

        detached_window = DetachedWindow(detached_tabs, self, title, self.current_theme)
        detached_window.setStyleSheet(apply_theme(self.current_theme))
        self.detached_windows.append(detached_window)
        detached_window.show()

    def close_tab(self, index: int):
        if index in self.pinned_tabs or self.count() == 1:
            return

        widget = self.widget(index)
        if hasattr(widget, 'session_manager') and isinstance(widget.session_manager, SessionManager):
            try:
                widget.session_manager.close_session()
            except Exception as e:
                QMessageBox.warning(self, "Ошибка", f"Ошибка при закрытии SSH-сессии: {str(e)}")

        if hasattr(widget, 'has_unsaved_changes') and widget.has_unsaved_changes():
            reply = QMessageBox.question(
                self,
                'Подтверждение закрытия',
                'У вас есть несохраненные изменения. Закрыть вкладку?',
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            if reply == QMessageBox.No:
                return

        self.removeTab(index)

    def rename_tab(self, index: int):
        current_title = self.tabText(index)
        new_title, ok = QInputDialog.getText(self, "Переименовать вкладку", "Введите новое название:",
                                             text=current_title)
        if ok and new_title:
            self.setTabText(index, new_title)

    def open_context_menu(self, position):
        index = self.tabBar().tabAt(position)
        if index == -1:
            return

        menu = QMenu()
        menu.setObjectName("tabMenu")

        rename_tab_action = QAction("✏️ Переименовать", self)
        pin_tab_action = QAction("📌 Открепить" if index in self.pinned_tabs else "📌 Закрепить", self)
        detach_tab_action = QAction("🔄 Открыть отдельно", self)
        close_tab_action = QAction("❌ Закрыть вкладку", self)
        close_others_action = QAction("❌ Закрыть другие", self)
        close_right_action = QAction("❌ Закрыть справа", self)

        menu.addAction(rename_tab_action)
        menu.addAction(pin_tab_action)
        menu.addSeparator()
        menu.addAction(detach_tab_action)
        menu.addSeparator()
        menu.addAction(close_tab_action)
        menu.addAction(close_others_action)
        menu.addAction(close_right_action)

        if any(w.tabs_widget.count() > 0 for w in self.detached_windows):
            reattach_action = QAction("🔁 Вернуть вкладку", self)
            menu.addSeparator()
            menu.addAction(reattach_action)
        else:
            reattach_action = None

        action = menu.exec(self.tabBar().mapToGlobal(position))

        if action == rename_tab_action:
            self.rename_tab(index)
        elif action == close_tab_action:
            self.close_tab(index)
        elif action == close_others_action:
            self.close_other_tabs(index)
        elif action == close_right_action:
            self.close_tabs_to_right(index)
        elif action == detach_tab_action:
            self.detach_tab(index)
        elif action == pin_tab_action:
            self.toggle_pin_tab(index)
        elif action == reattach_action:
            self.reattach_tab(index)

    def close_other_tabs(self, current_index: int):
        for i in reversed(range(self.count())):
            if i != current_index and i not in self.pinned_tabs:
                self.removeTab(i)

    def close_tabs_to_right(self, current_index: int):
        for i in reversed(range(current_index + 1, self.count())):
            if i not in self.pinned_tabs:
                self.removeTab(i)

    def toggle_pin_tab(self, index: int):
        current_title = self.tabText(index).replace("📌 ", "")
        if index in self.pinned_tabs:
            self.pinned_tabs.remove(index)
            self.setTabText(index, current_title)
        else:
            self.pinned_tabs.add(index)
            self.setTabText(index, f"📌 {current_title}")

    def reattach_tab(self, _index: int):
        for window in self.detached_windows:
            if window.tabs_widget.count() > 0:
                widget = window.tabs_widget.widget(0)
                title = window.tabs_widget.tabText(0)
                window.tabs_widget.removeTab(0)
                self.add_existing_tab(widget, title)
                if window.tabs_widget.count() == 0:
                    window.close()
                return
