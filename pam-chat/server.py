"""Pam chat server — local FastAPI app that puts a chat UI on top of OpenRouter
and gives Pam filesystem tools to edit her own PAM workspace.

Run with: python server.py
Then open: http://localhost:8765/
"""
from __future__ import annotations
import json
import os
import sys
import time
from pathlib import Path
from typing import Any

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, JSONResponse
from openai import OpenAI
from pydantic import BaseModel

HERE = Path(__file__).resolve().parent
PAM_ROOT = HERE.parent

sys.path.insert(0, str(HERE))
from pam_tools import TOOL_SCHEMAS, call as call_tool  # noqa: E402
from render_dashboard import render as render_dashboard  # noqa: E402


# ---------- env loading ----------
def load_env() -> None:
    env_path = PAM_ROOT / "secrets" / ".env"
    if not env_path.exists():
        sys.exit(f"Missing {env_path}. Put OPENROUTER_API_KEY in there.")
    for line in env_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        os.environ.setdefault(k.strip(), v.strip())


load_env()
API_KEY = os.environ.get("OPENROUTER_API_KEY")
MODEL = os.environ.get("PAM_MODEL", "openrouter/owl-alpha")
FALLBACK = os.environ.get("PAM_FALLBACK_MODEL", "meta-llama/llama-3.3-70b-instruct:free")
PORT = int(os.environ.get("PAM_PORT", "8765"))

if not API_KEY:
    sys.exit("OPENROUTER_API_KEY not set in secrets/.env")

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=API_KEY,
    default_headers={
        "HTTP-Referer": "http://localhost:8765",
        "X-Title": "Pam - PAM workspace assistant",
    },
)


# ---------- system prompt ----------
def build_system_prompt() -> str:
    parts = ["You are Pam (Personal Automation Machine), Glenn's operations brain."]
    claude_md = PAM_ROOT / "CLAUDE.md"
    if claude_md.exists():
        parts.append("\n# Your operating manual (CLAUDE.md)\n" + claude_md.read_text(encoding="utf-8"))

    dash_dir = PAM_ROOT / "dashboard"
    if dash_dir.exists():
        parts.append("\n# Current dashboard state")
        for f in sorted(dash_dir.glob("*.md")):
            parts.append(f"\n## dashboard/{f.name}\n" + f.read_text(encoding="utf-8"))

    parts.append(
        "\n# How you work\n"
        "- You have file tools (list_files, read_file, write_file, edit_file, render_dashboard). "
        "Use them to actually update PAM files when Glenn tells you something. Don't just acknowledge — act.\n"
        "- After editing any dashboard/ file, call render_dashboard.\n"
        "- Keep replies short and direct, no metaphors, no hype.\n"
        "- When Glenn shares info (a deadline, a meeting, a number), figure out which file it belongs in "
        "and update it. Confirm with one line what you did.\n"
        "- For external actions (sending email, scheduling, paying), draft only — don't send.\n"
    )
    return "\n".join(parts)


SYSTEM_PROMPT = build_system_prompt()


# ---------- conversation persistence ----------
HISTORY_FILE = HERE / "history.jsonl"


def load_history() -> list[dict]:
    if not HISTORY_FILE.exists():
        return []
    msgs = []
    for line in HISTORY_FILE.read_text(encoding="utf-8").splitlines():
        if line.strip():
            try:
                msgs.append(json.loads(line))
            except json.JSONDecodeError:
                pass
    return msgs


def append_history(msg: dict) -> None:
    with HISTORY_FILE.open("a", encoding="utf-8") as f:
        f.write(json.dumps(msg, ensure_ascii=False) + "\n")


# ---------- agent loop ----------
def serializable_tool_calls(tool_calls) -> list[dict]:
    return [
        {
            "id": tc.id,
            "type": "function",
            "function": {"name": tc.function.name, "arguments": tc.function.arguments},
        }
        for tc in tool_calls
    ]


def run_turn(user_text: str, max_tool_iterations: int = 8) -> dict:
    """Run one user turn. Returns {'reply': str, 'tool_log': list[str]}."""
    history = load_history()
    history.append({"role": "user", "content": user_text})
    append_history({"role": "user", "content": user_text, "ts": time.time()})

    messages = [{"role": "system", "content": SYSTEM_PROMPT}] + [
        {k: v for k, v in m.items() if k in ("role", "content", "tool_calls", "tool_call_id", "name")}
        for m in history
    ]

    tool_log: list[str] = []
    model_used = MODEL

    for _ in range(max_tool_iterations):
        try:
            resp = client.chat.completions.create(
                model=model_used,
                messages=messages,
                tools=TOOL_SCHEMAS,
                max_tokens=2048,
            )
        except Exception as e:
            err = str(e)
            if "429" in err or "rate" in err.lower():
                if model_used != FALLBACK:
                    tool_log.append(f"rate-limited on {model_used}, switching to {FALLBACK}")
                    model_used = FALLBACK
                    continue
            return {"reply": f"[error] {err[:300]}", "tool_log": tool_log}

        msg = resp.choices[0].message
        tool_calls = msg.tool_calls or []

        if not tool_calls:
            reply = msg.content or ""
            append_history({"role": "assistant", "content": reply, "ts": time.time()})
            return {"reply": reply, "tool_log": tool_log, "model": model_used}

        assistant_msg = {
            "role": "assistant",
            "content": msg.content or "",
            "tool_calls": serializable_tool_calls(tool_calls),
        }
        messages.append(assistant_msg)
        append_history({**assistant_msg, "ts": time.time()})

        for tc in tool_calls:
            name = tc.function.name
            try:
                args = json.loads(tc.function.arguments or "{}")
            except json.JSONDecodeError:
                args = {}
            result = call_tool(name, args)
            log_line = f"{name}({', '.join(f'{k}={v!r}'[:60] for k,v in args.items())}) → {str(result)[:120]}"
            tool_log.append(log_line)
            tool_msg = {
                "role": "tool",
                "tool_call_id": tc.id,
                "name": name,
                "content": str(result),
            }
            messages.append(tool_msg)
            append_history({**tool_msg, "ts": time.time()})

    return {"reply": "[stopped: too many tool iterations]", "tool_log": tool_log, "model": model_used}


# ---------- FastAPI app ----------
app = FastAPI(title="Pam")


class ChatIn(BaseModel):
    message: str


@app.post("/chat")
def chat(body: ChatIn) -> JSONResponse:
    if not body.message.strip():
        raise HTTPException(400, "empty message")
    result = run_turn(body.message)
    return JSONResponse(result)


@app.post("/reset")
def reset() -> dict:
    if HISTORY_FILE.exists():
        HISTORY_FILE.unlink()
    return {"ok": True}


@app.get("/history")
def get_history() -> JSONResponse:
    msgs = [m for m in load_history() if m.get("role") in ("user", "assistant") and m.get("content")]
    return JSONResponse(msgs)


@app.get("/")
def root() -> FileResponse:
    return FileResponse(HERE / "chat.html")


@app.get("/dashboard")
def dashboard() -> FileResponse:
    render_dashboard()
    return FileResponse(PAM_ROOT / "dashboard.html")


if __name__ == "__main__":
    import uvicorn

    try:
        render_dashboard()
    except Exception as e:
        print(f"[warn] could not render dashboard: {e}")
    print(f"Pam online at http://localhost:{PORT}")
    print(f"Model: {MODEL}  |  Fallback: {FALLBACK}")
    uvicorn.run(app, host="127.0.0.1", port=PORT, log_level="warning")
