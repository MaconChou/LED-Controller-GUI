"""Qt style sheet (macOS look)."""
from pathlib import Path

ASSETS = Path(__file__).parent / "assets"



STYLE = """
* { color:#1d1d1f; font-size:13px; }
QMainWindow, #Root { background:#f5f5f7; }
QStatusBar { background:#f5f5f7; color:#86868b; }
#Sidebar { background:#e8e8ed; border-right:1px solid #d6d6db; }
#AppTitle { font-size:12px; font-weight:600; color:#86868b; padding:18px 18px 8px 18px; }
#Sidebar QListWidget { background:transparent; border:none; outline:0; }
#Sidebar QListWidget::item { padding:7px 10px; border-radius:7px; margin:1px 10px; }
#Sidebar QListWidget::item:selected { background:#0a84ff; color:white; }
#Sidebar QListWidget::item:hover:!selected { background:#dcdce2; }
QLabel#h1 { font-size:26px; font-weight:700; }
QLabel#h2 { font-size:17px; font-weight:600; }
QLabel#caption { color:#86868b; font-size:12px; }
QFrame#card { background:white; border:1px solid #e0e0e5; border-radius:12px; }
QFrame#card QLabel { background:transparent; }
QPushButton { background:white; border:1px solid #d1d1d6; border-radius:7px; padding:5px 14px; }
QPushButton:hover { background:#f4f4f7; }
QPushButton:pressed { background:#e5e5ea; }
QPushButton:disabled { color:#aeaeb2; background:#f2f2f7; }
QPushButton#primary { background:#0a84ff; border:1px solid #0071e3; color:white; font-weight:600; }
QPushButton#primary:hover { background:#2e94ff; }
QPushButton#primary:pressed { background:#0071e3; }
QPushButton#danger { color:#ff3b30; }
QPushButton::menu-indicator { image:none; width:0; }
QComboBox, QSpinBox, QDoubleSpinBox, QLineEdit {
    background:white; border:1px solid #d1d1d6; border-radius:7px; padding:4px 8px; min-height:20px; }
QComboBox:focus, QSpinBox:focus, QDoubleSpinBox:focus, QLineEdit:focus { border:1px solid #0a84ff; }
QComboBox::drop-down { border:none; width:24px; }
QComboBox::down-arrow { image:url(@ARROW@); width:10px; height:10px; }
QComboBox QAbstractItemView { background:white; border:1px solid #d1d1d6; selection-background-color:#0a84ff;
    selection-color:white; outline:0; }
QListWidget, QTableWidget { background:white; border:1px solid #dcdce1; border-radius:10px; outline:0; }
QListWidget::item { padding:4px; border-radius:7px; margin:1px 4px; }
QListWidget::item:selected { background:#0a84ff; color:white; }
QTableWidget { selection-background-color:#e3f0ff; alternate-background-color:#fafafa; }
QTableWidget::item { padding-left:6px; }
QTableWidget::item:selected { background:#d6e9ff; color:#1d1d1f; }
QHeaderView::section { background:white; border:none; border-bottom:1px solid #e5e5ea; padding:6px;
    color:#86868b; font-size:11px; font-weight:600; }
QSlider::groove:horizontal { height:4px; background:#d1d1d6; border-radius:2px; }
QSlider::sub-page:horizontal { background:#0a84ff; border-radius:2px; }
QSlider::handle:horizontal { background:white; border:1px solid #c7c7cc; width:16px; height:16px;
    margin:-7px 0; border-radius:9px; }
QProgressBar { background:#e5e5ea; border:none; border-radius:2px; }
QProgressBar::chunk { background:#0a84ff; border-radius:2px; }
QScrollBar:vertical { background:transparent; width:10px; margin:2px; }
QScrollBar::handle:vertical { background:#c7c7cc; border-radius:3px; min-height:30px; }
QScrollBar:horizontal { background:transparent; height:10px; margin:2px; }
QScrollBar::handle:horizontal { background:#c7c7cc; border-radius:3px; min-width:30px; }
QScrollBar::add-line, QScrollBar::sub-line { width:0; height:0; }
QScrollBar::add-page, QScrollBar::sub-page { background:transparent; }
QPushButton:checked { background:#dcdce2; }
QFrame#DebugPanel { background:#f5f5f7; border-left:1px solid #d6d6db; }
QPlainTextEdit#console { background:#1e1e1e; color:#d4d4d4; border:none; border-radius:10px;
    padding:8px; selection-background-color:#0a84ff; }
QToolTip { background:#2c2c2e; color:white; border:none; padding:4px 8px; }
QMenu { background:white; border:1px solid #d1d1d6; border-radius:8px; padding:4px; }
QMenu::item { padding:5px 22px; border-radius:5px; }
QMenu::item:selected { background:#0a84ff; color:white; }
"""


def build_stylesheet():
    """Return the style sheet with asset paths resolved."""
    return STYLE.replace("@ARROW@", (ASSETS / "arrow_down.svg").as_posix())
