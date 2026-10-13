"""Readable system fonts and a neutral grayscale Qt Widgets theme."""

from __future__ import annotations

import sys

from PySide6.QtCore import QLocale, Qt
from PySide6.QtGui import QColor, QFont, QFontDatabase, QPalette
from PySide6.QtWidgets import QApplication

STYLESHEET = """
QMainWindow, QWidget#canvas { background: #f3f3f3; color: #202020; }
QFrame#panel { background: #ffffff; border: 1px solid #d8d8d8; border-radius: 12px; }
QLabel { color: #202020; background: transparent; }
QLabel#brand { font-size: 20pt; font-weight: 700; }
QLabel#eyebrow { color: #595959; font-size: 10pt; font-weight: 600; }
QLabel#heading { font-size: 14pt; font-weight: 600; }
QLabel#muted { color: #595959; }
QLabel#metric { color: #303030; font-size: 20pt; font-weight: 600; }
QLabel#status { color: #4c4c4c; padding: 4px; }
QPushButton { background: #ffffff; color: #292929; border: 1px solid #bfbfbf;
              border-radius: 8px; padding: 9px 12px; min-height: 19px; }
QPushButton:hover { background: #eeeeee; border-color: #858585; }
QPushButton:pressed { background: #e2e2e2; }
QPushButton:focus { border: 2px solid #404040; }
QPushButton#primary { background: #303030; color: #ffffff;
                     border: 1px solid #303030; font-weight: 600; }
QPushButton#primary:hover { background: #4c4c4c; }
QPushButton:disabled { color: #898989; background: #f2f2f2; border-color: #dddddd; }
QPushButton#primary:disabled { color: #ffffff; background: #929292; border-color: #929292; }
QListWidget { background: #ffffff; border: 0; outline: 0; padding: 2px; }
QListWidget::item { color: #303030; border: 1px solid transparent; border-radius: 8px;
                    padding: 10px 8px; margin: 3px 0; }
QListWidget::item:selected { background: #e6e6e6; color: #202020; border: 1px solid #aaaaaa; }
QListWidget::item:hover { background: #f1f1f1; }
QListWidget:focus { border: 1px solid #858585; border-radius: 8px; }
QTextBrowser, QPlainTextEdit { background: #ffffff; color: #202020; border: 0; padding: 8px; }
QTabWidget::pane { border: 0; background: #ffffff; }
QTabBar::tab { background: transparent; color: #595959; padding: 10px 14px;
              border-bottom: 2px solid transparent; }
QTabBar::tab:selected { color: #202020; border-bottom: 2px solid #404040; font-weight: 600; }
QSplitter::handle { background: transparent; }
QSplitter::handle:hover { background: #dedede; }
QProgressBar { border: 0; border-radius: 3px; background: #e5e5e5; max-height: 5px; }
QProgressBar::chunk { background: #404040; border-radius: 3px; }
QLineEdit { background: #fafafa; color: #202020; padding: 7px;
            border: 1px solid #d5d5d5; border-radius: 7px; }
QLineEdit:focus { border-color: #404040; }
QScrollBar:vertical { background: transparent; width: 10px; margin: 0; }
QScrollBar::handle:vertical { background: #bcbcbc; border-radius: 5px; min-height: 30px; }
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }
QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical { background: transparent; }
"""


def interface_font() -> QFont:
    """Use the native readable UI family at 11 pt, with Segoe UI on Windows."""
    font = QFontDatabase.systemFont(QFontDatabase.SystemFont.GeneralFont)
    families = QFontDatabase.families()
    if sys.platform == "win32" and "Segoe UI" in families:
        font.setFamily("Segoe UI")
    elif font.family() not in families:
        # Offscreen Qt may return a generic alias instead of the native family.
        candidates = (
            (".AppleSystemUIFont", "Helvetica Neue", "Helvetica")
            if sys.platform == "darwin"
            else ("Segoe UI", "Arial", "DejaVu Sans")
        )
        for family in candidates:
            if family in families:
                font.setFamily(family)
                break
    font.setPointSize(11)
    return font


def monospace_font() -> QFont:
    """Use the platform's fixed-width family for raw YAML and plain-text reports."""
    font = QFontDatabase.systemFont(QFontDatabase.SystemFont.FixedFont)
    preferred = "Consolas" if sys.platform == "win32" else "Menlo"
    if preferred in QFontDatabase.families():
        font.setFamily(preferred)
    font.setPointSize(11)
    font.setFixedPitch(True)
    return font


def configure_application(app: QApplication) -> None:
    """Apply the same English, readable grayscale configuration in every entry point."""
    app.setAttribute(Qt.ApplicationAttribute.AA_DontUseNativeDialogs, True)
    QLocale.setDefault(QLocale(QLocale.Language.English, QLocale.Country.UnitedStates))
    app.setStyle("Fusion")
    app.setFont(interface_font())
    palette = QPalette()
    for role, color in (
        (QPalette.ColorRole.Window, "#f3f3f3"),
        (QPalette.ColorRole.Base, "#ffffff"),
        (QPalette.ColorRole.AlternateBase, "#f5f5f5"),
        (QPalette.ColorRole.Text, "#202020"),
        (QPalette.ColorRole.WindowText, "#202020"),
        (QPalette.ColorRole.Button, "#ffffff"),
        (QPalette.ColorRole.ButtonText, "#292929"),
        (QPalette.ColorRole.ToolTipBase, "#ffffff"),
        (QPalette.ColorRole.ToolTipText, "#202020"),
        (QPalette.ColorRole.Highlight, "#404040"),
        (QPalette.ColorRole.HighlightedText, "#ffffff"),
        (QPalette.ColorRole.Link, "#404040"),
        (QPalette.ColorRole.LinkVisited, "#595959"),
    ):
        palette.setColor(role, QColor(color))
    for role in (
        QPalette.ColorRole.Text,
        QPalette.ColorRole.WindowText,
        QPalette.ColorRole.ButtonText,
    ):
        palette.setColor(QPalette.ColorGroup.Disabled, role, QColor("#898989"))
    app.setPalette(palette)
    app.setStyleSheet(STYLESHEET)
