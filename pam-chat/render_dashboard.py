"""Render PAM workspace into dashboard.html — sidebar nav + main content panel.

Sidebar groups:
  DASHBOARD          → dashboard/*.md
  ORG                → CLAUDE.md + org/*.md
  ROLES · BUSINESS   → roles/business/*.md
  ROLES · PERSONAL   → roles/personal/*.md

One section is visible at a time, switched by URL hash (#overview, #revenue, etc.).
"""
from __future__ import annotations
from pathlib import Path
from datetime import datetime
import re
import markdown

PAM_ROOT = Path(__file__).resolve().parent.parent
OUTPUT = PAM_ROOT / "dashboard.html"


# Label overrides — keys are file stems, values are sidebar labels.
LABELS = {
    "00-overview": "Overview · this week",
    "01-revenue-growth": "01 · Revenue & Growth",
    "02-platforms": "02 · Platforms",
    "03-outreach-meetings": "03 · Outreach & Meetings",
    "04-financial-planning": "04 · Financial Planning",
    "05-marketing-content": "05 · Marketing & Content",
    "06-deadlines-reminders": "06 · Deadlines & Reminders",
    "07-documents-assets": "07 · Documents & Assets",
    "08-weekly-review": "08 · Weekly Review",
    "CLAUDE": "CLAUDE.md (operating manual)",
    "pam-ceo": "Pam · CEO",
    "vp-business-aris": "Aris · VP Business",
    "vp-personal-vesta": "Vesta · VP Personal",
    "communication-flow": "Communication flow",
    "ops-lead": "Ops Lead",
    "platform-engineer": "Platform Engineer",
    "marketing-content": "Marketing / Content",
    "finance-liaison": "Finance Liaison",
    "outreach": "Outreach",
    "calendar-email": "Calendar / Email",
}


def slug_for(stem: str) -> str:
    """Map a file stem to its URL hash slug."""
    # 00-overview -> overview, 01-revenue-growth -> revenue-growth, etc.
    s = re.sub(r"^\d+-", "", stem)
    return s.lower().replace("_", "-")


def label_for(stem: str) -> str:
    return LABELS.get(stem, stem.replace("-", " ").title())


def collect_sections() -> list[dict]:
    """Build the section list in the order they should appear in the sidebar."""
    sections: list[dict] = []

    # DASHBOARD
    dash = PAM_ROOT / "dashboard"
    if dash.exists():
        for f in sorted(dash.glob("*.md")):
            sections.append({"group": "DASHBOARD", "file": f, "stem": f.stem})

    # ORG — CLAUDE.md first, then org/*.md
    claude = PAM_ROOT / "CLAUDE.md"
    if claude.exists():
        sections.append({"group": "ORG", "file": claude, "stem": "CLAUDE"})
    org = PAM_ROOT / "org"
    if org.exists():
        for f in sorted(org.glob("*.md")):
            sections.append({"group": "ORG", "file": f, "stem": f.stem})

    # ROLES · BUSINESS
    biz = PAM_ROOT / "roles" / "business"
    if biz.exists():
        for f in sorted(biz.glob("*.md")):
            sections.append({"group": "ROLES · BUSINESS", "file": f, "stem": f.stem})

    # ROLES · PERSONAL
    pers = PAM_ROOT / "roles" / "personal"
    if pers.exists():
        for f in sorted(pers.glob("*.md")):
            sections.append({"group": "ROLES · PERSONAL", "file": f, "stem": f.stem})

    # Annotate with slug + label
    seen_slugs: set[str] = set()
    for s in sections:
        base = slug_for(s["stem"])
        # avoid collision (e.g. CLAUDE and a section both becoming "claude")
        slug = base
        i = 1
        while slug in seen_slugs:
            i += 1
            slug = f"{base}-{i}"
        seen_slugs.add(slug)
        s["slug"] = slug
        s["label"] = label_for(s["stem"])
    return sections


CSS = """
:root {
  --bg: #0e1117; --sidebar: #0a0d12; --panel: #161b22; --text: #e6edf3;
  --muted: #8b949e; --accent: #ff7a3d; --accent-soft: rgba(255,122,61,0.12);
  --border: #21262d; --link: #58a6ff; --done: #3fb950;
}
* { box-sizing: border-box; }
html, body { margin: 0; height: 100%; background: var(--bg); color: var(--text);
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", system-ui, sans-serif;
  line-height: 1.55; }

.layout { display: grid; grid-template-columns: 260px 1fr; min-height: 100vh; }

aside.sidebar { background: var(--sidebar); border-right: 1px solid var(--border);
  padding: 24px 0 40px; overflow-y: auto; position: sticky; top: 0; height: 100vh; }
.brand { padding: 0 22px 24px; border-bottom: 1px solid var(--border); margin-bottom: 14px; }
.brand .title { color: var(--accent); font-weight: 800; font-size: 28px; letter-spacing: 1px; }
.brand .subtitle { color: var(--muted); font-size: 11px; letter-spacing: 1.2px; margin-top: 2px; }
.brand .meta { color: var(--text); font-size: 12px; margin-top: 8px; opacity: 0.85; }

.group-label { color: var(--muted); font-size: 11px; letter-spacing: 1.5px; font-weight: 600;
  padding: 18px 22px 6px; }
.nav { display: flex; flex-direction: column; }
.nav a { display: block; padding: 8px 22px; color: var(--text); text-decoration: none;
  font-size: 13.5px; border-left: 3px solid transparent; opacity: 0.85; }
.nav a:hover { background: rgba(255,255,255,0.03); opacity: 1; }
.nav a.active { background: var(--accent-soft); border-left-color: var(--accent); color: var(--accent); opacity: 1; }

main.content { padding: 28px 40px; max-width: 1000px; overflow-x: hidden; }
.section { display: none; }
.section.active { display: block; }
.section h1 { font-size: 24px; margin: 0 0 6px; }
.section h2 { font-size: 18px; margin-top: 28px; padding-bottom: 6px; border-bottom: 1px solid var(--border); }
.section h3 { font-size: 14px; color: var(--muted); margin-bottom: 4px; text-transform: uppercase; letter-spacing: 0.5px; }
.section a { color: var(--link); }
.section ul { padding-left: 22px; }
.section li { margin: 3px 0; }
.section pre { background: #0d1117; padding: 12px; border-radius: 6px; overflow-x: auto;
  border: 1px solid var(--border); font-size: 13px; }
.section code { background: #0d1117; padding: 2px 6px; border-radius: 4px; font-size: 13px; }
.section pre code { padding: 0; background: transparent; }
.section table { border-collapse: collapse; margin: 12px 0; width: 100%; font-size: 14px; }
.section th, .section td { border: 1px solid var(--border); padding: 8px 12px; text-align: left; }
.section th { background: #0d1117; color: var(--muted); font-weight: 600; }
.section hr { border: none; border-top: 1px solid var(--border); margin: 16px 0; }
.section blockquote { border-left: 3px solid var(--border); margin: 10px 0; padding: 4px 14px; color: var(--muted); }
.section input[type=checkbox] { margin-right: 6px; }
.foot { color: var(--muted); font-size: 11px; margin-top: 40px; padding-top: 14px; border-top: 1px solid var(--border); }
"""

JS = """
function pickSection() {
  const hash = (location.hash || '#overview').slice(1);
  document.querySelectorAll('.section').forEach(s => s.classList.toggle('active', s.id === hash));
  document.querySelectorAll('.nav a').forEach(a => a.classList.toggle('active', a.getAttribute('href') === '#' + hash));
  // If nothing matched, fall back to the first section.
  if (!document.querySelector('.section.active')) {
    const first = document.querySelector('.section');
    const firstLink = document.querySelector('.nav a');
    if (first) first.classList.add('active');
    if (firstLink) firstLink.classList.add('active');
  }
  window.scrollTo(0, 0);
}
window.addEventListener('hashchange', pickSection);
window.addEventListener('DOMContentLoaded', pickSection);
"""


def render() -> int:
    sections = collect_sections()
    md = markdown.Markdown(extensions=["extra", "tables", "fenced_code", "sane_lists"])

    # Sidebar — group consecutive entries with the same group label.
    sidebar_parts: list[str] = []
    last_group = None
    for s in sections:
        if s["group"] != last_group:
            sidebar_parts.append(f'<div class="group-label">{s["group"]}</div><div class="nav">')
            if last_group is not None:
                sidebar_parts.insert(-1, "</div>")  # close prev
            last_group = s["group"]
        sidebar_parts.append(f'<a href="#{s["slug"]}">{s["label"]}</a>')
    if last_group is not None:
        sidebar_parts.append("</div>")

    # Main content — one div per section.
    section_html_parts: list[str] = []
    for s in sections:
        body = md.convert(s["file"].read_text(encoding="utf-8"))
        md.reset()
        rel = s["file"].relative_to(PAM_ROOT).as_posix()
        section_html_parts.append(
            f'<div class="section" id="{s["slug"]}">'
            f'<h3>{s["group"]}</h3>'
            f'{body}'
            f'<div class="foot">source: {rel}</div>'
            f'</div>'
        )

    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    html = f"""<!DOCTYPE html>
<html lang="en"><head>
<meta charset="utf-8"><title>PAM Dashboard</title>
<style>{CSS}</style>
</head><body>
<div class="layout">
  <aside class="sidebar">
    <div class="brand">
      <div class="title">PAM</div>
      <div class="subtitle">PERSONAL AUTOMATION MACHINE</div>
      <div class="meta">CEO: Pam · Glenn (CET)</div>
    </div>
    {''.join(sidebar_parts)}
  </aside>
  <main class="content">
    {''.join(section_html_parts)}
    <div class="foot">Auto-generated {now} by pam-chat/render_dashboard.py</div>
  </main>
</div>
<script>{JS}</script>
</body></html>"""

    OUTPUT.write_text(html, encoding="utf-8")
    return OUTPUT.stat().st_size


if __name__ == "__main__":
    n = render()
    print(f"wrote {OUTPUT} ({n} bytes)")
