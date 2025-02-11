from pathlib import Path
import subprocess

from PySide6.QtCore import Qt, QSize, Signal, QRect, QUrl
from PySide6.QtGui import QColor, QPainter, QFontMetrics, QIcon, QAction, QDesktopServices, QFont
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QPushButton, QListWidget, QGroupBox,
    QListWidgetItem, QMenu, QLineEdit, QHBoxLayout, QLabel,
    QInputDialog, QStyledItemDelegate, QFileDialog, QMessageBox, QSpacerItem, QSizePolicy, QFrame
)

from notifications import Notification
from windows_gui.scripts import ScriptsManager

# Логирование можно добавить, если оно настроено в проекте
import logging
logger = logging.getLogger(__name__)


class ScriptItemDelegate(QStyledItemDelegate):
    """
    Делегат для отрисовки элемента списка скриптов с тегами.
    """
    def paint(self, painter: QPainter, option, index) -> None:
        # Сначала рисуем стандартное представление элемента
        super().paint(painter, option, index)
        script = index.data(Qt.UserRole)
        if script and script.get('tags'):
            painter.save()
            # Параметры отступов и стиля для тегов
            tag_spacing = 5
            tag_height = 20
            tag_radius = 8
            font_metrics = QFontMetrics(option.font)

            # Начинаем рисовать теги справа (отступ 10px от правого края)
            x_pos = option.rect.right() - 10

            # Рисуем теги в обратном порядке
            for tag in reversed(script['tags']):
                text_width = font_metrics.horizontalAdvance(tag) + 20
                tag_rect = QRect(
                    x_pos - text_width,
                    option.rect.top() + (option.rect.height() - tag_height) // 2,
                    text_width,
                    tag_height
                )
                # Если тег выходит за левую границу – прекращаем рисовать
                if tag_rect.left() < option.rect.left():
                    break

                painter.setBrush(QColor(230, 240, 255))
                painter.setPen(Qt.NoPen)
                painter.drawRoundedRect(tag_rect, tag_radius, tag_radius)
                painter.setPen(QColor(50, 100, 200))
                painter.drawText(tag_rect.adjusted(5, 0, -5, 0), Qt.AlignCenter, tag)
                x_pos -= text_width + tag_spacing
            painter.restore()


class ScriptsBlock(QWidget):
    """
    Виджет для работы с библиотекой скриптов:
    запуск, добавление, редактирование, переименовывание, удаление и управление тегами.
    """
    script_executed = Signal(str, str)  # (script_name, статус)

    def __init__(self, hostname: str, parent: QWidget = None) -> None:
        """
        Инициализирует виджет библиотеки скриптов.
        """
        super().__init__(parent)
        self.manager = ScriptsManager(hostname)
        self._init_ui()
        self.load_scripts()
        self.setMinimumSize(600, 400)

    def _init_ui(self) -> None:
        """Инициализирует пользовательский интерфейс."""
        self.group_box = QGroupBox("📜 Библиотека скриптов")
        self.group_box.setObjectName("groupBox")  # Стилизация через styles.py

        group_layout = QVBoxLayout(self.group_box)
        group_layout.setSpacing(10)
        group_layout.setContentsMargins(12, 12, 12, 12)

        # Фильтры: поиск по имени и тегам
        filter_layout = QHBoxLayout()
        filter_layout.setSpacing(10)

        filter_label = QLabel("Фильтры:")
        filter_layout.addWidget(filter_label)

        self.search_input = QLineEdit()
        self.search_input.setObjectName("searchInput")
        self.search_input.setPlaceholderText("🔍 Поиск по имени...")
        self.search_input.setClearButtonEnabled(True)
        self.search_input.setToolTip("Введите текст для поиска скриптов по имени")
        filter_layout.addWidget(self.search_input)

        self.tag_input = QLineEdit()
        self.tag_input.setObjectName("tagInput")
        self.tag_input.setPlaceholderText("🏷 Фильтр по тегам...")
        self.tag_input.setClearButtonEnabled(True)
        self.tag_input.setToolTip("Введите теги через запятую для фильтрации")
        filter_layout.addWidget(self.tag_input)

        filter_layout.addItem(QSpacerItem(20, 10, QSizePolicy.Expanding, QSizePolicy.Minimum))

        # Список скриптов
        self.scripts_list = QListWidget()
        self.scripts_list.setObjectName("scriptsList")
        self.scripts_list.setItemDelegate(ScriptItemDelegate())
        self.scripts_list.setContextMenuPolicy(Qt.CustomContextMenu)
        self.scripts_list.setAlternatingRowColors(True)
        self.scripts_list.setMinimumHeight(200)
        self.scripts_list.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        # Кнопки
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(10)

        self.add_btn = QPushButton("➕ Добавить скрипт")
        self.add_btn.setObjectName("addScriptButton")
        self.add_btn.setMinimumHeight(40)
        self.add_btn.setCursor(Qt.PointingHandCursor)
        self.add_btn.setToolTip("Добавить новый скрипт в библиотеку")

        self.tag_btn = QPushButton("🏷 Управление тегами")
        self.tag_btn.setObjectName("manageTagsButton")
        self.tag_btn.setMinimumHeight(40)
        self.tag_btn.setCursor(Qt.PointingHandCursor)
        self.tag_btn.setToolTip("Просмотреть и управлять существующими тегами")

        btn_layout.addStretch()
        btn_layout.addWidget(self.add_btn)
        btn_layout.addWidget(self.tag_btn)
        btn_layout.addStretch()

        # Подключаем сигналы
        self.search_input.textChanged.connect(self.apply_filters)
        self.tag_input.textChanged.connect(self.apply_filters)
        self.scripts_list.customContextMenuRequested.connect(self.show_context_menu)
        self.scripts_list.itemDoubleClicked.connect(self.execute_script)
        self.add_btn.clicked.connect(self.add_script_dialog)
        self.tag_btn.clicked.connect(self.manage_tags_dialog)

        group_layout.addLayout(filter_layout)
        group_layout.addWidget(self.scripts_list, 1)
        group_layout.addLayout(btn_layout)

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

    def _notify(self, message: str, notif_type: str = "success", duration: int = 3000) -> None:
        """
        Унифицированный метод показа уведомлений.
        """
        Notification(message, notif_type, duration, parent=self.window()).show_notification()

    def load_scripts(self) -> None:
        """
        Загружает список скриптов из менеджера и отображает их.
        """
        self.scripts_list.clear()
        try:
            scripts = self.manager.get_scripts()
            for script in scripts:
                item_text = f"{script['name']} [{script['type']}]"
                item = QListWidgetItem(item_text)
                item.setData(Qt.UserRole, script)
                self.scripts_list.addItem(item)
            self.apply_filters()
            logger.info("Скрипты успешно загружены")
            Notification(
                "✅ Скрипты загружены",
                "Список скриптов успешно обновлён.",
                "success",
                duration=3000,
                parent=self.window()
            ).show_notification()
        except Exception as e:
            logger.error(f"Ошибка загрузки скриптов: {e}")
            Notification(
                "❌ Ошибка загрузки скриптов",
                f"Не удалось загрузить скрипты: {e}",
                "error",
                duration=3000,
                parent=self.window()
            ).show_notification()

    def apply_filters(self) -> None:
        """
        Фильтрует скрипты по имени и тегам.
        (Можно рассмотреть переход на QSortFilterProxyModel для больших объёмов данных)
        """
        search_text = self.search_input.text().lower().strip()
        tag_text = self.tag_input.text().lower().strip()
        filter_tags = [t.strip() for t in tag_text.split(',') if t.strip()]

        for i in range(self.scripts_list.count()):
            item = self.scripts_list.item(i)
            script = item.data(Qt.UserRole)
            name_match = search_text in item.text().lower() if search_text else True
            script_tags = [t.lower() for t in script.get('tags', [])]
            tags_match = all(ft in script_tags for ft in filter_tags) if filter_tags else True
            item.setHidden(not (name_match and tags_match))

    def show_context_menu(self, pos) -> None:
        """
        Отображает контекстное меню для выбранного скрипта или для пустой области.
        """
        menu = QMenu()
        item = self.scripts_list.itemAt(pos)
        if item:
            execute_action = QAction("▶ Запустить", self)
            execute_action.triggered.connect(lambda _, itm=item: self.execute_script(itm))
            edit_file_action = QAction("📝 Редактировать скрипт", self)
            edit_file_action.triggered.connect(lambda _, itm=item: self.edit_script_dialog(itm))
            rename_action = QAction("✎ Переименовать", self)
            rename_action.triggered.connect(lambda _, itm=item: self.rename_script_dialog(itm))
            edit_tags_action = QAction("🏷 Редактировать теги", self)
            edit_tags_action.triggered.connect(lambda _, itm=item: self.edit_tags_dialog(itm))
            delete_action = QAction("❌ Удалить", self)
            delete_action.triggered.connect(lambda _, itm=item: self.delete_script_dialog(itm))
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

    def add_script_dialog(self) -> None:
        """
        Открывает диалог для выбора файла скрипта и добавляет его в библиотеку.
        """
        path, _ = QFileDialog.getOpenFileName(
            self, "Выберите скрипт", "",
            "Скрипты (*.ps1 *.bat *.cmd *.vbs);;Все файлы (*)"
        )
        if path:
            tags, ok = QInputDialog.getText(
                self, "Добавить теги", "Введите теги через запятую:"
            )
            if ok:
                tags_list = [t.strip().lower() for t in tags.split(',') if t.strip()]
                try:
                    self.manager.add_script(path, tags_list)
                    self.load_scripts()
                    Notification(
                        "✅ Скрипт добавлен",
                        "Скрипт успешно добавлен в библиотеку.",
                        "success",
                        duration=3000,
                        parent=self.window()
                    ).show_notification()
                except Exception as e:
                    logger.error(f"Ошибка добавления скрипта: {e}")
                    Notification(
                        "❌ Ошибка добавления скрипта",
                        f"Не удалось добавить скрипт: {e}",
                        "error",
                        duration=3000,
                        parent=self.window()
                    ).show_notification()

    def rename_script_dialog(self, item: QListWidgetItem) -> None:
        """
        Открывает диалог для переименования скрипта.
        """
        script = item.data(Qt.UserRole)
        old_name = script['name']
        new_name, ok = QInputDialog.getText(
            self, "Переименовать скрипт", "Введите новое имя:", QLineEdit.Normal, old_name
        )
        if ok and new_name and new_name != old_name:
            try:
                extension = Path(script['full_name']).suffix
                new_full_name = f"{new_name}{extension}"
                if self.manager.rename_script(script['full_name'], new_full_name):
                    self.load_scripts()
                    Notification(
                        "✅ Скрипт переименован",
                        "Скрипт успешно переименован.",
                        "success",
                        duration=3000,
                        parent=self.window()
                    ).show_notification()
            except Exception as e:
                logger.error(f"Ошибка переименования: {e}")
                Notification(
                    "❌ Ошибка переименования",
                    f"Не удалось переименовать скрипт: {e}",
                    "error",
                    duration=3000,
                    parent=self.window()
                ).show_notification()

    def delete_script_dialog(self, item: QListWidgetItem) -> None:
        """
        Подтверждает удаление скрипта и удаляет его.
        """
        script = item.data(Qt.UserRole)
        reply = QMessageBox.question(
            self, "Подтверждение удаления",
            f"Вы уверены, что хотите удалить скрипт '{script['name']}'?",
            QMessageBox.Yes | QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            try:
                self.manager.delete_script(script['full_name'])
                self.load_scripts()
                Notification(
                    "✅ Скрипт удалён",
                    "Скрипт успешно удалён из библиотеки.",
                    "success",
                    duration=3000,
                    parent=self.window()
                ).show_notification()
            except Exception as e:
                logger.error(f"Ошибка удаления: {e}")
                Notification(
                    "❌ Ошибка удаления",
                    f"Не удалось удалить скрипт: {e}",
                    "error",
                    duration=3000,
                    parent=self.window()
                ).show_notification()

    def edit_tags_dialog(self, item: QListWidgetItem) -> None:
        """
        Открывает диалог для редактирования тегов скрипта.
        """
        script = item.data(Qt.UserRole)
        current_tags = ", ".join(script.get('tags', []))
        new_tags, ok = QInputDialog.getText(
            self, "Редактировать теги", "Введите теги через запятую:", text=current_tags
        )
        if ok:
            tags_list = [t.strip().lower() for t in new_tags.split(',') if t.strip()]
            unique_tags = list(dict.fromkeys(tags_list))
            try:
                self.manager.update_tags(script['full_name'], unique_tags)
                self.load_scripts()
                Notification(
                    "✅ Теги обновлены",
                    "Теги скрипта успешно обновлены.",
                    "success",
                    duration=3000,
                    parent=self.window()
                ).show_notification()
            except Exception as e:
                logger.error(f"Ошибка обновления тегов: {e}")
                Notification(
                    "❌ Ошибка обновления тегов",
                    f"Не удалось обновить теги: {e}",
                    "error",
                    duration=3000,
                    parent=self.window()
                ).show_notification()

    def manage_tags_dialog(self) -> None:
        """
        Отображает все существующие теги в информационном окне.
        """
        all_tags = set()
        try:
            for script in self.manager.get_scripts():
                all_tags.update(script.get('tags', []))
            tags_str = ", ".join(sorted(all_tags))
            QMessageBox.information(self, "Все теги", f"Существующие теги:\n{tags_str}")
        except Exception as e:
            logger.error(f"Ошибка получения тегов: {e}")
            Notification(
                "❌ Ошибка получения тегов",
                f"Не удалось получить теги: {e}",
                "error",
                duration=3000,
                parent=self.window()
            ).show_notification()

    def execute_script(self, item: QListWidgetItem) -> None:
        """
        Выполняет скрипт и показывает уведомление о результате.
        """
        script = item.data(Qt.UserRole)
        file_to_execute = script.get('path', script.get('full_name'))
        try:
            self.manager.execute_script(file_to_execute)
            self.script_executed.emit(script['name'], "success")
            Notification(
                "✅ Скрипт выполнен",
                f"Скрипт '{script['name']}' выполнен успешно.",
                "success",
                duration=3000,
                parent=self.window()
            ).show_notification()
        except Exception as e:
            logger.error(f"Ошибка выполнения скрипта '{script['name']}': {e}")
            self.script_executed.emit(script['name'], f"error: {e}")
            Notification(
                "❌ Ошибка выполнения скрипта",
                f"Не удалось выполнить '{script['name']}': {e}",
                "error",
                duration=3000,
                parent=self.window()
            ).show_notification()

    def edit_script_dialog(self, item: QListWidgetItem) -> None:
        """
        Открывает скрипт в системном редакторе по умолчанию.
        """
        script = item.data(Qt.UserRole)
        file_to_edit = script.get('path', script.get('full_name'))
        url = QUrl.fromLocalFile(file_to_edit)
        if not QDesktopServices.openUrl(url):
            Notification(
                "❌ Ошибка открытия скрипта",
                "Не удалось открыть скрипт в редакторе.",
                "error",
                duration=3000,
                parent=self.window()
            ).show_notification()

