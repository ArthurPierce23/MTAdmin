# styles.py

THEMES = {
    "Светлая": {
        "background": "qlineargradient(spread:pad, x1:0, y1:0, x2:1, y2:1, stop:0 #FFFFFF, stop:1 #E3F2FD)",
        "foreground": "#000000",
        "button_bg": "qlineargradient(spread:pad, x1:0, y1:0, x2:1, y2:1, stop:0 #E3F2FD, stop:1 #BBDEFB)",
        "button_fg": "#000000",
        "menu_bg": "#F5F5F5",
        "menu_fg": "#000000",
        "menu_hover": "#BBDEFB",
        "tab_bg": "#F5F5F5",
        "tab_fg": "#000000",
        "groupbox_bg": "#D6D6D6",
        "groupbox_fg": "#000000",
        "table_bg": "#FFFFFF",
        "table_header": "#B0BEC5",
        "highlight": "#2196F3",
    },

    "Темная": {
        "background": "qlineargradient(spread:pad, x1:0, y1:0, x2:1, y2:1, stop:0 #121212, stop:1 #1E1E1E)",
        "foreground": "#DDDDDD",
        "button_bg": "qlineargradient(spread:pad, x1:0, y1:0, x2:1, y2:1, stop:0 #2B2B2B, stop:1 #444444)",
        "button_fg": "#FFFFFF",
        "menu_bg": "#252525",
        "menu_fg": "#DDDDDD",
        "menu_hover": "#444444",
        "tab_bg": "#1E1E1E",
        "tab_fg": "#DDDDDD",
        "groupbox_bg": "#252525",
        "groupbox_fg": "#FFFFFF",
        "table_bg": "#2B2B2B",
        "table_header": "#616161",
        "highlight": "#2196F3",
    },

    "Синяя": {
        "background": "qlineargradient(spread:pad, x1:0, y1:0, x2:1, y2:1, stop:0 #E3F2FD, stop:1 #90CAF9)",
        "foreground": "#0D47A1",
        "button_bg": "qlineargradient(spread:pad, x1:0, y1:0, x2:1, y2:1, stop:0 #64B5F6, stop:1 #42A5F5)",
        "button_fg": "#FFFFFF",
        "menu_bg": "#64B5F6",
        "menu_fg": "#FFFFFF",
        "menu_hover": "#42A5F5",
        "tab_bg": "#90CAF9",
        "tab_fg": "#0D47A1",
        "groupbox_bg": "#64B5F6",
        "groupbox_fg": "#FFFFFF",
        "table_bg": "#E3F2FD",
        "table_header": "#42A5F5",
        "highlight": "#1976D2",
    },
}


def apply_theme(theme_name):
    """Применяет тему на основе словаря THEMES"""
    if theme_name not in THEMES:
        theme_name = "Светлая"
    colors = THEMES[theme_name]

    return f"""
        QMainWindow {{
            background: {colors["background"]};
            color: {colors["foreground"]};
        }}

        QWidget {{
            background: {colors["background"]};
            color: {colors["foreground"]};
        }}

        /* Верхнее меню */
        QMenuBar {{
            background: {colors["menu_bg"]};
            color: {colors["menu_fg"]};
            padding: 5px;
        }}

        QMenuBar::item {{
            background: transparent;
            padding: 6px;
            color: {colors["menu_fg"]};
        }}

        QMenuBar::item:selected {{
            background: {colors["menu_hover"]};
            border-radius: 4px;
        }}

        QMenu {{
            background: {colors["menu_bg"]};
            color: {colors["menu_fg"]};
            border: 1px solid {colors["highlight"]};
        }}

        QMenu::item:selected {{
            background: {colors["menu_hover"]};
        }}

        QPushButton {{
            background: {colors["button_bg"]};
            color: {colors["button_fg"]};
            border-radius: 5px;
            padding: 6px;
            border: 1px solid {colors["highlight"]};
        }}

        QPushButton:hover {{
            background: {colors["highlight"]};
            color: white;
        }}

        QPushButton:pressed {{
            background: {colors["highlight"]};
            border: 2px solid white;
        }}

        /* Вкладки */
        QTabWidget::pane {{
            background: {colors["tab_bg"]};
            border: 1px solid {colors["highlight"]};
        }}

        QTabBar::tab {{
            background: {colors["tab_bg"]};
            color: {colors["tab_fg"]};
            padding: 5px;
            border-radius: 5px;
            margin-right: 3px;
        }}

        QTabBar::tab:selected {{
            background: {colors["highlight"]};
            color: white;
            border: 1px solid {colors["highlight"]};
            padding: 6px;
        }}

        /* Групповые боксы */
        QGroupBox {{
            background: {colors["groupbox_bg"]};
            color: {colors["groupbox_fg"]};
            border: 1px solid {colors["highlight"]};
            border-radius: 5px;
            padding: 10px;
            font-weight: bold;
        }}

        /* Таблицы */
        QTableWidget {{
            background: {colors["table_bg"]};
            gridline-color: {colors["table_header"]};
            color: {colors["foreground"]};
            border: 1px solid {colors["highlight"]};
        }}

        QHeaderView::section {{
            background: {colors["table_header"]};
            padding: 5px;
            border: 1px solid {colors["foreground"]};
        }}

        QLabel {{
            color: {colors["foreground"]};
            font-weight: bold;
        }}

        /* Поля ввода */
        QLineEdit {{
            background: white;
            border: 1px solid {colors["highlight"]};
            padding: 3px;
            border-radius: 3px;
        }}
    """
