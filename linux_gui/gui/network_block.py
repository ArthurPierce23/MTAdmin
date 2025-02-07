# linux_gui/gui/network_block.py

from PySide6.QtWidgets import (
    QGroupBox, QVBoxLayout, QLabel, QPushButton,
    QTextEdit
)
from PySide6.QtCore import Qt
import logging

from linux_gui.session_manager import SessionManager
from linux_gui.network import NetworkInfo
from notifications import Notification

logger = logging.getLogger(__name__)


class NetworkBlock(QGroupBox):
    """
    Виджет для отображения информации о сети удалённого Linux-хоста.

    Отображает краткое резюме (список интерфейсов с найденными IP)
    и полный вывод команды.
    Есть возможность обновить информацию по кнопке.
    """
    def __init__(self, hostname, parent=None):
        """
        :param hostname: имя или IP-адрес удалённого хоста.
        """
        super().__init__("🌐 Сетевые настройки", parent)
        self.hostname = hostname
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)

        # Информационная метка с кратким описанием
        self.info_label = QLabel("💡 Нажмите кнопку «Обновить», чтобы загрузить свежую сетевую информацию.")
        self.info_label.setWordWrap(True)
        layout.addWidget(self.info_label)

        # Текстовое поле для детального вывода информации
        self.network_info_text = QTextEdit()
        self.network_info_text.setReadOnly(True)
        layout.addWidget(self.network_info_text)

        # Кнопка обновления данных
        self.refresh_button = QPushButton("🔄 Обновить данные сети")
        self.refresh_button.setToolTip("Нажмите для обновления сетевой информации")
        self.refresh_button.clicked.connect(self.refresh_network_info)
        layout.addWidget(self.refresh_button)

        self.setLayout(layout)

    def refresh_network_info(self):
        """
        Обновляет сетевую информацию.

        Получает SSH-сессию через SessionManager, затем использует NetworkInfo для получения данных.
        Отображает краткое резюме (интерфейсы и их IP) и полный вывод команды.
        """
        try:
            # Получаем SSH-сессию (логин/пароль уже должны быть установлены ранее)
            session = SessionManager.get_instance(self.hostname, "", "").get_client()
            network_info_obj = NetworkInfo(session)
            net_info = network_info_obj.get_network_info()

            raw_output = net_info.get("raw", "")
            interfaces = net_info.get("interfaces", {})

            # Формируем краткое резюме интерфейсов
            summary = "Интерфейсы:\n"
            for iface, data in interfaces.items():
                ips = ", ".join(data.get("ips", [])) if data.get("ips") else "Нет IP"
                summary += f" • {iface}: {ips}\n"

            display_text = summary + "\nПолный вывод команды:\n" + raw_output
            self.network_info_text.setPlainText(display_text)
            Notification("Сеть", "✅ Сетевая информация успешно обновлена.", "success").show_notification()
        except Exception as e:
            logger.error(f"Ошибка обновления сетевой информации: {e}")
            Notification("Ошибка", f"❌ Не удалось обновить данные сети:\n{e}", "error").show_notification()
