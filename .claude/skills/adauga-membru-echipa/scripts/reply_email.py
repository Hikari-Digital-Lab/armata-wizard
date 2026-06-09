#!/usr/bin/env python3
"""Reply to an incoming email ON THE SAME THREAD, identified only by its inbox UID.

The watcher (check_inbox.py) saves each new email's metadata to
<HERMES_HOME>/cache/inbox/<UID>.json (sender, Message-ID, subject). This script reads
that file and sends a proper threaded reply:
  - To       = the original sender
  - Subject  = "Re: <original subject>" (no double "Re:")
  - In-Reply-To / References = the original Message-ID  → mail clients thread it

So Erin never starts a new disconnected email when she's answering someone — she replies
in-thread, like a real secretary. Credentials come from <HERMES_HOME>/.env (Yahoo App Pwd).

Usage:
  reply_email.py --uid 12 --body "Mulțumim pentru mesaj, confirmăm pentru luni."
  reply_email.py --uid 12 --body-file /tmp/erin_reply.txt
"""
import argparse
import json
import os
import pathlib
import smtplib
import ssl
import sys
from email.message import EmailMessage
from email.utils import formatdate, make_msgid

HERMES_HOME = pathlib.Path(os.environ.get("HERMES_HOME") or pathlib.Path.home() / ".hermes" / "profiles" / "erin")


def _env(key, default=None):
    f = HERMES_HOME / ".env"
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


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--uid", required=True, help="inbox UID of the email to reply to")
    ap.add_argument("--body")
    ap.add_argument("--body-file")
    a = ap.parse_args()

    meta_f = HERMES_HOME / "cache" / "inbox" / f"{a.uid}.json"
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

    subj = orig_subj if orig_subj[:3].lower() == "re:" else f"Re: {orig_subj}" if orig_subj else "Re:"

    addr = _env("MAILBOX_ADDRESS") or _env("EMAIL_ADDRESS")
    pwd = _env("MAILBOX_PASSWORD") or _env("EMAIL_PASSWORD")
    host = _env("MAILBOX_SMTP_HOST") or _env("EMAIL_SMTP_HOST", "smtp.mail.yahoo.com")
    port = int(_env("MAILBOX_SMTP_PORT") or _env("EMAIL_SMTP_PORT", "465") or 465)
    if not addr or not pwd or pwd.startswith("__"):
        print("ERROR: MAILBOX_ADDRESS / MAILBOX_PASSWORD missing in .env (Yahoo App Password).")
        sys.exit(2)

    msg = EmailMessage()
    msg["From"] = addr
    msg["To"] = to_addr
    msg["Subject"] = subj
    msg["Date"] = formatdate(localtime=True)
    msg["Message-ID"] = make_msgid()
    if msgid:
        msg["In-Reply-To"] = msgid
        msg["References"] = msgid
    msg.set_content(body)

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
