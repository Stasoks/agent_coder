from __future__ import annotations

from pathlib import Path
from typing import Any
import logging

from app.core.file_ops import ensure_within_root, read_text_file, write_text_file

logger = logging.getLogger(__name__)


class AgentActionExecutor:
    def __init__(self, workspace_root: Path) -> None:
        self.workspace_root = workspace_root

    def set_root(self, workspace_root: Path) -> None:
        self.workspace_root = workspace_root

    def execute(self, actions: list[dict[str, Any]]) -> list[str]:
        logs: list[str] = []

        # Log available files in workspace
        try:
            available_files = list(self.workspace_root.glob("**/*.lua")) + \
                            list(self.workspace_root.glob("**/*.txt")) + \
                            list(self.workspace_root.glob("**/*.py"))
            logger.info(f"Available files in workspace: {[f.relative_to(self.workspace_root) for f in available_files[:10]]}")
        except Exception as e:
            logger.warning(f"Could not list workspace files: {e}")

        for action in actions:
            action_type = str(action.get("type", "")).strip().lower()
            path_value = action.get("path", "")
            if not path_value:
                msg = "Skipped action without path."
                logs.append(msg)
                logger.warning(msg)
                continue

            try:
                target = ensure_within_root(self.workspace_root, self.workspace_root / str(path_value))
                logger.info(f"Action: {action_type} on {target.relative_to(self.workspace_root)} (exists: {target.exists()})")
            except Exception as e:
                msg = f"Path validation failed for {path_value}: {e}"
                logs.append(msg)
                logger.error(msg)
                continue

            if action_type == "read_file":
                try:
                    if not target.exists():
                        msg = f"read_file: file does not exist {target.relative_to(self.workspace_root)}"
                        logs.append(msg)
                        logger.warning(msg)
                        continue

                    content = read_text_file(target)
                    msg = f"read_file: {target.relative_to(self.workspace_root)} ({len(content)} bytes)"
                    logs.append(msg)
                    logger.info(msg)
                except Exception as e:
                    msg = f"read_file failed: {e}"
                    logs.append(msg)
                    logger.error(msg)
                continue

            if action_type == "write_file":
                content = str(action.get("content", ""))
                try:
                    write_text_file(target, content)
                    msg = f"write_file: {target.relative_to(self.workspace_root)}"
                    logs.append(msg)
                    logger.info(msg)
                except Exception as e:
                    msg = f"write_file failed: {e}"
                    logs.append(msg)
                    logger.error(msg)
                continue

            if action_type == "append_file":
                content = str(action.get("content", ""))
                try:
                    old = read_text_file(target) if target.exists() else ""
                    write_text_file(target, old + content)
                    msg = f"append_file: {target.relative_to(self.workspace_root)}"
                    logs.append(msg)
                    logger.info(msg)
                except Exception as e:
                    msg = f"append_file failed: {e}"
                    logs.append(msg)
                    logger.error(msg)
                continue

            if action_type == "replace_in_file":
                old_text = str(action.get("old_text", ""))
                new_text = str(action.get("new_text", ""))
                try:
                    if not target.exists():
                        msg = f"replace_in_file: file does not exist {target.relative_to(self.workspace_root)}"
                        logs.append(msg)
                        logger.warning(msg)
                        continue

                    original = read_text_file(target)
                    if old_text and old_text in original:
                        write_text_file(target, original.replace(old_text, new_text, 1))
                        msg = f"replace_in_file: {target.relative_to(self.workspace_root)}"
                        logs.append(msg)
                        logger.info(msg)
                    else:
                        msg = f"replace_in_file: text not found in {target.relative_to(self.workspace_root)}"
                        logs.append(msg)
                        logger.warning(msg)
                except Exception as e:
                    msg = f"replace_in_file failed: {e}"
                    logs.append(msg)
                    logger.error(msg)
                continue

            msg = f"Unknown action type: {action_type}"
            logs.append(msg)
            logger.warning(msg)

        return logs
