#!/usr/bin/env python3
"""Reply to an incoming email ON THE SAME THREAD, identified only by its inbox UID. stdlib-only.

check_inbox.py saves each new email's metadata to <profile>/cache/inbox/<UID>.json (sender,
Message-ID, subject). This reads that file and sends a proper threaded reply:
  To = original sender · Subject = "Re: <subject>" (no double Re:) ·
  In-Reply-To / References = the original Message-ID  → mail clients thread it.

So the secretary never starts a disconnected new email when answering someone. Credentials come
from <profile>/.env (MAILBOX_* — App Password). Supports --cc and --attachment.

Usage:
  reply_email.py --uid 12 --body "Mulțumim, confirmăm pentru luni."
  reply_email.py --uid 12 --body-file reply.txt --cc boss@x.com --attachment oferta.pdf
"""
import argparse
import json
import mimetypes
import os
import pathlib
import smtplib
import ssl
import sys
from email.message import EmailMessage
from email.utils import formatdate, make_msgid


def _profile_home():
    env = os.environ.get("HERMES_HOME")
    if env:
        return pathlib.Path(env)
    try:
        return pathlib.Path(__file__).resolve().parents[3]
    except Exception:
        return pathlib.Path.home() / ".hermes"


HOME = _profile_home()


def _env(key, default=None):
    f = HOME / ".env"
    try:
        for line in f.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line.startswith("#") or "=" not in line:
                continue
            k, _, v = line.partition("=")
            if k.strip() == key:
                return v.strip().strip('"').strip("'")
    except Exception:
        pass
    return default


def _attach(msg, paths):
    for att in paths or []:
        p = pathlib.Path(att)
        if not p.exists():
            print(f"ERROR: attachment not found: {p}")
            sys.exit(2)
        ctype, encoding = mimetypes.guess_type(str(p))
        if ctype is None or encoding is not None:
            ctype = "application/octet-stream"
        maintype, subtype = ctype.split("/", 1)
        msg.add_attachment(p.read_bytes(), maintype=maintype, subtype=subtype, filename=p.name)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--uid", required=True, help="inbox UID of the email to reply to")
    ap.add_argument("--cc", action="append")
    ap.add_argument("--body")
    ap.add_argument("--body-file")
    ap.add_argument("--attachment", action="append")
    a = ap.parse_args()

    meta_f = HOME / "cache" / "inbox" / f"{a.uid}.json"
    if not meta_f.exists():
        print(f"ERROR: no saved metadata for UID {a.uid} ({meta_f}). "
              "Run check_inbox.py first, or send a new email with send_email.py instead.")
        sys.exit(2)
    meta = json.loads(meta_f.read_text(encoding="utf-8"))
    to_addr = meta.get("from_addr")
    orig_subj = (meta.get("subject") or "").strip()
    msgid = (meta.get("message_id") or "").strip()
    if not to_addr:
        print(f"ERROR: no sender address stored for UID {a.uid}.")
        sys.exit(2)

    if a.body_file:
        body = pathlib.Path(a.body_file).read_text(encoding="utf-8")
    elif a.body is not None:
        body = a.body
    else:
        print("ERROR: provide --body or --body-file")
        sys.exit(2)

    subj = orig_subj if orig_subj[:3].lower() == "re:" else (f"Re: {orig_subj}" if orig_subj else "Re:")

    addr = _env("MAILBOX_ADDRESS")
    pwd = _env("MAILBOX_PASSWORD")
    host = _env("MAILBOX_SMTP_HOST", "smtp.mail.yahoo.com")
    port = int(_env("MAILBOX_SMTP_PORT", "465") or 465)
    if not addr or not pwd or pwd.startswith("__"):
        print("ERROR: MAILBOX_ADDRESS / MAILBOX_PASSWORD missing in .env (App Password).")
        sys.exit(2)

    msg = EmailMessage()
    msg["From"] = addr
    msg["To"] = to_addr
    if a.cc:
        msg["Cc"] = ", ".join(a.cc)
    msg["Subject"] = subj
    msg["Date"] = formatdate(localtime=True)
    msg["Message-ID"] = make_msgid()
    if msgid:
        msg["In-Reply-To"] = msgid
        msg["References"] = msgid
    msg.set_content(body)
    _attach(msg, a.attachment)

    ctx = ssl.create_default_context()
    try:
        if port == 465:
            with smtplib.SMTP_SSL(host, port, context=ctx, timeout=30) as s:
                s.login(addr, pwd)
                s.send_message(msg)
        else:
            with smtplib.SMTP(host, port, timeout=30) as s:
                s.ehlo(); s.starttls(context=ctx); s.login(addr, pwd)
                s.send_message(msg)
    except Exception as e:
        print(f"ERROR: failed to send reply: {e}")
        sys.exit(1)

    print(f"REPLY_SENT ✓ to={to_addr} subject={subj!r} (threaded on UID {a.uid})")


if __name__ == "__main__":
    main()
