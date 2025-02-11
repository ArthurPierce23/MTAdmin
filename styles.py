# styles.py
"""
Модуль определения стилей для программы.
Содержит стили уведомлений и набор тем оформления.
Функция apply_theme(theme_name: str) возвращает CSS-строку для применения выбранной темы.
"""

from typing import Optional, Dict

# Стили уведомлений
NOTIFICATION_STYLES: Dict[str, Dict[str, str]] = {
    "default": {
        "background": "rgba(250, 250, 250, 0.98)",
        "border": "1px solid rgba(0, 0, 0, 0.15)",
        "text": "#222222",
        "shadow": "0px 4px 8px rgba(0, 0, 0, 0.2)",
        "icon": ""
    },
    "error": {
        "background": "#ffdddd",
        "border": "1px solid #ff5555",
        "text": "#a00000",
        "shadow": "0px 4px 8px rgba(255, 85, 85, 0.5)",
        "icon": "⚠️"
    },
    "success": {
        "background": "#ddffdd",
        "border": "1px solid #55aa55",
        "text": "#007700",
        "shadow": "0px 4px 8px rgba(85, 170, 85, 0.5)",
        "icon": "✅"
    },
    "info": {
        "background": "#ddeeff",
        "border": "1px solid #3399ff",
        "text": "#0055aa",
        "shadow": "0px 4px 8px rgba(51, 153, 255, 0.5)",
        "icon": "ℹ️"
    },
    "warning": {
        "background": "#fff2cc",
        "border": "1px solid #ffaa00",
        "text": "#aa5500",
        "shadow": "0px 4px 8px rgba(255, 170, 0, 0.5)",
        "icon": "⚠️"
    }
}

# Определение тем оформления
THEMES: Dict[str, Optional[Dict[str, str]]] = {
    "Стандартная": None,
    "Светлая": {
        "background": "#fefefe",
        "foreground": "#222222",
        "button_bg": "#e6e6e6",
        "button_fg": "#222222",
        "button_hover": "#d4d4d4",
        "menu_bg": "#ffffff",
        "menu_fg": "#222222",
        "menu_hover": "#e0e0e0",
        "tab_bg": "#fafafa",
        "tab_fg": "#222222",
        "tab_hover": "#dddddd",
        "groupbox_bg": "#ffffff",
        "groupbox_fg": "#222222",
        "table_bg": "#ffffff",
        "table_header": "#e0e0e0",
        "highlight": "#007aff",
        "border": "1px solid #c0c0c0",
        "border_radius": "12px",
        "padding": "14px",
        "font_family": "Inter, sans-serif",
        "font_size": "14px",
        "header_font_size": "16px",
        "disabled": "#aaaaaa",
        "scroll_handle": "#bbbbbb",
        "progress_bg": "#e0e0e0",
        "progress_fg": "#007aff",
        "input_border": "1px solid #c0c0c0",
    },
    "Темная": {
        "background": "#121212",
        "foreground": "#e0e0e0",
        "button_bg": "#1f1f1f",
        "button_fg": "#e0e0e0",
        "button_hover": "#292929",
        "menu_bg": "#1a1a1a",
        "menu_fg": "#e0e0e0",
        "menu_hover": "#242424",
        "tab_bg": "#1a1a1a",
        "tab_fg": "#e0e0e0",
        "tab_hover": "#242424",
        "groupbox_bg": "#1a1a1a",
        "groupbox_fg": "#e0e0e0",
        "table_bg": "#121212",
        "table_header": "#2c2c2c",
        "highlight": "#ff4081",
        "border": "1px solid #333333",
        "border_radius": "12px",
        "padding": "14px",
        "font_family": "Inter, sans-serif",
        "font_size": "14px",
        "header_font_size": "16px",
        "disabled": "#666666",
        "scroll_handle": "#444444",
        "progress_bg": "#333333",
        "progress_fg": "#ff4081",
        "input_border": "1px solid #555555",
    },
    "Material Blue": {
        "background": "#e0f7fa",
        "foreground": "#01579b",
        "button_bg": "#b3e5fc",
        "button_fg": "#01579b",
        "button_hover": "#81d4fa",
        "menu_bg": "#e0f7fa",
        "menu_fg": "#01579b",
        "menu_hover": "#81d4fa",
        "tab_bg": "#b3e5fc",
        "tab_fg": "#01579b",
        "tab_hover": "#81d4fa",
        "groupbox_bg": "#e0f7fa",
        "groupbox_fg": "#01579b",
        "table_bg": "#e0f7fa",
        "table_header": "#81d4fa",
        "highlight": "#0288d1",
        "border": "1px solid #81d4fa",
        "border_radius": "12px",
        "padding": "14px",
        "font_family": "Segoe UI, sans-serif",
        "font_size": "14px",
        "header_font_size": "16px",
        "disabled": "#90a4ae",
        "scroll_handle": "#81d4fa",
        "progress_bg": "#b3e5fc",
        "progress_fg": "#0288d1",
        "input_border": "1px solid #81d4fa",
    },
    "Deep Space": {
        "background": "#0d0d0d",
        "foreground": "#cfcfcf",
        "button_bg": "#181818",
        "button_fg": "#cfcfcf",
        "button_hover": "#242424",
        "menu_bg": "#121212",
        "menu_fg": "#cfcfcf",
        "menu_hover": "#1e1e1e",
        "tab_bg": "#181818",
        "tab_fg": "#cfcfcf",
        "tab_hover": "#242424",
        "groupbox_bg": "#121212",
        "groupbox_fg": "#cfcfcf",
        "table_bg": "#0d0d0d",
        "table_header": "#1e1e1e",
        "highlight": "#00e5ff",
        "border": "1px solid #1e1e1e",
        "border_radius": "12px",
        "padding": "14px",
        "font_family": "'Roboto Mono', monospace",
        "font_size": "14px",
        "header_font_size": "16px",
        "disabled": "#616e88",
        "scroll_handle": "#1e1e1e",
        "progress_bg": "#1e1e1e",
        "progress_fg": "#00e5ff",
        "input_border": "1px solid #444444",
    },
    "Nord": {
        "background": "#2E3440",
        "foreground": "#D8DEE9",
        "button_bg": "#3B4252",
        "button_fg": "#81A1C1",
        "button_hover": "#4C566A",
        "menu_bg": "#3B4252",
        "menu_fg": "#D8DEE9",
        "menu_hover": "#4C566A",
        "tab_bg": "#3B4252",
        "tab_fg": "#D8DEE9",
        "tab_hover": "#4C566A",
        "groupbox_bg": "#3B4252",
        "groupbox_fg": "#D8DEE9",
        "table_bg": "#2E3440",
        "table_header": "#4C566A",
        "highlight": "#88C0D0",
        "border": "1px solid #4C566A",
        "border_radius": "12px",
        "padding": "14px",
        "font_family": "'Fira Code', monospace",
        "font_size": "14px",
        "header_font_size": "16px",
        "scroll_handle": "#4C566A",
        "disabled": "#616E88",
        "progress_bg": "#4C566A",
        "progress_fg": "#88C0D0",
        "input_border": "1px solid #5c6773",
    },
    "Solarized Light": {
        "background": "#FDF6E3",
        "foreground": "#4d4d4d",
        "button_bg": "#EEE8D5",
        "button_fg": "#4d4d4d",
        "button_hover": "#e1d7c6",
        "menu_bg": "#FDF6E3",
        "menu_fg": "#4d4d4d",
        "menu_hover": "#e1d7c6",
        "tab_bg": "#FDF6E3",
        "tab_fg": "#4d4d4d",
        "tab_hover": "#e1d7c6",
        "groupbox_bg": "#FDF6E3",
        "groupbox_fg": "#4d4d4d",
        "table_bg": "#FDF6E3",
        "table_header": "#e1d7c6",
        "highlight": "#268bd2",
        "border": "1px solid #93A1A1",
        "border_radius": "12px",
        "padding": "14px",
        "font_family": "'Source Sans Pro', sans-serif",
        "font_size": "14px",
        "header_font_size": "16px",
        "scroll_handle": "#93A1A1",
        "disabled": "#B5BFC9",
        "progress_bg": "#e1d7c6",
        "progress_fg": "#268bd2",
        "input_border": "1px solid #aaa",
    },
    "Cyberpunk Neon": {
        "background": "#000814",
        "foreground": "#00ffcc",
        "button_bg": "#001f3f",
        "button_fg": "#00ffcc",
        "button_hover": "#003366",
        "menu_bg": "#001f3f",
        "menu_fg": "#00ffcc",
        "menu_hover": "#003366",
        "tab_bg": "#001f3f",
        "tab_fg": "#00ffcc",
        "tab_hover": "#003366",
        "groupbox_bg": "#001f3f",
        "groupbox_fg": "#00ffcc",
        "table_bg": "#000814",
        "table_header": "#003366",
        "highlight": "#ff0077",
        "border": "1px solid #00ffcc",
        "border_radius": "12px",
        "padding": "14px",
        "font_family": "'Orbitron', sans-serif",
        "font_size": "14px",
        "header_font_size": "16px",
        "scroll_handle": "#00ffcc",
        "disabled": "#4a4a6f",
        "progress_bg": "#003366",
        "progress_fg": "#ff0077",
        "input_border": "1px solid #00ffcc",
    },
    "Forest": {
        "background": "#0b3d0b",
        "foreground": "#d0f0c0",
        "button_bg": "#145214",
        "button_fg": "#d0f0c0",
        "button_hover": "#1a6a1a",
        "menu_bg": "#0b3d0b",
        "menu_fg": "#d0f0c0",
        "menu_hover": "#1a6a1a",
        "tab_bg": "#0b3d0b",
        "tab_fg": "#d0f0c0",
        "tab_hover": "#1a6a1a",
        "groupbox_bg": "#0b3d0b",
        "groupbox_fg": "#d0f0c0",
        "table_bg": "#0b3d0b",
        "table_header": "#1a6a1a",
        "highlight": "#81c784",
        "border": "1px solid #4caf50",
        "border_radius": "12px",
        "padding": "14px",
        "font_family": "'Open Sans', sans-serif",
        "font_size": "14px",
        "header_font_size": "16px",
        "scroll_handle": "#4caf50",
        "disabled": "#6b8b6b",
        "progress_bg": "#1a6a1a",
        "progress_fg": "#81c784",
        "input_border": "1px solid #4caf50",
    },
    "Valentine": {
        "background": "#ffe6f2",
        "foreground": "#8a1538",
        "button_bg": "#ffb6c1",
        "button_fg": "#8a1538",
        "button_hover": "#ff9aa2",
        "menu_bg": "#ffe6f2",
        "menu_fg": "#8a1538",
        "menu_hover": "#ffb3ba",
        "tab_bg": "#ffe6f2",
        "tab_fg": "#8a1538",
        "tab_hover": "#ffb3ba",
        "groupbox_bg": "#ffe6f2",
        "groupbox_fg": "#8a1538",
        "table_bg": "#fff5f7",
        "table_header": "#ffb6c1",
        "highlight": "#e91e63",
        "border": "1px solid #ff4081",
        "border_radius": "10px",
        "padding": "14px",
        "font_family": "'Poppins', sans-serif",
        "font_size": "14px",
        "header_font_size": "16px",
        "disabled": "#e0a4ac",
        "scroll_handle": "#ffb6c1",
        "progress_bg": "#ffe6f2",
        "progress_fg": "#e91e63",
        "input_border": "1px solid #ff4081",
    },
    "HACKERMAN": {
        "background": "#000000",
        "foreground": "#00ff00",
        "button_bg": "#000000",
        "button_fg": "#00ff00",
        "button_hover": "#003300",
        "menu_bg": "#000000",
        "menu_fg": "#00ff00",
        "menu_hover": "#003300",
        "tab_bg": "#000000",
        "tab_fg": "#00ff00",
        "tab_hover": "#003300",
        "groupbox_bg": "#000000",
        "groupbox_fg": "#00ff00",
        "table_bg": "#000000",
        "table_header": "#003300",
        "highlight": "#00ff00",
        "border": "1px solid #00ff00",
        "border_radius": "0px",
        "padding": "14px",
        "font_family": "'OCR A Extended', 'Courier New', monospace",
        "font_size": "14px",
        "header_font_size": "16px",
        "disabled": "#005500",
        "scroll_handle": "#00ff00",
        "progress_bg": "#000000",
        "progress_fg": "#00ff00",
        "input_border": "1px solid #00ff00",
    }
}

def apply_theme(theme_name: str) -> str:
    """
    Возвращает CSS-строку для применения выбранной темы.
    Если выбран ключ "Без темы" (None), возвращается пустая строка.
    Для отсутствующих ключей используются значения из базовой темы ("Светлая").
    """
    base_theme: Dict[str, str] = THEMES.get("Светлая", {})
    current_theme: Optional[Dict[str, str]] = THEMES.get(theme_name, {})

    if current_theme is None:
        safe_theme = {
            "font_size": base_theme.get("font_size", "14px"),
            "foreground": base_theme.get("foreground", "#333333"),
            "button_bg": base_theme.get("button_bg", "#d9d9d9"),
            "button_fg": base_theme.get("button_fg", "#333333"),
            "button_hover": base_theme.get("button_hover", "#c9c9c9"),
            "border": base_theme.get("border", "2px solid #b3b3b3"),
            "border_radius": base_theme.get("border_radius", "6px"),
            "background": base_theme.get("background", "#f0f0f0"),
            "highlight": base_theme.get("highlight", "#007aff")
        }
        css = f"""
            QPushButton#addTabButton {{
                font-size: {safe_theme['font_size']};
                font-weight: bold;
                color: {safe_theme['foreground']};
                background-color: {safe_theme['button_bg']};
                border: 2px solid {safe_theme['button_fg']};
                border-radius: {safe_theme['border_radius']};
                padding: 2px;
                min-width: 14px;
                min-height: 14px;
            }}
            QPushButton#addTabButton:hover {{
                background-color: {safe_theme['button_hover']};
                border-color: {safe_theme['highlight']};
            }}
            QPushButton#addTabButton:pressed {{
                background-color: {safe_theme['highlight']};
                color: {safe_theme['background']};
            }}
        """
        return " ".join(css.split())

    safe_theme: Dict[str, str] = {
        "background": "#f0f0f0",
        "foreground": "#333333",
        "button_bg": "#d9d9d9",
        "button_fg": "#333333",
        "button_hover": "#c9c9c9",
        "border": "2px solid #b3b3b3",
        "border_radius": "6px",
        "padding": "6px 10px",
        "font_size": "14px",
        "header_font_size": "18px",
        **base_theme,
        **current_theme,
    }
    safe_theme.setdefault("table_header", safe_theme["button_hover"])
    safe_theme.setdefault("progress_bg", "#dddddd")
    safe_theme.setdefault("progress_fg", "#4d90fe")
    safe_theme["header_font_size"] = safe_theme.get("header_font_size", "18px")

    # Вычисляем цвет границы из полного описания (например, "1px solid #c0c0c0")
    border_parts = safe_theme["border"].split()
    safe_theme["border_color"] = border_parts[-1] if len(border_parts) >= 3 else safe_theme["border"]

    css = f"""
        QWidget {{
            font-size: {safe_theme['font_size']};
            background: {safe_theme['background']};
            color: {safe_theme['foreground']};
            font-family: {safe_theme['font_family']};
            border: none;
        }}
        QLabel {{
            font-size: {safe_theme['font_size']};
            font-weight: bold;
            color: {safe_theme['foreground']};
            text-shadow: 0 0 4px {safe_theme['highlight']};
            background: transparent;
        }}
        QPushButton {{
            background: {safe_theme['button_bg']};
            color: {safe_theme['button_fg']};
            border: {safe_theme['border']};
            border-radius: {safe_theme['border_radius']};
            padding: {safe_theme['padding']};
            min-width: 80px;
            transition: background 0.2s ease-in-out, box-shadow 0.2s ease-in-out;
        }}
        QPushButton:hover {{
            background: {safe_theme['button_hover']};
            box-shadow: 0 0 8px {safe_theme['highlight']};
        }}
        QPushButton:pressed {{
            background: {safe_theme['highlight']};
            color: {safe_theme['background']};
            box-shadow: none;
        }}
        QLineEdit, QTextEdit {{
            background: {safe_theme['background']};
            color: {safe_theme['foreground']};
            border: {safe_theme.get('input_border', '1px solid #888888')};
            border-radius: 6px;
            padding: 6px 10px;
            selection-background-color: {safe_theme['highlight']};
        }}
        QLineEdit:focus, QTextEdit:focus {{
            border-color: {safe_theme['highlight']};
            box-shadow: 0 0 8px {safe_theme['highlight']};
        }}
        QLineEdit:empty, QTextEdit:empty {{
            background: {safe_theme['background']};
            color: {safe_theme['foreground']};
        }}
        QLabel#labelBold {{
            font-size: 14px;
            font-weight: bold;
            color: {safe_theme['foreground']};
        }}
        QLineEdit#inputField {{
            border: {safe_theme.get('input_border', '1px solid #888888')};
            border-radius: 6px;
            padding: 6px;
            font-size: {safe_theme['font_size']};
        }}
        QPushButton#actionButton {{
            font-size: {safe_theme['font_size']};
            font-weight: bold;
            background: {safe_theme['button_bg']};
            color: {safe_theme['button_fg']};
            border: {safe_theme['border']};
            border-radius: {safe_theme['border_radius']};
            padding: {safe_theme['padding']};
            min-height: 40px;
        }}
        QPushButton#actionButton:hover {{
            background: {safe_theme['button_hover']};
        }}
        QPushButton#actionButton:pressed {{
            background: {safe_theme['highlight']};
            color: {safe_theme['background']};
        }}
        QPushButton#addTabButton {{
            font-size: {safe_theme.get('font_size', '14px')};
            font-weight: bold;
            color: {safe_theme.get('foreground', '#333333')};
            background-color: {safe_theme.get('button_bg', '#d9d9d9')};
            border: 2px solid {safe_theme.get('button_fg', '#222222')};
            border-radius: 6px;
            padding: 4px;
            min-width: 16px;
            min-height: 16px;
        }}
        QPushButton#addTabButton:hover {{
            background-color: {safe_theme['button_hover']};
            border-color: {safe_theme['highlight']};
        }}
        QPushButton#addTabButton:pressed {{
            background-color: {safe_theme['highlight']};
            color: {safe_theme['background']};
        }}
        QFrame::HLine {{
            background-color: {safe_theme['border_color']};
            height: 1px;
        }}
        QLineEdit:disabled {{
            background: {safe_theme['disabled']};
            color: #666666;
        }}
        QTableWidget {{
            background: {safe_theme['table_bg']};
            gridline-color: {safe_theme['border_color']};
            alternate-background-color: rgba(0, 0, 0, 0.05);
            border-radius: 6px;
        }}
        QHeaderView::section {{
            background: {safe_theme['table_header']};
            font-weight: bold;
            color: {safe_theme['foreground']};
            padding: 6px;
            border-bottom: 2px solid {safe_theme['border_color']};
        }}
        QProgressBar {{
            background: {safe_theme['progress_bg']};
            border: none;
        }}
        QProgressBar::chunk {{
            background: {safe_theme['highlight']};
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
            font-size: {safe_theme['header_font_size']};
            font-weight: bold;
            color: {safe_theme['groupbox_fg']};
            background: {safe_theme['groupbox_bg']};
            border: {safe_theme['border']};
            border-radius: {safe_theme['border_radius']};
            margin-top: 10px;
            padding: 10px;
            box-shadow: 0px 2px 4px rgba(0, 0, 0, 0.1);
        }}
        QGroupBox::title {{
            subcontrol-origin: margin;
            left: 10px;
            padding: 4px 10px;
            background: {safe_theme['groupbox_bg']};
            border-radius: {safe_theme['border_radius']};
            border: {safe_theme['border']};
            box-shadow: 0px 2px 4px rgba(0, 0, 0, 0.1);
            font-size: {safe_theme['header_font_size']};
        }}
        QLabel#title {{
            font-size: 16px;
            font-weight: bold;
            padding-bottom: 4px;
        }}
        QTableWidget#usersTable {{
            alternate-background-color: rgba(0, 0, 0, 0.05);
            gridline-color: transparent;
        }}
        QToolTip {{
            background: {safe_theme['background']};
            color: {safe_theme['foreground']};
            border: {safe_theme['border']};
            border-radius: {safe_theme['border_radius']};
            padding: 4px;
            text-shadow: 0 0 4px {safe_theme['highlight']};
        }}
        QMenuBar {{
            background: {safe_theme['menu_bg']};
            padding: 4px;
            border-bottom: 1px solid {safe_theme['border_color']};
            color: {safe_theme['menu_fg']};
        }}
        QMenu {{
            background: {safe_theme['menu_bg']};
            border: {safe_theme['border']};
            color: {safe_theme['menu_fg']};
            margin-top: 2px;
            padding: 4px;
        }}
        QPushButton#refreshButton {{
            font-size: {safe_theme['font_size']};
            font-weight: bold;
            background: {safe_theme['button_bg']};
            color: {safe_theme['button_fg']};
            border: {safe_theme['border']};
            border-radius: {safe_theme['border_radius']};
            padding: {safe_theme['padding']};
            min-width: 80px;
        }}
        QPushButton#refreshButton:hover {{
            background: {safe_theme['button_hover']};
        }}
        QPushButton#refreshButton:pressed {{
            background: {safe_theme['highlight']};
            color: {safe_theme['background']};
        }}
        QGroupBox#groupBox {{
            font-size: {safe_theme['header_font_size']};
            font-weight: bold;
            color: {safe_theme['groupbox_fg']};
            background: {safe_theme['groupbox_bg']};
            border: {safe_theme['border']};
            border-radius: {safe_theme['border_radius']};
            padding: {safe_theme['padding']};
            margin-top: 10px;
        }}
        QPushButton#commandButton {{
            font-size: {safe_theme['font_size']};
            font-weight: bold;
            color: {safe_theme['button_fg']};
            background: {safe_theme['button_bg']};
            border: {safe_theme['border']};
            border-radius: {safe_theme['border_radius']};
            padding: {safe_theme['padding']};
            min-height: 40px;
        }}
        QPushButton#commandButton:hover {{
            background: {safe_theme['button_hover']};
        }}
        QPushButton#commandButton:pressed {{
            background: {safe_theme['highlight']};
            color: {safe_theme['background']};
        }}
        QFrame#separator {{
            background-color: {safe_theme['border_color']};
            height: 1px;
        }}
        QLabel#headerLabel {{
            font-size: 18px;
            font-weight: bold;
            padding: 10px;
            border: 2px solid {safe_theme['border_color']};
            border-radius: {safe_theme['border_radius']};
            background: {safe_theme['menu_bg']};
            color: {safe_theme['menu_fg']};
            text-align: center;
            margin-bottom: 10px;
            box-shadow: 0px 2px 4px rgba(0, 0, 0, 0.1);
        }}
        QScrollArea#scrollArea {{
            border: none;
            background: {safe_theme['background']};
        }}
        QWidget#contentWidget {{
            background: {safe_theme['background']};
            padding: 12px;
        }}
        QWidget#mainWindow {{
            background: {safe_theme['background']};
        }}
        QMenuBar::item {{
            background: transparent;
            padding: 6px 12px;
            margin: 0 4px;
        }}
        QMenu::item {{
            padding: 4px 20px;
        }}
        QMessageBox {{
            background: {safe_theme['background']};
            color: {safe_theme['foreground']};
        }}
        QMenuBar::item:selected, QMenu::item:selected {{
            background: {safe_theme['menu_hover']};
            border-radius: 4px;
        }}
        QScrollBar:vertical {{
            width: 10px;
            background: transparent;
        }}
        QScrollBar::handle:vertical {{
            background: {safe_theme['scroll_handle']};
            min-height: 20px;
            border-radius: 5px;
            transition: background 0.2s;
        }}
        QScrollBar::handle:vertical:hover {{
            background: {safe_theme['highlight']};
        }}
        QScrollBar::add-line, QScrollBar::sub-line {{
            background: none;
        }}
    """
    return " ".join(css.split())
