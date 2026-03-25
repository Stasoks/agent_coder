from __future__ import annotations

import argparse
import sys
from pathlib import Path

from PySide6.QtWidgets import QApplication

from app.core.settings import APP_NAME, APP_STYLE, DEBUG_MODEL, DEFAULT_MODEL, DEFAULT_WINDOW_SIZE
from app.ui.main_window import MainWindow


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--debug", action="store_true", help="Enable debug mode with live trace window.")
    parser.add_argument("--model", type=str, default=None, help="Override model name.")
    args, _unknown = parser.parse_known_args()

    app = QApplication(sys.argv)
    app.setApplicationName(APP_NAME)
    app.setStyleSheet(APP_STYLE)

    workspace_root = Path.cwd()
    model_name = args.model or (DEBUG_MODEL if args.debug else DEFAULT_MODEL)
    window = MainWindow(workspace_root=workspace_root, model_name=model_name, debug_mode=args.debug)
    window.resize(*DEFAULT_WINDOW_SIZE)
    suffix = " [DEBUG]" if args.debug else ""
    window.setWindowTitle(f"{APP_NAME}{suffix}")
    window.show()

    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
