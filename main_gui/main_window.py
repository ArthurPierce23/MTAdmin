from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QMenuBar, QMenu, QLabel, QTabWidget, QPushButton,
    QLineEdit, QGroupBox, QTableWidget, QTableWidgetItem, QHeaderView,
    QDialog, QListWidget
)
from PySide6.QtGui import QIcon, QPixmap, QFont, QAction
from PySide6.QtCore import Qt, QObject, Signal
from styles import apply_theme, THEMES
from settings import load_settings, save_settings
from database.db_manager import (
    add_recent_connection, get_recent_connections,
    add_to_workstation_map, get_workstation_map, init_db
)
from main_gui.utils import is_valid_ip, detect_os




class ThemeDialog(QDialog):
    """Диалоговое окно для выбора темы"""

    def __init__(self, theme_list):
        super().__init__()
        self.setWindowTitle("Выбор темы")
        self.setFixedSize(300, 200)

        layout = QVBoxLayout(self)
        self.theme_list = QListWidget()
        self.theme_list.addItems(["Без темы"] + theme_list)

        self.ok_button = QPushButton("OK")
        self.ok_button.clicked.connect(self.accept)

        layout.addWidget(self.theme_list)
        layout.addWidget(self.ok_button)
        self.setStyleSheet(apply_theme("Темная"))

    def get_selected_theme(self):
        return self.theme_list.currentItem().text() if self.theme_list.currentItem() else None


class UpdateEmitter(QObject):
    data_updated = Signal()

    def __init__(self):
        super().__init__()


update_emitter = UpdateEmitter()

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        try:
            init_db()
        except Exception as e:
            print(f"Ошибка инициализации БД: {e}")
            raise

        self.settings = load_settings()
        self.current_theme = self.settings.get("theme", "Без темы")
        self.setAttribute(Qt.WA_DeleteOnClose)  # Для корректной очистки
        self._init_ui()

    def _handle_recent_double_click(self, row, col, tab):
        ip_item = tab.recent_table.item(row, 0)
        if ip_item:
            tab.ip_input.setText(ip_item.text())

    def _handle_workstation_double_click(self, row, col, tab):
        if col == 0:  # Игнорируем столбец "РМ"
            return
        ip_item = tab.workstation_table.item(row, 1)
        if ip_item:
            tab.ip_input.setText(ip_item.text())

    def _create_menubar(self):
        """Создание главного меню"""
        menubar = self.menuBar()

        # Меню "Файл"
        file_menu = menubar.addMenu("Файл")
        exit_action = QAction("Выход", self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        # Меню "Настройки"
        settings_menu = menubar.addMenu("Настройки")
        theme_action = QAction("Тема", self)
        theme_action.triggered.connect(self._open_theme_dialog)
        settings_menu.addAction(theme_action)

        # Меню "Экспорт/Импорт"
        export_menu = menubar.addMenu("Экспорт/Импорт")
        export_action = QAction("Экспорт данных", self)
        import_action = QAction("Импорт данных", self)
        export_menu.addActions([export_action, import_action])

        # Меню "Справка"
        help_menu = menubar.addMenu("Справка")
        about_action = QAction("О программе", self)
        help_menu.addAction(about_action)

    def _open_theme_dialog(self):
        """Открытие диалогового окна выбора темы"""
        theme_list = list(THEMES.keys())  # Получаем список доступных тем
        dialog = ThemeDialog(theme_list)  # Передаем список тем в диалог
        if dialog.exec() == QDialog.Accepted:
            selected_theme = dialog.get_selected_theme()
            if selected_theme:
                self.current_theme = selected_theme
                save_settings({"theme": self.current_theme})  # Сохранение выбранной темы
                self.apply_current_theme()  # Применение новой темы

    def _init_ui(self):
        """Инициализация интерфейса"""
        self.setWindowTitle("MTAdmin")
        self.setFixedSize(800, 800)

        # Добавляем меню
        self._create_menubar()  # <-- Важная строка!

        # Центральный виджет
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)

        # Шапка
        self._setup_header(main_layout)

        # Основные вкладки
        self.tabs = QTabWidget()
        main_layout.addWidget(self.tabs)

        # Вкладка управления ПК
        self._setup_pc_management_tab()
        self.tabs.addTab(QWidget(), "В разработке")  # Заглушка

        self.apply_current_theme()

    def _setup_header(self, layout):
        """Создание шапки с логотипом"""
        header = QHBoxLayout()

        # Логотип
        logo = QLabel()
        pixmap = QPixmap("logo.png").scaled(50, 50, Qt.KeepAspectRatio)
        logo.setPixmap(pixmap)

        # Заголовок
        title = QLabel("MTAdmin")
        title.setFont(QFont("Arial", 20, QFont.Bold))

        header.addWidget(logo)
        header.addWidget(title)
        header.addStretch()
        layout.addLayout(header)

    def _setup_pc_management_tab(self):
        """Создание вкладки управления ПК"""
        tab = QWidget()
        self.tabs.addTab(tab, "Управление ПК")
        layout = QVBoxLayout(tab)

        # Внутренние вкладки
        self.inner_tabs = QTabWidget()
        self.inner_tabs.setTabsClosable(True)
        self.inner_tabs.tabCloseRequested.connect(self._close_inner_tab)

        # Кнопка добавления вкладок
        add_btn = QPushButton("+")
        add_btn.clicked.connect(self._add_session_tab)
        self.inner_tabs.setCornerWidget(add_btn, Qt.TopRightCorner)

        layout.addWidget(self.inner_tabs)
        self._add_session_tab()

    def _add_session_tab(self):
        """Добавление новой сессии"""
        tab = QWidget()
        self.inner_tabs.addTab(tab, "Новая сессия")
        layout = QVBoxLayout(tab)

        # Блок подключения
        self._setup_connection_block(layout, tab)

        # Поиск
        self._setup_search(layout)

        # Таблицы
        self._setup_tables(layout, tab)

        # Первоначальная загрузка данных
        self._load_tab_data(tab)

        update_emitter.data_updated.connect(lambda: self._load_tab_data(tab))

    def _setup_connection_block(self, layout, tab):
        """Блок подключения к ПК"""
        connection_box = QGroupBox("Подключение к ПК")
        conn_layout = QHBoxLayout()

        tab.ip_input = QLineEdit()
        tab.ip_input.setPlaceholderText("Введите IP-адрес")

        connect_btn = QPushButton("Подключиться")
        connect_btn.clicked.connect(lambda: self._handle_connection(tab))

        conn_layout.addWidget(tab.ip_input)
        conn_layout.addWidget(connect_btn)
        connection_box.setLayout(conn_layout)
        layout.addWidget(connection_box)

    def _setup_search(self, layout):
        """Поля поиска"""
        search_layout = QHBoxLayout()

        self.search_recent = QLineEdit()
        self.search_recent.setPlaceholderText("Поиск в недавних подключениях...")

        self.search_map = QLineEdit()
        self.search_map.setPlaceholderText("Поиск по карте РМ...")

        search_layout.addWidget(self.search_recent)
        search_layout.addWidget(self.search_map)
        layout.addLayout(search_layout)

    def _setup_tables(self, layout, tab):
        """Настройка таблиц"""
        tables_layout = QHBoxLayout()

        # Таблица недавних подключений
        tab.recent_table = QTableWidget(0, 2)
        tab.recent_table.setHorizontalHeaderLabels(["IP", "Дата"])
        tab.recent_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)

        # Таблица рабочих мест
        tab.workstation_table = QTableWidget(0, 4)
        tab.workstation_table.setHorizontalHeaderLabels(["РМ", "IP", "ОС", "Последнее подключение"])
        tab.workstation_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)

        # После создания tab.recent_table и tab.workstation_table:
        tab.recent_table.cellDoubleClicked.connect(
            lambda row, col, t=tab: self._handle_recent_double_click(row, col, t)
        )
        tab.workstation_table.cellDoubleClicked.connect(
            lambda row, col, t=tab: self._handle_workstation_double_click(row, col, t)
        )

        tables_layout.addWidget(tab.recent_table)
        tables_layout.addWidget(tab.workstation_table)
        layout.addLayout(tables_layout)

    def _load_tab_data(self, tab):
        """Загрузка данных в таблицы вкладки"""
        self._load_recent_connections(tab.recent_table)
        self._load_workstation_map(tab.workstation_table)

    def _handle_connection(self, tab):
        """Обработка подключения"""
        ip = tab.ip_input.text().strip()

        if not is_valid_ip(ip):
            print("Некорректный IP-адрес")
            return

        os_name = detect_os(ip)

        # Добавляем подключение в таблицу недавних подключений
        add_recent_connection(ip)

        # Добавляем или обновляем запись в карте рабочих мест
        add_to_workstation_map(ip, os_name)

        # Загружаем обновлённые данные в таблицы
        self._load_tab_data(tab)
        tab.ip_input.clear()

        update_emitter.data_updated.emit()  # <-- Добавить эту строку

    def _load_recent_connections(self, table):
        """Загрузка недавних подключений"""
        data = get_recent_connections()
        table.setRowCount(len(data))

        for row, (ip, date) in enumerate(data):
            ip_item = QTableWidgetItem(ip)
            ip_item.setFlags(ip_item.flags() & ~Qt.ItemIsEditable)
            date_item = QTableWidgetItem(date)
            date_item.setFlags(date_item.flags() & ~Qt.ItemIsEditable)
            table.setItem(row, 0, ip_item)
            table.setItem(row, 1, date_item)

    def _load_workstation_map(self, table):
        """Загрузка карты рабочих мест"""
        data = get_workstation_map()
        table.setRowCount(len(data))

        for row, (rm, ip, os_name, last_seen) in enumerate(data):
            table.setItem(row, 0, QTableWidgetItem(rm))
            table.setItem(row, 1, QTableWidgetItem(ip))
            table.setItem(row, 2, QTableWidgetItem(os_name))
            table.setItem(row, 3, QTableWidgetItem(last_seen))

            # Настройка редактирования
            for col in range(1, 4):
                item = table.item(row, col)
                item.setFlags(item.flags() & ~Qt.ItemIsEditable)

            table.item(row, 0).setFlags(Qt.ItemIsEditable | Qt.ItemIsEnabled)

    def _close_inner_tab(self, index):
        """Закрытие внутренней вкладки"""
        if self.inner_tabs.count() > 1:
            self.inner_tabs.removeTab(index)

    def apply_current_theme(self):
        """Применение выбранной темы"""
        if self.current_theme == "Без темы":
            self.setStyleSheet("")
        else:
            self.setStyleSheet(apply_theme(self.current_theme))
        self.repaint()


if __name__ == "__main__":
    app = QApplication([])
    window = MainWindow()
    window.show()
    app.exec()
