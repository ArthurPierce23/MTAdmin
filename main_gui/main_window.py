import shutil
from platform import platform

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QMenu, QLabel, QTabWidget, QPushButton,
    QLineEdit, QGroupBox, QTableWidget, QTableWidgetItem, QHeaderView,
    QDialog, QListWidget, QMessageBox, QSizePolicy
)
from PySide6.QtGui import QIcon, QPixmap, QFont, QAction
from PySide6.QtCore import Qt, QObject, Signal, QThread, QTimer
from styles import apply_theme, THEMES
from database.db_manager import (
    add_recent_connection, get_recent_connections,
    add_to_workstation_map, get_workstation_map, init_db
)
from main_gui.utils import is_valid_ip, detect_os
from database.db_manager import remove_from_workstation_map, clear_recent_connections  # Добавляем функцию удаления
from PySide6.QtWidgets import QFileDialog, QDialogButtonBox, QSpinBox
from settings import load_settings, save_settings, SETTINGS_FILE  # Правильный импорт
from linux_gui.linux_window import LinuxWindow
from windows_gui.windows_window import WindowsWindow
import platform
from notification import Notification, NotificationManager
from styles import NOTIFICATION_STYLES


class ConnectionThread(QThread):
    finished = Signal(str, str, str)  # ip, os_name, error

    def __init__(self, ip):
        super().__init__()
        self.ip = ip

    def run(self):
        try:
            if not is_valid_ip(self.ip):
                self.finished.emit(self.ip, "", "Неверный формат IP")
                return

            os_name = detect_os(self.ip)
            if os_name in ["Недоступен", "Ошибка проверки"]:
                self.finished.emit(self.ip, "", f"Адрес {self.ip} недоступен")
                return

            self.finished.emit(self.ip, os_name, "")  # Передаем данные в основной поток

        except Exception as e:
            self.finished.emit(self.ip, "", f"Ошибка: {str(e)}")

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
        self.setAttribute(Qt.WA_DeleteOnClose)
        self.status_bar = self.statusBar()

        status_widget = QWidget()
        self.notification_layout = QHBoxLayout(status_widget)
        self.notification_label = QLabel()
        self.notification_layout.addWidget(self.notification_label)

        self.status_bar.addPermanentWidget(status_widget)  # <-- Исправлено
        self.threads = []  # Хранение активных потоков
        self.notification_manager = NotificationManager(self)
        self._init_ui()

    def _show_about_dialog(self):
        """Показ информации о программе"""
        about_text = "Здесь будет информация о программе"
        QMessageBox.about(self, "О программе", about_text)

    def show_notification(self, message, style_type="default"):
        style = NOTIFICATION_STYLES.get(style_type, {})
        notification = Notification(self, message, style=style)
        self.notification_manager.add_notification(notification)

    def moveEvent(self, event):
        self.notification_manager._update_positions()
        super().moveEvent(event)

    def resizeEvent(self, event):
        self.notification_manager._update_positions()
        super().resizeEvent(event)

    def showEvent(self, event):
        self.notification_manager._update_positions()
        super().showEvent(event)

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

        # Дополнительные настройки
        self.advanced_settings_action = QAction("Дополнительные настройки", self)
        self.advanced_settings_action.triggered.connect(self._open_settings_dialog)
        settings_menu.addActions([theme_action, self.advanced_settings_action])

        # Меню "Экспорт/Импорт"
        export_menu = menubar.addMenu("Экспорт/Импорт")
        self.export_action = QAction("Экспорт данных", self)  # Используем self.
        self.import_action = QAction("Импорт данных", self)  # Используем self.
        self.export_action.triggered.connect(self._export_settings)  # Переносим сюда
        self.import_action.triggered.connect(self._import_settings)  # Переносим сюда
        export_menu.addActions([self.export_action, self.import_action])

        # Меню "Справка"
        help_menu = menubar.addMenu("Справка")
        self.about_action = QAction("О программе", self)  # Используем self.
        self.about_action.triggered.connect(self._show_about_dialog)
        help_menu.addAction(self.about_action)

    def _open_theme_dialog(self):
        theme_list = list(THEMES.keys())
        dialog = ThemeDialog(theme_list)
        if dialog.exec() == QDialog.Accepted:
            selected_theme = dialog.selected_theme
            if selected_theme:
                self.current_theme = selected_theme
                save_settings({"theme": self.current_theme})
                self.apply_current_theme()
                self.show_notification(f"Тема '{selected_theme}' применена", "success")

    def _init_ui(self):
        """Инициализация интерфейса"""
        self.setWindowTitle("MTAdmin")
        self.resize(800, 800)  # Позволит изменять размер окна
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
        main_layout.addWidget(self.tabs, stretch=1)

        # Вкладка управления ПК
        self._setup_pc_management_tab()
        self.tabs.addTab(QWidget(), "В разработке")  # Заглушка

        self.apply_current_theme()

    def _setup_header(self, layout):
        """Создание шапки с логотипом"""
        header = QHBoxLayout()

        # Логотип
        logo = QLabel()
        try:
            if QPixmap("logo.png").isNull():
                raise FileNotFoundError
            pixmap = QPixmap("logo.png").scaled(50, 50, Qt.KeepAspectRatio)
        except:
            pixmap = QPixmap(50, 50)
            pixmap.fill(Qt.GlobalColor.transparent)

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
        self.inner_tabs.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.MinimumExpanding)
        self._add_session_tab()

    def _add_session_tab(self):
        """Добавление новой сессии"""
        tab = QWidget()
        self.inner_tabs.addTab(tab, "Новая сессия")
        layout = QVBoxLayout(tab)

        # Блок подключения
        self._setup_connection_block(layout, tab)

        # Поиск
        self._setup_search(layout, tab)  # ✅ Передаём tab

        # Таблицы
        self._setup_tables(layout, tab)

        # Первоначальная загрузка данных
        self._load_tab_data(tab)

        update_emitter.data_updated.connect(lambda: self._load_tab_data(tab))

    def _setup_connection_block(self, layout, tab):
        """Блок подключения к ПК"""
        connection_box = QGroupBox("Подключение к ПК")
        conn_layout = QHBoxLayout()

        # Уменьшаем отступы
        conn_layout.setContentsMargins(5, 5, 5, 5)  # Были стандартные
        conn_layout.setSpacing(5)  # Было больше

        tab.ip_input = QLineEdit()
        tab.ip_input.setFixedHeight(28)  # Фиксированная высота
        tab.ip_input.setPlaceholderText("Введите IP-адрес")
        tab.ip_input.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        tab.connect_btn = QPushButton("Подключиться")
        tab.connect_btn.setObjectName("connect_btn")  # Добавить идентификатор
        tab.connect_btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        tab.connect_btn.clicked.connect(lambda: self._handle_connection(tab))
        tab.connect_btn.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)


        conn_layout.addWidget(tab.ip_input)
        conn_layout.addWidget(tab.connect_btn)
        connection_box.setLayout(conn_layout)
        layout.addWidget(connection_box)

    def _export_settings(self):
        path, _ = QFileDialog.getSaveFileName(
            self, "Экспорт настроек", "settings.json", "JSON Files (*.json)"
        )
        if path:
            try:
                shutil.copy(SETTINGS_FILE, path)
                self.show_notification("Настройки успешно экспортированы", "success")
            except Exception as e:
                self.show_notification(f"Ошибка экспорта: {str(e)}", "error")

    def _import_settings(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Импорт настроек", "", "JSON Files (*.json)"
        )
        if path:
            try:
                shutil.copy(path, SETTINGS_FILE)
                self.settings = load_settings()
                self.apply_current_theme()
                self.show_notification("Настройки успешно импортированы", "success")
            except Exception as e:
                self.show_notification(f"Ошибка импорта: {str(e)}", "error")

    def _setup_search(self, layout, tab):
        """Добавляет поля поиска по таблицам"""
        search_layout = QHBoxLayout()

        # Поле поиска по недавним подключениям
        search_recent = QLineEdit()
        search_recent.setPlaceholderText("Поиск в недавних подключениях...")
        search_recent.textChanged.connect(lambda text: self._filter_table(tab.recent_table, text))

        # Поле поиска по карте рабочих мест
        search_map = QLineEdit()
        search_map.setPlaceholderText("Поиск по карте РМ...")
        search_map.textChanged.connect(lambda text: self._filter_table(tab.workstation_table, text))

        search_layout.addWidget(search_recent)
        search_layout.addWidget(search_map)
        layout.addLayout(search_layout)

    def _filter_table(self, table, text):
        """Фильтрует таблицу по введённому тексту"""
        for row in range(table.rowCount()):
            match = False
            for col in range(table.columnCount()):
                item = table.item(row, col)
                if item and text.lower() in item.text().lower():
                    match = True
                    break
            table.setRowHidden(row, not match)

    def _setup_tables(self, layout, tab):
        """Настройка таблиц"""
        tables_layout = QHBoxLayout()

        # === Контейнер для "Недавних подключений" ===
        recent_box = QGroupBox("Недавние подключения")
        recent_layout = QVBoxLayout()

        tab.recent_table = QTableWidget(0, 2)
        tab.recent_table.setHorizontalHeaderLabels(["IP", "Дата"])
        tab.recent_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)

        # Кнопка очистки списка
        clear_recent_btn = QPushButton("Очистить список")
        clear_recent_btn.clicked.connect(lambda: self._clear_recent_connections(tab.recent_table))

        recent_layout.addWidget(tab.recent_table)
        recent_layout.addWidget(clear_recent_btn)
        recent_box.setLayout(recent_layout)

        # === Контейнер для "Карта РМ" ===
        workstation_box = QGroupBox("Карта рабочих мест")
        workstation_layout = QVBoxLayout()

        tab.workstation_table = QTableWidget(0, 4)
        tab.workstation_table.setHorizontalHeaderLabels(["РМ", "IP", "ОС", "Последнее подключение"])
        tab.workstation_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)

        # Добавляем контекстное меню (ПКМ -> Удалить)
        tab.workstation_table.setContextMenuPolicy(Qt.CustomContextMenu)
        tab.workstation_table.customContextMenuRequested.connect(
            lambda pos, t=tab: self._show_context_menu(t.workstation_table, pos)
        )

        workstation_layout.addWidget(tab.workstation_table)
        workstation_box.setLayout(workstation_layout)

        # === Добавляем контейнеры в основной layout ===
        tables_layout.addWidget(recent_box)
        tables_layout.addWidget(workstation_box)
        layout.addLayout(tables_layout)

        # === Подключаем обработчики двойного клика ===
        tab.recent_table.cellDoubleClicked.connect(
            lambda row, col, t=tab: self._handle_recent_double_click(row, col, t)
        )
        tab.workstation_table.cellDoubleClicked.connect(
            lambda row, col, t=tab: self._handle_workstation_double_click(row, col, t)
        )

    def _load_tab_data(self, tab):
        """Загрузка данных в таблицы вкладки"""
        self._load_recent_connections(tab.recent_table)
        self._load_workstation_map(tab.workstation_table)

    def _handle_connection(self, tab):
        """Обработка подключения"""
        ip = tab.ip_input.text().strip()
        if not ip:
            self._show_notification("Введите IP-адрес", error=True)
            return

        if not is_valid_ip(ip):
            self._show_notification("Некорректный IP-адрес", error=True)
            return

        # Определяем ОС локального компьютера
        local_os = platform.system()

        # Блокируем кнопку на время проверки
        tab.connect_btn.setEnabled(False)
        tab.connect_btn.setText("Проверка...")

        # Запускаем проверку ОС в отдельном потоке
        thread = ConnectionThread(ip)
        thread.finished.connect(
            lambda ip, os_name, err: self._handle_connection_result(tab, ip, os_name, err, thread, local_os))
        self.threads.append(thread)  # Добавляем поток в список
        thread.start()

    def _handle_connection_result(self, tab, ip, os_name, error, thread, local_os):
        if thread in self.threads:
            self.threads.remove(thread)
        tab.connect_btn.setEnabled(True)
        tab.connect_btn.setText("Подключиться")

        if error:
            self.show_notification(error, "error")
            return

        if local_os == "Linux" and os_name == "Windows":
            self.show_notification("Подключение к Windows возможно только с Windows!", "error")
            return

        try:
            add_recent_connection(ip)
            add_to_workstation_map(ip, os_name)
            self.show_notification(f"Успешно добавлено: {ip} ({os_name})", "success")
            self._load_tab_data(tab)
            tab.ip_input.clear()
            update_emitter.data_updated.emit()

            os_tab = QWidget()
            os_tab.setAttribute(Qt.WA_DeleteOnClose)
            os_layout = QVBoxLayout(os_tab)

            if os_name == "Windows":
                windows_gui = WindowsWindow(ip=ip, os_name=os_name)
                windows_gui.setAttribute(Qt.WA_DeleteOnClose)
                os_layout.addWidget(windows_gui)
                windows_gui.setMaximumHeight(400)
            else:
                linux_gui = LinuxWindow(ip=ip, os_name=os_name)
                linux_gui.setAttribute(Qt.WA_DeleteOnClose)
                os_layout.addWidget(linux_gui)

            os_tab.setLayout(os_layout)
            self.inner_tabs.addTab(os_tab, f"{os_name} - {ip}")

        except Exception as e:
            self.show_notification(f"Ошибка подключения: {str(e)}", "error")

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
        """Закрытие внутренней вкладки с корректным уничтожением виджета"""
        widget = self.inner_tabs.widget(index)
        if widget:
            widget.deleteLater()  # Инициируем удаление виджета
        if self.inner_tabs.count() > 1:
            self.inner_tabs.removeTab(index)

    def apply_current_theme(self):
        """Применение выбранной темы"""
        self.setStyleSheet(apply_theme(self.current_theme) if self.current_theme != "Без темы" else "")
        self.repaint()

    def _clear_recent_connections(self, table):
        confirm = QMessageBox.question(
            self, "Очистка", "Вы уверены, что хотите очистить список?",
            QMessageBox.Yes | QMessageBox.No
        )
        if confirm == QMessageBox.Yes:
            clear_recent_connections()
            table.setRowCount(0)
            self.show_notification("Список очищен", "success")

    def _show_context_menu(self, table, pos):
        """Показывает контекстное меню"""
        index = table.indexAt(pos)
        if not index.isValid():
            return

        menu = QMenu(self)
        delete_action = QAction("Удалить", self)
        delete_action.triggered.connect(lambda: self._delete_workstation_entry(table, index.row()))
        menu.addAction(delete_action)
        menu.exec(table.viewport().mapToGlobal(pos))

    def _delete_workstation_entry(self, table, row):
        ip_item = table.item(row, 1)
        if ip_item:
            ip = ip_item.text()
            confirm = QMessageBox.question(
                self, "Удаление", f"Удалить {ip} из карты РМ?",
                QMessageBox.Yes | QMessageBox.No
            )
            if confirm == QMessageBox.Yes:
                remove_from_workstation_map(ip)
                table.removeRow(row)
                self.show_notification(f"{ip} удален из Карты РМ", "success")

    def _open_settings_dialog(self):
        dialog = SettingsDialog(self.settings)
        if dialog.exec() == QDialog.Accepted:
            new_settings = {
                "theme": self.settings.get("theme"),
                "timeout": dialog.timeout_input.value(),
                "font_size": dialog.font_size.value()
            }
            save_settings(new_settings)
            self.settings = new_settings
            self._apply_font_settings()

    def _apply_font_settings(self):
        font = QApplication.font()
        font.setPointSize(self.settings.get("font_size", 12))
        QApplication.setFont(font)

class SettingsDialog(QDialog):
    def __init__(self, current_settings):
        super().__init__()
        self.setWindowTitle("Настройки приложения")
        layout = QVBoxLayout()

        # Таймаут подключения
        self.timeout_input = QSpinBox()
        self.timeout_input.setRange(1, 60)
        self.timeout_input.setValue(current_settings.get("timeout", 5))
        layout.addWidget(QLabel("Таймаут подключения (сек):"))
        layout.addWidget(self.timeout_input)

        # Размер шрифта
        self.font_size = QSpinBox()
        self.font_size.setRange(8, 20)
        self.font_size.setValue(current_settings.get("font_size", 12))
        layout.addWidget(QLabel("Размер шрифта:"))
        layout.addWidget(self.font_size)

        # Кнопки
        btn_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        btn_box.accepted.connect(self.accept)
        btn_box.rejected.connect(self.reject)
        layout.addWidget(btn_box)

        self.setLayout(layout)
