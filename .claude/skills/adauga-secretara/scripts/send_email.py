#!/usr/bin/env python3
"""Send a NEW email from the secretary's mailbox (Gmail or Yahoo). stdlib-only.

Reads the mailbox credentials from <profile>/.env (resolved from HERMES_HOME or from this
script's own location):
  MAILBOX_ADDRESS, MAILBOX_PASSWORD (App Password — NOT the normal password),
  MAILBOX_SMTP_HOST, MAILBOX_SMTP_PORT (465 = SSL, 587 = STARTTLS).

⚠️ The vars are MAILBOX_* (not EMAIL_*) ON PURPOSE: if they were EMAIL_ADDRESS/EMAIL_PASSWORD,
Hermes would auto-start its NATIVE email gateway and fight this script for the inbox. Keeping
them MAILBOX_* disables the native channel so this deterministic script owns sending.

This is the ONLY way the secretary sends a brand-new email — the content is composed and
approved upstream (by the CEO / human). She runs this verbatim.

Usage:
  send_email.py --to client@example.com --subject "Subiect" --body "Text..."
  send_email.py --to a@x.com --to b@y.com --cc boss@z.com --subject "..." --body-file body.txt
  send_email.py --to a@x.com --subject "..." --body-file b.txt --attachment /path/file.pdf
"""
import argparse
import mimetypes
import os
import pathlib
import smtplib
import ssl
import sys
from email.message import EmailMessage
from email.utils import formatdate, make_msgid


def _profile_home():
    """Resolve the Hermes profile dir: HERMES_HOME, else from this script's path
    (<profile>/skills/email-studio/scripts/send_email.py -> up 3)."""
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


def _send(host, port, addr, pwd, msg):
    ctx = ssl.create_default_context()
    if int(port) == 465:
        with smtplib.SMTP_SSL(host, int(port), context=ctx, timeout=30) as s:
            s.login(addr, pwd)
            s.send_message(msg)
    else:
        with smtplib.SMTP(host, int(port), timeout=30) as s:
            s.ehlo()
            s.starttls(context=ctx)
            s.login(addr, pwd)
            s.send_message(msg)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--to", action="append", required=True, help="recipient (repeatable)")
    ap.add_argument("--cc", action="append", help="cc recipient (repeatable)")
    ap.add_argument("--subject", required=True)
    ap.add_argument("--body")
    ap.add_argument("--body-file")
    ap.add_argument("--reply-to")
    ap.add_argument("--attachment", action="append", help="file path (repeatable)")
    a = ap.parse_args()

    addr = _env("MAILBOX_ADDRESS")
    pwd = _env("MAILBOX_PASSWORD")
    host = _env("MAILBOX_SMTP_HOST", "smtp.mail.yahoo.com")
    port = _env("MAILBOX_SMTP_PORT", "465")
    if not addr or not pwd or pwd.startswith("__"):
        print("ERROR: MAILBOX_ADDRESS / MAILBOX_PASSWORD missing in .env (App Password needed).")
        sys.exit(2)

    if a.body_file:
        body = pathlib.Path(a.body_file).read_text(encoding="utf-8")
    elif a.body is not None:
        body = a.body
    else:
        print("ERROR: provide --body or --body-file")
        sys.exit(2)

    msg = EmailMessage()
    msg["From"] = addr
    msg["To"] = ", ".join(a.to)
    if a.cc:
        msg["Cc"] = ", ".join(a.cc)
    msg["Subject"] = a.subject
    msg["Date"] = formatdate(localtime=True)
    msg["Message-ID"] = make_msgid()
    if a.reply_to:
        msg["Reply-To"] = a.reply_to
    msg.set_content(body)
    _attach(msg, a.attachment)

    try:
        _send(host, port, addr, pwd, msg)
    except Exception as e:
        print(f"ERROR: failed to send email: {e}")
        sys.exit(1)

    extra = f" +cc {', '.join(a.cc)}" if a.cc else ""
    extra += f" +{len(a.attachment)} attachment(s)" if a.attachment else ""
    print(f"EMAIL_SENT ✓ to={', '.join(a.to)}{extra} subject={a.subject!r}")


if __name__ == "__main__":
    main()
