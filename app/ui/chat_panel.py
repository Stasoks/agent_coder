from __future__ import annotations

from PySide6.QtCore import QPropertyAnimation, QEasingCurve, QTimer, Signal
from PySide6.QtGui import QTextCursor
from PySide6.QtWidgets import (
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QComboBox,
    QTextEdit,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)


class AttachmentItemWidget(QWidget):
    remove_requested = Signal(str)

    def __init__(self, path: str, parent=None) -> None:
        super().__init__(parent)
        self.path = path

        short_name = path.replace("\\", "/").split("/")[-1]
        self.name_label = QLabel(short_name, self)
        self.name_label.setToolTip(path)
        self.name_label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)

        self.remove_btn = QPushButton("x", self)
        self.remove_btn.setObjectName("tinyActionButton")
        self.remove_btn.setVisible(False)
        self.remove_btn.clicked.connect(lambda: self.remove_requested.emit(self.path))

        row = QHBoxLayout(self)
        row.setContentsMargins(6, 2, 6, 2)
        row.addWidget(self.name_label)
        row.addWidget(self.remove_btn)

    def enterEvent(self, event) -> None:
        self.remove_btn.setVisible(True)
        super().enterEvent(event)

    def leaveEvent(self, event) -> None:
        self.remove_btn.setVisible(False)
        super().leaveEvent(event)


class ChatPanel(QWidget):
    send_requested = Signal(str, str, list)

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._attached: list[str] = []
        self._thinking_step = 0
        self._thinking_timer = QTimer(self)
        self._thinking_timer.setInterval(350)
        self._thinking_timer.timeout.connect(self._update_thinking)

        self.mode = QComboBox(self)
        self.mode.addItems(["assistant", "agent"])

        self.chat_history = QTextEdit(self)
        self.chat_history.setReadOnly(True)

        self.input = QTextEdit(self)
        self.input.setPlaceholderText("Write your request...")
        self.input.setFixedHeight(110)

        self.attach_list = QListWidget(self)
        self.attach_list.setFixedHeight(30)

        self.attach_btn = QPushButton("+", self)
        self.attach_btn.setObjectName("tinyActionButton")
        self.attach_btn.setToolTip("Attach file")
        self.attach_btn.clicked.connect(self._attach_file)

        self.send_btn = QPushButton("Send", self)
        self.send_btn.clicked.connect(self._send)

        self.status = QLabel("Idle", self)
        self.status.setObjectName("statusLabel")

        self._send_anim = QPropertyAnimation(self.send_btn, b"maximumWidth", self)
        self._send_anim.setDuration(260)
        self._send_anim.setStartValue(92)
        self._send_anim.setEndValue(102)
        self._send_anim.setEasingCurve(QEasingCurve.Type.InOutCubic)

        top = QHBoxLayout()
        top.addWidget(QLabel("Chat"))
        top.addWidget(QLabel("Mode:"))
        top.addWidget(self.mode)

        composer_row = QHBoxLayout()
        composer_row.addWidget(self.attach_btn)
        composer_row.addWidget(self.send_btn)

        bottom = QHBoxLayout()
        bottom.addWidget(self.status)
        bottom.addStretch(1)

        layout = QVBoxLayout(self)
        layout.addLayout(top)
        layout.addWidget(self.chat_history)
        layout.addWidget(QLabel("Attached files"))
        layout.addWidget(self.attach_list)
        layout.addWidget(self.input)
        layout.addLayout(composer_row)
        layout.addLayout(bottom)

    def append_message(self, role: str, text: str, is_streaming: bool = False) -> None:
        """Append message to chat history."""
        cursor = self.chat_history.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)
        self.chat_history.setTextCursor(cursor)

        if is_streaming:
            self.chat_history.insertPlainText(f"{role}: ")
        else:
            self.chat_history.insertPlainText(f"{role}: {text}\n")

    def append_stream_token(self, token: str) -> None:
        """Append a single token as streaming output."""
        cursor = self.chat_history.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)
        self.chat_history.setTextCursor(cursor)
        self.chat_history.insertPlainText(token)

    def _attach_file(self) -> None:
        file_path, _ = QFileDialog.getOpenFileName(self, "Attach file")
        if not file_path:
            return
        if file_path in self._attached:
            return
        self._attached.append(file_path)

        item = QListWidgetItem(self.attach_list)
        widget = AttachmentItemWidget(file_path, self.attach_list)
        widget.remove_requested.connect(self._remove_attachment)
        item.setSizeHint(widget.sizeHint())
        self.attach_list.addItem(item)
        self.attach_list.setItemWidget(item, widget)

    def _remove_attachment(self, file_path: str) -> None:
        if file_path in self._attached:
            self._attached.remove(file_path)
        for i in range(self.attach_list.count()):
            item = self.attach_list.item(i)
            widget = self.attach_list.itemWidget(item)
            if isinstance(widget, AttachmentItemWidget) and widget.path == file_path:
                self.attach_list.takeItem(i)
                break

    def _send(self) -> None:
        text = self.input.toPlainText().strip()
        if not text:
            return
        mode = self.mode.currentText()
        files = list(self._attached)
        self.send_requested.emit(text, mode, files)
        self.input.clear()
        self._send_anim.stop()
        self._send_anim.setDirection(QPropertyAnimation.Direction.Forward)
        self._send_anim.start()

    def start_thinking(self) -> None:
        self._thinking_step = 0
        self._thinking_timer.start()
        self._update_thinking()

    def stop_thinking(self, status_text: str = "Idle") -> None:
        self._thinking_timer.stop()
        self.status.setText(status_text)

    def _update_thinking(self) -> None:
        dots = "." * ((self._thinking_step % 3) + 1)
        self.status.setText(f"Thinking{dots}")
        self._thinking_step += 1

    def set_busy(self, busy: bool) -> None:
        self.input.setEnabled(not busy)
        self.send_btn.setEnabled(not busy)
        self.attach_btn.setEnabled(not busy)
