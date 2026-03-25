from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QFont, QSyntaxHighlighter, QTextCharFormat
from PySide6.QtWidgets import QPlainTextEdit


class LuaSyntaxHighlighter(QSyntaxHighlighter):
    def __init__(self, parent) -> None:
        super().__init__(parent)
        keyword_format = QTextCharFormat()
        keyword_format.setForeground(QColor("#7fb4ff"))
        keyword_format.setFontWeight(QFont.Weight.Bold)

        self.keywords = {
            "and",
            "break",
            "do",
            "else",
            "elseif",
            "end",
            "false",
            "for",
            "function",
            "if",
            "in",
            "local",
            "nil",
            "not",
            "or",
            "repeat",
            "return",
            "then",
            "true",
            "until",
            "while",
        }
        self.keyword_format = keyword_format

        self.comment_format = QTextCharFormat()
        self.comment_format.setForeground(QColor("#6a9955"))

        self.string_format = QTextCharFormat()
        self.string_format.setForeground(QColor("#ce9178"))

    def highlightBlock(self, text: str) -> None:
        # Lightweight token highlighting is enough for an embedded editor.
        for word in text.replace("(", " ").replace(")", " ").replace(",", " ").split():
            clean = word.strip()
            if clean in self.keywords:
                i = text.find(clean)
                if i >= 0:
                    self.setFormat(i, len(clean), self.keyword_format)

        comment_index = text.find("--")
        if comment_index >= 0:
            self.setFormat(comment_index, len(text) - comment_index, self.comment_format)

        quote_open = None
        for idx, ch in enumerate(text):
            if ch in {"\"", "'"}:
                if quote_open is None:
                    quote_open = idx
                else:
                    self.setFormat(quote_open, idx - quote_open + 1, self.string_format)
                    quote_open = None


class LuaEditor(QPlainTextEdit):
    def __init__(self, path: Path | None = None, parent=None) -> None:
        super().__init__(parent)
        self.path = path
        self._dirty = False
        self.setTabStopDistance(4 * self.fontMetrics().horizontalAdvance(" "))
        self.setLineWrapMode(QPlainTextEdit.LineWrapMode.NoWrap)
        self.document().modificationChanged.connect(self._on_modification_changed)
        self.highlighter = LuaSyntaxHighlighter(self.document())

    def _on_modification_changed(self, dirty: bool) -> None:
        self._dirty = dirty

    @property
    def dirty(self) -> bool:
        return self._dirty

    def set_text(self, text: str) -> None:
        self.setPlainText(text)
        self.document().setModified(False)

    def get_text(self) -> str:
        return self.toPlainText()

    def set_path(self, path: Path) -> None:
        self.path = path
