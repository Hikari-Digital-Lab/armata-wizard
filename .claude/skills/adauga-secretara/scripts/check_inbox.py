#!/usr/bin/env python3
"""One pass over the secretary's INBOX (Gmail/Yahoo): find NEW mail and wake the secretary.

For each genuinely-new message (UID > a stored baseline, never processed) it:
  1. saves metadata to <profile>/cache/inbox/<UID>.json (sender, Message-ID, subject) so a
     reply can be threaded from just the UID,
  2. downloads any attachments to <profile>/cache/inbox/attachments/<UID>/,
  3. posts a DIRECTIVE wake-up into the secretary's topic via the CEO's bot token
     (TELEGRAM_NOTIFY_TOKEN), with an EXCLUSIVE @secretary mention.

Why the directive lives in the WAKE-UP (not only the SOUL): on a fresh session Gemini tends to
introduce itself / answer the email instead of reporting. Putting the exact instruction + report
format in the message the model actually reads fixes that. Because the mention is exclusive, ONLY
the secretary reacts — the free CEO ignores the raw dump; only her FILTERED report reaches him.

It uses BODY.PEEK (does NOT mark \\Seen on the server) and keeps baseline+dedup locally so history
is never re-flooded on (re)start. On the very first run it adopts the current max UID as baseline
and posts nothing.

Reads from <profile>/.env:
  MAILBOX_ADDRESS, MAILBOX_PASSWORD, MAILBOX_IMAP_HOST, MAILBOX_IMAP_PORT (993)
  TELEGRAM_NOTIFY_TOKEN (CEO's bot token), TELEGRAM_GROUP_ALLOWED_CHATS, SECRETARIAT_THREAD_ID,
  SECRETARY_MENTION (@<secretary>_bot)

Usage:
  check_inbox.py            # one pass
  check_inbox.py --baseline # (re)set the baseline to current max UID, post nothing
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
from email.utils import parseaddr


def _profile_home():
    env = os.environ.get("HERMES_HOME")
    if env:
        return pathlib.Path(env)
    try:
        return pathlib.Path(__file__).resolve().parents[3]
    except Exception:
        return pathlib.Path.home() / ".hermes"


HOME = _profile_home()
STATE = HOME / "cache" / "secretary_inbox_state.json"


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


def _load_state():
    try:
        return json.loads(STATE.read_text(encoding="utf-8"))
    except Exception:
        return {"baseline": 0, "processed": []}


def _save_state(st):
    STATE.parent.mkdir(parents=True, exist_ok=True)
    st["processed"] = sorted(set(st.get("processed", [])))[-500:]
    STATE.write_text(json.dumps(st), encoding="utf-8")


def _dec(s):
    try:
        return str(make_header(decode_header(s or "")))
    except Exception:
        return s or ""


def _body_text(msg, limit=1500):
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
            text = msg.get_payload(decode=True).decode(msg.get_content_charset() or "utf-8", "replace")
        except Exception:
            text = ""
    return re.sub(r"\n{3,}", "\n\n", text).strip()[:limit]


def _save_attachments(msg, uid):
    paths = []
    if not msg.is_multipart():
        return paths
    out = HOME / "cache" / "inbox" / "attachments" / str(uid)
    for part in msg.walk():
        disp = str(part.get("Content-Disposition", ""))
        fn = part.get_filename()
        if fn and ("attachment" in disp or "inline" in disp):
            try:
                out.mkdir(parents=True, exist_ok=True)
                safe = re.sub(r"[^\w.\-]+", "_", _dec(fn)) or "file"
                p = out / safe
                p.write_bytes(part.get_payload(decode=True) or b"")
                paths.append(str(p))
            except Exception:
                continue
    return paths


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

    addr = _env("MAILBOX_ADDRESS")
    pwd = _env("MAILBOX_PASSWORD")
    host = _env("MAILBOX_IMAP_HOST", "imap.mail.yahoo.com")
    port = int(_env("MAILBOX_IMAP_PORT", "993") or 993)
    if not addr or not pwd or pwd.startswith("__"):
        print("ERROR: MAILBOX_ADDRESS / MAILBOX_PASSWORD missing in .env (App Password needed).")
        sys.exit(2)

    token = _env("TELEGRAM_NOTIFY_TOKEN")
    chat_id = (_env("TELEGRAM_GROUP_ALLOWED_CHATS") or "").split(",")[0].strip()
    thread = _env("SECRETARIAT_THREAD_ID")
    mention = _env("SECRETARY_MENTION", "@secretara_bot")

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
            msg = email.message_from_bytes(md[0][1])
        except Exception as e:
            print(f"WARN: fetch UID {u} failed: {e}")
            processed.add(u)
            continue
        frm = _dec(msg.get("From"))
        subj = _dec(msg.get("Subject"))
        date = _dec(msg.get("Date"))
        msgid = (msg.get("Message-ID") or "").strip()
        from_addr = parseaddr(frm)[1]
        snippet = _body_text(msg)
        atts = _save_attachments(msg, u)

        meta_dir = HOME / "cache" / "inbox"
        meta_dir.mkdir(parents=True, exist_ok=True)
        (meta_dir / f"{u}.json").write_text(json.dumps({
            "uid": u, "message_id": msgid, "from": frm, "from_addr": from_addr,
            "subject": subj, "date": date, "attachments": atts,
        }), encoding="utf-8")

        att_line = ""
        if atts:
            att_line = "Atașamente (deja descărcate): " + "; ".join(atts) + "\n"
        wake = (
            f"{mention} 📨 MAIL NOU (UID {u}). Ești secretara la recepție — NU te prezenta, NU saluta, "
            f"NU răspunde la conținutul emailului. Tu DOAR trieezi pentru CEO:\n"
            f"• dacă e IMPORTANT pentru birou → trimite-i CEO-ului EXACT un mesaj în formatul:\n"
            f"   „📬 email nou (UID {u}) de la <expeditor>: <rezumat într-o frază>.\"\n"
            f"• dacă e promo / newsletter / reclamă / notificare automată / spam → nu scrie NIMIC, oprește-te.\n"
            f"(Răspunsul îl trimite CEO-ul mai târziu prin tine, cu UID {u}. Tu acum doar raportezi.)\n"
            f"--- emailul ---\n"
            f"De la: {frm}\nSubiect: {subj}\nData: {date}\n{att_line}{snippet}"
        )
        try:
            ok = _tg_send(token, chat_id, thread, wake[:4000])
        except Exception as e:
            print(f"ERROR: Telegram wake-up failed for UID {u}: {e}")
            break
        if not ok:
            print(f"ERROR: Telegram rejected wake-up for UID {u}.")
            break
        processed.add(u)
        sent += 1
        print(f"NOTIFIED secretary about UID {u} | {frm} | {subj}" + (f" | {len(atts)} attachment(s)" if atts else ""))

    if uids:
        st["baseline"] = max(baseline, max(uids))
    st["processed"] = list(processed)
    _save_state(st)
    try:
        M.logout()
    except Exception:
        pass
    print(f"DONE: {sent} new mail(s) sent to the secretary. baseline={st['baseline']}")


if __name__ == "__main__":
    main()
