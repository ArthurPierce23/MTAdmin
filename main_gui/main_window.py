import shutil
from platform import platform

from PySide6.QtWidgets import (
    QHBoxLayout, QMenu, QPushButton, QLineEdit, QGroupBox, QTableWidget,
    QTableWidgetItem, QHeaderView, QDialog, QMessageBox, QSizePolicy
)
from PySide6.QtGui import QIcon, QPixmap, QFont, QAction, QKeyEvent, QKeySequence, QValidator
from PySide6.QtCore import Qt, QObject, Signal, QThread
from styles import apply_theme, THEMES
from database.db_manager import (
    add_recent_connection, get_recent_connections,
    add_to_workstation_map, get_workstation_map, init_db
)
from main_gui.utils import is_valid_ip, detect_os
from database.db_manager import remove_from_workstation_map, clear_recent_connections
from PySide6.QtWidgets import QFileDialog, QDialogButtonBox, QSpinBox
from settings import load_settings, save_settings, SETTINGS_FILE
from linux_gui.linux_window import LinuxWindow
from windows_gui.windows_window import WindowsWindow
import platform
from notification import Notification, NotificationManager
from styles import NOTIFICATION_STYLES
import traceback
import logging
from .tab_widgets import DetachableTabWidget


logger = logging.getLogger(__name__)


from PySide6.QtWidgets import QApplication, QMainWindow, QTabWidget, QTabBar, QWidget, QVBoxLayout, QLabel
from PySide6.QtCore import Qt
from .tab_widgets import DetachableTabWidget, DetachableTabBar
from .ui_components import IPLineEdit, ThemeDialog

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
        self.drag_pos = None  # Для обработки перетаскивания
        self.setAcceptDrops(True)
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
        exit_action = self._create_action("Выход", self.close)
        file_menu.addAction(exit_action)

        # Меню "Настройки"
        settings_menu = menubar.addMenu("Настройки")
        theme_action = self._create_action("Тема", self._open_theme_dialog)

        # Дополнительные настройки
        self.advanced_settings_action = self._create_action("Дополнительные настройки", self._open_settings_dialog)
        settings_menu.addActions([theme_action, self.advanced_settings_action])

        # Меню "Экспорт/Импорт"
        export_menu = menubar.addMenu("Экспорт/Импорт")
        self.export_action = self._create_action("Экспорт данных", self._export_settings)  # Используем self.
        self.import_action = self._create_action("Импорт данных", self._import_settings)  # Используем self.
        export_menu.addActions([self.export_action, self.import_action])

        # Меню "Справка"
        help_menu = menubar.addMenu("Справка")
        self.about_action = self._create_action("О программе", self._show_about_dialog)  # Используем self.
        help_menu.addAction(self.about_action)

    def _create_action(self, text, slot, parent=None):
        action = QAction(text, parent or self)
        action.triggered.connect(slot)
        return action

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
        # Подключаем обработчики событий
        self.inner_tabs.lastTabClosed.connect(self._add_default_tab)
        self.inner_tabs.tabPinned.connect(self._on_tab_pinned)
        self.inner_tabs.tabUnpinned.connect(self._on_tab_unpinned)
        self.apply_current_theme()

    def _add_new_tab(self):
        """Обработчик создания новой вкладки по запросу (например, нажатие '+')"""
        print("Adding a new tab...")
        tab = QWidget()  # Создаем новый виджет для вкладки
        tab.setLayout(QVBoxLayout())  # Устанавливаем layout
        tab_index = self.inner_tabs.addTab(tab, "Новая сессия")  # Добавляем вкладку
        self.inner_tabs.setCurrentIndex(tab_index)  # Переключаемся на новую вкладку
        self._setup_tab_content(tab)  # Настраиваем содержимое
        print(f"New tab added and content set: {tab}")

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

        # Инициализация кастомного табвиджета
        self.inner_tabs = DetachableTabWidget()
        self.inner_tabs.tabAdded.connect(self._setup_tab_content)  # Подключаем сигнал
        self.inner_tabs.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.MinimumExpanding)

        # Добавляем первую вкладку по умолчанию
        self._add_default_tab()

        layout.addWidget(self.inner_tabs)

    def _setup_tab_content(self, tab):
        print(f"Setting up content for tab: {tab}")  # Отладочный вывод
        tab.setProperty('pinned', False)
        layout = QVBoxLayout(tab)
        print(f"Layout set for tab: {layout}")  # Проверим, создается ли layout

        self._setup_connection_block(layout, tab)
        self._setup_search(layout, tab)
        self._setup_tables(layout, tab)

        self._load_tab_data(tab)
        update_emitter.data_updated.connect(lambda: self._load_tab_data(tab))

    def _on_tab_pinned(self, index):
        """Обработка закрепления вкладки"""

    def _on_tab_unpinned(self, index):
        """Обработка открепления вкладки"""

    def _add_default_tab(self):
        """Добавление вкладки по умолчанию"""
        tab = QWidget()  # Создаем новый виджет
        self.inner_tabs.addTab(tab, "Новая сессия")  # Добавляем вкладку
        self._setup_tab_content(tab)  # Настраиваем содержимое

    def _update_tab_style(self, index):
        """Обновление стиля закрепленной вкладки"""
        tab_bar = self.inner_tabs.tabBar()
        pinned = self.inner_tabs.widget(index).property('pinned')

        if pinned:
            tab_bar.setTabText(index, f"📌 {tab_bar.tabText(index)}")
            tab_bar.setTabIcon(index, QIcon(":/icons/pin.png"))  # Добавьте свою иконку
        else:
            text = tab_bar.tabText(index).replace("📌 ", "")
            tab_bar.setTabText(index, text)
            tab_bar.setTabIcon(index, QIcon())

    def _create_ip_input_handler(self, input_field):
        def handler(event: QKeyEvent):
            text = input_field.text()
            cursor_pos = input_field.cursorPosition()

            # Разрешаем все управляющие клавиши
            if event.key() in (Qt.Key_Backspace, Qt.Key_Delete,
                               Qt.Key_Left, Qt.Key_Right,
                               Qt.Key_Home, Qt.Key_End):
                return super(QLineEdit, input_field).keyPressEvent(event)

            # Обработка точки
            if event.key() in (Qt.Key_Period, Qt.Key_Space):
                if len(text.split('.')) < 4:
                    input_field.insert('.')
                return True

            # Разрешаем цифры (включая Numpad)
            if event.text().isdigit() or event.key() in range(Qt.Key_0, Qt.Key_9 + 1):
                parts = text.split('.')
                current_part = len(text[:cursor_pos].split('.')) - 1

                if current_part < 4:
                    if len(parts[current_part]) < 3:
                        super(QLineEdit, input_field).keyPressEvent(event)

                        # Автоматическое добавление точки
                        new_text = input_field.text()
                        new_parts = new_text.split('.')
                        if len(new_parts[current_part]) == 3 and current_part < 3:
                            input_field.insert('.')
                    return True

            # Для всех остальных случаев
            return super(QLineEdit, input_field).keyPressEvent(event)

        return handler

    def _setup_connection_block(self, layout, tab):
        """Блок подключения к ПК с кастомным вводом IP"""
        connection_box = QGroupBox("Подключение к ПК")
        conn_layout = QHBoxLayout()

        # Используем наш кастомный виджет для ввода IP
        tab.ip_input = IPLineEdit()
        tab.ip_input.setFixedHeight(28)

        # Кнопка подключения
        tab.connect_btn = QPushButton("Подключиться")
        tab.connect_btn.setShortcut(QKeySequence("Ctrl+Return"))
        tab.connect_btn.setFixedHeight(28)
        tab.connect_btn.clicked.connect(lambda: self._handle_connection(tab))

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
        self._configure_table(tab.recent_table, ["IP", "Дата"])

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
        self._configure_table(tab.workstation_table, ["РМ", "IP", "ОС", "Последнее подключение"], editable_columns=[0])

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

        # Сохраняем изменения номера РМ в БД
        tab.workstation_table.itemChanged.connect(
            lambda item: self._save_workstation_changes(item, tab.workstation_table))

    def _configure_table(self, table, headers, editable_columns=[]):
        table.setColumnCount(len(headers))
        table.setHorizontalHeaderLabels(headers)
        table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        table.setSortingEnabled(True)
        for col in range(len(headers)):
            if col not in editable_columns:
                for row in range(table.rowCount()):
                    if item := table.item(row, col):
                        item.setFlags(item.flags() & ~Qt.ItemIsEditable)

    def _save_workstation_changes(self, item, table):
        """Сохраняет изменения в номере РМ в базе данных"""
        try:
            # Игнорируем программные изменения
            if item.column() != 0 or not table.isPersistentEditorOpen(item):
                return

            row = item.row()
            if row >= table.rowCount():
                return

            ip_item = table.item(row, 1)
            os_item = table.item(row, 2)

            if not ip_item or not os_item:
                return  # Не показываем уведомление

            ip = ip_item.text()
            new_rm = item.text().strip()
            os_name = os_item.text()

            # Обновляем запись в базе данных (пустой RM допустим)
            remove_from_workstation_map(ip)
            add_to_workstation_map(ip, os_name, new_rm)
            # Показываем уведомление только при явном изменении
            self.show_notification("Изменения сохранены", "success")

        except Exception as e:
            logger.error(f"Ошибка сохранения: {str(e)}")

    def _load_tab_data(self, tab):
        """Загрузка данных в таблицы вкладки"""
        self._load_recent_connections(tab.recent_table)
        self._load_workstation_map(tab.workstation_table)

    def _handle_connection(self, tab):
        """Обработка подключения"""
        ip = tab.ip_input.text().strip()

        # Проверка валидности IP через валидатор
        state, _, _ = tab.ip_input.validator().validate(ip, 0)
        if state != QValidator.Acceptable:
            self.show_notification("Неверный формат IP-адреса", "error")
            return

        if not is_valid_ip(ip):
            self.show_notification("Некорректный IP-адрес", "error")
            return

        # Обновленный код обработки подключения
        local_os = platform.system()
        tab.connect_btn.setEnabled(False)
        tab.connect_btn.setText("Проверка...")

        try:
            thread = ConnectionThread(ip)
            thread.finished.connect(
                lambda ip, os_name, err: self._handle_connection_result(tab, ip, os_name, err, thread, local_os))
            self.threads.append(thread)
            thread.start()
        except Exception as e:
            self.show_notification(f"Ошибка запуска потока: {str(e)}", "error")
            tab.connect_btn.setEnabled(True)
            tab.connect_btn.setText("Подключиться")

    def _handle_connection_result(self, tab, ip, os_name, error, thread, local_os):
        try:
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

            # Добавление в историю и карту рабочих мест
            add_recent_connection(ip)
            add_to_workstation_map(ip, os_name)
            self._load_tab_data(tab)
            tab.ip_input.clear()
            update_emitter.data_updated.emit()

            # Создание новой вкладки подключения
            os_tab = self._create_os_tab(os_name, ip)
            self.inner_tabs.addTab(os_tab, f"{os_name} - {ip}")
            # Делаем новую вкладку активной
            self.inner_tabs.setCurrentIndex(self.inner_tabs.indexOf(os_tab))

        except Exception as e:
            self.show_notification(f"Ошибка: {str(e)}", "error")
            logger.error(traceback.format_exc())

    def _create_os_tab(self, os_name, ip):
        os_tab = QWidget()
        os_tab.setAttribute(Qt.WA_DeleteOnClose)
        os_layout = QVBoxLayout(os_tab)
        gui_class = WindowsWindow if os_name == "Windows" else LinuxWindow
        os_layout.addWidget(gui_class(ip=ip, os_name=os_name))
        return os_tab

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
        table.blockSignals(True)
        try:
            data = get_workstation_map()  # <-- Был дубль
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

                    # Настройка флагов редактирования
                    table.item(row, 0).setFlags(Qt.ItemIsEditable | Qt.ItemIsEnabled)

        finally:
            table.blockSignals(False)  # Включаем обратно

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

        # Формат даты
        self.date_format = QLineEdit(current_settings.get("date_format", "dd.MM.yyyy HH:mm"))
        layout.addWidget(QLabel("Формат даты:"))
        layout.addWidget(self.date_format)