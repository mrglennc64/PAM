"""Render dashboard/*.md into a single styled dashboard.html at PAM root."""
from __future__ import annotations
from pathlib import Path
import markdown

PAM_ROOT = Path(__file__).resolve().parent.parent
DASHBOARD_DIR = PAM_ROOT / "dashboard"
OUTPUT = PAM_ROOT / "dashboard.html"

CSS = """
:root {
  --bg: #0e1117; --panel: #161b22; --text: #e6edf3; --muted: #8b949e;
  --accent: #58a6ff; --border: #30363d; --done: #3fb950; --warn: #d29922;
}
* { box-sizing: border-box; }
body {
  margin: 0; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", system-ui, sans-serif;
  background: var(--bg); color: var(--text); line-height: 1.55;
}
.wrap { max-width: 1100px; margin: 0 auto; padding: 24px; }
h1.title { font-size: 28px; margin: 0 0 4px; }
.sub { color: var(--muted); margin-bottom: 24px; font-size: 14px; }
nav.toc { background: var(--panel); border: 1px solid var(--border); border-radius: 8px; padding: 12px 16px; margin-bottom: 20px; }
nav.toc a { color: var(--accent); text-decoration: none; margin-right: 14px; font-size: 14px; }
nav.toc a:hover { text-decoration: underline; }
section.card { background: var(--panel); border: 1px solid var(--border); border-radius: 8px; padding: 18px 22px; margin-bottom: 18px; }
section.card h1, section.card h2 { margin-top: 0; border-bottom: 1px solid var(--border); padding-bottom: 6px; }
section.card h1 { font-size: 20px; color: var(--accent); }
section.card h2 { font-size: 16px; }
section.card h3 { font-size: 14px; color: var(--muted); margin-bottom: 4px; }
code { background: #0d1117; padding: 2px 6px; border-radius: 4px; font-size: 13px; }
pre { background: #0d1117; padding: 12px; border-radius: 6px; overflow-x: auto; }
ul { padding-left: 22px; }
li { margin: 3px 0; }
a { color: var(--accent); }
hr { border: none; border-top: 1px solid var(--border); margin: 16px 0; }
.foot { color: var(--muted); font-size: 12px; margin-top: 20px; text-align: center; }
input[type=checkbox] { margin-right: 6px; }
table { border-collapse: collapse; width: 100%; margin: 10px 0; }
th, td { border: 1px solid var(--border); padding: 6px 10px; text-align: left; font-size: 14px; }
th { background: #0d1117; }
"""


def render() -> int:
    if not DASHBOARD_DIR.exists():
        OUTPUT.write_text("<h1>No dashboard/ directory found.</h1>", encoding="utf-8")
        return OUTPUT.stat().st_size

    md_files = sorted(DASHBOARD_DIR.glob("*.md"))
    md = markdown.Markdown(extensions=["extra", "tables", "fenced_code", "sane_lists"])

    toc = []
    sections = []
    for f in md_files:
        slug = f.stem
        title = slug.replace("-", " ").title()
        toc.append(f'<a href="#{slug}">{title}</a>')
        body_html = md.convert(f.read_text(encoding="utf-8"))
        md.reset()
        sections.append(f'<section class="card" id="{slug}">{body_html}</section>')

    from datetime import datetime
    now = datetime.now().strftime("%Y-%m-%d %H:%M")

    html = f"""<!DOCTYPE html>
<html lang="en"><head>
<meta charset="utf-8"><title>PAM Dashboard</title>
<style>{CSS}</style>
</head><body>
<div class="wrap">
  <h1 class="title">PAM Dashboard</h1>
  <div class="sub">Personal Automation Machine · last rendered {now}</div>
  <nav class="toc">{' '.join(toc)}</nav>
  {''.join(sections)}
  <div class="foot">Auto-generated from dashboard/*.md by render_dashboard.py</div>
</div>
</body></html>"""

    OUTPUT.write_text(html, encoding="utf-8")
    return OUTPUT.stat().st_size


if __name__ == "__main__":
    n = render()
    print(f"wrote {OUTPUT} ({n} bytes)")
