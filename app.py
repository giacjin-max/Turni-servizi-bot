import os
import logging
import requests
from flask import Flask, request
from supabase import create_client

app = Flask(__name__)

# =====================
# ENV
# =====================
BOT_TOKEN = os.environ["BOT_TOKEN"]
SUPABASE_URL = os.environ["SUPABASE_URL"]
SUPABASE_KEY = os.environ["SUPABASE_KEY"]

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# =====================
# LOG
# =====================
logging.basicConfig(level=logging.INFO)

# =====================
# SAVE RESPONSE (SUPABASE)
# =====================
def save_response(date, username, status):

    try:
        data = [{
            "date": date,
            "username": username,
            "status": status
        }]

        res = supabase.table("responses") \
            .upsert(data, on_conflict="date,username") \
            .execute()

        print("SUPABASE OK:", res, flush=True)

    except Exception as e:
        print("SUPABASE ERROR:", e, flush=True)

# =====================
# TELEGRAM SEND MESSAGE
# =====================
def send_message(chat_id, text, buttons=None):

    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"

    payload = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "HTML"
    }

    if buttons:
        payload["reply_markup"] = buttons

    requests.post(url, json=payload)

# =====================
# EDIT MESSAGE
# =====================
def edit_message(chat_id, message_id, text):

    url = f"https://api.telegram.org/bot{BOT_TOKEN}/editMessageText"

    payload = {
        "chat_id": chat_id,
        "message_id": message_id,
        "text": text,
        "parse_mode": "HTML"
    }

    requests.post(url, json=payload)

# =====================
# WEBHOOK
# =====================
@app.route("/", methods=["POST"])
def webhook():

    data = request.get_json(silent=True)

    if not data:
        return "ok", 200

    # =====================
    # CALLBACK BUTTON CLICK
    # =====================
    if "callback_query" in data:

        cb = data["callback_query"]

        cb_id = cb["id"]
        chat_id = cb["message"]["chat"]["id"]
        msg_id = cb["message"]["message_id"]

        username = cb["from"].get("username") or str(cb["from"]["id"])
        username = username.lower()

        action, date = cb["data"].split("|")

        print("CLICK:", username, action, date, flush=True)

        # salva su supabase
        save_response(date, username, action)

        # risposta telegram obbligatoria
        requests.post(
            f"https://api.telegram.org/bot{BOT_TOKEN}/answerCallbackQuery",
            data={
                "callback_query_id": cb_id,
                "text": "Salvato ✔"
            }
        )

        # aggiorna messaggio
        edit_message(chat_id, msg_id, f"Risposta registrata ✔\n{username}: {action}")

        return "ok", 200

    return "ok", 200

@app.route("/test-sender")
def test_sender():
    import os
    os.system("python sender.py")
    return "sender eseguito", 200

# =====================
# RUN
# =====================
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)