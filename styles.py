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
        "border": "1px solid #B0BEC5",
        "border_radius": "4px",


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
        "border": "1px solid #616161",
        "border_radius": "4px"
    },

    "Синяя": {
        "background": "qlineargradient(spread:pad, x1:0, y1:0, x2:1, y2:1, stop:0 #E3F2FD, stop:1 #90CAF9)",
        "foreground": "#FFFFFF",
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
        "border": "1px solid #1976D2",
        "border_radius": "4px"
    },
    "Material Dark": {
        "background": "#263238",
        "foreground": "#ECEFF1",
        "button_bg": "#37474F",
        "button_fg": "#FFFFFF",
        "menu_bg": "#37474F",
        "menu_fg": "#B0BEC5",
        "menu_hover": "#455A64",
        "tab_bg": "#37474F",
        "tab_fg": "#B0BEC5",
        "groupbox_bg": "#455A64",
        "groupbox_fg": "#FFFFFF",
        "table_bg": "#37474F",
        "table_header": "#546E7A",
        "highlight": "#80CBC4",
        "border": "1px solid #607D8B",
        "border_radius": "4px"
    },

    "Solarized Dark": {
        "background": "#002b36",
        "foreground": "#EEE8D5",
        "button_bg": "#073642",
        "button_fg": "#93a1a1",
        "menu_bg": "#073642",
        "menu_fg": "#839496",
        "menu_hover": "#586e75",
        "tab_bg": "#073642",
        "tab_fg": "#93a1a1",
        "groupbox_bg": "#073642",
        "groupbox_fg": "#839496",
        "table_bg": "#002b36",
        "table_header": "#073642",
        "highlight": "#b58900",
        "border": "1px solid #586e75",
        "border_radius": "3px"
    },

    "Dracula": {
        "background": "#282a36",
        "foreground": "#f8f8f2",
        "button_bg": "#44475a",
        "button_fg": "#f8f8f2",
        "menu_bg": "#44475a",
        "menu_fg": "#f8f8f2",
        "menu_hover": "#6272a4",
        "tab_bg": "#44475a",
        "tab_fg": "#f8f8f2",
        "groupbox_bg": "#44475a",
        "groupbox_fg": "#f8f8f2",
        "table_bg": "#282a36",
        "table_header": "#44475a",
        "highlight": "#bd93f9",
        "border": "1px solid #6272a4",
        "border_radius": "5px"
    },

    "Розовая мечта": {
        "background": "qlineargradient(spread:pad, x1:0, y1:0, x2:1, y2:1, stop:0 #FFB6C1, stop:1 #FF69B4)",
        "foreground": "#FFFFFF",
        "button_bg": "qlineargradient(spread:pad, x1:0, y1:0, x2:1, y2:1, stop:0 #FFC0CB, stop:1 #FF1493)",
        "button_fg": "#FFFFFF",
        "menu_bg": "#FFB6C1",
        "menu_fg": "#8B0000",
        "menu_hover": "#FF69B4",
        "tab_bg": "#FFC0CB",
        "tab_fg": "#8B0000",
        "groupbox_bg": "#FFB6C1",
        "groupbox_fg": "#8B0000",
        "table_bg": "#FFF0F5",
        "table_header": "#FF69B4",
        "highlight": "#FF1493",
        "border": "2px dashed #FF1493",
        "border_radius": "8px"
    }
}


def apply_theme(theme_name):
    """Применяет тему на основе словаря THEMES"""
    if theme_name not in THEMES:
        theme_name = "Светлая"
    colors = THEMES[theme_name]

    # Заполняем обязательные параметры
    required_keys = {
        'border': f"1px solid {colors.get('highlight', '#CCCCCC')}",
        'border_radius': '4px',
        'table_header': colors.get('highlight', '#CCCCCC'),
        'highlight': '#2196F3'
    }

    # Объединяем параметры
    colors = {**required_keys, **colors}

    # Формируем CSS
    return f"""
        QMainWindow, QWidget {{
            background: {colors["background"]};
            color: {colors["foreground"]};
            font-family: 'Segoe UI', Arial, sans-serif;
            font-size: 12px;
        }}

        QPushButton {{
            background: {colors["button_bg"]};
            color: {colors["button_fg"]};
            border: {colors["border"]};
            border-radius: {colors["border_radius"]};
            padding: 8px 16px;
            min-width: 80px;
        }}

        QPushButton:hover {{
            background: {colors["highlight"]};
            border-color: {colors["highlight"]};
        }}

        QPushButton:pressed {{
            background: {colors["highlight"]};
            padding: 7px 15px;
        }}

        /* Остальные стили */
        QMenuBar {{
            background: {colors["menu_bg"]};
            color: {colors["menu_fg"]};
            border-bottom: {colors["border"]};
        }}

        QTabBar::tab:selected {{
            background: {colors["highlight"]};
        }}

        QTableWidget::item:selected {{
            background: {colors["highlight"]};
        }}
    """.replace('\n', ' ').strip()
