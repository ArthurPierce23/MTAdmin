import os
import sys
import logging
from pathlib import Path
from subprocess import Popen

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QPushButton, QListWidget, QGroupBox,
    QListWidgetItem, QMenu, QLineEdit, QHBoxLayout, QLabel,
    QInputDialog, QFileDialog, QMessageBox, QSpacerItem, QSizePolicy, QFrame, QStyledItemDelegate
)
from PySide6.QtCore import Qt, QUrl, Signal
from PySide6.QtGui import QDesktopServices, QAction, QFontMetrics, QColor, QPainter

from linux_gui.scripts import ScriptsManager
from notifications import Notification

logger = logging.getLogger(__name__)


class ScriptItemDelegate(QStyledItemDelegate):
    """
    Делегат для отрисовки элемента списка скриптов с тегами.
    Теги рисуются в виде округлых облачков справа от названия.
    """

    def paint(self, painter: QPainter, option, index) -> None:
        """
        Отрисовывает элемент списка, включая облачка с тегами.
        """
        # Стандартная отрисовка элемента
        super().paint(painter, option, index)
        script = index.data(Qt.UserRole)
        if script and script.get("tags"):
            painter.save()
            tag_spacing: int = 5
            tag_height: int = 20
            tag_radius: int = 8
            font_metrics = QFontMetrics(option.font)
            # Начинаем рисование с правой границы элемента
            x_pos: int = option.rect.right() - 10
            for tag in reversed(script["tags"]):
                # Вычисляем ширину текста с учётом отступов (5 пикселей слева и справа)
                text_width: int = font_metrics.horizontalAdvance(tag) + 10
                # Определяем прямоугольник для облачка
                tag_rect = option.rect.adjusted(
                    x_pos - text_width,
                    (option.rect.height() - tag_height) // 2,
                    - (option.rect.right() - x_pos),
                    0
                )
                # Если тег выходит за левую границу, прекращаем отрисовку
                if tag_rect.left() < option.rect.left():
                    break
                # Рисуем закруглённый прямоугольник с заливкой
                painter.setBrush(QColor(230, 240, 255))
                painter.setPen(Qt.NoPen)
                painter.drawRoundedRect(tag_rect, tag_radius, tag_radius)
                # Рисуем текст тега внутри прямоугольника
                painter.setPen(QColor(50, 100, 200))
                painter.drawText(tag_rect.adjusted(5, 0, -5, 0), Qt.AlignCenter, tag)
                # Смещаем позицию для следующего облачка
                x_pos -= (text_width + tag_spacing)
            painter.restore()


class ScriptsBlock(QWidget):
    """
    Виджет для работы с библиотекой скриптов (.sh) удалённого Linux-хоста.

    Позволяет запускать, добавлять, редактировать, переименовывать, удалять скрипты
    и управлять тегами. Также доступны фильтрация по имени и тегам, а также контекстное меню
    для удобных действий.
    """
    script_executed = Signal(str, str)

    def __init__(self, hostname: str, parent=None) -> None:
        """
        :param hostname: Имя или IP-адрес удалённого хоста.
        :param parent: Родительский виджет.
        """
        super().__init__(parent)
        self.hostname: str = hostname
        self.manager: ScriptsManager = ScriptsManager(hostname)
        self._init_ui()
        self.load_scripts()
        self.setMinimumSize(600, 400)

    def _init_ui(self) -> None:
        """Инициализирует интерфейс виджета."""
        # Группа для библиотеки скриптов
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
        # Устанавливаем делегат для отрисовки тегов
        self.scripts_list.setItemDelegate(ScriptItemDelegate())

        # Кнопки управления
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

        # Подключаем сигналы для фильтрации и кнопок
        self.search_input.textChanged.connect(self.filter_scripts)
        self.tag_input.textChanged.connect(self.filter_by_tags)
        self.add_btn.clicked.connect(self.add_script_dialog)
        self.tag_btn.clicked.connect(self.manage_tags_dialog)

        # Компоновка элементов внутри группы
        group_layout.addLayout(filter_layout)
        group_layout.addWidget(self.scripts_list, 1)
        group_layout.addLayout(btn_layout, 0)

        # Основной макет виджета
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(12, 12, 12, 12)
        main_layout.setSpacing(10)
        main_layout.addWidget(self.group_box)

        # Разделитель
        separator = QFrame()
        separator.setObjectName("separator")
        separator.setFrameShape(QFrame.HLine)
        separator.setFrameShadow(QFrame.Sunken)
        main_layout.addWidget(separator)

        self.setLayout(main_layout)

    def load_scripts(self) -> None:
        """
        Загружает список скриптов из менеджера и отображает их в списке.
        """
        self.scripts_list.clear()
        for script in self.manager.get_scripts():
            item_text: str = f"{script['name']}"
            item = QListWidgetItem(item_text)
            item.setData(Qt.UserRole, script)
            self.scripts_list.addItem(item)

    def filter_scripts(self, text: str) -> None:
        """
        Фильтрует скрипты по имени.

        :param text: Строка для поиска в имени скрипта.
        """
        for i in range(self.scripts_list.count()):
            item = self.scripts_list.item(i)
            item.setHidden(text.lower() not in item.text().lower())

        if text and all(self.scripts_list.item(i).isHidden() for i in range(self.scripts_list.count())):
            Notification(
                "🔎 Поиск скриптов",
                "По вашему запросу ничего не найдено.",
                "warning",
                parent=self.window()
            ).show_notification()

    def filter_by_tags(self, text: str) -> None:
        """
        Фильтрует скрипты по тегам.

        :param text: Строка с тегами, разделёнными запятыми.
        """
        filter_tags = [t.strip().lower() for t in text.split(",") if t.strip()]
        for i in range(self.scripts_list.count()):
            item = self.scripts_list.item(i)
            script_tags = [t.lower() for t in item.data(Qt.UserRole).get("tags", [])]
            match = all(ft in script_tags for ft in filter_tags)
            item.setHidden(not match)

    def show_context_menu(self, pos) -> None:
        """
        Отображает контекстное меню для выбранного скрипта или для пустой области списка.

        :param pos: Позиция, по которой вызвано контекстное меню.
        """
        menu = QMenu()
        item = self.scripts_list.itemAt(pos)
        if item:
            copy_action = QAction("📋 Копировать содержимое", self)
            copy_action.triggered.connect(lambda: self.copy_script_content(item))
            edit_file_action = QAction("📝 Редактировать скрипт", self)
            edit_file_action.triggered.connect(lambda: self.edit_script_dialog(item))
            rename_action = QAction("✎ Переименовать", self)
            rename_action.triggered.connect(lambda: self.rename_script_dialog(item))
            edit_tags_action = QAction("🏷 Редактировать теги", self)
            edit_tags_action.triggered.connect(lambda: self.edit_tags_dialog(item))
            delete_action = QAction("❌ Удалить", self)
            delete_action.triggered.connect(lambda: self.delete_script_dialog(item))
            menu.addAction(copy_action)
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

    def add_script_dialog(self) -> None:
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
                    Notification(
                        "📜 Новый скрипт",
                        "Скрипт успешно добавлен в библиотеку!",
                        "success",
                        parent=self.window()
                    ).show_notification()

                except Exception as e:
                    logger.exception("Ошибка добавления скрипта")
                    Notification(
                        "🚫 Ошибка добавления",
                        f"Не удалось добавить скрипт.\nОшибка: `{e}`",
                        "error",
                        parent=self.window()
                    ).show_notification()

    def copy_script_content(self, item: QListWidgetItem) -> None:
        """
        Копирует содержимое выбранного скрипта в буфер обмена.

        :param item: Выбранный элемент списка со скриптом.
        """
        script = item.data(Qt.UserRole)
        try:
            self.manager.copy_script_content(script["full_name"])
            Notification(
                "📋 Копирование",
                f"Содержимое скрипта `{script['name']}` скопировано в буфер обмена.",
                "success",
                parent=self.window()
            ).show_notification()

        except Exception as e:
            logger.exception("Ошибка копирования содержимого скрипта")
            Notification(
                "🚫 Ошибка копирования",
                f"Не удалось скопировать содержимое скрипта.\nОшибка: `{e}`",
                "error",
                parent=self.window()
            ).show_notification()

    def rename_script_dialog(self, item: QListWidgetItem) -> None:
        """
        Открывает диалог для переименования скрипта.

        :param item: Выбранный элемент списка со скриптом.
        """
        script = item.data(Qt.UserRole)
        old_name: str = script["name"]
        new_name, ok = QInputDialog.getText(
            self, "Переименовать скрипт", "Введите новое имя:", QLineEdit.Normal, old_name
        )
        if ok and new_name and new_name != old_name:
            try:
                new_full_name = f"{new_name}.sh"
                if self.manager.rename_script(script["full_name"], new_full_name):
                    self.load_scripts()
                    Notification(
                        "✎ Переименование",
                        "Скрипт успешно переименован.",
                        "success",
                        parent=self.window()
                    ).show_notification()

            except Exception as e:
                logger.exception("Ошибка переименования скрипта")
                Notification(
                    "🚫 Ошибка переименования",
                    f"Не удалось переименовать скрипт.\nОшибка: `{e}`",
                    "error",
                    parent=self.window()
                ).show_notification()

    def delete_script_dialog(self, item: QListWidgetItem) -> None:
        """
        Подтверждает удаление скрипта и удаляет его из библиотеки.

        :param item: Выбранный элемент списка со скриптом.
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
                Notification(
                    "🗑 Удаление скрипта",
                    "Скрипт успешно удалён из библиотеки.",
                    "success",
                    parent=self.window()
                ).show_notification()
            except Exception as e:
                logger.exception("Ошибка удаления скрипта")
                Notification(
                    "🚫 Ошибка удаления",
                    f"Не удалось удалить скрипт.\nОшибка: `{e}`",
                    "error",
                    parent=self.window()
                ).show_notification()

    def edit_tags_dialog(self, item: QListWidgetItem) -> None:
        """
        Открывает диалог для редактирования тегов скрипта.

        :param item: Выбранный элемент списка со скриптом.
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
                Notification(
                    "🏷 Обновление тегов",
                    "Теги успешно обновлены.",
                    "success",
                    parent=self.window()
                ).show_notification()
            except Exception as e:
                logger.exception("Ошибка обновления тегов")
                Notification(
                    "🚫 Ошибка обновления тегов",
                    f"Не удалось обновить теги скрипта.\nОшибка: `{e}`",
                    "error",
                    parent=self.window()
                ).show_notification()

    def manage_tags_dialog(self) -> None:
        """
        Отображает все существующие теги в информационном окне.
        """
        all_tags = set()
        for script in self.manager.get_scripts():
            all_tags.update(script.get("tags", []))
        tags_str = ", ".join(sorted(all_tags))
        QMessageBox.information(self, "Все теги", f"Существующие теги:\n{tags_str}")

    def edit_script_dialog(self, item: QListWidgetItem) -> None:
        """
        Открывает скрипт в редакторе по умолчанию.

        Используется функция os.startfile (под Windows) для открытия файла в ассоциированном редакторе.
        В случае ошибки выводится уведомление.

        :param item: Выбранный элемент списка со скриптом.
        """
        script = item.data(Qt.UserRole)
        file_to_edit = script.get("path")
        try:
            os.startfile(file_to_edit)
            logger.info(f"Скрипт '{script['name']}' открыт в редакторе по умолчанию.")
        except Exception as e:
            logger.exception("Ошибка открытия скрипта в редакторе")
            Notification("Ошибка", "Не удалось открыть скрипт в редакторе", "error",
                         parent=self.window()).show_notification()
