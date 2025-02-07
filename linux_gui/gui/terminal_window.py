# linux_gui/gui/terminal_window.py

import os
from PySide6.QtWidgets import QDialog, QVBoxLayout
from PySide6.QtCore import QTimer, QObject, Signal, Slot
from PySide6.QtWebEngineWidgets import QWebEngineView, QWebEngineSettings
from PySide6.QtWebChannel import QWebChannel

class TerminalBridge(QObject):
    """
    Объект-мост для обмена данными между Python и JavaScript через QWebChannel.
    """
    sendToTerminal = Signal(str)  # сигнал для отправки данных в xterm.js

    @Slot(str)
    def receiveFromTerminal(self, data):
        """
        Слот, вызываемый из JavaScript при вводе данных пользователем.
        Данные передаются в вызывающий объект (TerminalWindow).
        """
        if hasattr(self, "onDataReceived"):
            self.onDataReceived(data)

class TerminalWindow(QDialog):
    """
    Окно-терминал, реализованное на базе QWebEngineView и xterm.js.
    Обеспечивает полноценную интерактивность.
    """
    def __init__(self, ssh_channel, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Интерактивный терминал")
        self.resize(800, 600)
        self.ssh_channel = ssh_channel

        layout = QVBoxLayout(self)
        self.view = QWebEngineView(self)
        layout.addWidget(self.view)

        # Разрешаем локальному контенту доступ к удалённым URL
        self.view.settings().setAttribute(QWebEngineSettings.LocalContentCanAccessRemoteUrls, True)

        # Настраиваем QWebChannel для связи с JS
        self.channel = QWebChannel(self.view.page())
        self.bridge = TerminalBridge()
        self.bridge.onDataReceived = self._send_to_ssh  # ввод пользователя в SSH-канал
        self.channel.registerObject("bridge", self.bridge)
        self.view.page().setWebChannel(self.channel)

        # Формирование корректного пути до xterm.html.
        # Если данный модуль находится в linux_gui/gui, а HTML в linux_gui/resources
        html_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "resources", "xterm.html")
        self.view.load("file:///" + html_path.replace("\\", "/"))

        # Таймер для периодического чтения данных из SSH-канала
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._read_from_ssh)
        self.timer.start(50)

    def _read_from_ssh(self):
        """
        Если от удалённого хоста пришли данные, пересылает их в xterm.js.
        """
        if self.ssh_channel.recv_ready():
            try:
                data = self.ssh_channel.recv(1024)
                if data:
                    text = data.decode("utf-8", errors="ignore")
                    # Передаём данные в JS через мост
                    self.bridge.sendToTerminal.emit(text)
            except Exception as e:
                print(f"Ошибка чтения из SSH-канала: {e}")

    def _send_to_ssh(self, data):
        """
        Отправляет данные, полученные из xterm.js (ввод пользователя), в SSH-канал.
        """
        try:
            self.ssh_channel.send(data)
        except Exception as e:
            print(f"Ошибка отправки данных в SSH-канал: {e}")
