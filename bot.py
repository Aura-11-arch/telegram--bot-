import requests
import time
import re

TOKEN = "8354114088:AAGeDFj2NbUkhWWLfDK0moeelCRlP4qAsXA"
URL = f"https://api.telegram.org/bot{TOKEN}/"

last_update = None

warnings = {}
user_messages = {}

stats = {
"messages":0,
"deleted":0,
"banned":0,
"muted":0,
"warnings":0
}

# -------- API --------

def api(method,data=None):

    try:
        r = requests.post(URL+method,data=data,timeout=10)
        return r.json()
    except:
        return {}

def get_updates(offset=None):

    try:
        r = requests.get(
            URL+"getUpdates",
            params={"timeout":60,"offset":offset},
            timeout=70
        )
        return r.json()
    except:
        return {}

# -------- ACTIONS --------

def send(chat,text):

    api("sendMessage",{
    "chat_id":chat,
    "text":text
    })

def delete(chat,msg):

    api("deleteMessage",{
    "chat_id":chat,
    "message_id":msg
    })

    stats["deleted"]+=1

def ban(chat,user):

    api("banChatMember",{
    "chat_id":chat,
    "user_id":user
    })

    stats["banned"]+=1

def unban(chat,user):

    api("unbanChatMember",{
    "chat_id":chat,
    "user_id":user
    })

def kick(chat,user):

    ban(chat,user)
    unban(chat,user)

def mute(chat,user):

    api("restrictChatMember",{
    "chat_id":chat,
    "user_id":user,
    "permissions":'{"can_send_messages":false}'
    })

    stats["muted"]+=1

def unmute(chat,user):

    api("restrictChatMember",{
    "chat_id":chat,
    "user_id":user,
    "permissions":'{"can_send_messages":true}'
    })

# -------- ADMIN CHECK --------

def is_admin(chat,user):

    try:

        r = requests.get(
            URL+"getChatAdministrators",
            params={"chat_id":chat}
        ).json()

        admins = [a["user"]["id"] for a in r["result"]]

        return user in admins

    except:

        return False

# -------- FILTER --------

link_regex = re.compile(
r"(https?://|www\.|t\.me|\.com|\.net|\.org|\.gg|\.io|bit\.ly)",
re.IGNORECASE
)

porn_regex = re.compile(
r"(porn|sex|xvideos|xnxx|pornhub|hentai|nsfw|onlyfans)",
re.IGNORECASE
)

badword_regex = re.compile(
r"(fuck|shit|bitch|asshole|motherfucker|slut|whore|"
r"arschloch|hurensohn|fotze|wichser|nutte|spast|mongo)",
re.IGNORECASE
)

# -------- BOT START --------

try:

    bot = requests.get(URL+"getMe").json()
    BOT_ID = bot["result"]["id"]

    print("Bot gestartet:",bot["result"]["username"])

except:

    print("TOKEN ERROR")
    exit()

# -------- MAIN LOOP --------

print("Bot läuft...")

while True:

    try:

        updates = get_updates(last_update)

        if "result" not in updates:

            time.sleep(1)
            continue

        for update in updates["result"]:

            last_update = update["update_id"] + 1

            if "message" not in update:
                continue

            msg = update["message"]

            chat = msg["chat"]["id"]
            user = msg["from"]["id"]
            text = msg.get("text","").lower()

            stats["messages"]+=1

# -------- BOT PROTECTION --------

            if "new_chat_members" in msg:

                for m in msg["new_chat_members"]:

                    if m.get("is_bot") and m["id"] != BOT_ID:

                        kick(chat,m["id"])
                        send(chat,"🤖 Fremder Bot entfernt")

# -------- LINK FILTER --------

            if text and not is_admin(chat,user):

                if link_regex.search(text):

                    delete(chat,msg["message_id"])
                    send(chat,"🚫 Links sind verboten")

# -------- PORN FILTER --------

            if text and not is_admin(chat,user):

                if porn_regex.search(text):

                    delete(chat,msg["message_id"])
                    send(chat,"🚫 NSFW / Porn Inhalte sind verboten")

# -------- BADWORD FILTER --------

            if text and not is_admin(chat,user):

                if badword_regex.search(text):

                    delete(chat,msg["message_id"])
                    send(chat,"⚠️ Beleidigung entfernt")

# -------- SPAM PROTECTION --------

            now = time.time()

            if user not in user_messages:
                user_messages[user] = []

            user_messages[user].append(now)

            user_messages[user] = [
            t for t in user_messages[user]
            if now - t < 5
            ]

            if len(user_messages[user]) > 6 and not is_admin(chat,user):

                mute(chat,user)
                send(chat,"🚫 Spam erkannt – User gemutet")

# -------- COMMANDS --------

            if text.startswith("/warn") and is_admin(chat,user):

                if "reply_to_message" in msg:

                    target = msg["reply_to_message"]["from"]["id"]

                    warnings[target] = warnings.get(target,0)+1

                    stats["warnings"]+=1

                    send(chat,f"⚠️ Verwarnung ({warnings[target]}/3)")

                    if warnings[target] >= 3:

                        ban(chat,target)
                        send(chat,"🚫 User wegen Warnungen gebannt")

# BAN
            if text.startswith("/ban") and is_admin(chat,user):

                if "reply_to_message" in msg:

                    target = msg["reply_to_message"]["from"]["id"]

                    ban(chat,target)
                    send(chat,"🚫 User gebannt")

# UNBAN
            if text.startswith("/unban") and is_admin(chat,user):

                if "reply_to_message" in msg:

                    target = msg["reply_to_message"]["from"]["id"]

                    unban(chat,target)
                    send(chat,"✅ User entbannt")

# KICK
            if text.startswith("/kick") and is_admin(chat,user):

                if "reply_to_message" in msg:

                    target = msg["reply_to_message"]["from"]["id"]

                    kick(chat,target)
                    send(chat,"👢 User gekickt")

# MUTE
            if text.startswith("/mute") and is_admin(chat,user):

                if "reply_to_message" in msg:

                    target = msg["reply_to_message"]["from"]["id"]

                    mute(chat,target)
                    send(chat,"🔇 User gemutet")

# UNMUTE
            if text.startswith("/unmute") and is_admin(chat,user):

                if "reply_to_message" in msg:

                    target = msg["reply_to_message"]["from"]["id"]

                    unmute(chat,target)
                    send(chat,"🔊 User entmutet")

# DELETE
            if text.startswith("/delete") and is_admin(chat,user):

                if "reply_to_message" in msg:

                    delete(chat,msg["reply_to_message"]["message_id"])

# PURGE
            if text.startswith("/purge") and is_admin(chat,user):

                if "reply_to_message" not in msg:

                    send(chat,"Reply auf eine Nachricht benutzen")
                    continue

                start = msg["reply_to_message"]["message_id"]
                end = msg["message_id"]

                for m in range(start+1,end):

                    delete(chat,m)

                send(chat,"🧹 Nachrichten gelöscht")

# DASHBOARD
            if text.startswith("/dashboard") and is_admin(chat,user):

                text_msg = f"""
📊 BOT DASHBOARD

Messages geprüft: {stats['messages']}
Gelöscht: {stats['deleted']}
Warnungen: {stats['warnings']}
Gebannt: {stats['banned']}
Gemutet: {stats['muted']}
"""

                send(chat,text_msg)

# STATS
            if text.startswith("/stats"):

                text_msg = f"""
🤖 BOT STATS

Messages: {stats['messages']}
Deleted: {stats['deleted']}
Bans: {stats['banned']}
Mutes: {stats['muted']}
Warnings: {stats['warnings']}
"""

                send(chat,text_msg)

    except Exception as e:

        print("Fehler:",e)

        time.sleep(5)