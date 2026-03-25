from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path


@dataclass(slots=True)
class ValidationResult:
    ok: bool
    message: str


def is_lua_filename(path: Path) -> bool:
    return path.suffix.lower() == ".lua"


def validate_lua_code(code: str) -> ValidationResult:
    """Simple static checks for common Lua mistakes.

    This is intentionally lightweight and does not replace a real parser.
    """
    stack: list[str] = []
    token_pattern = re.compile(r"\b(function|if|do|repeat|end|until)\b")
    for token in token_pattern.findall(code):
        if token in {"function", "if", "do", "repeat"}:
            stack.append(token)
        elif token == "end":
            if not stack or stack[-1] == "repeat":
                return ValidationResult(False, "Unexpected 'end'.")
            stack.pop()
        elif token == "until":
            if not stack or stack[-1] != "repeat":
                return ValidationResult(False, "Unexpected 'until'.")
            stack.pop()

    if stack:
        return ValidationResult(False, f"Unclosed block(s): {', '.join(stack)}")

    if code.count("(") != code.count(")"):
        return ValidationResult(False, "Unbalanced parentheses.")

    return ValidationResult(True, "Basic Lua validation passed.")


def ensure_within_root(root: Path, target: Path) -> Path:
    root_resolved = root.resolve()
    target_resolved = target.resolve()
    if root_resolved == target_resolved:
        return target_resolved
    if root_resolved not in target_resolved.parents:
        raise ValueError("Operation outside opened workspace is not allowed.")
    return target_resolved


def read_text_file(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def write_text_file(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
