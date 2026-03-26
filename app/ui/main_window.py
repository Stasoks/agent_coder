from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtGui import QCloseEvent
from PySide6.QtWidgets import (
    QFileDialog,
    QMainWindow,
    QMessageBox,
    QSplitter,
    QTabWidget,
    QToolBar,
    QWidget,
    QVBoxLayout,
)

from app.core.file_ops import ensure_within_root, read_text_file, validate_lua_code, write_text_file
from app.core.settings import Theme, get_style_for_theme
from app.services.agent_actions import AgentActionExecutor
from app.services.llm_service import ChatResult, ChatWorker, LlmService
from app.ui.chat_panel import ChatPanel
from app.ui.debug_window import DebugWindow
from app.ui.editor import LuaEditor
from app.ui.file_panel import FilePanel
from app.ui.terminal_panel import TerminalPanel


class MainWindow(QMainWindow):
    def __init__(self, workspace_root: Path, model_name: str, debug_mode: bool = False, quantization_mode: str = "4bit") -> None:
        super().__init__()
        self.workspace_root = workspace_root
        self.debug_mode = debug_mode
        self._workers: list[ChatWorker] = []
        self._current_theme = Theme.DARK
        self._chat_streaming = False

        self.llm_service = LlmService(model_name=model_name, quantization_mode=quantization_mode)
        self.agent_executor = AgentActionExecutor(workspace_root)
        self.debug_window = DebugWindow() if debug_mode else None
        if self.debug_window is not None:
            self.debug_window.show()

        self.file_panel = FilePanel(workspace_root)
        self.file_panel.file_open_requested.connect(self.open_file)
        self.file_panel.refresh_requested.connect(self._refresh_tree)

        self.editor_tabs = QTabWidget(self)
        self.editor_tabs.setTabsClosable(True)
        self.editor_tabs.tabCloseRequested.connect(self._close_tab)

        self.terminal_panel = TerminalPanel(working_directory=workspace_root, parent=self)

        center = QWidget(self)
        center_layout = QVBoxLayout(center)
        center_layout.setContentsMargins(0, 0, 0, 0)
        center_layout.addWidget(self.editor_tabs, 3)
        center_layout.addWidget(self.terminal_panel, 1)

        self.chat_panel = ChatPanel(self)
        self.chat_panel.send_requested.connect(self._handle_chat_request)

        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.addWidget(self.file_panel)
        splitter.addWidget(center)
        splitter.addWidget(self.chat_panel)
        splitter.setSizes([340, 820, 380])

        self.setCentralWidget(splitter)
        self._build_toolbar()
        self._log_debug(f"Application started (debug={self.debug_mode})", "INIT")
        self._log_debug(f"Workspace: {self.workspace_root}", "INIT")
        self._log_debug(f"Model: {self.llm_service.model_name}", "INIT")

    def _build_toolbar(self) -> None:
        tb = QToolBar("Main")
        self.addToolBar(tb)

        open_folder = tb.addAction("Open Folder")
        open_folder.triggered.connect(self.choose_folder)

        new_file = tb.addAction("New File")
        new_file.triggered.connect(self.new_file)

        save_file = tb.addAction("Save")
        save_file.triggered.connect(self.save_current_file)

        validate = tb.addAction("Validate Lua")
        validate.triggered.connect(self.validate_current_lua)

        tb.addSeparator()

        theme_light = tb.addAction("☀️ Light")
        theme_light.triggered.connect(lambda: self._set_theme(Theme.LIGHT))

        theme_dark = tb.addAction("🌙 Dark")
        theme_dark.triggered.connect(lambda: self._set_theme(Theme.DARK))

    def choose_folder(self) -> None:
        selected = QFileDialog.getExistingDirectory(self, "Open folder", str(self.workspace_root))
        if not selected:
            return
        self.workspace_root = Path(selected)
        self.file_panel.set_root(self.workspace_root)
        self.agent_executor.set_root(self.workspace_root)
        self.terminal_panel.set_working_directory(self.workspace_root)
        self._log_debug(f"Switched workspace: {self.workspace_root}", "INIT")

    def new_file(self) -> None:
        file_path, _ = QFileDialog.getSaveFileName(self, "New File", str(self.workspace_root))
        if not file_path:
            return
        target = ensure_within_root(self.workspace_root, Path(file_path))
        write_text_file(target, "")
        self.open_file(target)

    def open_file(self, path: Path) -> None:
        path = ensure_within_root(self.workspace_root, path)

        for i in range(self.editor_tabs.count()):
            editor = self.editor_tabs.widget(i)
            if isinstance(editor, LuaEditor) and editor.path == path:
                self.editor_tabs.setCurrentIndex(i)
                return

        editor = LuaEditor(path=path)
        editor.set_text(read_text_file(path))
        self.editor_tabs.addTab(editor, path.name)
        self.editor_tabs.setCurrentWidget(editor)

    def save_current_file(self) -> None:
        editor = self._current_editor()
        if editor is None:
            return
        if editor.path is None:
            return
        write_text_file(editor.path, editor.get_text())
        editor.document().setModified(False)
        self.statusBar().showMessage(f"Saved {editor.path.name}", 2500)

    def validate_current_lua(self) -> None:
        editor = self._current_editor()
        if editor is None:
            return
        result = validate_lua_code(editor.get_text())
        title = "Lua Validation"
        if result.ok:
            QMessageBox.information(self, title, result.message)
        else:
            QMessageBox.warning(self, title, result.message)

    def _close_tab(self, index: int) -> None:
        widget = self.editor_tabs.widget(index)
        if isinstance(widget, LuaEditor) and widget.dirty:
            ans = QMessageBox.question(
                self,
                "Unsaved Changes",
                f"Save changes in {widget.path.name if widget.path else 'file'}?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No | QMessageBox.StandardButton.Cancel,
            )
            if ans == QMessageBox.StandardButton.Cancel:
                return
            if ans == QMessageBox.StandardButton.Yes:
                if widget.path is not None:
                    write_text_file(widget.path, widget.get_text())
                    widget.document().setModified(False)
        self.editor_tabs.removeTab(index)

    def _current_editor(self) -> LuaEditor | None:
        widget = self.editor_tabs.currentWidget()
        if isinstance(widget, LuaEditor):
            return widget
        return None

    def _refresh_tree(self) -> None:
        self.file_panel.set_root(self.workspace_root)

    def _collect_attached_files(self, file_paths: list[str]) -> dict[str, str]:
        attached: dict[str, str] = {}
        for raw in file_paths:
            path = Path(raw)
            try:
                path = ensure_within_root(self.workspace_root, path)
                attached[str(path.relative_to(self.workspace_root))] = read_text_file(path)
            except Exception as exc:
                attached[str(path)] = f"<Failed to read: {exc}>"
        return attached

    def _handle_chat_request(self, prompt: str, mode: str, file_paths: list[str]) -> None:
        self.chat_panel.append_message("You", prompt)
        self.chat_panel.append_message("System", "Request queued")
        self.chat_panel.set_busy(True)
        self.chat_panel.start_thinking()
        self._log_debug(f"Request mode={mode} | Files={len(file_paths)}", "CHAT")

        attached = self._collect_attached_files(file_paths)
        self._log_debug(f"Files: {', '.join(attached.keys())}", "CHAT")

        worker = ChatWorker(self.llm_service, prompt, mode, attached, self.workspace_root, self)
        worker.finished_ok.connect(lambda result: self._on_chat_result(mode, result))
        worker.failed.connect(self._on_chat_failed)
        worker.progress.connect(self._on_worker_progress)
        worker.token_received.connect(self._on_token_received)
        worker.finished.connect(lambda: self._cleanup_worker(worker))
        self._workers.append(worker)

        # Start AI response header
        self._chat_streaming = True
        self.chat_panel.append_message("AI", "")

        worker.start()

    def _cleanup_worker(self, worker: ChatWorker) -> None:
        if worker in self._workers:
            self._workers.remove(worker)

    def _on_chat_result(self, mode: str, result: ChatResult) -> None:
        self.chat_panel.stop_thinking("Idle")
        self.chat_panel.set_busy(False)
        self._log_debug(f"Response length: {len(result.text)} chars", "GEN")

        if mode == "agent" and result.actions:
            try:
                self._log_debug(f"Executing {len(result.actions)} action(s)", "AGENT")
                logs = self.agent_executor.execute(result.actions)
                for log in logs:
                    self.chat_panel.append_message("Agent", log)
                    self._log_debug(f"{log}", "AGENT")
                self._refresh_tree()
                self._reload_open_tabs_from_disk()
            except Exception as exc:
                self.chat_panel.append_message("Agent", f"Action error: {exc}")
                self._log_debug(f"Error: {exc}", "ERROR")

    def _on_chat_failed(self, error_text: str) -> None:
        self.chat_panel.stop_thinking("Error")
        self.chat_panel.set_busy(False)
        self.chat_panel.append_message("Error", error_text)
        self._log_debug(f"Failed: {error_text}", "ERROR")

    def _on_worker_progress(self, text: str) -> None:
        self.statusBar().showMessage(text, 2500)
        self._log_debug(text, "GEN")

        # Track performance metrics
        if "tokens in" in text and "tok/s" in text:
            # Extract metrics from message like "Generated 156 tokens in 4.23s (36.9 tok/s)"
            try:
                if self.debug_window:
                    parts = text.split()
                    for i, part in enumerate(parts):
                        if part == "tokens" and i > 0:
                            token_count = int(parts[i-1])
                            self.debug_window.track_tokens(token_count)
                        if part.endswith("s)"):
                            time_str = part[:-1]
                            tok_per_sec = float(parts[-2][:-1])
                            self.debug_window.track_generation_time(float(time_str), tok_per_sec)
            except (ValueError, IndexError):
                pass

    def _on_token_received(self, token: str) -> None:
        """Handle streaming token from worker."""
        self.chat_panel.append_stream_token(token)

    def _reload_open_tabs_from_disk(self) -> None:
        for i in range(self.editor_tabs.count()):
            editor = self.editor_tabs.widget(i)
            if isinstance(editor, LuaEditor) and editor.path and editor.path.exists():
                editor.set_text(read_text_file(editor.path))

    def _set_theme(self, theme: Theme) -> None:
        """Switch application theme."""
        self._current_theme = theme
        style = get_style_for_theme(theme)
        from PySide6.QtWidgets import QApplication
        QApplication.instance().setStyleSheet(style)
        self._log_debug(f"Theme switched to {theme.value}", "INIT")

    def _log_debug(self, message: str, category: str = "INFO", *args) -> None:
        """Log debug message with category."""
        if args:
            message = message.format(*args)
        self.statusBar().showMessage(message, 4000)
        if self.debug_window is not None:
            self.debug_window.log(message, category)

    def closeEvent(self, event: QCloseEvent) -> None:
        self._log_debug("Closing app, releasing resources...", "INIT")

        for worker in list(self._workers):
            if worker.isRunning():
                worker.requestInterruption()
                worker.quit()
                worker.wait(1200)

        self.terminal_panel.shutdown()
        self.llm_service.shutdown(progress_callback=lambda msg: self._log_debug(msg, "LOAD"))

        if self.debug_window is not None:
            self.debug_window.close()

        super().closeEvent(event)
