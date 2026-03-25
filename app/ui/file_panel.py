from __future__ import annotations

import shutil
from pathlib import Path

from PySide6.QtCore import QPoint, Qt, Signal
from PySide6.QtWidgets import (
    QFileSystemModel,
    QInputDialog,
    QMenu,
    QMessageBox,
    QTreeView,
    QVBoxLayout,
    QWidget,
)


class FilePanel(QWidget):
    file_open_requested = Signal(Path)
    refresh_requested = Signal()

    def __init__(self, root: Path, parent=None) -> None:
        super().__init__(parent)
        self.root = root

        self.model = QFileSystemModel(self)
        self.model.setRootPath(str(root))

        self.tree = QTreeView(self)
        self.tree.setModel(self.model)
        self.tree.setRootIndex(self.model.index(str(root)))
        self.tree.doubleClicked.connect(self._on_double_clicked)
        self.tree.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.tree.customContextMenuRequested.connect(self._open_context_menu)

        layout = QVBoxLayout(self)
        layout.addWidget(self.tree)

    def set_root(self, root: Path) -> None:
        self.root = root
        self.model.setRootPath(str(root))
        self.tree.setRootIndex(self.model.index(str(root)))

    def _on_double_clicked(self, index) -> None:
        file_path = Path(self.model.filePath(index))
        if file_path.is_file():
            self.file_open_requested.emit(file_path)

    def _open_context_menu(self, pos: QPoint) -> None:
        index = self.tree.indexAt(pos)
        if not index.isValid():
            return
        selected = Path(self.model.filePath(index))

        menu = QMenu(self)
        create_file = menu.addAction("New File")
        create_folder = menu.addAction("New Folder")
        rename = menu.addAction("Rename")
        delete = menu.addAction("Delete")
        open_action = menu.addAction("Open")

        action = menu.exec(self.tree.viewport().mapToGlobal(pos))
        if action == create_file:
            self._create_file(selected)
        elif action == create_folder:
            self._create_folder(selected)
        elif action == rename:
            self._rename_path(selected)
        elif action == delete:
            self._delete_path(selected)
        elif action == open_action and selected.is_file():
            self.file_open_requested.emit(selected)

    def _create_file(self, selected: Path) -> None:
        base = selected if selected.is_dir() else selected.parent
        name, ok = QInputDialog.getText(self, "New file", "Filename:")
        if not ok or not name.strip():
            return
        target = base / name.strip()
        try:
            target.write_text("", encoding="utf-8")
            self.refresh_requested.emit()
        except Exception as exc:
            QMessageBox.warning(self, "Error", f"Failed to create file: {exc}")

    def _create_folder(self, selected: Path) -> None:
        base = selected if selected.is_dir() else selected.parent
        name, ok = QInputDialog.getText(self, "New folder", "Folder name:")
        if not ok or not name.strip():
            return
        try:
            (base / name.strip()).mkdir(parents=True, exist_ok=True)
            self.refresh_requested.emit()
        except Exception as exc:
            QMessageBox.warning(self, "Error", f"Failed to create folder: {exc}")

    def _rename_path(self, selected: Path) -> None:
        name, ok = QInputDialog.getText(self, "Rename", "New name:", text=selected.name)
        if not ok or not name.strip():
            return
        try:
            selected.rename(selected.with_name(name.strip()))
            self.refresh_requested.emit()
        except Exception as exc:
            QMessageBox.warning(self, "Error", f"Failed to rename: {exc}")

    def _delete_path(self, selected: Path) -> None:
        confirm = QMessageBox.question(
            self,
            "Delete",
            f"Delete {selected.name}?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if confirm != QMessageBox.StandardButton.Yes:
            return

        try:
            if selected.is_dir():
                shutil.rmtree(selected)
            else:
                selected.unlink(missing_ok=True)
            self.refresh_requested.emit()
        except Exception as exc:
            QMessageBox.warning(self, "Error", f"Failed to delete: {exc}")
