#!/usr/bin/env python3
"""Send an email from Erin's Yahoo mailbox. Cross-platform, stdlib-only.

Reads the mailbox credentials from <HERMES_HOME>/.env:
  EMAIL_ADDRESS, EMAIL_PASSWORD (Yahoo App Password — NOT the normal password),
  EMAIL_SMTP_HOST (default smtp.mail.yahoo.com), EMAIL_SMTP_PORT (default 465 / SSL).

This is the ONLY way Erin sends mail — the content is provided by Michael (the CEO),
already approved by the human. Erin runs this script verbatim with the approved fields.

Usage:
  send_email.py --to client@example.com --subject "Subiect" --body "Text..."
  send_email.py --to a@x.com --to b@y.com --subject "..." --body-file /path/body.txt
"""
import argparse
import os
import pathlib
import smtplib
import ssl
import sys
from email.message import EmailMessage
from email.utils import formatdate, make_msgid

HERMES_HOME = pathlib.Path(os.environ.get("HERMES_HOME") or pathlib.Path.home() / ".hermes")


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
    ap.add_argument("--to", action="append", required=True, help="recipient (repeatable)")
    ap.add_argument("--subject", required=True)
    ap.add_argument("--body")
    ap.add_argument("--body-file")
    ap.add_argument("--reply-to")
    a = ap.parse_args()

    addr = _env("MAILBOX_ADDRESS") or _env("EMAIL_ADDRESS")
    pwd = _env("MAILBOX_PASSWORD") or _env("EMAIL_PASSWORD")
    host = _env("MAILBOX_SMTP_HOST") or _env("EMAIL_SMTP_HOST", "smtp.mail.yahoo.com")
    port = int(_env("MAILBOX_SMTP_PORT") or _env("EMAIL_SMTP_PORT", "465") or 465)
    if not addr or not pwd or pwd.startswith("__"):
        print("ERROR: EMAIL_ADDRESS / EMAIL_PASSWORD missing in .env (Yahoo App Password needed).")
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
    msg["Subject"] = a.subject
    msg["Date"] = formatdate(localtime=True)
    msg["Message-ID"] = make_msgid()
    if a.reply_to:
        msg["Reply-To"] = a.reply_to
    msg.set_content(body)

    ctx = ssl.create_default_context()
    try:
        if port == 465:
            with smtplib.SMTP_SSL(host, port, context=ctx, timeout=30) as s:
                s.login(addr, pwd)
                s.send_message(msg)
        else:
            with smtplib.SMTP(host, port, timeout=30) as s:
                s.ehlo()
                s.starttls(context=ctx)
                s.login(addr, pwd)
                s.send_message(msg)
    except Exception as e:
        print(f"ERROR: failed to send email: {e}")
        sys.exit(1)

    print(f"EMAIL_SENT ✓ to={', '.join(a.to)} subject={a.subject!r}")


if __name__ == "__main__":
    main()
