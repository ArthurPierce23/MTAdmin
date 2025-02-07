# styles.py

NOTIFICATION_STYLES = {
    "default": {
        "background": "rgba(250, 250, 250, 0.95)",
        "border": "1px solid rgba(0, 0, 0, 0.1)",
        "text": "#222222",
        "shadow": "0px 3px 6px rgba(0, 0, 0, 0.15)",
        "icon": ""
    },
    "error": {
        "background": "#ffdddd",
        "border": "1px solid #ff5555",
        "text": "#a00000",
        "icon": "⚠️"
    },
    "success": {
        "background": "#ddffdd",
        "border": "1px solid #55aa55",
        "text": "#007700",
        "icon": "✅"
    },
    "info": {  # Добавил стиль информационных сообщений
        "background": "#ddeeff",
        "border": "1px solid #3399ff",
        "text": "#0055aa",
        "icon": "ℹ️"
    },
    "warning": {  # Добавил стиль предупреждений
        "background": "#fff2cc",
        "border": "1px solid #ffaa00",
        "text": "#aa5500",
        "icon": "⚠️"
    }
}

THEMES = {
    "Без темы": None,  # Отключает применение CSS
    "Светлая": {
        "background": "#ffffff",
        "foreground": "#333333",
        "button_bg": "#f0f0f0",
        "button_fg": "#222222",
        "button_hover": "#e0e0e0",
        "menu_bg": "#ffffff",
        "menu_fg": "#222222",
        "menu_hover": "#f0f0f0",
        "tab_bg": "#f5f5f5",
        "tab_fg": "#222222",
        "tab_hover": "#dddddd",
        "groupbox_bg": "#ffffff",
        "groupbox_fg": "#333333",
        "table_bg": "#ffffff",
        "table_header": "#e0e0e0",
        "highlight": "#4a90e2",
        "border": "1px solid #d0d0d0",
        "border_radius": "10px",  # Было 6px – уменьшил
        "padding": "10px",  # Было 6px – уменьшил
        "font_family": "Inter, sans-serif",
        "font_size": "13px",  # Было 14px – уменьшил
        "header_font_size": "16px",  # Было 18px – уменьшил
        "disabled": "#aaaaaa",
        "scroll_handle": "#cccccc",
        "progress_bg": "#e0e0e0",
        "progress_fg": "#4a90e2",
    },

    "Темная": {
        "background": "#181818",
        "foreground": "#e0e0e0",
        "button_bg": "#222222",
        "button_fg": "#ffffff",
        "button_hover": "#2d2d2d",
        "menu_bg": "#222222",
        "menu_fg": "#dddddd",
        "menu_hover": "#333333",
        "tab_bg": "#222222",
        "tab_fg": "#cccccc",
        "tab_hover": "#444444",
        "groupbox_bg": "#222222",
        "groupbox_fg": "#dddddd",
        "table_bg": "#181818",
        "table_header": "#333333",
        "highlight": "#5ab4f8",
        "border": "1px solid #333333",
        "border_radius": "10px",  # Было 6px
        "padding": "10px",  # Было 6px
        "font_family": "Inter, sans-serif",
        "font_size": "13px",  # Было 14px
        "header_font_size": "16px",  # Было 18px
        "disabled": "#666666",
        "scroll_handle": "#444444",
        "progress_bg": "#555555",
        "progress_fg": "#5ab4f8",
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
        "border_radius": "10px",  # Было 8px
        "padding": "10px",  # Было 8px
        "font_family": "Segoe UI, sans-serif",
        "font_size": "13px",
        "header_font_size": "16px",
        "disabled": "#90a4ae",
        "scroll_handle": "#bbdefb",
        "progress_bg": "#bbdefb",
        "progress_fg": "#0d47a1",
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
        "font_size": "13px",
        "header_font_size": "16px",
        "disabled": "#616E88",
        "scroll_handle": "#2A2A2A",
        "progress_bg": "#2A2A2A",
        "progress_fg": "#74B3CE",
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
        "border_radius": "10px",  # Было 5px
        "padding": "10px",  # Было 8px
        "font_family": "'Fira Code', monospace",
        "font_size": "13px",
        "header_font_size": "16px",
        "scroll_handle": "#4C566A",
        "disabled": "#616E88",
        "progress_bg": "#4C566A",
        "progress_fg": "#88C0D0",
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
        "border_radius": "10px",  # Было 5px
        "padding": "10px",  # Было 8px
        "font_family": "'Source Sans Pro', sans-serif",
        "font_size": "13px",
        "header_font_size": "16px",
        "scroll_handle": "#93A1A1",
        "disabled": "#B5BFC9",
        "progress_bg": "#D5D8DC",
        "progress_fg": "#268BD2",

    },

    "Cyberpunk Neon": {  # Улучшенная киберпанк-тема
        "background": "#000814",
        "foreground": "#00ffcc",
        "button_bg": "#001f3f",
        "button_fg": "#00ffcc",
        "button_hover": "#003366",
        "menu_bg": "#001f3f",
        "menu_fg": "#ff0077",
        "menu_hover": "#003366",
        "tab_bg": "#001f3f",
        "tab_fg": "#00ffcc",
        "tab_hover": "#003366",
        "groupbox_bg": "#001f3f",
        "groupbox_fg": "#ff0077",
        "table_bg": "#000814",
        "table_header": "#003366",
        "highlight": "#ff0077",
        "border": "1px solid #00ffcc",
        "border_radius": "10px",  # Было 8px
        "padding": "10px",
        "font_family": "'Orbitron', sans-serif",
        "font_size": "13px",  # Было 14px
        "header_font_size": "16px",  # Было 18px
        "scroll_handle": "#00ffcc",
        "disabled": "#4A4A6F",
        "progress_bg": "#003366",
        "progress_fg": "#ff0077",
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
        "font_size": "13px",
        "header_font_size": "16px",
        "scroll_handle": "#4CAF50",
        "disabled": "#6B8B6B",
        "progress_bg": "#2D522D",
        "progress_fg": "#81C784",
    },
    "Valentine": {
        "background": "#ffe6e9",  # Убрали агрессивный градиент, заменили на нежно-розовый
        "foreground": "#5a2d2f",
        "button_bg": "#ffb6c1",
        "button_fg": "#5a2d2f",
        "button_hover": "#ff9aa2",
        "menu_bg": "#ffccd5",
        "menu_fg": "#5a2d2f",
        "menu_hover": "#ffb3ba",
        "tab_bg": "#ffccd5",
        "tab_fg": "#5a2d2f",
        "tab_hover": "#ffb3ba",
        "groupbox_bg": "#ffdde1",
        "groupbox_fg": "#5a2d2f",
        "table_bg": "#fff5f7",
        "table_header": "#ffb6c1",
        "highlight": "#ff85a2",
        "border": "1px solid #ffb3ba",
        "border_radius": "6px",  # Уменьшен радиус скругления
        "padding": "8px",  # Уменьшены отступы
        "font_family": "'Poppins', sans-serif",
        "font_size": "13px",
        "header_font_size": "16px",
        "disabled": "#e0a4ac",
        "scroll_handle": "#ffb6c1",
        "progress_bg": "#ffe6e9",
        "progress_fg": "#ff85a2",
    }
}

def apply_theme(theme_name):
    """Возвращает CSS-строку для применения темы с защитой от отсутствующих ключей."""
    base_theme = THEMES.get("Светлая", {})
    current_theme = THEMES.get(theme_name, {})

    if current_theme is None:  # 🔥 Проверяем, если тема "Без темы"
        return ""  # Если темы нет, сбрасываем стили

    safe_theme = {
        "background": "#f0f0f0",
        "foreground": "#333",
        "button_bg": "#d9d9d9",
        "button_fg": "#333",
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
    safe_theme.setdefault("border", f"1px solid {safe_theme['button_hover']}")
    safe_theme.setdefault("progress_bg", "#dddddd")
    safe_theme.setdefault("progress_fg", "#4d90fe")
    safe_theme["header_font_size"] = safe_theme.get("header_font_size", "16px")

    # Формируем CSS с более компактными правилами
    return f"""
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
            text-shadow: 1px 1px 2px rgba(0, 0, 0, 0.2);
            background: transparent;  /* Убираем лишний фон */
        }}
        QPushButton {{
            background: {safe_theme['button_bg']};
            color: {safe_theme['button_fg']};
            border: {safe_theme['border']};
            border-radius: {safe_theme['border_radius']};
            padding: {safe_theme['padding']};
            min-width: 80px;
            transition: background 0.2s ease-in-out, box-shadow 0.2s ease-in-out;  /* 🔥 Плавный переход */
        }}
        QPushButton:hover {{ 
            background: {safe_theme['button_hover']};
            box-shadow: 0px 3px 6px rgba(0, 0, 0, 0.15);  /* 🔥 Лёгкая тень при наведении */
        }}
        QPushButton:pressed {{
            background: {safe_theme['highlight']};
            color: {safe_theme['background']};
            box-shadow: none;
        }}
        QLineEdit, QTextEdit {{
            background: {safe_theme['background']};
            color: {safe_theme['foreground']};
            border: 1px solid {safe_theme['border']};
            border-radius: 8px;  /* 🔥 Чуть больше скругления */
            padding: 6px 10px;
            selection-background-color: {safe_theme['highlight']}; /* Красивое выделение */
        }}
        QLineEdit:focus {{
            border-color: {safe_theme['highlight']};
            box-shadow: 0 0 5px rgba(0, 120, 255, 0.4);
        }}
        
        QLabel#labelBold {{
            font-size: 14px;
            font-weight: bold;
            color: {safe_theme['foreground']};
        }}

        QLineEdit#inputField {{
            border: 1px solid {safe_theme['border']};
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
    
        QLineEdit, QTextEdit {{
            background: {safe_theme['background']};
            color: {safe_theme['foreground']};
            border: 1px solid {safe_theme['border']};
            border-radius: 6px;
            padding: 6px 10px;
            selection-background-color: {safe_theme['highlight']};
        }}
        QLineEdit:focus, QTextEdit:focus {{
            background: {safe_theme['background']};  /* 🔥 Теперь цвет не сбрасывается на белый */
            color: {safe_theme['foreground']};
            border-color: {safe_theme['highlight']};  /* 🔵 Подсветка рамки при фокусе */
            box-shadow: 0 0 5px rgba(0, 120, 255, 0.4);
        }}

        QLineEdit:empty, QTextEdit:empty {{  /* 🔥 Фикс сброса цвета на белый */
            background: {safe_theme['background']};  
            color: {safe_theme['foreground']};
        }}
    
        QPushButton#actionButton:hover {{
            background: {safe_theme['button_hover']};
        }}
    
        QPushButton#actionButton:pressed {{
            background: {safe_theme['highlight']};
            color: {safe_theme['background']};
        }}

        
        QPushButton#addTabButton {{
            font-size: {safe_theme['font_size'] if 'font_size' in safe_theme else '14px'};
            font-weight: bold;
            color: {safe_theme['foreground'] if 'foreground' in safe_theme else '#333'};
            background-color: {safe_theme['button_bg'] if 'button_bg' in safe_theme else '#d9d9d9'};
            border: '2px solid #b3b3b3';
            border-radius: '6px';
            padding: '6px';
            min-width: 16px;  /* Фиксируем размер, чтобы не скукоживалась */
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
            background-color: {safe_theme['border']}; /* Цвет границы темы */
            height: 1px;
        }}
        QLineEdit:disabled {{
            background: {safe_theme['disabled']};
            color: #666;
        }}
        QTableWidget {{
            background: {safe_theme['table_bg']};
            gridline-color: {safe_theme['border']};
            alternate-background-color: rgba(0, 0, 0, 0.05); /* 🔥 Чередование строк */
            border-radius: 6px;
        }}
        QHeaderView::section {{
            background: {safe_theme['table_header']};
            font-weight: bold;
            color: {safe_theme['foreground']};
            padding: 6px;
            border-bottom: 2px solid {safe_theme['border']}; /* 🔥 Подчеркиваем заголовок */
        }}
        QProgressBar {{
            background: {safe_theme['progress_bg']};
            border: none;
        }}
        QProgressBar::chunk {{ background: {safe_theme['highlight']}; }}
        QTabWidget::pane {{ border: {safe_theme['border']}; }}
        QTabBar::tab {{
            background: {safe_theme['tab_bg']};
            color: {safe_theme['tab_fg']};
            padding: 6px 12px;
            border-bottom: 2px solid transparent;
        }}
        QTabBar::tab:hover {{ background: {safe_theme['tab_hover']}; }}
        QTabBar::tab:selected {{ border-bottom: 2px solid {safe_theme['highlight']}; }}
        QGroupBox {{
            font-size: {safe_theme['header_font_size']};
            font-weight: bold;
            color: {safe_theme['groupbox_fg']};
            background: {safe_theme['groupbox_bg']};
            border: {safe_theme['border']};
            border-radius: {safe_theme['border_radius']};
            margin-top: 10px;
            padding: 10px;
            box-shadow: 0px 3px 6px rgba(0, 0, 0, 0.1); /* 🔥 Легкая тень */
        }}
        QGroupBox::title {{
            subcontrol-origin: margin;
            left: 10px;
            padding: 4px 10px;
            background: {safe_theme['groupbox_bg']};  /* 🔥 Заголовок теперь с мягким фоном */
            border-radius: {safe_theme['border_radius']};  /* 🔥 Скругление */
            border: 1px solid {safe_theme['border']};  /* 🔥 Тонкая граница */
            box-shadow: 0px 2px 4px rgba(0, 0, 0, 0.1); /* 🔥 Легкая тень */
        }}
        QLabel#title {{
            font-size: 16px; /* Можно поменять на safe_theme['header_font_size'] */
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
        }}
        QMenuBar {{
            background: {safe_theme['menu_bg']};
            padding: 4px;
            border-bottom: 1px solid {safe_theme['border']};
            color: {safe_theme['menu_fg']};
        }} 
        QMenu {{
            background: {safe_theme['menu_bg']};
            border: 1px solid {safe_theme['border']};
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
            background-color: var(--border);
            height: 1px;
        }}

        QLabel#headerLabel {{
            font-size: 18px;
            font-weight: bold;
            padding: 10px;
            border: 2px solid {safe_theme['border']};  /* Добавил границу */
            border-radius: {safe_theme['border_radius']}; /* Скругление углов */
            background: {safe_theme['menu_bg']};
            color: {safe_theme['menu_fg']};
            text-align: center;
            margin-bottom: 10px;  /* Чуть ниже от остальных элементов */
            box-shadow: 0px 3px 6px rgba(0, 0, 0, 0.1); /* Лёгкая тень */
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
            background: {safe_theme['highlight']};  /* 🔥 При наведении становится ярче */
        }}
        QScrollBar::add-line, QScrollBar::sub-line {{
            background: none; /* 🔥 Убираем кнопки вверх/вниз */
        }}
    """.replace('\n', ' ').strip()

