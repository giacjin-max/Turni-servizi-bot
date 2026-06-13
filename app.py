from flask import Flask, request
import os
import json
import requests
import sqlite3
import re

app = Flask(__name__)

BOT_TOKEN = os.environ["BOT_TOKEN"]

DB_NAME = "bot.db"
RUBRICA_FILE = "rubrica.json"

# =====================
# INIT DB
# =====================
def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()

    c.execute("""
    CREATE TABLE IF NOT EXISTS responses (
        date TEXT,
        user TEXT,
        status TEXT,
        PRIMARY KEY (date, user)
    )
    """)

    conn.commit()
    conn.close()

init_db()

# =====================
# RUBRICA
# =====================
def load_rubrica():
    try:
        with open(RUBRICA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return {}

rubrica = load_rubrica()

def to_name(user):
    for k, v in rubrica.items():
        if v.lower().replace("@", "") == user.lower().replace("@", ""):
            return k
    return user

# =====================
# EXPECTED USERS DAL MESSAGGIO
# =====================
def extract_expected_users(text):
    return set(re.findall(r"@([a-zA-Z0-9_]+)", text.lower()))

# =====================
# DB FUNCTIONS
# =====================
def save_response(date, user, status):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()

    c.execute("""
    INSERT OR REPLACE INTO responses VALUES (?, ?, ?)
    """, (date, user, status))

    conn.commit()
    conn.close()

def get_responses(date):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()

    c.execute("SELECT user, status FROM responses WHERE date=?", (date,))
    rows = c.fetchall()

    conn.close()
    return dict(rows)

# =====================
# WEBHOOK
# =====================
@app.route("/", methods=["POST"])
def webhook():

    data = request.get_json(silent=True)
    print("UPDATE:", json.dumps(data, ensure_ascii=False), flush=True)

    if not data or "callback_query" not in data:
        return "ok", 200

    cb = data["callback_query"]

    cb_id = cb["id"]
    chat_id = cb["message"]["chat"]["id"]
    msg_id = cb["message"]["message_id"]

    username = cb["from"].get("username")

    if username:
        username = username.lower()
    else:
        username = str(cb["from"]["id"])

    action, date = cb["data"].split("|")

    # =====================
    # SALVA RISPOSTA
    # =====================
    save_response(date, username, action)

    responses = get_responses(date)

    # =====================
    # UTENTI ATTESI (DAL MESSAGGIO)
    # =====================
    expected_users = extract_expected_users(cb["message"]["text"])

    responded_users = set(responses.keys())
    missing = expected_users - responded_users

    # =====================
    # COSTRUISCI LISTA
    # =====================
    ok_users = [to_name(u) for u, s in responses.items() if s == "ok"]
    no_users = [to_name(u) for u, s in responses.items() if s != "ok"]

    status_text = "\n\n📋 RISPOSTE\n\n"

    status_text += "✅ OK:\n"
    status_text += "\n".join(ok_users) if ok_users else "-"

    status_text += "\n\n❌ NON POSSO:\n"
    status_text += "\n".join(no_users) if no_users else "-"

    status_text += f"\n\n⏳ Mancano {len(missing)} risposte"

    # =====================
    # BOTTONI (CHIUSURA SOLO SE TUTTI HANNO RISPOSTO)
    # =====================
    if len(missing) == 0 and len(expected_users) > 0:
        keyboard = {"inline_keyboard": []}
        status_text += "\n\n🔒 Risposte chiuse"
    else:
        keyboard = {
            "inline_keyboard": [[
                {"text": "✅ OK", "callback_data": f"ok|{date}"},
                {"text": "❌ NON POSSO", "callback_data": f"no|{date}"}
            ]]
        }

    # =====================
    # AGGIORNA MESSAGGIO
    # =====================
    original = cb["message"]["text"]

    if "\n\n📋 RISPOSTE" in original:
        original = original.split("\n\n📋 RISPOSTE")[0]

    requests.post(
        f"https://api.telegram.org/bot{BOT_TOKEN}/editMessageText",
        json={
            "chat_id": chat_id,
            "message_id": msg_id,
            "text": original + status_text,
            "reply_markup": keyboard
        }
    )

    # =====================
    # POPUP
    # =====================
    requests.post(
        f"https://api.telegram.org/bot{BOT_TOKEN}/answerCallbackQuery",
        data={
            "callback_query_id": cb_id,
            "text": "Salvato ✔"
        }
    )

    return "ok", 200

# =====================
# HEALTHCHECK
# =====================
@app.route("/", methods=["GET"])
def home():
    return "Webhook attivo", 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
