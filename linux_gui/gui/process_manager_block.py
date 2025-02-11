from PySide6.QtWidgets import (
    QGroupBox, QVBoxLayout, QLabel, QPushButton,
    QTreeWidget, QTreeWidgetItem, QLineEdit, QHBoxLayout,
    QSizePolicy, QApplication
)
from PySide6.QtCore import Qt
import logging
from typing import List, Dict, Any

from linux_gui.session_manager import SessionManager
from linux_gui.process_manager import ProcessManager
from notifications import Notification

logger = logging.getLogger(__name__)


class ProcessManagerBlock(QGroupBox):
    """
    Виджет для отображения информации о процессах на удалённом Linux-хосте.

    Отображает список процессов в виде дерева, подобного htop, с возможностью
    поиска по строкам. Процессы отображаются в виде иерархической структуры
    (с родительскими и дочерними процессами).
    """

    def __init__(self, hostname: str, parent=None) -> None:
        """
        :param hostname: Имя или IP-адрес удалённого хоста.
        :param parent: Родительский виджет.
        """
        super().__init__("🛠️ Процессы", parent)
        self.hostname: str = hostname
        self.init_ui()

    def init_ui(self) -> None:
        """Инициализирует визуальные компоненты виджета."""
        layout = QVBoxLayout(self)

        # Информационная метка с подсказкой по обновлению списка процессов
        self.info_label = QLabel("💡 Нажмите «Обновить», чтобы загрузить список процессов.")
        self.info_label.setWordWrap(True)
        layout.addWidget(self.info_label)

        # Блок поиска по процессам
        search_layout = QHBoxLayout()
        search_label = QLabel("🔎 Поиск:")
        self.search_field = QLineEdit()
        self.search_field.setPlaceholderText("Введите текст для поиска...")
        self.search_field.textChanged.connect(self.filter_table)
        search_layout.addWidget(search_label)
        search_layout.addWidget(self.search_field)
        layout.addLayout(search_layout)

        # Дерево процессов для отображения списка процессов в виде иерархии
        self.process_tree = QTreeWidget()
        self.process_tree.setHeaderLabels(["PID", "USER", "CPU%", "MEM%", "TIME", "COMMAND"])
        self.process_tree.setSortingEnabled(True)
        self.process_tree.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        layout.addWidget(self.process_tree)

        # Кнопка обновления списка процессов
        self.refresh_button = QPushButton("🔄 Обновить процессы")
        self.refresh_button.setToolTip("Нажмите для обновления списка процессов")
        self.refresh_button.clicked.connect(self.refresh_processes)
        layout.addWidget(self.refresh_button)

        self.setLayout(layout)

    def refresh_processes(self) -> None:
        """
        Обновляет список процессов.

        Получает данные через ProcessManager, обновляет дерево процессов и
        выводит уведомление об успешном обновлении или ошибке.
        """
        # Деактивируем кнопку, чтобы избежать повторных запросов
        self.refresh_button.setEnabled(False)
        self.refresh_button.setText("🔄 Обновление...")

        try:
            session = SessionManager.get_instance(self.hostname, "", "").get_client()
            proc_manager = ProcessManager(session)
            data = proc_manager.get_processes_info()
            processes: List[Dict[str, Any]] = data.get("processes", [])

            self.populate_tree(processes)

            if not processes:
                Notification(
                    "⚠ Нет активных процессов",
                    "На удалённом хосте не найдено активных процессов.",
                    "warning",
                    parent=self.window()
                ).show_notification()
                return

            Notification(
                "🛠 Обновление процессов",
                "Список активных процессов успешно загружен.",
                "success",
                parent=self.window()
            ).show_notification()

        except Exception as e:
            logger.exception("Ошибка обновления процессов")
            Notification(
                "🚫 Ошибка загрузки процессов",
                f"Не удалось получить данные о процессах.\nОшибка: `{e}`",
                "error",
                parent=self.window()
            ).show_notification()

        finally:
            # Восстанавливаем исходное состояние кнопки
            self.refresh_button.setEnabled(True)
            self.refresh_button.setText("🔄 Обновить процессы")

    def populate_tree(self, processes: List[Dict[str, Any]]) -> None:
        """
        Заполняет дерево процессов данными.

        :param processes: Список словарей с информацией о процессах.
        """
        self.process_tree.clear()
        process_map: Dict[str, QTreeWidgetItem] = {}  # Для построения иерархии процессов

        for process in processes:
            pid = process.get("PID", "")
            ppid = process.get("PPID", "")
            user = process.get("USER", "")
            cpu = process.get("%CPU", "")
            mem = process.get("%MEM", "")
            time_str = process.get("TIME", "")
            cmd = process.get("COMMAND", "")

            item = QTreeWidgetItem([str(pid), user, str(cpu), str(mem), time_str, cmd])
            # Центрируем столбцы с процентами
            item.setTextAlignment(2, Qt.AlignCenter)
            item.setTextAlignment(3, Qt.AlignCenter)

            process_map[str(pid)] = item

            # Если родительский процесс найден, добавляем как дочерний элемент
            if ppid and str(ppid) in process_map:
                process_map[str(ppid)].addChild(item)
            else:
                self.process_tree.addTopLevelItem(item)

        # Применяем фильтрацию, если в поле поиска что-то введено
        self.filter_table(self.search_field.text())

    def filter_table(self, text: str) -> None:
        """
        Фильтрует дерево процессов по введённому тексту.

        :param text: Строка для поиска.
        """
        filter_text = text.strip().lower()

        if filter_text and all(self.process_tree.topLevelItem(i).isHidden()
                               for i in range(self.process_tree.topLevelItemCount())):
            Notification(
                "🔎 Поиск процессов",
                "По вашему запросу ничего не найдено.",
                "warning",
                parent=self.window()
            ).show_notification()

        def match_item(item: QTreeWidgetItem) -> bool:
            """
            Рекурсивно проверяет, содержит ли данный элемент или его дочерние элементы
            текст фильтра.
            """
            for col in range(item.columnCount()):
                if filter_text in item.text(col).lower():
                    return True
            # Рекурсивная проверка дочерних элементов
            for i in range(item.childCount()):
                if match_item(item.child(i)):
                    return True
            return False

        # Применяем фильтр к каждому топ-уровневому элементу дерева
        for i in range(self.process_tree.topLevelItemCount()):
            item = self.process_tree.topLevelItem(i)
            item.setHidden(not match_item(item))
