from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QProcess, Qt, Signal
from PySide6.QtGui import QTextCursor
from PySide6.QtWidgets import (
    QLabel,
    QVBoxLayout,
    QWidget,
    QPlainTextEdit,
)


class TerminalConsole(QPlainTextEdit):
    command_entered = Signal(str)

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._prompt_position = 0
        self._prompt = "PS > "
        self.setLineWrapMode(QPlainTextEdit.LineWrapMode.NoWrap)
        self.setUndoRedoEnabled(False)

    def append_output(self, text: str) -> None:
        cursor = self.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)
        cursor.insertText(text)
        self.setTextCursor(cursor)
        self.ensureCursorVisible()

    def append_prompt(self) -> None:
        cursor = self.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)
        if not self.toPlainText().endswith("\n") and self.toPlainText():
            cursor.insertText("\n")
        cursor.insertText(self._prompt)
        self._prompt_position = cursor.position()
        self.setTextCursor(cursor)
        self.ensureCursorVisible()

    def keyPressEvent(self, event) -> None:
        if event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
            cursor = self.textCursor()
            cursor.movePosition(QTextCursor.MoveOperation.End)
            self.setTextCursor(cursor)
            full = self.toPlainText()
            command = full[self._prompt_position :].strip()
            self.append_output("\n")
            self.command_entered.emit(command)
            return

        if event.key() == Qt.Key.Key_Backspace and self.textCursor().position() <= self._prompt_position:
            return

        if event.key() == Qt.Key.Key_Left and self.textCursor().position() <= self._prompt_position:
            return

        if self.textCursor().position() < self._prompt_position:
            cursor = self.textCursor()
            cursor.movePosition(QTextCursor.MoveOperation.End)
            self.setTextCursor(cursor)

        super().keyPressEvent(event)


class TerminalPanel(QWidget):
    def __init__(self, working_directory: Path | None = None, parent=None) -> None:
        super().__init__(parent)
        self.working_directory = working_directory or Path.cwd()
        self.process = QProcess(self)
        self.process.setWorkingDirectory(str(self.working_directory))
        self.process.readyReadStandardOutput.connect(self._handle_stdout)
        self.process.readyReadStandardError.connect(self._handle_stderr)
        self.process.finished.connect(self._on_process_finished)

        self.console = TerminalConsole(self)
        self.console.command_entered.connect(self.send_command)

        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("Terminal"))
        layout.addWidget(self.console)

        self.process.start("powershell", ["-NoLogo", "-NoProfile", "-NonInteractive", "-Command", "-"])
        self.console.append_prompt()

    def set_working_directory(self, working_directory: Path) -> None:
        self.working_directory = working_directory
        self.process.setWorkingDirectory(str(self.working_directory))
        self.send_command(f"Set-Location '{str(self.working_directory)}'")

    def _handle_stdout(self) -> None:
        data = self.process.readAllStandardOutput().data().decode("utf-8", errors="ignore")
        self.console.append_output(data)

    def _handle_stderr(self) -> None:
        data = self.process.readAllStandardError().data().decode("utf-8", errors="ignore")
        self.console.append_output(data)

    def send_command(self, cmd: str) -> None:
        if self.process.state() == QProcess.ProcessState.NotRunning:
            self.process.start("powershell", ["-NoLogo", "-NoProfile", "-NonInteractive", "-Command", "-"])
        if not cmd:
            self.console.append_prompt()
            return
        self.process.write((cmd + "\n").encode("utf-8"))
        self.console.append_prompt()

    def _on_process_finished(self, _exit_code: int, _exit_status) -> None:
        self.console.append_output("\n[terminal process finished]\n")

    def shutdown(self) -> None:
        if self.process.state() != QProcess.ProcessState.NotRunning:
            self.process.terminate()
            if not self.process.waitForFinished(800):
                self.process.kill()
