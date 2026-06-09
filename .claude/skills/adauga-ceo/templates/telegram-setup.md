# Telegram foundation — create the group with Topics + the CEO bot

Guide the user through these (pause and collect values via AskUserQuestion; token/group id → "Other").

## A. Create the bot (BotFather)
1. Open **@BotFather** → `/newbot` → display name (e.g. "Michael Scott") + username ending in
   `bot` (e.g. `michael_scott_dm_bot`). **Save the token.**
2. Still in BotFather, on this bot:
   - `/setprivacy` → **Disable** (so it sees all messages in the group), and
   - **Group Privacy / Bot-to-Bot Communication Mode → ON** (so it can later talk with worker bots).

## B. Create the group WITH Topics (forum mode)
3. In Telegram, create a **new group** (add yourself / a placeholder, you can remove later).
4. Open the group → **Edit → Topics → enable** (this turns it into a forum supergroup with a
   **General** topic). On mobile: group settings → toggle "Topics".
   - Enabling Topics may upgrade the group to a supergroup and change its id — that's fine, we read
     the final id below.
5. Add your **CEO bot** to the group and **promote it to admin** (so it can read/manage).

## C. Get the group id
6. Send any message in the **General** topic of the group.
7. Read the id with the bot token:
   ```bash
   curl -s "https://api.telegram.org/bot<TOKEN>/getUpdates" \
     | python3 -c "import sys,json;[print('chat',m.get('message',{}).get('chat',{}).get('id'),'thread',m.get('message',{}).get('message_thread_id')) for m in json.load(sys.stdin).get('result',[])]"
   ```
   The `chat` id (a `-100…` number) is your **<GROUP_ID>**. The **General** topic is id **1**
   (messages in General usually have no `message_thread_id`, or thread `1`).

## D. Verify the bot
```bash
curl -s "https://api.telegram.org/bot<TOKEN>/getMe"
```
Confirm `ok:true` and note the real `username`.

> Only the General topic is needed now. Worker topics (Art, Copywriting, …) are created later by
> the adauga-artist / adauga-copywriter skills.
