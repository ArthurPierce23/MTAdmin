# linux_gui/gui/scripts_block.py

from pathlib import Path
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QPushButton, QListWidget, QGroupBox,
    QListWidgetItem, QMenu, QLineEdit, QHBoxLayout, QLabel,
    QInputDialog, QFileDialog, QMessageBox, QSpacerItem, QSizePolicy, QFrame
)
from PySide6.QtCore import Qt, QUrl, Signal
from PySide6.QtGui import QDesktopServices, QAction
import logging

from linux_gui.scripts import ScriptsManager
from notifications import Notification

logger = logging.getLogger(__name__)


class ScriptsBlock(QWidget):
    """
    Виджет для работы с библиотекой скриптов (sh) удалённого Linux-хоста.

    Позволяет запускать, добавлять, редактировать, переименовывать, удалять скрипты и управлять тегами.
    Также доступны фильтрация по имени и тегам, а также контекстное меню для удобных действий.
    """
    script_executed = Signal(str, str)

    def __init__(self, hostname: str, parent=None):
        super().__init__(parent)
        self.manager = ScriptsManager(hostname)
        self.hostname = hostname
        self._init_ui()
        self.load_scripts()
        self.setMinimumSize(600, 400)

    def _init_ui(self):
        # Основная группа с библиотекой скриптов
        self.group_box = QGroupBox("📜 Библиотека скриптов")
        self.group_box.setObjectName("groupBox")
        group_layout = QVBoxLayout(self.group_box)
        group_layout.setSpacing(10)
        group_layout.setContentsMargins(12, 12, 12, 12)

        # Фильтры: поиск по имени и тегам
        filter_layout = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setObjectName("searchInput")
        self.search_input.setPlaceholderText("🔍 Поиск по имени...")
        self.search_input.setClearButtonEnabled(True)
        self.tag_input = QLineEdit()
        self.tag_input.setObjectName("tagInput")
        self.tag_input.setPlaceholderText("🏷 Фильтр по тегам...")
        self.tag_input.setClearButtonEnabled(True)
        filter_layout.addWidget(QLabel("Фильтры:"))
        filter_layout.addWidget(self.search_input)
        filter_layout.addWidget(self.tag_input)

        # Список скриптов
        self.scripts_list = QListWidget()
        self.scripts_list.setObjectName("scriptsList")
        self.scripts_list.setAlternatingRowColors(True)
        self.scripts_list.setMinimumHeight(200)
        self.scripts_list.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.scripts_list.setContextMenuPolicy(Qt.CustomContextMenu)
        self.scripts_list.customContextMenuRequested.connect(self.show_context_menu)
        self.scripts_list.itemDoubleClicked.connect(self.execute_script)

        # Кнопки
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(10)
        self.add_btn = QPushButton("➕ Добавить скрипт")
        self.add_btn.setObjectName("addScriptButton")
        self.add_btn.setMinimumHeight(40)
        self.tag_btn = QPushButton("🏷 Управление тегами")
        self.tag_btn.setObjectName("manageTagsButton")
        self.tag_btn.setMinimumHeight(40)
        btn_layout.addStretch()
        btn_layout.addWidget(self.add_btn)
        btn_layout.addWidget(self.tag_btn)

        # Подключение сигналов для фильтрации и кнопок
        self.search_input.textChanged.connect(self.filter_scripts)
        self.tag_input.textChanged.connect(self.filter_by_tags)
        self.add_btn.clicked.connect(self.add_script_dialog)
        self.tag_btn.clicked.connect(self.manage_tags_dialog)

        # Компоновка элементов
        group_layout.addLayout(filter_layout)
        group_layout.addWidget(self.scripts_list, 1)
        group_layout.addLayout(btn_layout, 0)

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(12, 12, 12, 12)
        main_layout.setSpacing(10)
        main_layout.addWidget(self.group_box)

        separator = QFrame()
        separator.setObjectName("separator")
        separator.setFrameShape(QFrame.HLine)
        separator.setFrameShadow(QFrame.Sunken)
        main_layout.addWidget(separator)

        self.setLayout(main_layout)

    def load_scripts(self):
        """
        Загружает список скриптов из менеджера и отображает их в списке.
        """
        self.scripts_list.clear()
        for script in self.manager.get_scripts():
            item_text = f"{script['name']}"
            if script.get("tags"):
                tags_str = ", ".join(script.get("tags"))
                item_text += f" [{tags_str}]"
            item = QListWidgetItem(item_text)
            item.setData(Qt.UserRole, script)
            self.scripts_list.addItem(item)

    def filter_scripts(self, text: str):
        """
        Фильтрует скрипты по имени.
        """
        for i in range(self.scripts_list.count()):
            item = self.scripts_list.item(i)
            item.setHidden(text.lower() not in item.text().lower())

    def filter_by_tags(self, text: str):
        """
        Фильтрует скрипты по тегам.
        """
        filter_tags = [t.strip().lower() for t in text.split(",") if t.strip()]
        for i in range(self.scripts_list.count()):
            item = self.scripts_list.item(i)
            script_tags = [t.lower() for t in item.data(Qt.UserRole).get("tags", [])]
            match = all(ft in script_tags for ft in filter_tags)
            item.setHidden(not match)

    def show_context_menu(self, pos):
        """
        Отображает контекстное меню для выбранного скрипта или для пустой области списка.
        """
        menu = QMenu()
        item = self.scripts_list.itemAt(pos)
        if item:
            execute_action = QAction("▶ Запустить", self)
            execute_action.triggered.connect(lambda: self.execute_script(item))
            edit_file_action = QAction("📝 Редактировать скрипт", self)
            edit_file_action.triggered.connect(lambda: self.edit_script_dialog(item))
            rename_action = QAction("✎ Переименовать", self)
            rename_action.triggered.connect(lambda: self.rename_script_dialog(item))
            edit_tags_action = QAction("🏷 Редактировать теги", self)
            edit_tags_action.triggered.connect(lambda: self.edit_tags_dialog(item))
            delete_action = QAction("❌ Удалить", self)
            delete_action.triggered.connect(lambda: self.delete_script_dialog(item))
            menu.addAction(execute_action)
            menu.addAction(edit_file_action)
            menu.addSeparator()
            menu.addAction(rename_action)
            menu.addAction(edit_tags_action)
            menu.addAction(delete_action)
        else:
            refresh_action = QAction("🔄 Обновить список", self)
            refresh_action.triggered.connect(self.load_scripts)
            add_action = QAction("➕ Добавить скрипт", self)
            add_action.triggered.connect(self.add_script_dialog)
            menu.addAction(refresh_action)
            menu.addAction(add_action)
        menu.exec_(self.scripts_list.viewport().mapToGlobal(pos))

    def add_script_dialog(self):
        """
        Открывает диалог выбора файла скрипта и добавляет его в библиотеку.
        """
        path, _ = QFileDialog.getOpenFileName(
            self, "Выберите скрипт", "",
            "Скрипты (*.sh);;Все файлы (*)"
        )
        if path:
            tags, ok = QInputDialog.getText(
                self, "Добавить теги", "Введите теги через запятую:"
            )
            if ok:
                tags_list = [t.strip().lower() for t in tags.split(",") if t.strip()]
                try:
                    self.manager.add_script(path, tags_list)
                    self.load_scripts()
                    Notification("Скрипт успешно добавлен!", "success").show_notification()
                except Exception as e:
                    Notification(f"Ошибка добавления скрипта: {str(e)}", "error").show_notification()

    def rename_script_dialog(self, item):
        """
        Открывает диалог для переименования скрипта.
        """
        script = item.data(Qt.UserRole)
        old_name = script["name"]
        new_name, ok = QInputDialog.getText(
            self, "Переименовать скрипт", "Введите новое имя:", QLineEdit.Normal, old_name
        )
        if ok and new_name and new_name != old_name:
            try:
                new_full_name = f"{new_name}.sh"
                if self.manager.rename_script(script["full_name"], new_full_name):
                    self.load_scripts()
                    Notification("Скрипт успешно переименован", "success").show_notification()
            except Exception as e:
                Notification(f"Ошибка переименования: {str(e)}", "error").show_notification()

    def delete_script_dialog(self, item):
        """
        Подтверждает удаление скрипта и удаляет его из библиотеки.
        """
        script = item.data(Qt.UserRole)
        reply = QMessageBox.question(
            self, "Подтверждение удаления",
            f"Вы уверены, что хотите удалить скрипт '{script['name']}'?",
            QMessageBox.Yes | QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            try:
                self.manager.delete_script(script["full_name"])
                self.load_scripts()
                Notification("Скрипт успешно удален", "success").show_notification()
            except Exception as e:
                Notification(f"Ошибка удаления: {str(e)}", "error").show_notification()

    def edit_tags_dialog(self, item):
        """
        Открывает диалог для редактирования тегов скрипта.
        """
        script = item.data(Qt.UserRole)
        current_tags = ", ".join(script.get("tags", []))
        new_tags, ok = QInputDialog.getText(
            self, "Редактировать теги", "Введите теги через запятую:", text=current_tags
        )
        if ok:
            tags_list = [t.strip().lower() for t in new_tags.split(",") if t.strip()]
            try:
                self.manager.update_tags(script["full_name"], tags_list)
                self.load_scripts()
                Notification("Теги обновлены", "success").show_notification()
            except Exception as e:
                Notification(f"Ошибка обновления тегов: {str(e)}", "error").show_notification()

    def manage_tags_dialog(self):
        """
        Отображает все существующие теги в информационном окне.
        """
        all_tags = set()
        for script in self.manager.get_scripts():
            all_tags.update(script.get("tags", []))
        tags_str = ", ".join(sorted(all_tags))
        QMessageBox.information(self, "Все теги", f"Существующие теги:\n{tags_str}")

    def execute_script(self, item):
        """
        Выполняет выбранный скрипт на удалённом хосте.

        Считывает путь из данных элемента и вызывает метод execute_script менеджера.
        При успешном выполнении или ошибке показывается уведомление.
        """
        script = item.data(Qt.UserRole)
        file_to_execute = script.get("path")
        try:
            self.manager.execute_script(file_to_execute)
            self.script_executed.emit(script["name"], "success")
            Notification(f"Скрипт '{script['name']}' выполнен успешно", "success").show_notification()
        except Exception as e:
            self.script_executed.emit(script["name"], f"error: {str(e)}")
            Notification(f"Ошибка выполнения '{script['name']}': {str(e)}", "error").show_notification()

    def edit_script_dialog(self, item):
        """
        Открывает скрипт в редакторе по умолчанию.
        """
        script = item.data(Qt.UserRole)
        file_to_edit = script.get("path")
        url = QUrl.fromLocalFile(file_to_edit)
        if not QDesktopServices.openUrl(url):
            Notification("Не удалось открыть скрипт в редакторе", "error").show_notification()
