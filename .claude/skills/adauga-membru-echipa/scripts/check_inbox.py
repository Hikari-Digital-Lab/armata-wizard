#!/usr/bin/env python3
"""One pass over Erin's Yahoo INBOX: find NEW mail and wake Erin on Telegram.

For each genuinely-new message (UID greater than a stored baseline, never processed
before) it posts a wake-up into the Secretariat topic via the CEO's bot token, with an
EXCLUSIVE @erin mention. Because the mention is exclusive, ONLY Erin's gateway reacts —
the free CEO ignores the raw dump. Erin then FILTERS: she reports only the important mail
to the CEO (a plain message he relays to the human), and stays silent on promo/spam.

It does NOT mark messages \\Seen on the server (BODY.PEEK), so the human's own unread
state in Yahoo is untouched. Dedup + baseline are kept in a local state file so history
is never re-flooded on (re)start.

Reads from <HERMES_HOME>/.env:
  EMAIL_ADDRESS, EMAIL_PASSWORD, EMAIL_IMAP_HOST (imap.mail.yahoo.com), EMAIL_IMAP_PORT (993)
  TELEGRAM_NOTIFY_TOKEN (CEO's bot token), TELEGRAM_GROUP_ALLOWED_CHATS, SECRETARIAT_THREAD_ID,
  ERIN_MENTION (@erin_..._bot)

Usage:
  check_inbox.py            # one pass
  check_inbox.py --baseline # just (re)set the baseline to current max UID, post nothing
"""
import argparse
import email
import imaplib
import json
import os
import pathlib
import re
import sys
import urllib.parse
import urllib.request
from email.header import decode_header, make_header

HERMES_HOME = pathlib.Path(os.environ.get("HERMES_HOME") or pathlib.Path.home() / ".hermes")
STATE = HERMES_HOME / "cache" / "erin_inbox_state.json"


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


def _load_state():
    try:
        return json.loads(STATE.read_text(encoding="utf-8"))
    except Exception:
        return {"baseline": 0, "processed": []}


def _save_state(st):
    STATE.parent.mkdir(parents=True, exist_ok=True)
    # keep the processed list bounded
    st["processed"] = sorted(set(st.get("processed", [])))[-500:]
    STATE.write_text(json.dumps(st), encoding="utf-8")


def _dec(s):
    try:
        return str(make_header(decode_header(s or "")))
    except Exception:
        return s or ""


def _extract_addr(raw):
    """Pull the bare email address out of a From header value."""
    from email.utils import parseaddr
    return parseaddr(_dec(raw))[1]


def _body_text(msg, limit=1500):
    """Best-effort plain-text snippet of the email body."""
    text = ""
    if msg.is_multipart():
        for part in msg.walk():
            if part.get_content_type() == "text/plain" and "attachment" not in str(
                part.get("Content-Disposition", "")
            ):
                try:
                    text = part.get_payload(decode=True).decode(
                        part.get_content_charset() or "utf-8", "replace"
                    )
                    break
                except Exception:
                    continue
    else:
        try:
            text = msg.get_payload(decode=True).decode(
                msg.get_content_charset() or "utf-8", "replace"
            )
        except Exception:
            text = ""
    text = re.sub(r"\n{3,}", "\n\n", text).strip()
    return text[:limit]


def _tg_send(token, chat_id, thread_id, text):
    payload = {"chat_id": chat_id, "text": text}
    if thread_id and str(thread_id) not in ("", "None", "1"):
        payload["message_thread_id"] = str(thread_id)
    data = urllib.parse.urlencode(payload).encode()
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    with urllib.request.urlopen(url, data=data, timeout=20) as r:
        return json.loads(r.read().decode("utf-8")).get("ok", False)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--baseline", action="store_true", help="reset baseline to current max UID, post nothing")
    a = ap.parse_args()

    addr = _env("MAILBOX_ADDRESS") or _env("EMAIL_ADDRESS")
    pwd = _env("MAILBOX_PASSWORD") or _env("EMAIL_PASSWORD")
    host = _env("MAILBOX_IMAP_HOST") or _env("EMAIL_IMAP_HOST", "imap.mail.yahoo.com")
    port = int(_env("MAILBOX_IMAP_PORT") or _env("EMAIL_IMAP_PORT", "993") or 993)
    if not addr or not pwd or pwd.startswith("__"):
        print("ERROR: EMAIL_ADDRESS / EMAIL_PASSWORD missing in .env (Yahoo App Password needed).")
        sys.exit(2)

    token = _env("TELEGRAM_NOTIFY_TOKEN")
    chat_id = (_env("TELEGRAM_GROUP_ALLOWED_CHATS") or "").split(",")[0].strip()
    thread = _env("SECRETARIAT_THREAD_ID")
    mention = _env("ERIN_MENTION", "@erin_hannon_office_bot")

    try:
        M = imaplib.IMAP4_SSL(host, port)
        M.login(addr, pwd)
        M.select("INBOX")
    except Exception as e:
        print(f"ERROR: IMAP login/select failed: {e}")
        sys.exit(1)

    typ, data = M.uid("search", None, "ALL")
    uids = [int(x) for x in data[0].split()] if data and data[0] else []
    st = _load_state()
    baseline = int(st.get("baseline", 0))
    processed = set(st.get("processed", []))

    if a.baseline or baseline == 0:
        # First ever run (or explicit reset): adopt current max as baseline, post nothing.
        st["baseline"] = max(uids) if uids else 0
        _save_state(st)
        try:
            M.logout()
        except Exception:
            pass
        print(f"BASELINE set to UID {st['baseline']} (no notifications sent).")
        return

    new = [u for u in uids if u > baseline and u not in processed]
    sent = 0
    for u in sorted(new):
        try:
            typ, md = M.uid("fetch", str(u), "(BODY.PEEK[])")
            raw = md[0][1]
            msg = email.message_from_bytes(raw)
        except Exception as e:
            print(f"WARN: fetch UID {u} failed: {e}")
            processed.add(u)
            continue
        frm = _dec(msg.get("From"))
        subj = _dec(msg.get("Subject"))
        date = _dec(msg.get("Date"))
        msgid = (msg.get("Message-ID") or "").strip()
        from_addr = _extract_addr(msg.get("From") or "")
        snippet = _body_text(msg)
        # Persist per-UID metadata so a reply can be threaded from just the UID.
        meta_dir = HERMES_HOME / "cache" / "inbox"
        meta_dir.mkdir(parents=True, exist_ok=True)
        (meta_dir / f"{u}.json").write_text(json.dumps({
            "uid": u, "message_id": msgid, "from": frm, "from_addr": from_addr,
            "subject": subj, "date": date,
        }), encoding="utf-8")
        wake = (
            f"{mention} 📨 MAIL NOU (UID {u}). Ești secretara la recepție — NU te prezenta, NU saluta, "
            f"NU răspunde la conținutul emailului. Tu DOAR trieezi pentru Michael:\n"
            f"• dacă e IMPORTANT pentru birou → trimite-i lui Michael EXACT un mesaj în formatul:\n"
            f"   „📬 Michael, email nou (UID {u}) de la <expeditor>: <rezumat într-o frază>.\"\n"
            f"• dacă e promo / newsletter / reclamă / notificare automată / spam → nu scrie NIMIC, oprește-te.\n"
            f"(Răspunsul la email îl trimite Michael mai târziu prin tine, cu UID {u}. Tu acum doar raportezi.)\n"
            f"--- emailul ---\n"
            f"De la: {frm}\n"
            f"Subiect: {subj}\n"
            f"Data: {date}\n"
            f"{snippet}"
        )
        try:
            ok = _tg_send(token, chat_id, thread, wake[:4000])
        except Exception as e:
            print(f"ERROR: Telegram wake-up failed for UID {u}: {e}")
            break  # don't advance; retry next pass
        if not ok:
            print(f"ERROR: Telegram rejected wake-up for UID {u}.")
            break
        processed.add(u)
        sent += 1
        print(f"NOTIFIED Erin about UID {u} | {frm} | {subj}")

    if uids:
        st["baseline"] = max(baseline, max(uids))
    st["processed"] = list(processed)
    _save_state(st)
    try:
        M.logout()
    except Exception:
        pass
    print(f"DONE: {sent} new mail(s) sent to Erin. baseline={st['baseline']}")


if __name__ == "__main__":
    main()
