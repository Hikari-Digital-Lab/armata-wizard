#!/usr/bin/env python3
"""Deterministic contract-review DELIVERY (Michael → human, in General).

This is the ONE command Michael runs to finish a contract review. It:
  1. renders Toby's full analysis (Markdown) into a styled PDF (via make_pdf.py), then
  2. posts to the **General** topic, through Michael's own bot token, a SHORT message
     (verdict + the bullets Michael wrote + disclaimer) with the PDF attached as a document.

Because the script — not the LLM — composes and sends the chat message, the delivery is
ALWAYS short (no "romane"): the full detail lives only in the attached PDF.

Usage:
  deliver_verdict.py --md analiza.md --decision NO-GO \
      --summary "- clauza X e abuzivă\n- plată la 90 zile\n- cedare totală drepturi" \
      [--title "Analiză contract — <obiect>"] [--intro "o linie Michael"]

Reads the bot token + group id from the owning profile's .env. Stdlib-only.
"""
from __future__ import annotations

import argparse
import json
import mimetypes
import os
import pathlib
import re
import subprocess
import sys
import urllib.request
import uuid

HERE = pathlib.Path(__file__).resolve().parent
PROFILE_DIR = HERE.parents[2]            # <profile>/skills/contract-report/scripts → profile
MAKE_PDF = HERE / "make_pdf.py"
CAPTION_LIMIT = 1024                      # Telegram document caption hard cap
# Default PDF source: the full analysis Toby saves here on his final round.
SHARED_ANALYSIS = PROFILE_DIR / "workspace" / "contracts" / "avocat_analiza.md"
MIN_ANALYSIS_CHARS = 400                  # guard: the PDF must hold Toby's DEEP analysis, not a teaser

_DECISION_LABEL = {
    "GO": "✅ GO — se poate semna",
    "NO-GO": "⛔ NO-GO — nu semna ca atare",
    "GO-CONDITII": "⚠️ GO CU CONDIȚII — semnează doar după renegociere",
}
_DISCLAIMER = "⚖️ Analiză asistată de AI, nu consultanță juridică formală — confirmă cu un avocat uman."


def _env(key: str) -> str:
    for env_file in (PROFILE_DIR / ".env",):
        try:
            for line in env_file.read_text(encoding="utf-8").splitlines():
                line = line.strip()
                if line.startswith("#") or "=" not in line:
                    continue
                k, _, v = line.partition("=")
                if k.strip() == key:
                    return v.strip().strip('"').strip("'")
        except Exception:
            continue
    return ""


def _build_pdf(md: str, title: str, decision: str) -> str | None:
    """Run make_pdf.py and return the produced PDF path (from its MEDIA: line)."""
    py = sys.executable
    cmd = [py, str(MAKE_PDF), "--md", md, "--title", title]
    if decision:
        cmd += ["--decision", decision]
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=180)
    except Exception as exc:
        print(f"ERROR: make_pdf failed to run: {exc}")
        return None
    for line in (proc.stdout or "").splitlines():
        if line.startswith("MEDIA:"):
            return line[len("MEDIA:"):].strip()
    print("ERROR: make_pdf did not return a PDF.")
    if proc.stdout:
        print(proc.stdout[-400:])
    if proc.stderr:
        print(proc.stderr[-400:])
    return None


def _send_document(token: str, chat_id: str, caption: str, doc_path: str) -> bool:
    boundary = "----hermes" + uuid.uuid4().hex
    fields = {"chat_id": str(chat_id), "caption": caption}
    # General topic = no message_thread_id (forum General).
    doc = pathlib.Path(doc_path)
    ctype = mimetypes.guess_type(doc.name)[0] or "application/pdf"
    body = bytearray()
    for k, v in fields.items():
        body += f"--{boundary}\r\n".encode()
        body += f'Content-Disposition: form-data; name="{k}"\r\n\r\n'.encode()
        body += f"{v}\r\n".encode()
    body += f"--{boundary}\r\n".encode()
    body += f'Content-Disposition: form-data; name="document"; filename="{doc.name}"\r\n'.encode()
    body += f"Content-Type: {ctype}\r\n\r\n".encode()
    body += doc.read_bytes()
    body += f"\r\n--{boundary}--\r\n".encode()
    url = f"https://api.telegram.org/bot{token}/sendDocument"
    req = urllib.request.Request(url, data=bytes(body))
    req.add_header("Content-Type", f"multipart/form-data; boundary={boundary}")
    try:
        with urllib.request.urlopen(req, timeout=120) as r:
            return json.loads(r.read().decode("utf-8")).get("ok", False)
    except Exception as exc:
        print(f"ERROR: Telegram sendDocument failed: {exc}")
        return False


def _build_caption(decision: str, summary: str, intro: str) -> str:
    key = (decision or "").strip().upper().replace(" ", "-").replace("_", "-")
    verdict = _DECISION_LABEL.get(key, decision.strip() or "Verdict")
    parts = []
    if intro.strip():
        parts.append(intro.strip())
    parts.append(verdict)
    if summary.strip():
        # Normalize: turn literal "\n" into real newlines; ensure bullet lines.
        s = summary.replace("\\n", "\n").strip()
        parts.append(s)
    parts.append("📎 Analiza completă e în PDF-ul atașat.")
    parts.append(_DISCLAIMER)
    caption = "\n\n".join(parts)
    if len(caption) > CAPTION_LIMIT:
        caption = caption[: CAPTION_LIMIT - 1].rstrip() + "…"
    return caption


def main() -> int:
    ap = argparse.ArgumentParser(description="Build PDF + deliver short verdict to General.")
    ap.add_argument("--md", help="path to Markdown file with Toby's full analysis (for the PDF)")
    ap.add_argument("--text", help="full analysis Markdown inline (alternative to --md)")
    ap.add_argument("--decision", required=True, help="GO | NO-GO | GO-CONDITII")
    ap.add_argument("--summary", default="", help="the SHORT body (3–5 bullets) Michael wrote")
    ap.add_argument("--title", default="Analiză contract", help="PDF title")
    ap.add_argument("--intro", default="", help="optional one-line Michael intro")
    a = ap.parse_args()

    # Resolve the analysis markdown. Priority: --md > --text > the file Toby saved (default).
    if a.md:
        md_path = a.md
    elif a.text and a.text.strip():
        tmp = PROFILE_DIR / "workspace" / "contracts"
        tmp.mkdir(parents=True, exist_ok=True)
        md_path = str(tmp / f"analiza-{uuid.uuid4().hex[:8]}.md")
        pathlib.Path(md_path).write_text(a.text, encoding="utf-8")
    else:
        md_path = str(SHARED_ANALYSIS)

    if not pathlib.Path(md_path).is_file():
        print(f"ERROR: full analysis not found: {md_path}")
        print("→ Avocatul trebuie să-și salveze analiza completă în 'avocat_analiza.md' (runda finală), "
              "sau pasează tu --md <fișier> / --text \"<analiza completă>\".")
        return 2

    # Guard: the PDF must contain Toby's DEEP analysis, not just the short summary.
    body_len = len(pathlib.Path(md_path).read_text(encoding="utf-8").strip())
    if body_len < MIN_ANALYSIS_CHARS:
        print(f"ERROR: analiza din {md_path} are doar {body_len} caractere — pare trunchiată.")
        print("PDF-ul trebuie să conțină analiza APROFUNDATĂ completă a lui Toby (toate secțiunile: "
              "REZUMAT / DE VERIFICAT / TEMEI LEGAL / CONCLUZIE), NU doar rezumatul din mesaj. "
              "Asigură-te că fișierul conține analiza integrală și reia.")
        return 2

    pdf = _build_pdf(md_path, a.title, a.decision)
    if not pdf or not pathlib.Path(pdf).is_file():
        return 3

    token = _env("TELEGRAM_BOT_TOKEN")
    chat_id = _env("TELEGRAM_GROUP_ALLOWED_CHATS")
    if not token:
        print("ERROR: TELEGRAM_BOT_TOKEN not found in profile .env.")
        return 4

    # Idempotency: never deliver the SAME analysis twice (the two per-topic Michael sessions
    # can both reach delivery). Hash the analysis content; skip if delivered in the last 30 min.
    import hashlib, time
    body = pathlib.Path(md_path).read_text(encoding="utf-8")
    digest = hashlib.sha256(body.encode("utf-8")).hexdigest()[:16]
    lock = PROFILE_DIR / "workspace" / "contracts" / ".delivered.json"
    try:
        prev = json.loads(lock.read_text(encoding="utf-8"))
    except Exception:
        prev = {}
    now = int(time.time())
    if prev.get("digest") == digest and (now - int(prev.get("ts", 0))) < 1800:
        print(f"SKIP: această analiză a fost deja livrată acum {now - int(prev.get('ts', 0))}s. "
              "Nu o retrimit (anti-duplicat).")
        return 0

    caption = _build_caption(a.decision, a.summary, a.intro)
    ok = _send_document(token, chat_id, caption, pdf)
    if ok:
        try:
            lock.write_text(json.dumps({"digest": digest, "ts": now}), encoding="utf-8")
        except Exception:
            pass
    if not ok:
        print("ERROR: delivery failed — PDF was built but not posted.")
        print(f"PDF:{pdf}")
        return 5

    print(f"DELIVERED: posted verdict + PDF to General. PDF={pdf}")
    print("DONE — do NOT post anything else to General or Juridic.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
