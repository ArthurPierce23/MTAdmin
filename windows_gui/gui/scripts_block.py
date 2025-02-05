from pathlib import Path
import subprocess

from PySide6.QtCore import Qt, QSize, Signal, QRect, QUrl
from PySide6.QtGui import QColor, QPainter, QFontMetrics, QIcon, QAction, QDesktopServices
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QPushButton, QListWidget, QGroupBox,
    QListWidgetItem, QMenu, QLineEdit, QHBoxLayout, QLabel,
    QInputDialog, QStyledItemDelegate, QFileDialog, QMessageBox
)

# Импорт уведомлений
from notifications import Notification
from windows_gui.scripts import ScriptsManager


class ScriptItemDelegate(QStyledItemDelegate):
    """
    Делегат для отрисовки элемента списка скриптов с тегами.
    """
    def paint(self, painter, option, index):
        super().paint(painter, option, index)
        script = index.data(Qt.UserRole)

        if script and script.get('tags'):
            painter.save()

            # Настройки отступов и стиля для тегов
            tag_spacing = 5
            tag_height = 20
            tag_radius = 8
            font_metrics = QFontMetrics(option.font)

            # Начальная позиция для тегов (справа налево)
            x_pos = option.rect.right() - 10  # отступ 10px от правого края

            # Рисуем теги в обратном порядке
            for tag in reversed(script['tags']):
                # Рассчитываем ширину текста с отступами
                text_width = font_metrics.horizontalAdvance(tag) + 20

                tag_rect = QRect(
                    x_pos - text_width,
                    option.rect.top() + (option.rect.height() - tag_height) // 2,
                    text_width,
                    tag_height
                )

                # Если тег выходит за левую границу — прекращаем отрисовку
                if tag_rect.left() < option.rect.left():
                    break

                # Рисуем фон тега
                painter.setBrush(QColor(230, 240, 255))
                painter.setPen(Qt.NoPen)
                painter.drawRoundedRect(tag_rect, tag_radius, tag_radius)

                # Рисуем текст тега
                painter.setPen(QColor(50, 100, 200))
                painter.drawText(
                    tag_rect.adjusted(5, 0, -5, 0),
                    Qt.AlignCenter,
                    tag
                )

                x_pos -= text_width + tag_spacing

            painter.restore()


class ScriptsBlock(QWidget):
    """
    Виджет для работы с библиотекой скриптов:
    запуск, добавление, редактирование, переименование, удаление и управление тегами.
    """
    script_executed = Signal(str, str)

    def __init__(self, hostname: str, parent=None):
        super().__init__(parent)
        self.manager = ScriptsManager(hostname)
        self._init_ui()
        self.load_scripts()

    def _init_ui(self):
        """Инициализация пользовательского интерфейса."""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(5, 5, 5, 5)

        group_box = QGroupBox("Библиотека скриптов")
        group_box.setStyleSheet("""
            QGroupBox {
                font-size: 14px;
                font-weight: bold;
                margin-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 3px;
            }
        """)

        group_layout = QVBoxLayout(group_box)
        group_layout.setSpacing(10)

        # Фильтры: поиск по имени и тегам
        filter_layout = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Поиск по имени...")
        self.search_input.setClearButtonEnabled(True)

        self.tag_input = QLineEdit()
        self.tag_input.setPlaceholderText("Фильтр по тегам...")
        self.tag_input.setClearButtonEnabled(True)

        filter_layout.addWidget(QLabel("Фильтры:"))
        filter_layout.addWidget(self.search_input)
        filter_layout.addWidget(QLabel("   "))
        filter_layout.addWidget(self.tag_input)

        # Список скриптов
        self.scripts_list = QListWidget()
        self.scripts_list.setItemDelegate(ScriptItemDelegate())
        self.scripts_list.setContextMenuPolicy(Qt.CustomContextMenu)
        self.scripts_list.setAlternatingRowColors(True)
        self.scripts_list.setStyleSheet("""
            QListWidget {
                border: 1px solid #d0d0d0;
                border-radius: 3px;
                padding: 2px;
            }
        """)

        # Кнопки для операций
        btn_layout = QHBoxLayout()
        self.add_btn = QPushButton("Добавить скрипт")
        self.add_btn.setIcon(QIcon.fromTheme("document-open"))

        self.tag_btn = QPushButton("Управление тегами")
        self.tag_btn.setIcon(QIcon.fromTheme("preferences-other"))

        btn_layout.addStretch()
        btn_layout.addWidget(self.add_btn)
        btn_layout.addWidget(self.tag_btn)

        # Подключаем сигналы
        self.search_input.textChanged.connect(self.filter_scripts)
        self.tag_input.textChanged.connect(self.filter_by_tags)
        self.scripts_list.customContextMenuRequested.connect(self.show_context_menu)
        self.scripts_list.itemDoubleClicked.connect(self.execute_script)
        self.add_btn.clicked.connect(self.add_script_dialog)
        self.tag_btn.clicked.connect(self.manage_tags_dialog)

        # Компоновка
        group_layout.addLayout(filter_layout)
        group_layout.addWidget(self.scripts_list)
        group_layout.addLayout(btn_layout)
        main_layout.addWidget(group_box)

    def load_scripts(self):
        """
        Загружает список скриптов из менеджера и отображает их.
        """
        self.scripts_list.clear()
        for script in self.manager.get_scripts():
            item = QListWidgetItem(f"{script['name']} [{script['type']}]")
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
        filter_tags = [t.strip().lower() for t in text.split(',') if t.strip()]

        for i in range(self.scripts_list.count()):
            item = self.scripts_list.item(i)
            script_tags = [t.lower() for t in item.data(Qt.UserRole).get('tags', [])]
            # Скрипт проходит фильтр, если содержит все указанные теги
            match = all(ft in script_tags for ft in filter_tags)
            item.setHidden(not match)

    def show_context_menu(self, pos):
        """
        Отображает контекстное меню для выбранного скрипта или для пустой области.
        """
        menu = QMenu()
        item = self.scripts_list.itemAt(pos)

        if item:
            # Действия для выбранного скрипта
            execute_action = QAction("▶ Запустить", self)
            execute_action.triggered.connect(lambda: self.execute_script(item))

            # Новое действие: редактировать (открыть файл в редакторе)
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
            # Контекстное меню для пустой области
            refresh_action = QAction("🔄 Обновить список", self)
            refresh_action.triggered.connect(self.load_scripts)

            add_action = QAction("➕ Добавить скрипт", self)
            add_action.triggered.connect(self.add_script_dialog)

            menu.addAction(refresh_action)
            menu.addAction(add_action)

        menu.exec_(self.scripts_list.viewport().mapToGlobal(pos))

    def add_script_dialog(self):
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
                    Notification("Скрипт успешно добавлен!", "success").show_notification()
                except Exception as e:
                    Notification(f"Ошибка добавления скрипта: {str(e)}", "error").show_notification()

    def rename_script_dialog(self, item):
        """
        Открывает диалог для переименования скрипта.
        """
        script = item.data(Qt.UserRole)
        old_name = script['name']
        new_name, ok = QInputDialog.getText(
            self, "Переименовать скрипт",
            "Введите новое имя:",
            QLineEdit.Normal,
            old_name
        )
        if ok and new_name and new_name != old_name:
            try:
                extension = Path(script['full_name']).suffix
                new_full_name = f"{new_name}{extension}"
                if self.manager.rename_script(script['full_name'], new_full_name):
                    self.load_scripts()
                    Notification("Скрипт успешно переименован", "success").show_notification()
            except Exception as e:
                Notification(f"Ошибка переименования: {str(e)}", "error").show_notification()

    def delete_script_dialog(self, item):
        """
        Подтверждает удаление скрипта и удаляет его.
        """
        script = item.data(Qt.UserRole)
        reply = QMessageBox.question(
            self,
            "Подтверждение удаления",
            f"Вы уверены, что хотите удалить скрипт '{script['name']}'?",
            QMessageBox.Yes | QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            try:
                self.manager.delete_script(script['full_name'])
                self.load_scripts()
                Notification("Скрипт успешно удален", "success").show_notification()
            except Exception as e:
                Notification(f"Ошибка удаления: {str(e)}", "error").show_notification()

    def edit_tags_dialog(self, item):
        """
        Открывает диалог для редактирования тегов скрипта.
        """
        script = item.data(Qt.UserRole)
        current_tags = ", ".join(script.get('tags', []))

        new_tags, ok = QInputDialog.getText(
            self,
            "Редактировать теги",
            "Введите теги через запятую:",
            text=current_tags
        )

        if ok:
            tags_list = [t.strip().lower() for t in new_tags.split(',') if t.strip()]
            unique_tags = list(dict.fromkeys(tags_list))
            try:
                self.manager.update_tags(script['full_name'], unique_tags)
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
            all_tags.update(script.get('tags', []))
        tags_str = ", ".join(sorted(all_tags))
        QMessageBox.information(self, "Все теги", f"Существующие теги:\n{tags_str}")

    def execute_script(self, item):
        """
        Выполняет скрипт. Теперь используется значение из поля 'path', а если его нет – берется 'full_name'.
        При успешном выполнении или возникновении ошибки показывается уведомление.
        """
        script = item.data(Qt.UserRole)
        file_to_execute = script.get('path', script.get('full_name'))
        try:
            # Если требуется запуск через менеджер, то используем его метод.
            self.manager.execute_script(file_to_execute)
            self.script_executed.emit(script['name'], "success")
            Notification(f"Скрипт '{script['name']}' выполнен успешно", "success").show_notification()
        except Exception as e:
            self.script_executed.emit(script['name'], f"error: {str(e)}")
            Notification(f"Ошибка выполнения '{script['name']}': {str(e)}", "error").show_notification()

    def edit_script_dialog(self, item):
        """
        Открывает скрипт в системном редакторе по умолчанию.
        """
        script = item.data(Qt.UserRole)
        file_to_edit = script.get('path', script.get('full_name'))
        url = QUrl.fromLocalFile(file_to_edit)
        if not QDesktopServices.openUrl(url):
            Notification("Не удалось открыть скрипт в редакторе", "error").show_notification()
