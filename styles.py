# styles.py

NOTIFICATION_STYLES = {
    "default": {
        "background": "rgba(255, 255, 255, 0.95)",
        "border": "1px solid rgba(0, 0, 0, 0.1)",
        "text": "#333333",
        "shadow": "0px 2px 4px rgba(0, 0, 0, 0.15)",
        "icon": ""
    },
    "error": {
        "background": "#ffe6e6",
        "border": "1px solid #ff4d4d",
        "text": "#cc0000",
        "icon": "⚠️"
    },
    "success": {
        "background": "#e6ffe6",
        "border": "1px solid #4dff4d",
        "text": "#008000",
        "icon": "✅"
    }
}

THEMES = {
    "Без темы": None,  # Отключает применение CSS
    "Светлая": {
        "background": "#ffffff",
        "foreground": "#333333",
        "button_bg": "#f5f5f5",
        "button_fg": "#333333",
        "button_hover": "#e0e0e0",
        "menu_bg": "#ffffff",
        "menu_fg": "#333333",
        "menu_hover": "#e0e0e0",
        "tab_bg": "#f5f5f5",
        "tab_fg": "#333333",
        "tab_hover": "#e0e0e0",
        "groupbox_bg": "#ffffff",
        "groupbox_fg": "#333333",
        "table_bg": "#ffffff",
        "table_header": "#e0e0e0",
        "highlight": "#4d90fe",
        "border": "1px solid #dddddd",
        "border_radius": "4px",
        "padding": "6px",
        "font_family": "Segoe UI, sans-serif",
        "disabled": "#a0a0a0",
        "scroll_handle": "#dddddd",
    },

    "Темная": {
        "background": "#222222",
        "foreground": "#dddddd",
        "button_bg": "#333333",
        "button_fg": "#dddddd",
        "button_hover": "#444444",
        "menu_bg": "#333333",
        "menu_fg": "#dddddd",
        "menu_hover": "#444444",
        "tab_bg": "#333333",
        "tab_fg": "#cccccc",
        "tab_hover": "#444444",
        "groupbox_bg": "#333333",
        "groupbox_fg": "#dddddd",
        "table_bg": "#2a2a2a",
        "table_header": "#444444",
        "highlight": "#4d90fe",
        "border": "1px solid #444444",
        "border_radius": "4px",
        "padding": "6px",
        "font_family": "Segoe UI, sans-serif",
        "disabled": "#888888",
        "scroll_handle": "#444444",
    },

    "Material Blue": {
        "background": "rgba(245, 245, 245, 0.85)",
        "foreground": "#333333",
        "button_bg": "#e3f2fd",
        "button_fg": "#0d47a1",
        "button_hover": "#bbdefb",
        "menu_bg": "rgba(227, 242, 253, 0.8)",
        "menu_fg": "#0d47a1",
        "menu_hover": "#bbdefb",
        "tab_bg": "#e3f2fd",
        "tab_fg": "#0d47a1",
        "tab_hover": "#bbdefb",
        "groupbox_bg": "rgba(255, 255, 255, 0.85)",
        "groupbox_fg": "#0d47a1",
        "table_bg": "#ffffff",
        "table_header": "#bbdefb",
        "highlight": "#2196f3",
        "border": "1px solid #bbdefb",
        "border_radius": "8px",
        "padding": "8px",
        "font_family": "Segoe UI, sans-serif",
        "disabled": "#90a4ae",
        "scroll_handle": "#bbdefb",
    },

    "Deep Space": {
        "background": "rgba(10, 10, 10, 0.9)",
        "foreground": "#E9ECEF",
        "button_bg": "#1A1A1A",
        "button_fg": "#74B3CE",
        "button_hover": "#2A2A2A",
        "menu_bg": "rgba(26, 26, 26, 0.8)",
        "menu_fg": "#74B3CE",
        "menu_hover": "#2A2A2A",
        "tab_bg": "#1A1A1A",
        "tab_fg": "#74B3CE",
        "tab_hover": "#2A2A2A",
        "groupbox_bg": "rgba(26, 26, 26, 0.8)",
        "groupbox_fg": "#74B3CE",
        "table_bg": "rgba(10, 10, 10, 0.9)",
        "table_header": "#2A2A2A",
        "highlight": "#74B3CE",
        "border": "1px solid #2A2A2A",
        "border_radius": "10px",
        "padding": "10px",
        "font_family": "'Roboto Mono', monospace",
        "disabled": "#616E88",
        "scroll_handle": "#2A2A2A",
    },

    "Nord": {
        "background": "#2E3440",
        "foreground": "#D8DEE9",
        "button_bg": "#3B4252",
        "button_fg": "#81A1C1",
        "button_hover": "#434C5E",
        "menu_bg": "#3B4252",
        "menu_fg": "#88C0D0",
        "menu_hover": "#4C566A",
        "tab_bg": "#3B4252",
        "tab_fg": "#81A1C1",
        "tab_hover": "#4C566A",
        "groupbox_bg": "#3B4252",
        "groupbox_fg": "#8FBCBB",
        "table_bg": "#2E3440",
        "table_header": "#4C566A",
        "highlight": "#88C0D0",
        "border": "1px solid #4C566A",
        "border_radius": "5px",
        "padding": "8px",
        "font_family": "'Fira Code', monospace",
        "scroll_handle": "#4C566A",
        "disabled": "#616E88",
    },

    "Solarized Light": {
        "background": "#FDF6E3",
        "foreground": "#657B83",
        "button_bg": "#EEE8D5",
        "button_fg": "#268BD2",
        "button_hover": "#D5D8DC",
        "menu_bg": "#EEE8D5",
        "menu_fg": "#2AA198",
        "menu_hover": "#D5D8DC",
        "tab_bg": "#EEE8D5",
        "tab_fg": "#859900",
        "tab_hover": "#D5D8DC",
        "groupbox_bg": "#EEE8D5",
        "groupbox_fg": "#CB4B16",
        "table_bg": "#FDF6E3",
        "table_header": "#D5D8DC",
        "highlight": "#268BD2",
        "border": "1px solid #93A1A1",
        "border_radius": "5px",
        "padding": "8px",
        "font_family": "'Source Sans Pro', sans-serif",
        "scroll_handle": "#93A1A1",
        "disabled": "#B5BFC9",

    },

    "Cyberpunk": {
        "background": "#0A0A12",
        "foreground": "#FF00FF",
        "button_bg": "#1A1A2F",
        "button_fg": "#00FFEE",
        "button_hover": "#2A2A4F",
        "menu_bg": "rgba(26, 26, 47, 0.9)",  # Лёгкая прозрачность
        "menu_fg": "#FF0055",
        "menu_hover": "#2A2A4F",
        "tab_bg": "#1A1A2F",
        "tab_fg": "#00FFEE",
        "tab_hover": "#2A2A4F",
        "groupbox_bg": "rgba(26, 26, 47, 0.85)",
        "groupbox_fg": "#FF0055",
        "table_bg": "#0A0A12",
        "table_header": "#2A2A4F",
        "highlight": "#FF0055",
        "border": "2px solid #00FFEE",
        "border_radius": "8px",  # Чуть мягче
        "padding": "10px",
        "font_family": "'Rajdhani', sans-serif",
        "scroll_handle": "#00FFEE",
        "disabled": "#4A4A6F",
    },

    "Forest": {
        "background": "#132A13",
        "foreground": "#C8E6C9",
        "button_bg": "#1F3D1F",
        "button_fg": "#A5D6A7",
        "button_hover": "#2D522D",
        "menu_bg": "#1F3D1F",
        "menu_fg": "#81C784",
        "menu_hover": "#2D522D",
        "tab_bg": "#1F3D1F",
        "tab_fg": "#A5D6A7",
        "tab_hover": "#2D522D",
        "groupbox_bg": "#1F3D1F",
        "groupbox_fg": "#81C784",
        "table_bg": "#132A13",
        "table_header": "#2D522D",
        "highlight": "#81C784",
        "border": "1px solid #4CAF50",
        "border_radius": "10px",
        "padding": "10px",
        "font_family": "'Open Sans', sans-serif",
        "scroll_handle": "#4CAF50",
        "disabled": "#6B8B6B",
    }
}


def apply_theme(theme_name):
    """Возвращает CSS-строку для применения темы с защитой от отсутствующих ключей."""
    base_theme = THEMES.get("Светлая", {})
    current_theme = THEMES.get(theme_name, {})  # Если нет, берется Светлая
    safe_theme = {
        "disabled": "#808080",
        "scroll_handle": "#cccccc",
        "font_family": "Arial, sans-serif",
        "button_hover": "#e0e0e0",
        "tab_hover": "#e0e0e0",
        "menu_hover": "#e0e0e0",
        **base_theme,
        **current_theme
    }
    safe_theme.setdefault("table_header", safe_theme["button_hover"])
    safe_theme.setdefault("border", f"1px solid {safe_theme['button_hover']}")

    # Формируем CSS с более компактными правилами
    return f"""
        QWidget {{
            background: {safe_theme['background']};
            color: {safe_theme['foreground']};
            font-family: {safe_theme['font_family']};
            font-size: 13px;
            border: none;
        }}
        QPushButton {{
            background: {safe_theme['button_bg']};
            color: {safe_theme['button_fg']};
            border: {safe_theme['border']};
            border-radius: {safe_theme['border_radius']};
            padding: {safe_theme['padding']};
            min-width: 80px;
        }}
        QPushButton:hover {{
            background: {safe_theme['button_hover']};
        }}
        QPushButton:pressed {{
            background: {safe_theme['highlight']};
            color: {safe_theme['background']};
        }}
        QLineEdit, QTextEdit {{
            background: {safe_theme['background']};
            border: {safe_theme['border']};
            border-radius: {safe_theme['border_radius']};
            padding: 4px;
        }}
        QTableWidget {{
            background: {safe_theme['table_bg']};
            gridline-color: {safe_theme['border']};
        }}
        QHeaderView::section {{
            background: {safe_theme['table_header']};
            padding: 6px;
        }}
        QTabWidget::pane {{
            border: {safe_theme['border']};
        }}
        QTabBar::tab {{
            background: {safe_theme['tab_bg']};
            color: {safe_theme['tab_fg']};
            padding: 6px 12px;
            border-bottom: 2px solid transparent;
        }}
        QTabBar::tab:hover {{
            background: {safe_theme['tab_hover']};
        }}
        QTabBar::tab:selected {{
            border-bottom: 2px solid {safe_theme['highlight']};
        }}
        QGroupBox {{
            background: {safe_theme['groupbox_bg']};
            color: {safe_theme['groupbox_fg']};
            border: {safe_theme['border']};
            border-radius: {safe_theme['border_radius']};
            margin-top: 1em;
            padding-top: 8px;
        }}
        QGroupBox::title {{
            subcontrol-origin: margin;
            left: 8px;
            padding: 0 3px;
        }}
        QToolTip {{
            background: {safe_theme['background']};
            color: {safe_theme['foreground']};
            border: {safe_theme['border']};
            border-radius: {safe_theme['border_radius']};
            padding: 4px;
        }}
        QMenuBar {{
            background: {safe_theme['menu_bg']};
            padding: 4px;
        }}
        QMenuBar::item {{
            padding: 4px 8px;
        }}
        QMenuBar::item:selected, QMenu::item:selected {{
            background: {safe_theme['menu_hover']};
        }}
        QScrollBar:vertical {{
            width: 10px;
            background: {safe_theme['background']};
        }}
        QScrollBar::handle:vertical {{
            background: {safe_theme['scroll_handle']};
            min-height: 20px;
        }}
    """.replace('\n', ' ').strip()
