from PySide6.QtWidgets import (
    QGroupBox, QVBoxLayout, QLabel, QPushButton,
    QTextEdit, QTreeWidget, QSizePolicy, QTreeWidgetItem
)
from PySide6.QtCore import Qt
import logging
from typing import Dict, Any

from linux_gui.session_manager import SessionManager
from linux_gui.network import NetworkInfo
from notifications import Notification

logger = logging.getLogger(__name__)


class NetworkBlock(QGroupBox):
    """
    Виджет для отображения информации о сети удалённого Linux-хоста.

    Отображает краткое резюме (список интерфейсов с найденными IP) и полный вывод команды.
    Обновление информации производится по нажатию кнопки.
    """
    def __init__(self, hostname: str, parent=None) -> None:
        """
        Инициализирует виджет сетевых настроек.

        :param hostname: имя или IP-адрес удалённого хоста.
        :param parent: Родительский виджет (если имеется).
        """
        super().__init__("🌐 Сетевые настройки", parent)
        self.hostname: str = hostname
        self.init_ui()

    def init_ui(self) -> None:
        """Инициализирует визуальные компоненты виджета."""
        layout = QVBoxLayout(self)

        # Информационная метка
        self.info_label = QLabel("💡 Нажмите «Обновить», чтобы загрузить свежие сетевые данные.")
        self.info_label.setWordWrap(True)
        layout.addWidget(self.info_label)

        # QTreeWidget для отображения краткой информации по интерфейсам и IP-адресам
        self.network_tree = QTreeWidget()
        self.network_tree.setHeaderLabels(["Интерфейс", "IP-адреса"])
        self.network_tree.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum)
        layout.addWidget(self.network_tree)

        # QTextEdit для вывода полного результата сетевой команды
        self.network_info_text = QTextEdit()
        self.network_info_text.setReadOnly(True)
        layout.addWidget(self.network_info_text)

        # Кнопка обновления сетевой информации
        self.refresh_button = QPushButton("🔄 Обновить данные сети")
        self.refresh_button.setToolTip("Нажмите для обновления сетевой информации")
        self.refresh_button.clicked.connect(self.refresh_network_info)
        layout.addWidget(self.refresh_button)

        self.setLayout(layout)

    def update_network_tree(self, interfaces: Dict[str, Dict[str, Any]]) -> None:
        """
        Обновляет QTreeWidget данными об интерфейсах и их IP-адресах.

        :param interfaces: Словарь с информацией об интерфейсах.
        """
        self.network_tree.clear()
        for iface, data in interfaces.items():
            ips = ", ".join(data.get("ips", [])) if data.get("ips") else "Нет IP"
            item = QTreeWidgetItem([iface, ips])
            self.network_tree.addTopLevelItem(item)

    def update_network_info_text(self, raw_output: str) -> None:
        """
        Обновляет QTextEdit с полным выводом сетевой команды.

        :param raw_output: Полный вывод команды.
        """
        self.network_info_text.clear()
        self.network_info_text.setPlainText(raw_output)

    def refresh_network_info(self) -> None:
        """
        Обновляет сетевую информацию и отображает её:
          - Краткое резюме по интерфейсам и IP-адресам отображается в QTreeWidget.
          - Полный вывод команды – в QTextEdit.
        При успешном обновлении выводится уведомление, в противном случае – сообщение об ошибке.
        """
        try:
            # Получаем SSH-клиент через SessionManager
            session = SessionManager.get_instance(self.hostname, "", "").get_client()
            network_info_obj = NetworkInfo(session)
            net_info: Dict[str, Any] = network_info_obj.get_network_info()

            raw_output: str = net_info.get("raw", "")
            interfaces: Dict[str, Dict[str, Any]] = net_info.get("interfaces", {})

            # Обновляем данные в интерфейсе
            self.update_network_tree(interfaces)
            self.update_network_info_text(raw_output)
            if not interfaces:
                Notification(
                    "⚠ Нет сетевых интерфейсов",
                    "Система не обнаружила активных сетевых подключений.",
                    "warning",
                    parent=self.window()
                ).show_notification()
                return

            Notification(
                "🌍 Обновление сети",
                "Данные о сетевых интерфейсах успешно загружены.",
                "success",
                parent=self.window()
            ).show_notification()


        except Exception as e:
            logger.exception("Ошибка обновления сетевой информации")
            Notification(
                "🚫 Ошибка сети",
                f"Не удалось получить сетевую информацию.\nОшибка: `{e}`",
                "error",
                parent=self.window()
            ).show_notification()

