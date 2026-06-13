from flask import Flask, request
import os
import json
import re
import requests
from supabase import create_client

app = Flask(__name__)

# =====================
# CONFIG
# =====================
SUPABASE_URL = os.environ["SUPABASE_URL"]
SUPABASE_KEY = os.environ["SUPABASE_KEY"]
BOT_TOKEN = os.environ["BOT_TOKEN"]

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# =====================
# RUBRICA
# =====================
def load_rubrica():
    try:
        with open("rubrica.json", "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return {}

rubrica = load_rubrica()

# username -> nome
def to_name(username):
    username = username.lower().replace("@", "")
    for nome, tag in rubrica.items():
        if tag.lower().replace("@", "") == username:
            return nome
    return username

# =====================
# UTENTI ATTESI DAL MESSAGGIO
# =====================
def extract_expected_users(text):
    return set(re.findall(r"@([a-zA-Z0-9_]+)", text.lower()))

# =====================
# SUPABASE SAVE
# =====================
def save_response(date, username, status):
    supabase.table("responses").upsert({
        "date": date,
        "username": username,
        "status": status
    }).execute()

# =====================
# SUPABASE GET
# =====================
def get_responses(date):
    res = supabase.table("responses").select("*").eq("date", date).execute()
    return {r["username"]: r["status"] for r in res.data}

# =====================
# WEBHOOK
# =====================
@app.route("/", methods=["POST"])
def webhook():

    data = request.get_json(silent=True)

    if not data or "callback_query" not in data:
        return "ok", 200

    cb = data["callback_query"]

    cb_id = cb["id"]
    chat_id = cb["message"]["chat"]["id"]
    msg_id = cb["message"]["message_id"]

    # username telegram
    username = cb["from"].get("username")
    if username:
        username = username.lower()
    else:
        username = str(cb["from"]["id"])

    action, date = cb["data"].split("|")

    text_message = cb["message"]["text"]

    # =====================
    # UTENTI ASSEGNATI
    # =====================
    expected_users = extract_expected_users(text_message)

    # =====================
    # BLOCCO NON ASSEGNATI
    # =====================
    if username not in expected_users:

        requests.post(
            f"https://api.telegram.org/bot{BOT_TOKEN}/answerCallbackQuery",
            data={
                "callback_query_id": cb_id,
                "text": "Non sei assegnato a questo servizio 🚫"
            }
        )
        return "ok", 200

    # =====================
    # SALVA RISPOSTA
    # =====================
    save_response(date, username, action)

    responses = get_responses(date)

    responded_users = set(responses.keys())
    missing = expected_users - responded_users

    # =====================
    # LISTE NOMI
    # =====================
    ok_users = [to_name(u) for u, s in responses.items() if s == "ok"]
    no_users = [to_name(u) for u, s in responses.items() if s != "ok"]

    # =====================
    # MESSAGGIO
    # =====================
    status_text = "\n\n📋 RISPOSTE\n\n"

    status_text += "✅ OK:\n"
    status_text += "\n".join(ok_users) if ok_users else "-"

    status_text += "\n\n❌ NON POSSO:\n"
    status_text += "\n".join(no_users) if no_users else "-"

    status_text += f"\n\n⏳ Mancano {len(missing)} risposte"

    # =====================
    # CHIUSURA AUTOMATICA
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
    original = text_message

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


@app.route("/", methods=["GET"])
def home():
    return "OK", 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
