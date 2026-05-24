"""Filesystem tools Pam can call. Sandboxed to the PAM workspace root.

Default safety: edits land in drafts/<original-path>, not the live file.
Glenn explicitly says "go" / "commit" → Pam calls commit_drafts() to promote them.
"""
from __future__ import annotations
import os
import json
import shutil
import subprocess
from pathlib import Path

PAM_ROOT = Path(__file__).resolve().parent.parent
DRAFTS_DIR = PAM_ROOT / "drafts"
BLOCKED_DIRS = {"secrets", ".git", "pam-chat/.venv", ".venv"}
AUTO_PUSH = os.environ.get("PAM_AUTO_PUSH", "0") == "1"


def _git_sync(reason: str) -> None:
    """If PAM_AUTO_PUSH=1, commit any changes and push. Best-effort, never raises."""
    if not AUTO_PUSH:
        return
    try:
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


def _draft_path_for(real: Path) -> Path:
    """Where the draft of `real` lives — drafts/<relative path under PAM_ROOT>."""
    rel = real.relative_to(PAM_ROOT)
    return DRAFTS_DIR / rel


# ---------- read-only tools ----------

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


def fetch_url(url: str, max_chars: int = 8000) -> str:
    """Fetch a public web URL (website, GitHub page, etc.) and return title + cleaned text + links.

    Note: LinkedIn profile pages and most authenticated pages will return a login wall, not the
    underlying profile data. This tool only sees what an unauthenticated visitor sees.
    """
    if not url.startswith(("http://", "https://")):
        return "url must start with http:// or https://"
    try:
        import requests
        from bs4 import BeautifulSoup
    except ImportError as e:
        return f"missing dependency: {e}. Install with: pip install requests beautifulsoup4"
    try:
        r = requests.get(
            url,
            timeout=15,
            headers={
                "User-Agent": "Mozilla/5.0 (compatible; PamBot/1.0)",
                "Accept": "text/html,application/xhtml+xml,application/json,text/plain,*/*;q=0.8",
            },
            allow_redirects=True,
        )
    except requests.RequestException as e:
        return f"fetch error: {e}"
    ct = r.headers.get("content-type", "").lower()
    parts = [f"URL: {r.url}", f"STATUS: {r.status_code}", f"TYPE: {ct}"]
    if "html" in ct:
        soup = BeautifulSoup(r.text, "html.parser")
        title = soup.title.string.strip() if soup.title and soup.title.string else "(no title)"
        for tag in soup(["script", "style", "noscript", "iframe", "svg", "header", "footer", "nav"]):
            tag.decompose()
        lines = [ln.strip() for ln in soup.get_text(separator="\n").splitlines()]
        text = "\n".join(ln for ln in lines if ln)
        links: list[str] = []
        for a in soup.find_all("a", href=True):
            label = (a.get_text() or "").strip()[:80]
            href = a["href"]
            if href.startswith("#") or href.startswith("javascript:"):
                continue
            links.append(f"  - {label or '(no text)'} → {href}")
            if len(links) >= 25:
                break
        parts.append(f"TITLE: {title}")
        body = text if len(text) <= max_chars else text[:max_chars] + f"\n…[truncated, total {len(text)} chars]"
        parts.append("\nCONTENT:\n" + body)
        if links:
            parts.append("\nLINKS (first " + str(len(links)) + "):\n" + "\n".join(links))
    else:
        body = r.text[:max_chars]
        if len(r.text) > max_chars:
            body += f"\n…[truncated, total {len(r.text)} chars]"
        parts.append("\nCONTENT:\n" + body)
    return "\n".join(parts)


# ---------- delegation to Hermes ----------

HERMES_CONTAINER = os.environ.get("HERMES_CONTAINER", "hermes-agent-flou-hermes-agent-1")
HERMES_TIMEOUT = int(os.environ.get("HERMES_TIMEOUT", "180"))


def call_hermes(message: str, continue_session: str | None = None) -> str:
    """Delegate a task to the Hermes agent running in a sibling container.

    Hermes has its own skill catalog — browser automation (Playwright/Camofox with
    login support), NotebookLM MCP server, the `personal-operations-dashboard` PAM
    skill, Google Workspace, Linear, Notion, OCR, and many more. Use this for things
    Pam can't do natively: JS-rendered pages, login-gated scraping, file workflows
    against Notion/Google Drive, multi-step automation chains.

    Returns Hermes' stdout reply, or an error string starting with "[hermes ".
    Latency is 10-60s per call (cold-spawn a Hermes process per request).
    """
    if not message or not message.strip():
        return "[hermes error] empty message"
    args = ["docker", "exec", "-u", "hermes", HERMES_CONTAINER, "hermes"]
    if continue_session:
        args += ["--continue", continue_session]
    args += ["-z", message]
    try:
        r = subprocess.run(args, capture_output=True, text=True, timeout=HERMES_TIMEOUT)
    except FileNotFoundError:
        return "[hermes error] docker CLI not available on this host"
    except subprocess.TimeoutExpired:
        return f"[hermes error] timed out after {HERMES_TIMEOUT}s"
    if r.returncode != 0:
        stderr = (r.stderr or "").strip()[:500]
        return f"[hermes error] exit {r.returncode}: {stderr}"
    out = (r.stdout or "").strip()
    return out or "[hermes returned empty stdout]"


# ---------- draft-by-default writes ----------

def propose_change(path: str, content: str) -> str:
    """Stage a proposed full-file overwrite or new file under drafts/."""
    real = _resolve(path)
    if DRAFTS_DIR in real.parents or real == DRAFTS_DIR:
        return "don't write directly inside drafts/ — pass the real target path"
    draft = _draft_path_for(real)
    draft.parent.mkdir(parents=True, exist_ok=True)
    draft.write_text(content, encoding="utf-8")
    rel = real.relative_to(PAM_ROOT).as_posix()
    return f"DRAFTED: drafts/{rel} ({len(content)} chars). Not live yet — Glenn must say 'go' to commit."


def propose_edit(path: str, old: str, new: str) -> str:
    """Stage a snippet replacement under drafts/. Uses the current draft if one exists, otherwise the live file."""
    real = _resolve(path)
    if DRAFTS_DIR in real.parents:
        return "don't edit drafts/ directly — pass the real target path"
    draft = _draft_path_for(real)
    source = draft if draft.exists() else real
    if not source.exists():
        return f"not found: {path}"
    text = source.read_text(encoding="utf-8")
    if old not in text:
        return f"old string not found in {path}"
    if text.count(old) > 1:
        return f"old string is not unique in {path} (appears {text.count(old)} times) — pass a longer, unique snippet"
    draft.parent.mkdir(parents=True, exist_ok=True)
    draft.write_text(text.replace(old, new, 1), encoding="utf-8")
    rel = real.relative_to(PAM_ROOT).as_posix()
    return f"DRAFTED edit: drafts/{rel}. Not live yet — Glenn must say 'go' to commit."


def list_drafts() -> str:
    if not DRAFTS_DIR.exists():
        return "no drafts pending"
    items = []
    for p in sorted(DRAFTS_DIR.rglob("*")):
        if p.is_file():
            rel = p.relative_to(DRAFTS_DIR).as_posix()
            size = p.stat().st_size
            items.append(f"{rel}  ({size} bytes)")
    return "\n".join(items) if items else "no drafts pending"


def show_draft(path: str) -> str:
    """Show the content of a single draft (path is the REAL target path, not the drafts/ path)."""
    real = _resolve(path)
    draft = _draft_path_for(real)
    if not draft.exists():
        return f"no draft for {path}"
    return draft.read_text(encoding="utf-8")


def commit_drafts() -> str:
    """Promote all files in drafts/ to their real locations, then clear drafts/."""
    if not DRAFTS_DIR.exists():
        return "no drafts to commit"
    promoted: list[str] = []
    for draft in sorted(DRAFTS_DIR.rglob("*")):
        if not draft.is_file():
            continue
        rel = draft.relative_to(DRAFTS_DIR)
        target = PAM_ROOT / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(draft, target)
        promoted.append(rel.as_posix())
    # Clear drafts after promoting
    shutil.rmtree(DRAFTS_DIR, ignore_errors=True)
    if not promoted:
        return "no drafts to commit"
    _git_sync(f"commit {len(promoted)} draft(s): {', '.join(promoted[:3])}{'...' if len(promoted) > 3 else ''}")
    return "COMMITTED LIVE:\n" + "\n".join(f"  → {p}" for p in promoted)


def discard_drafts() -> str:
    if not DRAFTS_DIR.exists():
        return "no drafts to discard"
    shutil.rmtree(DRAFTS_DIR, ignore_errors=True)
    return "discarded all drafts"


def render_dashboard() -> str:
    """Regenerate dashboard.html from dashboard/*.md (live files only — drafts not included)."""
    from render_dashboard import render
    out = render()
    return f"rendered dashboard.html ({out} bytes)"


# ---------- tool schemas (OpenAI / OpenRouter format) ----------

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
            "description": "Read a text file from the PAM workspace (live version).",
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
            "name": "fetch_url",
            "description": "Fetch a public web page (website, GitHub README, blog post, company page, etc.) and return its title, cleaned text, and outgoing links. Use this when Glenn asks Pam to look at a URL or research something online. Note: LinkedIn profiles and other login-gated pages will only return a login wall.",
            "parameters": {
                "type": "object",
                "properties": {
                    "url": {"type": "string", "description": "Full URL starting with http:// or https://"},
                    "max_chars": {"type": "integer", "description": "Max chars of body text to return (default 8000)."},
                },
                "required": ["url"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "propose_change",
            "description": "Stage a NEW file or a FULL-FILE rewrite under drafts/. Use this for any change that hasn't been pre-approved. The change is NOT live until commit_drafts is called.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "Real target path under PAM root (NOT drafts/...)."},
                    "content": {"type": "string"},
                },
                "required": ["path", "content"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "propose_edit",
            "description": "Stage a single unique-snippet replacement under drafts/. Builds on top of any existing draft for the same file. NOT live until commit_drafts.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "Real target path."},
                    "old": {"type": "string"},
                    "new": {"type": "string"},
                },
                "required": ["path", "old", "new"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "list_drafts",
            "description": "List all files currently staged in drafts/.",
            "parameters": {"type": "object", "properties": {}},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "show_draft",
            "description": "Show the full contents of a single pending draft (pass the real target path).",
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
            "name": "commit_drafts",
            "description": "Promote ALL drafts to their live target paths. Only call this when Glenn explicitly says 'go', 'commit', 'ship it', or similar approval.",
            "parameters": {"type": "object", "properties": {}},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "discard_drafts",
            "description": "Throw away all pending drafts. Only call when Glenn explicitly rejects them.",
            "parameters": {"type": "object", "properties": {}},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "render_dashboard",
            "description": "Regenerate dashboard.html from dashboard/*.md. Run after commit_drafts if any dashboard file changed.",
            "parameters": {"type": "object", "properties": {}},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "call_hermes",
            "description": (
                "Delegate to the Hermes agent running on the same VPS. Use for tasks "
                "Pam can't do natively: JS-rendered or login-gated page scraping (Hermes "
                "has Playwright + stealth + login flows), NotebookLM lookups, Google "
                "Workspace / Notion / Linear file workflows, OCR, multi-step browser "
                "automation. DON'T use for things Pam can do herself (read_file, fetch_url "
                "on plain pages, drafting text, dashboard edits). Latency: 10-60s per call. "
                "Returns Hermes' answer as text, or '[hermes error] ...' on failure."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "message": {
                        "type": "string",
                        "description": "The full prompt/task to send to Hermes. Be specific — Hermes starts cold and has no prior context unless you pass continue_session.",
                    },
                    "continue_session": {
                        "type": "string",
                        "description": "Optional Hermes session ID to resume (multi-turn). Leave empty for a fresh session.",
                    },
                },
                "required": ["message"],
            },
        },
    },
]

DISPATCH = {
    "list_files": list_files,
    "read_file": read_file,
    "fetch_url": fetch_url,
    "propose_change": propose_change,
    "propose_edit": propose_edit,
    "list_drafts": list_drafts,
    "show_draft": show_draft,
    "commit_drafts": commit_drafts,
    "discard_drafts": discard_drafts,
    "render_dashboard": render_dashboard,
    "call_hermes": call_hermes,
}


def call(name: str, args: dict) -> str:
    fn = DISPATCH.get(name)
    if not fn:
        return f"unknown tool: {name}"
    try:
        return fn(**args)
    except Exception as e:
        return f"error in {name}: {e}"


# ---------- HTTP endpoint helpers (read by server.py) ----------

def drafts_summary() -> list[dict]:
    """Lightweight summary of pending drafts for the UI."""
    if not DRAFTS_DIR.exists():
        return []
    out = []
    for p in sorted(DRAFTS_DIR.rglob("*")):
        if p.is_file():
            rel = p.relative_to(DRAFTS_DIR).as_posix()
            out.append({"path": rel, "bytes": p.stat().st_size})
    return out
