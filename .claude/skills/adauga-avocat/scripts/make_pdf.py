#!/usr/bin/env python3
"""Render a contract legal-analysis (Markdown) into a styled PDF, via headless Chrome.

Michael runs this AFTER Toby's final analysis to produce the downloadable PDF he
attaches in General. It prints a ``MEDIA:<path>`` line that the gateway turns into
a Telegram document attachment.

Usage:
  make_pdf.py --md /path/to/analiza.md --title "Analiză contract — <client>"
  make_pdf.py --text "<full markdown analysis>" --title "Analiză contract"
  make_pdf.py --md a.md --decision "NO-GO" --title "..."   # decision shown on the cover

The body is Markdown (Toby's REZUMAT / DE VERIFICAT / TEMEI LEGAL / CONCLUZIE). It is
rendered with the ``markdown`` package when available, else as preformatted text.
Cross-platform, stdlib-only except the optional ``markdown`` package.
"""
from __future__ import annotations

import argparse
import datetime
import html
import os
import pathlib
import shutil
import subprocess
import sys
import tempfile
import uuid

HERE = pathlib.Path(__file__).resolve().parent
# <profile>/skills/contract-report/scripts/make_pdf.py → profile dir is 3 up.
PROFILE_DIR = HERE.parents[2]
OUT_DIR = PROFILE_DIR / "workspace" / "contracts"


def _find_chrome() -> str | None:
    candidates = [
        os.environ.get("AGENT_BROWSER_EXECUTABLE_PATH", "").strip(),
        "google-chrome", "google-chrome-stable", "chromium", "chromium-browser",
        "/usr/bin/google-chrome", "/usr/bin/chromium",
        "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
    ]
    for c in candidates:
        if not c:
            continue
        found = shutil.which(c) if not os.path.isabs(c) else (c if os.path.exists(c) else None)
        if found:
            return found
    return None


def _slugify(text: str) -> str:
    keep = "".join(ch.lower() if ch.isalnum() else "-" for ch in (text or "contract"))
    while "--" in keep:
        keep = keep.replace("--", "-")
    return keep.strip("-")[:40] or "contract"


def _md_to_html_fragment(md_text: str) -> str:
    try:
        import markdown  # type: ignore
        return markdown.markdown(
            md_text,
            extensions=["extra", "sane_lists", "nl2br", "toc"],
        )
    except Exception:
        return "<pre>" + html.escape(md_text) + "</pre>"


_DECISION_STYLE = {
    "GO": ("✅ GO — se poate semna", "#1a7f37", "#e6f4ea"),
    "NO-GO": ("⛔ NO-GO — nu semna ca atare", "#b3261e", "#fce8e6"),
    "GO-CONDITII": ("⚠️ GO CU CONDIȚII — semnează doar după renegociere", "#9a6700", "#fff4ce"),
}


def _build_html(title: str, body_md: str, decision: str | None) -> str:
    date_str = datetime.date.today().strftime("%d.%m.%Y")
    body_html = _md_to_html_fragment(body_md)

    decision_block = ""
    if decision:
        key = decision.strip().upper().replace(" ", "-").replace("_", "-")
        label, color, bg = _DECISION_STYLE.get(
            key, (decision, "#444", "#f0f0f0")
        )
        decision_block = (
            f'<div class="decision" style="border-left:6px solid {color};'
            f'background:{bg};color:{color};">{html.escape(label)}</div>'
        )

    return f"""<!DOCTYPE html>
<html lang="ro"><head><meta charset="utf-8"><title>{html.escape(title)}</title>
<style>
  @page {{ size: A4; margin: 18mm 16mm 20mm 16mm; }}
  * {{ box-sizing: border-box; }}
  body {{ font-family: "DejaVu Sans", "Liberation Sans", Arial, sans-serif;
         color:#1a1a1a; font-size:11.5pt; line-height:1.5; }}
  .head {{ border-bottom:3px solid #1a1a1a; padding-bottom:10px; margin-bottom:18px; }}
  .head h1 {{ font-size:18pt; margin:0 0 4px 0; }}
  .meta {{ color:#666; font-size:9.5pt; }}
  .decision {{ font-size:13pt; font-weight:700; padding:10px 14px; border-radius:4px;
              margin:0 0 18px 0; }}
  h1 {{ font-size:15pt; }}
  h2 {{ font-size:13pt; margin-top:20px; border-bottom:1px solid #ddd; padding-bottom:3px; }}
  h3 {{ font-size:11.5pt; margin-top:14px; }}
  ul, ol {{ margin:6px 0 12px 0; padding-left:22px; }}
  li {{ margin:4px 0; }}
  strong {{ color:#000; }}
  a {{ color:#0b57d0; word-break:break-all; }}
  code, pre {{ font-family:"DejaVu Sans Mono", monospace; font-size:10pt;
              background:#f6f6f6; padding:1px 4px; border-radius:3px; }}
  pre {{ padding:10px; white-space:pre-wrap; }}
  .footer {{ margin-top:26px; padding-top:10px; border-top:1px solid #ddd;
            color:#888; font-size:8.5pt; font-style:italic; }}
</style></head>
<body>
  <div class="head">
    <h1>{html.escape(title)}</h1>
    <div class="meta">Analiză juridică · {date_str}</div>
  </div>
  {decision_block}
  {body_html}
  <div class="footer">Document generat automat (analiză asistată de AI). NU constituie consultanță
  juridică formală — pentru contracte importante confirmați cu un avocat uman autorizat.</div>
</body></html>"""


def main() -> int:
    ap = argparse.ArgumentParser(description="Render contract analysis Markdown to a PDF.")
    ap.add_argument("--md", help="path to a Markdown file with the full analysis")
    ap.add_argument("--text", help="the analysis Markdown passed inline (alternative to --md)")
    ap.add_argument("--title", default="Analiză contract", help="document title")
    ap.add_argument("--decision", default="", help="GO | NO-GO | GO-CONDITII (shown on cover)")
    ap.add_argument("--out", default="", help="output PDF path (default: workspace/contracts/<slug>.pdf)")
    a = ap.parse_args()

    if a.md:
        try:
            body_md = pathlib.Path(a.md).read_text(encoding="utf-8")
        except Exception as exc:
            print(f"ERROR: cannot read --md file: {exc}")
            return 2
    elif a.text:
        body_md = a.text
    else:
        body_md = sys.stdin.read()
    if not body_md.strip():
        print("ERROR: empty analysis body (provide --md, --text, or stdin).")
        return 2

    chrome = _find_chrome()
    if not chrome:
        print("ERROR: Chrome/Chromium not found for PDF rendering.")
        return 3

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    stamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
    out_path = pathlib.Path(a.out) if a.out else OUT_DIR / f"analiza-{_slugify(a.title)}-{stamp}.pdf"
    out_path.parent.mkdir(parents=True, exist_ok=True)

    html_doc = _build_html(a.title, body_md, a.decision or None)

    with tempfile.TemporaryDirectory() as tmp:
        html_file = pathlib.Path(tmp) / "report.html"
        html_file.write_text(html_doc, encoding="utf-8")
        user_data = pathlib.Path(tmp) / f"chrome-{uuid.uuid4().hex}"
        cmd = [
            chrome, "--headless", "--disable-gpu", "--no-sandbox",
            "--no-pdf-header-footer",
            f"--user-data-dir={user_data}",
            f"--print-to-pdf={out_path}",
            html_file.as_uri(),
        ]
        try:
            proc = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
        except Exception as exc:
            print(f"ERROR: Chrome failed to render PDF: {exc}")
            return 3

    if not out_path.exists() or out_path.stat().st_size < 500:
        print("ERROR: PDF was not produced.")
        if proc.stderr:
            print(proc.stderr[-500:])
        return 3

    print(f"PDF_OK: {out_path} ({out_path.stat().st_size} bytes)")
    print(f"MEDIA:{out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
