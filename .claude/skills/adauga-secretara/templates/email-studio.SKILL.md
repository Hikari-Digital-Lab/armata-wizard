---
name: email-studio
description: "Trimite și verifică emailuri pe mailbox-ul biroului (Gmail/Yahoo). Secretara folosește send_email.py (email nou), reply_email.py (răspuns pe thread) și check_inbox.py (verificare manuală). Recepția automată o face watcher-ul, pornit cu echipa."
version: 1.0.0
license: MIT
platforms: [linux, darwin, win32]
metadata:
  hermes:
    tags: [Email, Gmail, Yahoo, Secretariat, Workflow]
---

# email-studio — mailbox-ul biroului
# Replace at install: <VENV_PYTHON>, <SECRETARY_PROFILE>.

Toate scripturile rulează cu venv-python (cale absolută): `<VENV_PYTHON>`
Credențialele mailbox (App Password) se iau singure din `.env` (`MAILBOX_*`). Nu le scrie nicăieri.

## A) RĂSPUNS la un email primit (pe ACELAȘI thread) — „răspunde-i"
NU trimite email nou — răspunde pe thread cu `reply_email.py`, dându-i DOAR `UID`-ul (din mesajul
de trezire `📨 MAIL NOU (UID N)`). Scriptul pune singur destinatarul, „Re: <subiect>" și header-ele
de threading. Pentru text multi-rând, salvează-l cu `write_file`:
```bash
<VENV_PYTHON> \
  <HERMES_HOME>/profiles/<SECRETARY_PROFILE>/skills/email-studio/scripts/reply_email.py \
  --uid N --body-file "<HERMES_HOME>/profiles/<SECRETARY_PROFILE>/workspace/secretary_reply.txt"   # opțional: --cc x@y.com --attachment /cale/fisier.pdf
```
- `REPLY_SENT ✓ ...` → răspunsul a plecat pe thread; confirmă scurt în topicul tău.
- `ERROR: ...` → NU a plecat; spune-i CEO-ului.

## B) Email NOU (destinatar nou, nu un răspuns)
```bash
<VENV_PYTHON> \
  <HERMES_HOME>/profiles/<SECRETARY_PROFILE>/skills/email-studio/scripts/send_email.py \
  --to "client@example.com" --subject "Subiect" --body-file "<HERMES_HOME>/profiles/<SECRETARY_PROFILE>/workspace/secretary_body.txt"
  # repetă --to pentru mai mulți; opțional --cc x@y.com --attachment /cale/fisier.pdf
```
- `EMAIL_SENT ✓ ...` → a plecat; confirmă scurt.
- `ERROR: ...` → spune-i CEO-ului, nu reîncerca la nesfârșit.

**Regula de aur:** răspuns la cineva care ne-a scris ⇒ `reply_email.py --uid N` (thread); email către
cineva nou ⇒ `send_email.py`. Niciodată email nou ca răspuns — e confuzant pentru destinatar.

## Verificare inbox la cerere
```bash
<VENV_PYTHON> \
  <HERMES_HOME>/profiles/<SECRETARY_PROFILE>/skills/email-studio/scripts/check_inbox.py
```
Postează mailurile noi (dacă există) ca mesaje de trezire către tine.

## Recepție automată (watcher)
`inbox_watcher.py` rulează în fundal (pornit/oprit de `manage.py` împreună cu echipa) și verifică
mailbox-ul la fiecare `MAILBOX_POLL_INTERVAL` secunde. La un mail nou îți trimite o trezire
`📨 MAIL NOU (UID N)` cu mențiune exclusivă (doar tu reacționezi). TU decizi: important → raportezi
CEO-ului cu UID; promo/spam → taci. Atașamentele primite sunt deja descărcate în
`cache/inbox/attachments/<UID>/`.

## Reguli
- Singurele moduri de a trimite sunt `send_email.py` / `reply_email.py`. Nu inventa alt canal.
- Tu ești filtrul: nu inunda echipa cu promoții. Raportează doar ce contează.
