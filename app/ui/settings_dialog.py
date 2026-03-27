from __future__ import annotations

from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QComboBox,
    QPushButton,
    QGroupBox,
    QMessageBox,
)
from PySide6.QtCore import Qt

from app.core.settings import Theme


class SettingsDialog(QDialog):
    """Settings dialog for model selection, theme, and quantization."""

    def __init__(self, parent=None, current_model: str = "", current_theme: Theme = Theme.DARK, current_quantization: str = "4bit"):
        super().__init__(parent)
        self.setWindowTitle("Settings")
        self.setModal(True)
        self.setMinimumWidth(400)

        self.model_select = None
        self.theme_select = None
        self.quantization_select = None
        self.current_model = current_model
        self.current_theme = current_theme
        self.current_quantization = current_quantization
        self.result_model = current_model
        self.result_theme = current_theme
        self.result_quantization = current_quantization

        self._build_ui()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)

        # Model selection group
        model_group = QGroupBox("AI Model", self)
        model_layout = QVBoxLayout(model_group)

        model_label = QLabel("Select Model:", self)
        self.model_select = QComboBox(self)

        # Available models
        models = [
            ("Qwen 2.5 Coder 1.5B (Recommended - Fast)", "Qwen/Qwen2.5-Coder-1.5B-Instruct"),
            ("Qwen 2.5 Coder 7B (Powerful)", "Qwen/Qwen2.5-Coder-7B-Instruct"),
            ("Meta Llama 3 8B", "Meta-Llama-3-8B-Instruct"),
            ("Mistral 7B Instruct", "mistralai/Mistral-7B-Instruct-v0.1"),
        ]

        for display_name, model_id in models:
            self.model_select.addItem(display_name, model_id)

        # Set current model
        for i in range(self.model_select.count()):
            if self.model_select.itemData(i) == self.current_model:
                self.model_select.setCurrentIndex(i)
                break

        model_layout.addWidget(model_label)
        model_layout.addWidget(self.model_select)
        layout.addWidget(model_group)

        # Quantization group
        quant_group = QGroupBox("Quantization (Affects GPU Memory)", self)
        quant_layout = QVBoxLayout(quant_group)

        quant_label = QLabel("Quantization Mode:", self)
        self.quantization_select = QComboBox(self)
        self.quantization_select.addItem("4-bit (Fast, ~2-3 GB)", "4bit")
        self.quantization_select.addItem("8-bit (Balanced, ~4-5 GB)", "8bit")
        self.quantization_select.addItem("None (Full Quality, ~7-10 GB)", "none")

        # Set current quantization
        current_idx = {"4bit": 0, "8bit": 1, "none": 2}.get(self.current_quantization, 0)
        self.quantization_select.setCurrentIndex(current_idx)

        quant_layout.addWidget(quant_label)
        quant_layout.addWidget(self.quantization_select)
        layout.addWidget(quant_group)

        # Theme group
        theme_group = QGroupBox("Theme", self)
        theme_layout = QVBoxLayout(theme_group)

        theme_label = QLabel("Select Theme:", self)
        self.theme_select = QComboBox(self)
        self.theme_select.addItem("🌙 Dark", Theme.DARK)
        self.theme_select.addItem("☀️ Light", Theme.LIGHT)

        # Set current theme
        current_idx = 0 if self.current_theme == Theme.DARK else 1
        self.theme_select.setCurrentIndex(current_idx)

        theme_layout.addWidget(theme_label)
        theme_layout.addWidget(self.theme_select)
        layout.addWidget(theme_group)

        # Info label
        info_label = QLabel(
            "⚠️ Changing the model will unload the current one and load the new model\n"
            "on the next AI request. This may take a few minutes.",
            self
        )
        info_label.setStyleSheet("color: #999; font-size: 11px;")
        layout.addWidget(info_label)

        # Buttons
        button_layout = QHBoxLayout()
        ok_button = QPushButton("Apply", self)
        ok_button.clicked.connect(self._apply_changes)
        cancel_button = QPushButton("Cancel", self)
        cancel_button.clicked.connect(self.reject)

        button_layout.addStretch()
        button_layout.addWidget(ok_button)
        button_layout.addWidget(cancel_button)
        layout.addLayout(button_layout)

    def _apply_changes(self) -> None:
        self.result_model = self.model_select.currentData()
        self.result_theme = self.theme_select.currentData()
        self.result_quantization = self.quantization_select.currentData()

        if self.result_model != self.current_model:
            QMessageBox.information(
                self,
                "Model Change",
                f"Model will switch to:\n{self.model_select.currentText()}\n\n"
                "Current model will be unloaded on next request.",
            )

        self.accept()

    @property
    def selected_model(self) -> str:
        return self.result_model

    @property
    def selected_theme(self) -> Theme:
        return self.result_theme

    @property
    def selected_quantization(self) -> str:
        return self.result_quantization
