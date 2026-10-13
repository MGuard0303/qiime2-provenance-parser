"""A restrained Qt Widgets theme with readable focus and selection states."""

STYLESHEET = """
QMainWindow, QWidget#canvas { background: #f3f5f6; color: #1b303b; }
QWidget { font-family: '.AppleSystemUIFont', 'Segoe UI', sans-serif; font-size: 13px; }
QFrame#panel { background: white; border: 1px solid #dfe5e8; border-radius: 14px; }
QLabel { color: #1b303b; background: transparent; }
QLabel#brand { font-size: 23px; font-weight: 700; }
QLabel#eyebrow { color: #637a84; font-size: 11px; font-weight: 600; }
QLabel#heading { font-size: 17px; font-weight: 600; }
QLabel#muted { color: #637780; }
QLabel#metric { color: #087d79; font-size: 23px; font-weight: 600; }
QLabel#status { color: #49636e; padding: 4px; }
QPushButton { background: #ffffff; color: #233e48; border: 1px solid #ccd8dd;
              border-radius: 8px; padding: 9px 12px; min-height: 17px; }
QPushButton:hover { background: #edf5f5; border-color: #79aba8; }
QPushButton:pressed { background: #deeeee; }
QPushButton:focus { border: 2px solid #07837e; }
QPushButton#primary { background: #087d79; color: white;
                     border: 1px solid #087d79; font-weight: 600; }
QPushButton#primary:hover { background: #096a68; }
QPushButton:disabled { color: #98a7ad; background: #f2f4f5; border-color: #e3e8ea; }
QPushButton#primary:disabled { color: #f0f5f5; background: #93b6b4; border-color: #93b6b4; }
QCheckBox { color: #29434e; spacing: 8px; padding: 5px 0; }
QListWidget { background: white; border: 0; outline: 0; padding: 2px; }
QListWidget::item { color: #2c4450; border: 1px solid transparent; border-radius: 8px;
                    padding: 10px 8px; margin: 3px 0; }
QListWidget::item:selected { background: #e9f4f3; color: #066b67; border: 1px solid #b8d9d5; }
QListWidget::item:hover { background: #f1f6f7; }
QListWidget:focus { border: 1px solid #94bfbc; border-radius: 8px; }
QTextBrowser, QPlainTextEdit { background: white; color: #233c48; border: 0; padding: 8px; }
QTabWidget::pane { border: 0; background: white; }
QTabBar::tab { background: transparent; color: #617883; padding: 10px 16px;
              border-bottom: 2px solid transparent; }
QTabBar::tab:selected { color: #087d79; border-bottom: 2px solid #087d79; font-weight: 600; }
QSplitter::handle { background: transparent; }
QSplitter::handle:hover { background: #dce9e8; }
QProgressBar { border: 0; border-radius: 3px; background: #e7eeef; max-height: 5px; }
QProgressBar::chunk { background: #087d79; border-radius: 3px; }
QLineEdit { background: #f7f9fa; color: #233c48; padding: 7px;
            border: 1px solid #e0e7ea; border-radius: 7px; }
QLineEdit:focus { border-color: #087d79; }
QScrollBar:vertical { background: transparent; width: 8px; margin: 0; }
QScrollBar::handle:vertical { background: #c7d3d8; border-radius: 4px; min-height: 30px; }
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }
QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical { background: transparent; }
"""
