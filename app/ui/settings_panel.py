from __future__ import annotations

from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QComboBox,
    QLineEdit,
    QPushButton,
    QGroupBox,
    QMessageBox,
)
from PySide6.QtCore import Qt, Signal

from app.core.settings import Theme


class SettingsPanel(QWidget):
    """Settings page for model selection, theme, and quantization."""

    back_requested = Signal()
    apply_requested = Signal(str, Theme, str)  # model, theme, quantization

    def __init__(self, parent=None, current_model: str = "", current_theme: Theme = Theme.DARK, current_quantization: str = "4bit"):
        super().__init__(parent)
        self.current_model = current_model
        self.current_theme = current_theme
        self.current_quantization = current_quantization

        self.model_input = None
        self.theme_select = None
        self.quantization_select = None

        self._build_ui()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        # Header with back button
        header_layout = QHBoxLayout()
        back_button = QPushButton("← Back to Editor", self)
        back_button.setMaximumWidth(150)
        back_button.clicked.connect(self.back_requested.emit)
        header_label = QLabel("⚙️ Settings", self)
        header_label.setStyleSheet("font-size: 18px; font-weight: bold;")
        header_layout.addWidget(back_button)
        header_layout.addWidget(header_label)
        header_layout.addStretch()
        layout.addLayout(header_layout)

        # Separator
        sep = QLabel("")
        sep.setStyleSheet("border-bottom: 1px solid #444;")
        layout.addWidget(sep)

        # Model selection group
        model_group = QGroupBox("AI Model", self)
        model_layout = QVBoxLayout(model_group)

        model_label = QLabel("Model (HuggingFace ID or select preset):", self)
        self.model_input = QLineEdit(self)
        self.model_input.setText(self.current_model)
        self.model_input.setPlaceholderText("e.g., Qwen/Qwen2.5-Coder-1.5B-Instruct")
        model_layout.addWidget(model_label)
        model_layout.addWidget(self.model_input)

        # Preset buttons
        preset_label = QLabel("Quick selection:", self)
        preset_layout = QHBoxLayout()
        presets = [
            ("Qwen 1.5B", "Qwen/Qwen2.5-Coder-1.5B-Instruct"),
            ("Qwen 7B", "Qwen/Qwen2.5-Coder-7B-Instruct"),
            ("Llama 8B", "Meta-Llama-3-8B-Instruct"),
            ("Mistral 7B", "mistralai/Mistral-7B-Instruct-v0.1"),
        ]
        for name, model_id in presets:
            btn = QPushButton(name, self)
            btn.setMaximumWidth(100)
            btn.clicked.connect(lambda checked, mid=model_id: self.model_input.setText(mid))
            preset_layout.addWidget(btn)
        preset_layout.addStretch()
        model_layout.addWidget(preset_label)
        model_layout.addLayout(preset_layout)

        layout.addWidget(model_group)

        # Quantization group
        quant_group = QGroupBox("Quantization Mode", self)
        quant_layout = QVBoxLayout(quant_group)

        quant_label = QLabel("Select mode:", self)
        self.quantization_select = QComboBox(self)
        self.quantization_select.addItem("4bit", "4bit")
        self.quantization_select.addItem("8bit", "8bit")
        self.quantization_select.addItem("None", "none")

        # Set current quantization
        current_idx = {"4bit": 0, "8bit": 1, "none": 2}.get(self.current_quantization, 0)
        self.quantization_select.setCurrentIndex(current_idx)

        quant_layout.addWidget(quant_label)
        quant_layout.addWidget(self.quantization_select)
        layout.addWidget(quant_group)

        # Theme group
        theme_group = QGroupBox("Theme", self)
        theme_layout = QVBoxLayout(theme_group)

        theme_label = QLabel("Select theme:", self)
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
            "💡 Changing model will unload current one and load new model on next request.\n"
            "Changing quantization will apply on next request.",
            self
        )
        info_label.setStyleSheet("color: #999; font-size: 11px;")
        layout.addWidget(info_label)

        # Buttons
        button_layout = QHBoxLayout()
        apply_button = QPushButton("Apply Changes", self)
        apply_button.clicked.connect(self._apply_changes)
        cancel_button = QPushButton("Cancel", self)
        cancel_button.clicked.connect(self.back_requested.emit)

        button_layout.addStretch()
        button_layout.addWidget(apply_button)
        button_layout.addWidget(cancel_button)
        layout.addLayout(button_layout)

        layout.addStretch()

    def _apply_changes(self) -> None:
        model = self.model_input.text().strip()
        if not model:
            QMessageBox.warning(self, "Error", "Model name cannot be empty!")
            return

        theme = self.theme_select.currentData()
        quantization = self.quantization_select.currentData()

        self.apply_requested.emit(model, theme, quantization)

    @property
    def selected_model(self) -> str:
        return self.model_input.text().strip()

    @property
    def selected_theme(self) -> Theme:
        return self.theme_select.currentData()

    @property
    def selected_quantization(self) -> str:
        return self.quantization_select.currentData()
