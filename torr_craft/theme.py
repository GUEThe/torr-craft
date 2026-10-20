"""Visual language for Torr Craft."""

from PySide2.QtGui import QColor, QFont, QFontDatabase
from PySide2.QtWidgets import QApplication

# Core palette ---------------------------------------------------------------
UI_FAMILY = "Microsoft YaHei UI"

BG = "#070d18"
BG_RAISED = "#0b1424"
PANEL = "#0d1728"
PANEL_ALT = "#101d31"
CARD = "#142238"
BORDER = "#233550"
BORDER_SOFT = "#1a2a42"
TEXT = "#e6eef8"
MUTED = "#8497ae"
DIM = "#586b83"
CYAN = "#22d3ee"
CYAN_SOFT = "#67e8f9"
GREEN = "#34d399"
AMBER = "#fbbf24"
ROSE = "#fb7185"
VIOLET = "#a78bfa"
SKY = "#7dd3fc"
ORANGE = "#fb923c"

TYPE_ACCENTS = {
    "chamber": SKY,
    "turbo": GREEN,
    "dry": AMBER,
    "angle": ORANGE,
    "gate": VIOLET,
    "pipe": CYAN,
}


def _font_family(*candidates: str) -> str:
    available = set(QFontDatabase().families())
    for family in candidates:
        if family in available:
            return family
    return "Sans Serif"


def ui_family() -> str:
    return _font_family("Microsoft YaHei UI", "Microsoft YaHei", "Segoe UI", "Noto Sans CJK SC")


def mono_family() -> str:
    return _font_family("Cascadia Mono", "Consolas", "JetBrains Mono", "DejaVu Sans Mono")


def font(size: int, weight: int = QFont.Normal, mono: bool = False) -> QFont:
    f = QFont(mono_family() if mono else ui_family())
    f.setPixelSize(max(7, int(size)))
    f.setWeight(weight)
    return f


def color(hex_value: str, alpha=None) -> QColor:
    c = QColor(hex_value)
    if alpha is not None:
        c.setAlpha(alpha)
    return c


STYLESHEET = f"""
* {{
    outline: none;
}}
QWidget {{
    color: {TEXT};
    font-family: "{UI_FAMILY}";
    font-size: 12px;
}}
QMainWindow, QWidget#Root {{
    background: {BG};
}}
QFrame#TopBar {{
    background: #091120;
    border-bottom: 1px solid {BORDER_SOFT};
}}
QFrame#Sidebar {{
    background: {PANEL};
    border-right: 1px solid {BORDER_SOFT};
}}
QFrame#Inspector {{
    background: {PANEL};
    border-left: 1px solid {BORDER_SOFT};
}}
QFrame#CanvasToolbar {{
    background: {BG_RAISED};
    border-bottom: 1px solid {BORDER_SOFT};
}}
QFrame#StatusBar {{
    background: #08101d;
    border-top: 1px solid {BORDER_SOFT};
}}
QLabel#Brand {{
    color: #f4f9ff;
    font-size: 18px;
    font-weight: 700;
    letter-spacing: 1px;
}}
QLabel#BrandSub {{
    color: {DIM};
    font-size: 8px;
    font-weight: 600;
    letter-spacing: 2px;
}}
QLabel#ProjectName {{
    color: {TEXT};
    font-size: 12px;
    font-weight: 600;
}}
QLabel#ProjectMeta {{
    color: {DIM};
    font-size: 10px;
}}
QLabel#SectionTitle {{
    color: {TEXT};
    font-size: 12px;
    font-weight: 700;
}}
QLabel#SectionKicker {{
    color: {CYAN};
    font-size: 8px;
    font-weight: 700;
    letter-spacing: 2px;
}}
QLabel#Hint {{
    color: {MUTED};
    font-size: 10px;
}}
QLabel#Muted {{
    color: {MUTED};
    font-size: 11px;
}}
QLabel#Tiny {{
    color: {DIM};
    font-size: 10px;
}}
QLabel#FieldLabel {{
    color: {MUTED};
    font-size: 11px;
}}
QLabel#ValueStrong {{
    color: {TEXT};
    font-size: 20px;
    font-weight: 700;
}}
QLabel#Danger {{
    color: {ROSE};
    font-size: 10px;
}}
QFrame#InsetCard {{
    background: #0a1524;
    border: 1px solid {BORDER_SOFT};
    border-radius: 10px;
}}
QFrame#InspectorHeader {{
    background: #0b1626;
    border-bottom: 1px solid {BORDER_SOFT};
}}
QFrame#InspectorFooter {{
    background: #0a1423;
    border-top: 1px solid {BORDER_SOFT};
}}
QWidget#InspectorPage {{
    background: transparent;
}}
QLineEdit, QSpinBox, QDoubleSpinBox, QComboBox {{
    background: #0a1526;
    border: 1px solid {BORDER};
    border-radius: 7px;
    color: {TEXT};
    padding: 7px 9px;
    selection-background-color: #164e63;
    min-height: 16px;
}}
QLineEdit:hover, QSpinBox:hover, QDoubleSpinBox:hover, QComboBox:hover {{
    border-color: #34516f;
}}
QLineEdit:focus, QSpinBox:focus, QDoubleSpinBox:focus, QComboBox:focus {{
    border-color: {CYAN};
    background: #0b192b;
}}
QSpinBox::up-button, QDoubleSpinBox::up-button,
QSpinBox::down-button, QDoubleSpinBox::down-button {{
    width: 15px;
    border: none;
    background: transparent;
}}
QSpinBox::up-arrow, QDoubleSpinBox::up-arrow {{
    image: none;
    border-left: 3px solid transparent;
    border-right: 3px solid transparent;
    border-bottom: 4px solid {MUTED};
    width: 0; height: 0;
}}
QSpinBox::down-arrow, QDoubleSpinBox::down-arrow {{
    image: none;
    border-left: 3px solid transparent;
    border-right: 3px solid transparent;
    border-top: 4px solid {MUTED};
    width: 0; height: 0;
}}
QPushButton {{
    background: #132137;
    border: 1px solid {BORDER};
    border-radius: 8px;
    color: {TEXT};
    padding: 8px 13px;
    font-size: 11px;
    font-weight: 600;
}}
QPushButton:hover {{
    background: #192a45;
    border-color: #3a5878;
}}
QPushButton:pressed {{
    background: #0d192b;
}}
QPushButton[role="primary"] {{
    background: {CYAN};
    border: 1px solid {CYAN};
    color: #041420;
}}
QPushButton[role="primary"]:hover {{
    background: {CYAN_SOFT};
    border-color: {CYAN_SOFT};
}}
QPushButton[role="ghost"] {{
    background: transparent;
    border: 1px solid transparent;
    color: {MUTED};
    padding: 7px 10px;
}}
QPushButton[role="ghost"]:hover {{
    background: #111f33;
    color: {TEXT};
}}
QPushButton[role="danger"] {{
    background: rgba(251, 113, 133, 0.08);
    border: 1px solid rgba(251, 113, 133, 0.28);
    color: #fda4af;
}}
QPushButton[role="danger"]:hover {{
    background: rgba(251, 113, 133, 0.16);
    border-color: {ROSE};
}}
QToolButton {{
    background: transparent;
    border: 1px solid transparent;
    border-radius: 7px;
    color: {MUTED};
    padding: 6px 9px;
    font-size: 11px;
    font-weight: 600;
}}
QToolButton:hover {{
    background: #122138;
    color: {TEXT};
}}
QToolButton:checked {{
    background: rgba(34, 211, 238, 0.12);
    border-color: rgba(34, 211, 238, 0.35);
    color: {CYAN_SOFT};
}}
QToolButton#HeaderAction {{
    background: #101d31;
    border: 1px solid {BORDER};
    color: {TEXT};
    padding: 8px 12px;
}}
QToolButton#HeaderAction:hover {{
    background: #17283f;
    border-color: #3a5878;
}}
QToolButton[role="primary"] {{
    background: {CYAN};
    border: 1px solid {CYAN};
    color: #041420;
    padding: 8px 13px;
}}
QToolButton[role="primary"]:hover {{
    background: {CYAN_SOFT};
    border-color: {CYAN_SOFT};
}}
QToolButton#SimPill {{
    background: rgba(52, 211, 153, 0.08);
    border: 1px solid rgba(52, 211, 153, 0.25);
    border-radius: 14px;
    color: #a7f3d0;
    font-size: 10px;
    font-weight: 600;
    padding: 5px 11px;
}}
QToolButton#SimPill:checked {{
    background: rgba(52, 211, 153, 0.15);
    border-color: rgba(52, 211, 153, 0.55);
    color: #d1fae5;
}}
QMenu {{
    background: #0f1c2f;
    border: 1px solid {BORDER};
    border-radius: 8px;
    padding: 5px;
    color: {TEXT};
}}
QMenu::item {{
    border-radius: 5px;
    padding: 7px 24px 7px 12px;
}}
QMenu::item:selected {{
    background: #1a304b;
}}
QMenu::separator {{
    height: 1px;
    background: {BORDER_SOFT};
    margin: 4px 8px;
}}
QScrollArea {{
    background: transparent;
    border: none;
}}
QScrollBar:vertical {{
    background: transparent;
    width: 10px;
    margin: 3px;
}}
QScrollBar::handle:vertical {{
    background: #273b55;
    border-radius: 3px;
    min-height: 32px;
}}
QScrollBar::handle:vertical:hover {{
    background: #385674;
}}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical,
QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{
    height: 0; background: transparent;
}}
QScrollBar:horizontal {{
    background: transparent;
    height: 10px;
    margin: 3px;
}}
QScrollBar::handle:horizontal {{
    background: #273b55;
    border-radius: 3px;
    min-width: 32px;
}}
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal,
QScrollBar::add-page:horizontal, QScrollBar::sub-page:horizontal {{
    width: 0; background: transparent;
}}
QToolTip {{
    background: #0c1829;
    color: {TEXT};
    border: 1px solid #35506e;
    border-radius: 5px;
    padding: 5px 8px;
}}
QMessageBox {{
    background: {PANEL};
}}
QDialog {{
    background: {PANEL};
}}
QSplitter::handle {{
    background: {BORDER_SOFT};
}}
"""


def apply_theme(app: QApplication) -> None:
    app.setStyle("Fusion")
    app_font = QFont(ui_family())
    app_font.setPixelSize(12)
    app.setFont(app_font)
    app.setStyleSheet(STYLESHEET)
