from database.db_manager import (
    init_db, add_recent_connection, get_recent_connections, clear_recent_connections,
    add_to_workstation_map, get_workstation_map, remove_from_workstation_map
)
from main_gui.tab_widgets import DetachableTabWidget, DetachableTabBar
from main_gui.ui_components import IPLineEdit, ThemeDialog