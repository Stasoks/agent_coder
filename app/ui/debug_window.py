from __future__ import annotations

from datetime import datetime

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QTextCharFormat, QTextCursor
from PySide6.QtWidgets import QHBoxLayout, QPushButton, QTextEdit, QVBoxLayout, QWidget


# Color mapping for log categories
LOG_COLORS = {
    "INIT": "#7fb4ff",    # Blue
    "CHAT": "#ce9178",    # Orange
    "LOAD": "#9cdcfe",    # Light blue
    "GEN": "#4ec9b0",     # Teal
    "PARSE": "#b8d7a3",   # Green
    "AGENT": "#d7ba7d",   # Gold
    "ERROR": "#f48771",   # Red
    "PERF": "#ff6b9d",    # Pink
    "TOKEN": "#5db4ff",   # Sky blue
    "DEBUG": "#c586c0",   # Purple
}


class DebugWindow(QWidget):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Lua AI Studio - Debug Console")
        self.resize(1000, 700)

        self.output = QTextEdit(self)
        self.output.setReadOnly(True)
        self.output.setFont(self.output.font())  # Monospace-like

        clear_btn = QPushButton("Clear", self)
        clear_btn.clicked.connect(self.output.clear)

        stats_btn = QPushButton("Show Stats", self)
        stats_btn.clicked.connect(self._show_stats)

        top = QHBoxLayout()
        top.addWidget(clear_btn)
        top.addWidget(stats_btn)
        top.addStretch(1)

        layout = QVBoxLayout(self)
        layout.addLayout(top)
        layout.addWidget(self.output)

        # Stats tracking
        self._token_count = 0
        self._generation_times = []
        self._layer_counts = {}

    def log(self, message: str, category: str = "INFO") -> None:
        """Log with structured format and colors."""
        ts = datetime.now().strftime("%H:%M:%S.%f")[:-3]

        # Create colored text
        text_format = QTextCharFormat()
        color = LOG_COLORS.get(category, "#d8dee9")
        text_format.setForeground(QColor(color))
        text_format.setFontWeight(500 if category in ["ERROR", "PERF"] else 400)

        cursor = self.output.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)
        self.output.setTextCursor(cursor)

        # Add timestamp
        ts_format = QTextCharFormat()
        ts_format.setForeground(QColor("#6a9955"))
        self.output.setCurrentCharFormat(ts_format)
        self.output.insertPlainText(f"[{ts}] ")

        # Add category with fixed width
        self.output.setCurrentCharFormat(text_format)
        self.output.insertPlainText(f"[{category:6s}] ")

        # Add message
        msg_format = QTextCharFormat()
        msg_format.setForeground(QColor("#d8dee9"))
        self.output.setCurrentCharFormat(msg_format)
        self.output.insertPlainText(f"{message}\n")

        # Auto-scroll to bottom
        self.output.verticalScrollBar().setValue(
            self.output.verticalScrollBar().maximum()
        )

    def track_tokens(self, count: int) -> None:
        """Track generated tokens."""
        self._token_count = count
        self.log(f"Generated tokens: {count}", "TOKEN")

    def track_generation_time(self, elapsed: float, tok_per_sec: float) -> None:
        """Track generation performance."""
        self._generation_times.append(elapsed)
        self.log(f"Generation time: {elapsed:.2f}s ({tok_per_sec:.1f} tok/s)", "PERF")

    def _show_stats(self) -> None:
        """Show accumulated statistics."""
        self.log("=" * 60, "DEBUG")
        self.log("STATISTICS", "DEBUG")
        self.log("=" * 60, "DEBUG")

        if self._token_count > 0:
            self.log(f"Total tokens generated: {self._token_count}", "TOKEN")

        if self._generation_times:
            avg_time = sum(self._generation_times) / len(self._generation_times)
            min_time = min(self._generation_times)
            max_time = max(self._generation_times)
            self.log(f"Generation stats - Avg: {avg_time:.2f}s, Min: {min_time:.2f}s, Max: {max_time:.2f}s", "PERF")
            self.log(f"Total generations: {len(self._generation_times)}", "PERF")

        self.log("=" * 60, "DEBUG")

