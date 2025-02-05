import unittest
from unittest.mock import patch, MagicMock
from PySide6.QtWidgets import QApplication, QLabel
from windows_gui.gui.windows_window import WindowsWindow  # Замените на фактический путь к вашему модулю

class TestWindowsWindow(unittest.TestCase):

    @patch('windows_window.SystemInfoBlock')
    @patch('windows_window.CommandsBlock')
    @patch('windows_window.RDPBlock')
    @patch('windows_window.ActiveUsers')
    @patch('windows_window.ScriptsBlock')
    def setUp(self, MockScriptsBlock, MockActiveUsers, MockRDPBlock, MockCommandsBlock, MockSystemInfoBlock):
        # Создаем экземпляр QApplication
        self.app = QApplication([])

        # Создаем мок-объекты для блоков
        self.mock_system_info = MockSystemInfoBlock.return_value
        self.mock_commands = MockCommandsBlock.return_value
        self.mock_rdp = MockRDPBlock.return_value
        self.mock_active_users = MockActiveUsers.return_value
        self.mock_scripts = MockScriptsBlock.return_value

        # Создаем экземпляр WindowsWindow
        self.hostname = "MyPC"
        self.ip = "192.168.1.100"
        self.window = WindowsWindow(self.hostname, self.ip)

    def test_window_title(self):
        self.assertEqual(self.window.windowTitle(), f"Windows: {self.hostname}")

    def test_header_label(self):
        header_label = self.window.findChild(QLabel)
        self.assertIsNotNone(header_label)
        self.assertEqual(header_label.text(), f"Имя ПК: {self.hostname}   |   IP: {self.ip}   |   ОС: Windows")

    def test_blocks_initialization(self):
        # Проверяем, что все блоки инициализировались
        self.assertIsInstance(self.window.system_info, MagicMock)
        self.assertIsInstance(self.window.commands_block, MagicMock)
        self.assertIsInstance(self.window.rdp_block, MagicMock)
        self.assertIsInstance(self.window.active_users_block, MagicMock)
        self.assertIsInstance(self.window.scripts_block, MagicMock)

    @patch('windows_window.QMessageBox')
    def test_initialization_error_handling(self, MockQMessageBox):
        # Проверяем, что окно закрывается при возникновении ошибки
        MockSystemInfoBlock.side_effect = Exception("Test error")
        window = WindowsWindow(self.hostname, self.ip)

        MockQMessageBox.critical.assert_called_once()
        self.assertFalse(window.isVisible())  # Окно должно быть закрыто

    def tearDown(self):
        self.window.close()
        self.app.quit()

if __name__ == '__main__':
    unittest.main()
