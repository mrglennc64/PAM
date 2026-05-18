"""Filesystem tools Pam can call. Sandboxed to the PAM workspace root.
Blocks any path that escapes the workspace or touches secrets/.
"""
from __future__ import annotations
import os
import json
import subprocess
from pathlib import Path

PAM_ROOT = Path(__file__).resolve().parent.parent
BLOCKED_DIRS = {"secrets", ".git", "pam-chat/.venv", ".venv"}
AUTO_PUSH = os.environ.get("PAM_AUTO_PUSH", "0") == "1"


def _git_sync(reason: str) -> None:
    """If PAM_AUTO_PUSH=1, commit any changes and push. Best-effort, never raises."""
    if not AUTO_PUSH:
        return
    try:
        # Are there any changes?
        st = subprocess.run(
            ["git", "status", "--porcelain"], cwd=PAM_ROOT, capture_output=True, text=True, timeout=10
        )
        if not st.stdout.strip():
            return
        subprocess.run(["git", "add", "-A"], cwd=PAM_ROOT, capture_output=True, timeout=10)
        subprocess.run(
            ["git", "commit", "-m", f"pam: {reason}"],
            cwd=PAM_ROOT, capture_output=True, timeout=10,
        )
        subprocess.run(
            ["git", "push", "origin", "main"],
            cwd=PAM_ROOT, capture_output=True, timeout=20,
        )
    except Exception:
        pass


def _resolve(path: str) -> Path:
    """Resolve a user-supplied path relative to PAM root, with safety checks."""
    p = (PAM_ROOT / path).resolve() if not os.path.isabs(path) else Path(path).resolve()
    try:
        rel = p.relative_to(PAM_ROOT)
    except ValueError:
        raise PermissionError(f"path escapes PAM workspace: {path}")
    parts = set(rel.parts)
    if parts & BLOCKED_DIRS:
        raise PermissionError(f"path is in a blocked area: {path}")
    return p


def list_files(path: str = ".") -> str:
    p = _resolve(path)
    if not p.exists():
        return f"not found: {path}"
    if p.is_file():
        return f"(file) {p.relative_to(PAM_ROOT)}"
    items = []
    for child in sorted(p.iterdir()):
        if child.name in BLOCKED_DIRS or child.name.startswith("."):
            continue
        kind = "dir " if child.is_dir() else "file"
        items.append(f"{kind}  {child.relative_to(PAM_ROOT).as_posix()}")
    return "\n".join(items) if items else "(empty)"


def read_file(path: str) -> str:
    p = _resolve(path)
    if not p.exists():
        return f"not found: {path}"
    if p.is_dir():
        return f"is a directory: {path}"
    try:
        return p.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return f"binary file, cannot read as text: {path}"


def write_file(path: str, content: str) -> str:
    p = _resolve(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    existed = p.exists()
    p.write_text(content, encoding="utf-8")
    rel = p.relative_to(PAM_ROOT).as_posix()
    _git_sync(f"write {rel}")
    return f"{'overwrote' if existed else 'created'}: {rel} ({len(content)} chars)"


def edit_file(path: str, old: str, new: str) -> str:
    p = _resolve(path)
    if not p.exists():
        return f"not found: {path}"
    text = p.read_text(encoding="utf-8")
    if old not in text:
        return f"old string not found in {path}"
    if text.count(old) > 1:
        return f"old string is not unique in {path} (appears {text.count(old)} times) — pass a longer, unique snippet"
    p.write_text(text.replace(old, new, 1), encoding="utf-8")
    rel = p.relative_to(PAM_ROOT).as_posix()
    _git_sync(f"edit {rel}")
    return f"edited: {rel}"


def render_dashboard() -> str:
    """Regenerate dashboard.html from dashboard/*.md."""
    from render_dashboard import render
    out = render()
    return f"rendered dashboard.html ({out} bytes)"


# OpenRouter / OpenAI-format tool schemas
TOOL_SCHEMAS = [
    {
        "type": "function",
        "function": {
            "name": "list_files",
            "description": "List files and folders inside the PAM workspace. Use '.' for root.",
            "parameters": {
                "type": "object",
                "properties": {"path": {"type": "string", "description": "Path relative to PAM root."}},
                "required": ["path"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "read_file",
            "description": "Read a text file from the PAM workspace.",
            "parameters": {
                "type": "object",
                "properties": {"path": {"type": "string"}},
                "required": ["path"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "write_file",
            "description": "Create or overwrite a file in the PAM workspace. Use for new files or full rewrites.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string"},
                    "content": {"type": "string"},
                },
                "required": ["path", "content"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "edit_file",
            "description": "Replace one unique snippet in an existing file. Prefer this for small changes.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string"},
                    "old": {"type": "string", "description": "Exact unique string to replace."},
                    "new": {"type": "string"},
                },
                "required": ["path", "old", "new"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "render_dashboard",
            "description": "Regenerate dashboard.html from dashboard/*.md. Run after editing any dashboard file.",
            "parameters": {"type": "object", "properties": {}},
        },
    },
]

DISPATCH = {
    "list_files": list_files,
    "read_file": read_file,
    "write_file": write_file,
    "edit_file": edit_file,
    "render_dashboard": render_dashboard,
}


def call(name: str, args: dict) -> str:
    fn = DISPATCH.get(name)
    if not fn:
        return f"unknown tool: {name}"
    try:
        return fn(**args)
    except Exception as e:
        return f"error in {name}: {e}"
