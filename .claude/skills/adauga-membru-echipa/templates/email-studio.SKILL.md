---
name: email-studio
description: "Trimite și verifică emailuri pe adresa Yahoo a biroului. Erin folosește send_email.py ca să trimită un email (conținut aprobat, primit de la Michael) și check_inbox.py ca să verifice manual inbox-ul. Recepția automată o face watcher-ul (pornit cu echipa)."
version: 1.0.0
license: MIT
platforms: [linux, darwin, win32]
metadata:
  hermes:
    tags: [Email, Yahoo, Secretariat, Workflow]
---

# email-studio — mailbox-ul Yahoo al lui Erin

Toate scripturile rulează cu venv-python (cale absolută):
`<HERMES_HOME>/hermes-agent/venv/bin/python`
(`<HERMES_HOME>` = calea absolută a dir-ului Hermes — `~/.hermes` expandat.)

## A) RĂSPUNS la un email primit (pe ACELAȘI thread) — folosește când Michael zice „răspunde-i"
Dacă Michael îți cere să RĂSPUNZI unui email care a venit în inbox, NU trimite un email nou —
răspunde pe thread-ul original cu `reply_email.py`, dându-i DOAR `UID`-ul emailului (din mesajul
de trezire `📨 MAIL NOU (UID N)`). Scriptul pune singur destinatarul corect, „Re: <subiect>" și
header-ele de threading (In-Reply-To/References). Pentru text multi-rând, salvează-l cu `write_file`:

```bash
<HERMES_HOME>/hermes-agent/venv/bin/python \
  <HERMES_HOME>/profiles/erin/skills/email-studio/scripts/reply_email.py \
  --uid N --body-file "<HERMES_HOME>/profiles/erin/workspace/erin_reply.txt"
```
- Output `REPLY_SENT ✓ ...` → răspunsul a plecat pe thread; confirmă scurt în topicul tău.
- Output `ERROR: ...` → NU a plecat; spune-i lui Michael ce s-a întâmplat.

## B) Email NOU (când Michael îți dă un destinatar nou, nu un răspuns)
Conținutul vine de la Michael și e deja aprobat. Pentru text multi-rând, salvează-l cu `write_file`
și folosește `--body-file`:

```bash
<HERMES_HOME>/hermes-agent/venv/bin/python \
  <HERMES_HOME>/profiles/erin/skills/email-studio/scripts/send_email.py \
  --to "client@example.com" --subject "Subiectul exact" --body-file "<HERMES_HOME>/profiles/erin/workspace/erin_body.txt"
```
- Output `EMAIL_SENT ✓ ...` → emailul a plecat; confirmă scurt în topicul tău.
- Output `ERROR: ...` → NU a plecat; spune-i lui Michael ce s-a întâmplat, nu reîncerca la nesfârșit.

**Regula de aur:** răspuns la cineva care ne-a scris ⇒ `reply_email.py --uid N` (thread); inițiezi un
email către cineva nou ⇒ `send_email.py`. Niciodată email nou ca răspuns — e confuzant pentru destinatar.

## Verificare inbox la cerere
```bash
<HERMES_HOME>/hermes-agent/venv/bin/python \
  <HERMES_HOME>/profiles/erin/skills/email-studio/scripts/check_inbox.py
```
Postează mailurile noi (dacă există) ca mesaje de trezire către tine în Secretariat.

## Recepție automată (watcher)
`inbox_watcher.py` rulează în fundal (pornit/oprit de `manage.py` împreună cu echipa) și
verifică Yahoo la fiecare `EMAIL_POLL_INTERVAL` secunde. La un mail nou îți trimite o
trezire `📨 MAIL NOU ...` cu mențiune exclusivă `@erin` (doar tu reacționezi, Michael nu
vede dump-ul brut). TU decizi: important pentru noi → raportezi lui Michael; promo/newsletter/
spam → taci.

## Reguli
- Singurul mod de a trimite mail e `send_email.py`. Nu inventa alt canal.
- Credențialele Yahoo se iau singure din `.env` (App Password). Nu le scrie nicăieri.
- Tu ești filtrul: nu inunda echipa cu promoții. Raportează doar ce contează pentru birou.
