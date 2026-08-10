# theme.py
VOID = "#04060c"
PANEL = "#0c1220"
PANEL_2 = "#0f1830"
LINE = "#1c2740"
TEXT = "#e7edf7"
TEXT_DIM = "#8a97b3"
TEXT_FAINT = "#4b566d"

CYAN = "#4dd8ff"
AMBER = "#ffb454"
VIOLET = "#9b8cff"
CORAL = "#ff7a6b"
GREEN = "#5eeba0"

SPATIAL = "#4dd8ff"
ORBITAL = "#5eeba0"
SPECTRAL = "#9b8cff"
RADIOMETRIC = "#ffb454"

ENGINE_COLORS = {
    "spatial": SPATIAL,
    "orbital": ORBITAL,
    "spectral": SPECTRAL,
    "radiometric": RADIOMETRIC,
}

FONT_FAMILY = "Segoe UI, Inter, Arial"
MONO_FAMILY = "Consolas, 'JetBrains Mono', monospace"

STYLESHEET = f"""
QWidget {{
    background: transparent;
    color: {TEXT};
    font-family: {FONT_FAMILY};
    font-size: 13px;
}}
QMainWindow {{
    background-color: {VOID};
}}
#RootBg {{
    background-color: {VOID};
}}
QLabel[role="h1"] {{
    font-size: 22px;
    font-weight: 700;
    color: {TEXT};
}}
QLabel[role="h2"] {{
    font-size: 15px;
    font-weight: 600;
    color: {TEXT};
}}
QLabel[role="tag"] {{
    color: {CYAN};
    font-size: 11px;
    font-weight: 600;
    letter-spacing: 2px;
}}
QLabel[role="dim"] {{
    color: {TEXT_DIM};
    font-size: 12px;
}}
QLabel[role="mono"] {{
    font-family: {MONO_FAMILY};
    color: {CYAN};
}}
QFrame[role="card"] {{
    background-color: rgba(14, 20, 36, 210);
    border: 1px solid {LINE};
    border-radius: 12px;
}}
QFrame[role="panel"] {{
    background-color: rgba(12, 18, 32, 235);
    border: 1px solid {LINE};
    border-radius: 14px;
}}
QTabWidget::pane {{
    border: none;
    background: transparent;
}}
QTabBar::tab {{
    background: rgba(14,20,36,180);
    color: {TEXT_DIM};
    padding: 10px 20px;
    margin-right: 6px;
    border-top-left-radius: 10px;
    border-top-right-radius: 10px;
    border: 1px solid {LINE};
    border-bottom: none;
    font-weight: 600;
    letter-spacing: 0.5px;
}}
QTabBar::tab:selected {{
    background: rgba(77,216,255,28);
    color: {TEXT};
    border-color: {CYAN};
}}
QTabBar::tab:hover {{
    color: {TEXT};
}}
QScrollArea {{
    border: none;
    background: transparent;
}}
QScrollBar:vertical {{
    background: transparent;
    width: 10px;
}}
QScrollBar::handle:vertical {{
    background: {LINE};
    border-radius: 5px;
    min-height: 30px;
}}
QScrollBar::handle:vertical:hover {{
    background: {CYAN};
}}
QPushButton {{
    background: rgba(77,216,255,20);
    color: {TEXT};
    border: 1px solid {CYAN};
    border-radius: 8px;
    padding: 8px 16px;
    font-weight: 600;
}}
QPushButton:hover {{
    background: rgba(77,216,255,55);
}}
QPushButton:pressed {{
    background: rgba(77,216,255,90);
}}
QPushButton[role="ghost"] {{
    background: rgba(255,255,255,8);
    border: 1px solid {LINE};
    color: {TEXT_DIM};
    padding: 4px 12px;
    font-weight: 600;
    font-size: 11px;
    border-radius: 6px;
}}
QPushButton[role="ghost"]:hover {{
    background: rgba(255,255,255,16);
    color: {TEXT};
    border-color: {CYAN};
}}
QListWidget {{
    background: transparent;
    border: none;
    outline: none;
}}
QListWidget::item {{
    padding: 11px 16px;
    border-radius: 9px;
    color: {TEXT_DIM};
    font-weight: 600;
    margin: 2px 0;
}}
QListWidget::item:selected {{
    background: rgba(77,216,255,22);
    color: {TEXT};
}}
QListWidget::item:hover {{
    background: rgba(255,255,255,8);
}}
QToolTip {{
    background-color: #0f1830;
    color: {TEXT};
    border: 1px solid {CYAN};
    padding: 6px 10px;
    border-radius: 6px;
}}
QSlider::groove:horizontal {{
    height: 5px;
    background: {LINE};
    border-radius: 2px;
}}
QSlider::sub-page:horizontal {{
    background: {CYAN};
    border-radius: 2px;
}}
QSlider::handle:horizontal {{
    background: {TEXT};
    border: 2px solid {CYAN};
    width: 14px;
    height: 14px;
    margin: -6px 0;
    border-radius: 7px;
}}
QSlider::handle:horizontal:hover {{
    background: {CYAN};
}}
QDoubleSpinBox, QSpinBox {{
    background: rgba(255,255,255,6);
    border: 1px solid {LINE};
    border-radius: 6px;
    padding: 3px 6px;
    color: {CYAN};
    font-family: {MONO_FAMILY};
}}
"""