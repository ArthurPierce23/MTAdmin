# tab_widgets.py
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QTabWidget, QMenu, QMainWindow, QMessageBox, QInputDialog
)
from PySide6.QtCore import Qt
# Импортируем модифицированный PCConnectionBlock
from main_gui.gui.pc_connection_block import PCConnectionBlock
# Импортируем другие виджеты (например, RecentConnectionsBlock, WPMapBlock)
from main_gui.gui.recent_connections_block import RecentConnectionsBlock
from main_gui.gui.wp_map_block import WPMapBlock
# Импорт окон для подключения
from windows_gui.gui.windows_window import WindowsWindow
from linux_gui.gui.linux_window import LinuxWindow
from main_gui.utils import detect_os, get_pc_name

class DetachedWindow(QMainWindow):
    def __init__(self, tabs_widget: 'DynamicTabs', parent: 'DynamicTabs', title: str):
        """
        tabs_widget – экземпляр DynamicTabs, который будет центральным виджетом.
        parent – родительское DynamicTabs, куда можно вернуть вкладки.
        """
        super().__init__()
        self.setWindowTitle(title)
        self.setGeometry(200, 200, 500, 600)
        self.setCentralWidget(tabs_widget)
        self.tabs_widget = tabs_widget
        self.parent_tabs = parent  # Запоминаем главное окно

    def closeEvent(self, event):
        """
        При закрытии окна переносим все вкладки обратно в главное окно.
        Добавлена проверка на наличие окна в списке.
        """
        for i in reversed(range(self.tabs_widget.count())):
            widget = self.tabs_widget.widget(i)
            title = self.tabs_widget.tabText(i)
            if isinstance(self.parent_tabs, DynamicTabs):
                self.parent_tabs.add_existing_tab(widget, title)
                if self in self.parent_tabs.detached_windows:  # Проверка на наличие окна в списке
                    self.parent_tabs.detached_windows.remove(self)
        super().closeEvent(event)

class DynamicTabs(QTabWidget):
    def __init__(self, with_initial_tab=True):
        super().__init__()
        self.setTabsClosable(True)
        self.tabCloseRequested.connect(self.close_tab)
        self.setMovable(True)
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.detached_windows = []
        self.pinned_tabs = set()
        self.customContextMenuRequested.connect(self.open_context_menu)
        self.addTabButton = QPushButton("+")
        self.addTabButton.setFixedSize(30, 30)
        self.addTabButton.setStyleSheet("""
            QPushButton {
                font-size: 18px;
                background-color: #f0f0f0;
                border: 1px solid #ccc;
                border-radius: 5px;
                margin-bottom: 5px;
            }
            QPushButton:hover {
                background-color: #e0e0e0;
            }
        """)
        self.addTabButton.clicked.connect(self.add_new_tab)

        corner_container = QWidget()
        corner_layout = QHBoxLayout(corner_container)
        corner_layout.setContentsMargins(0, 0, 0, 0)
        corner_layout.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        corner_layout.addWidget(self.addTabButton)
        self.setCornerWidget(corner_container, Qt.TopRightCorner)
        self.setStyleSheet("QTabWidget::corner { background: transparent; }")

        if with_initial_tab:
            self.add_new_tab()

    @staticmethod
    def create_tab_content(parent_tabs: 'DynamicTabs'):
        new_tab = QWidget()
        main_layout = QVBoxLayout()

        # Создаем блок недавних подключений
        recent_connections_block = RecentConnectionsBlock()
        wp_map_block = WPMapBlock()  # 🔥 Объявляем wp_map_block перед использованием
        # 🔥 Передаем wp_map_block в PCConnectionBlock
        connection_block = PCConnectionBlock(recent_connections_block=recent_connections_block,
                                             wp_map_block=wp_map_block)

        # !!! ВАЖНО: Передаем тот же самый PCConnectionBlock в WPMapBlock !!!
        wp_map_block = WPMapBlock(pc_connection_block=connection_block)

        # Передаем PCConnectionBlock в RecentConnectionsBlock (уже было)
        recent_connections_block.pc_connection_block = connection_block

        # Подключаем сигнал успешного подключения к обработчику DynamicTabs
        connection_block.connection_successful.connect(parent_tabs.handle_connection)

        # Добавляем в макет
        main_layout.addWidget(connection_block)

        bottom_widget = QWidget()
        bottom_layout = QHBoxLayout()
        bottom_layout.addWidget(recent_connections_block)
        bottom_layout.addWidget(wp_map_block)

        bottom_widget.setLayout(bottom_layout)
        main_layout.addWidget(bottom_widget)

        new_tab.setLayout(main_layout)
        return new_tab

    def add_new_tab(self, _checked=False, title="Новая сессия"):
        content = self.create_tab_content(self)
        index = self.addTab(content, title)
        self.setCurrentIndex(index)

    def add_existing_tab(self, widget, title="Новая сессия"):
        index = self.addTab(widget, title)
        self.setCurrentIndex(index)

    def handle_connection(self, os_name: str, pc_name: str, ip: str):
        """
        Обработка сигнала успешного подключения.
        В зависимости от типа ОС добавляем новую вкладку с соответствующим интерфейсом.
        """
        if os_name == "Windows":
            self.open_windows_gui(pc_name, ip)
        elif os_name == "Linux":
            self.open_linux_gui(ip)
        else:
            QMessageBox.warning(self, "Ошибка", "Не удалось определить операционную систему.")

    def open_windows_gui(self, hostname, ip):
        # Создаём виджет интерфейса для Windows и добавляем его как новую вкладку.
        windows_widget = WindowsWindow(hostname, ip)
        self.add_existing_tab(windows_widget, f"Windows: {hostname}")

    def open_linux_gui(self, ip):
        # Создаём виджет интерфейса для Linux и добавляем его как новую вкладку.
        linux_widget = LinuxWindow(ip)
        self.add_existing_tab(linux_widget, f"Linux: {ip}")

    def detach_tab(self, index):
        """
        Отрывает вкладку в отдельное окно.
        Если вкладка закреплена или это единственная вкладка – отрыв не производится.
        """
        if index in self.pinned_tabs or self.count() == 1:
            return

        title = self.tabText(index)
        widget = self.widget(index)
        self.removeTab(index)

        # Создаём новый экземпляр DynamicTabs без автодобавления вкладки
        detached_tabs = DynamicTabs(with_initial_tab=False)
        detached_tabs.add_existing_tab(widget, title)

        # Создаём новое окно
        detached_window = DetachedWindow(detached_tabs, self, title)
        self.detached_windows.append(detached_window)
        detached_window.show()

    def close_tab(self, index):
        """
        Закрывает вкладку и сессию, если она открыта.
        """
        if index in self.pinned_tabs or self.count() == 1:
            return

        widget = self.widget(index)
        if hasattr(widget, 'has_unsaved_changes') and widget.has_unsaved_changes():
            reply = QMessageBox.question(self, 'Подтверждение закрытия',
                                         'У вас есть несохраненные изменения. Закрыть вкладку?',
                                         QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                                         QMessageBox.StandardButton.No)
            if reply == QMessageBox.StandardButton.No:
                return

        # Закрываем сессию перед удалением вкладки
        if hasattr(widget, 'close_session'):
            widget.close_session()

        self.removeTab(index)

    def open_context_menu(self, position):
        menu = QMenu()
        index = self.tabBar().tabAt(position)
        if index == -1:
            return  # Клик вне вкладки

        # Действия для контекстного меню
        rename_tab_action = menu.addAction("Переименовать вкладку")
        if index in self.pinned_tabs:
            pin_tab_action = menu.addAction("Открепить вкладку")
        else:
            pin_tab_action = menu.addAction("Закрепить вкладку")
        detach_tab_action = menu.addAction("Открыть в новом окне")
        close_tab_action = menu.addAction("Закрыть вкладку")
        close_others_action = menu.addAction("Закрыть другие вкладки")
        close_right_action = menu.addAction("Закрыть вкладки справа")
        # Если есть отсоединённые окна, предлагаем вернуть вкладку
        reattach_action = None
        if any(w.tabs_widget.count() > 0 for w in self.detached_windows):
            reattach_action = menu.addAction("Вернуть вкладку в главное окно")

        action = menu.exec(self.tabBar().mapToGlobal(position))

        if action == rename_tab_action:
            new_title, ok = QInputDialog.getText(self, 'Переименовать вкладку', 'Введите новое название:')
            if ok and new_title:
                if index in self.pinned_tabs:
                    self.setTabText(index, f"📌 {new_title}")
                else:
                    self.setTabText(index, new_title)
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

    def close_other_tabs(self, current_index):
        for i in reversed(range(self.count())):
            if i != current_index and i not in self.pinned_tabs:
                self.removeTab(i)

    def close_tabs_to_right(self, current_index):
        for i in reversed(range(current_index + 1, self.count())):
            if i not in self.pinned_tabs:
                self.removeTab(i)

    def toggle_pin_tab(self, index):
        """
        Закрепляет или открепляет вкладку.
        """
        current_title = self.tabText(index).replace("📌 ", "")
        if index in self.pinned_tabs:
            self.pinned_tabs.remove(index)
            self.setTabText(index, current_title)
        else:
            self.pinned_tabs.add(index)
            self.setTabText(index, f"📌 {current_title}")

    def reattach_tab(self, _index):
        """
        Возвращает вкладку обратно в основное окно.
        """
        for window in self.detached_windows:
            if window.tabs_widget.count() > 0:
                widget = window.tabs_widget.widget(0)
                title = window.tabs_widget.tabText(0)
                window.tabs_widget.removeTab(0)
                self.add_existing_tab(widget, title)
                if window.tabs_widget.count() == 0:
                    window.close()
                return

def handle_connection(self, os_name: str, pc_name: str, ip: str):
    """
    Обработка сигнала успешного подключения.
    В зависимости от типа ОС добавляем новую вкладку с соответствующим интерфейсом.
    """
    try:
        if os_name == "Windows":
            self.open_windows_gui(pc_name, ip)
        elif os_name == "Linux":
            self.open_linux_gui(ip)
        else:
            QMessageBox.warning(self, "Ошибка", "Не удалось определить операционную систему.")
    except Exception as e:
        QMessageBox.critical(self, "Ошибка подключения", f"Не удалось установить сессию: {str(e)}")


def open_windows_gui(self, hostname, ip):
    try:
        windows_widget = WindowsWindow(hostname, ip)
        self.add_existing_tab(windows_widget, f"Windows: {hostname}")
    except Exception as e:
        QMessageBox.critical(self, "Ошибка подключения", f"Не удалось подключиться к {hostname}: {str(e)}")


def open_linux_gui(self, ip):
    linux_window = LinuxWindow(ip)
    self.add_existing_tab(linux_window, f"Linux: {ip}")
