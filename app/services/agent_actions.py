from __future__ import annotations

from pathlib import Path
from typing import Any

from app.core.file_ops import ensure_within_root, read_text_file, write_text_file


class AgentActionExecutor:
    def __init__(self, workspace_root: Path) -> None:
        self.workspace_root = workspace_root

    def set_root(self, workspace_root: Path) -> None:
        self.workspace_root = workspace_root

    def execute(self, actions: list[dict[str, Any]]) -> list[str]:
        logs: list[str] = []
        for action in actions:
            action_type = str(action.get("type", "")).strip().lower()
            path_value = action.get("path", "")
            if not path_value:
                logs.append("Skipped action without path.")
                continue

            target = ensure_within_root(self.workspace_root, self.workspace_root / str(path_value))

            if action_type == "write_file":
                content = str(action.get("content", ""))
                write_text_file(target, content)
                logs.append(f"write_file: {target.relative_to(self.workspace_root)}")
                continue

            if action_type == "append_file":
                content = str(action.get("content", ""))
                old = read_text_file(target) if target.exists() else ""
                write_text_file(target, old + content)
                logs.append(f"append_file: {target.relative_to(self.workspace_root)}")
                continue

            if action_type == "replace_in_file":
                old_text = str(action.get("old_text", ""))
                new_text = str(action.get("new_text", ""))
                original = read_text_file(target)
                if old_text and old_text in original:
                    write_text_file(target, original.replace(old_text, new_text, 1))
                    logs.append(f"replace_in_file: {target.relative_to(self.workspace_root)}")
                else:
                    logs.append(f"replace_in_file skipped: not found in {target.relative_to(self.workspace_root)}")
                continue

            logs.append(f"Unknown action type: {action_type}")
        return logs
