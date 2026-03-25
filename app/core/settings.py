from __future__ import annotations

from pathlib import Path
from enum import Enum

APP_NAME = "Lua AI Studio"
DEFAULT_MODEL = "Qwen/Qwen2.5-Coder-7B-Instruct"
DEBUG_MODEL = "Qwen/Qwen2.5-Coder-1.5B-Instruct"
DEFAULT_WINDOW_SIZE = (1400, 860)


class Theme(Enum):
    LIGHT = "light"
    DARK = "dark"
    AUTO = "auto"


def get_style_for_theme(theme: Theme | str = Theme.DARK) -> str:
    """Get QSS stylesheet for the given theme."""
    if isinstance(theme, str):
        try:
            theme = Theme[theme.upper()]
        except KeyError:
            theme = Theme.DARK

    if theme == Theme.LIGHT:
        return _LIGHT_STYLE
    else:  # DARK or AUTO
        return _DARK_STYLE


# Modern Dark theme - sleek and professional with animations
_DARK_STYLE = """
QWidget {
    background-color: #0f1419;
    color: #e0e6ed;
    font-family: "Segoe UI", "Noto Sans", sans-serif;
    font-size: 13px;
}
QMainWindow {
    background-color: #0a0e13;
}
QLineEdit, QTextEdit, QPlainTextEdit, QListWidget, QTreeView, QComboBox {
    background-color: #1a2332;
    border: 2px solid #2d3d50;
    border-radius: 8px;
    padding: 8px;
    color: #e0e6ed;
    selection-background-color: #3b82f6;
}
QLineEdit:focus, QTextEdit:focus, QPlainTextEdit:focus, QComboBox:focus {
    border: 2px solid #60a5fa;
    background-color: #202d3f;
    outline: none;
}
QLineEdit:disabled, QTextEdit:disabled, QPlainTextEdit:disabled {
    background-color: #0f1419;
    color: #6b7280;
}
QLabel#statusLabel {
    color: #9ca3af;
    font-size: 12px;
}
QPushButton {
    background-color: #2563eb;
    color: #ffffff;
    border: none;
    border-radius: 6px;
    padding: 8px 14px;
    font-weight: 600;
}
QPushButton#tinyActionButton {
    min-width: 28px;
    max-width: 28px;
    min-height: 28px;
    max-height: 28px;
    border-radius: 14px;
    padding: 0;
    font-size: 12px;
    background-color: #1e40af;
    font-weight: 700;
}
QPushButton:hover {
    background-color: #1d4ed8;
}
QPushButton#tinyActionButton:hover {
    background-color: #3b82f6;
}
QPushButton:pressed {
    background-color: #1e40af;
}
QPushButton:disabled {
    background-color: #374151;
    color: #9ca3af;
}
QTabWidget::pane {
    border: 1px solid #2d3d50;
    border-radius: 8px;
    background-color: #0f1419;
}
QTabBar::tab {
    background-color: #1a2332;
    border: 1px solid #2d3d50;
    border-bottom: none;
    border-top-left-radius: 8px;
    border-top-right-radius: 8px;
    padding: 10px 16px;
    color: #9ca3af;
    font-weight: 500;
}
QTabBar::tab:hover {
    background-color: #202d3f;
    color: #b0c4de;
}
QTabBar::tab:selected {
    background-color: #3b82f6;
    color: #ffffff;
    border-bottom: 3px solid #3b82f6;
    font-weight: 600;
}
QHeaderView::section {
    background-color: #1a2332;
    border: 1px solid #2d3d50;
    padding: 4px;
}
QSplitter::handle {
    background: #2d3d50;
}
QSplitter::handle:hover {
    background: #3b4a61;
}
QScrollBar:vertical {
    background: #0a0e13;
    width: 12px;
    border: none;
}
QScrollBar::handle:vertical {
    background: #2d3d50;
    border-radius: 6px;
    min-height: 20px;
}
QScrollBar::handle:vertical:hover {
    background: #3b82f6;
}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    border: none;
    background: none;
}
QToolBar {
    background-color: #0f1419;
    border-bottom: 2px solid #2d3d50;
    spacing: 8px;
    padding: 8px;
}
QToolBar::separator {
    background-color: #2d3d50;
    width: 2px;
    height: 20px;
}
QToolButton {
    color: #e0e6ed;
    spacing: 4px;
    padding: 4px 6px;
    border-radius: 4px;
}
QToolButton:hover {
    background-color: #1a2332;
    border-radius: 4px;
}
QToolButton:pressed {
    background-color: #2563eb;
    color: #ffffff;
}
QMenuBar {
    background-color: #0f1419;
    color: #e0e6ed;
    border-bottom: 1px solid #2d3d50;
}
QMenuBar::item:selected {
    background-color: #2563eb;
}
QMenu {
    background-color: #1a2332;
    color: #e0e6ed;
    border: 1px solid #2d3d50;
    border-radius: 4px;
}
QMenu::item:selected {
    background-color: #2563eb;
}
"""

# Modern Light theme - clean and bright with animations
_LIGHT_STYLE = """
QWidget {
    background-color: #f8fafc;
    color: #1f2937;
    font-family: "Segoe UI", "Noto Sans", sans-serif;
    font-size: 13px;
}
QMainWindow {
    background-color: #ffffff;
}
QLineEdit, QTextEdit, QPlainTextEdit, QListWidget, QTreeView, QComboBox {
    background-color: #ffffff;
    border: 2px solid #e5e7eb;
    border-radius: 8px;
    padding: 8px;
    color: #1f2937;
    selection-background-color: #3b82f6;
}
QLineEdit:focus, QTextEdit:focus, QPlainTextEdit:focus, QComboBox:focus {
    border: 2px solid #60a5fa;
    background-color: #f9fafb;
    outline: none;
}
QLineEdit:disabled, QTextEdit:disabled, QPlainTextEdit:disabled {
    background-color: #f3f4f6;
    color: #9ca3af;
}
QLabel#statusLabel {
    color: #6b7280;
    font-size: 12px;
}
QPushButton {
    background-color: #2563eb;
    color: #ffffff;
    border: none;
    border-radius: 6px;
    padding: 8px 14px;
    font-weight: 600;
}
QPushButton#tinyActionButton {
    min-width: 28px;
    max-width: 28px;
    min-height: 28px;
    max-height: 28px;
    border-radius: 14px;
    padding: 0;
    font-size: 12px;
    background-color: #1e40af;
    font-weight: 700;
}
QPushButton:hover {
    background-color: #1d4ed8;
}
QPushButton#tinyActionButton:hover {
    background-color: #1e40af;
}
QPushButton:pressed {
    background-color: #1e3a8a;
}
QPushButton:disabled {
    background-color: #e5e7eb;
    color: #9ca3af;
}
QTabWidget::pane {
    border: 1px solid #e5e7eb;
    border-radius: 8px;
    background-color: #ffffff;
}
QTabBar::tab {
    background-color: #f8fafc;
    border: 1px solid #e5e7eb;
    border-bottom: none;
    border-top-left-radius: 8px;
    border-top-right-radius: 8px;
    padding: 10px 16px;
    color: #6b7280;
    font-weight: 500;
}
QTabBar::tab:hover {
    background-color: #f3f4f6;
    color: #374151;
}
QTabBar::tab:selected {
    background-color: #3b82f6;
    color: #ffffff;
    border-bottom: 3px solid #3b82f6;
    font-weight: 600;
}
QHeaderView::section {
    background-color: #f8fafc;
    border: 1px solid #e5e7eb;
    padding: 4px;
}
QSplitter::handle {
    background: #e5e7eb;
}
QSplitter::handle:hover {
    background: #d1d5db;
}
QScrollBar:vertical {
    background: #ffffff;
    width: 12px;
    border: none;
}
QScrollBar::handle:vertical {
    background: #d1d5db;
    border-radius: 6px;
    min-height: 20px;
}
QScrollBar::handle:vertical:hover {
    background: #3b82f6;
}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    border: none;
    background: none;
}
QToolBar {
    background-color: #ffffff;
    border-bottom: 2px solid #e5e7eb;
    spacing: 8px;
    padding: 8px;
}
QToolBar::separator {
    background-color: #e5e7eb;
    width: 2px;
    height: 20px;
}
QToolButton {
    color: #1f2937;
    spacing: 4px;
    padding: 4px 6px;
    border-radius: 4px;
}
QToolButton:hover {
    background-color: #f3f4f6;
    border-radius: 4px;
}
QToolButton:pressed {
    background-color: #2563eb;
    color: #ffffff;
}
QMenuBar {
    background-color: #ffffff;
    color: #1f2937;
    border-bottom: 1px solid #e5e7eb;
}
QMenuBar::item:selected {
    background-color: #2563eb;
    color: #ffffff;
}
QMenu {
    background-color: #ffffff;
    color: #1f2937;
    border: 1px solid #e5e7eb;
    border-radius: 4px;
}
QMenu::item:selected {
    background-color: #2563eb;
    color: #ffffff;
}
"""

# Default to dark style
APP_STYLE = _DARK_STYLE

ROOT_HINT = Path.cwd()
