import os
import json
import requests
from flask import Flask, request
from supabase import create_client

app = Flask(__name__)

BOT_TOKEN = os.environ["BOT_TOKEN"]
SUPABASE_URL = os.environ["SUPABASE_URL"]
SUPABASE_KEY = os.environ["SUPABASE_KEY"]

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# =====================
# RUBRICA (reverse mapping)
# =====================
with open("rubrica.json", "r", encoding="utf-8") as f:
    rubrica = json.load(f)

reverse_rubrica = {
    v.lower().replace("@", ""): k
    for k, v in rubrica.items()
}

def get_service_name(telegram_user):
    user = telegram_user.lower().replace("@", "")
    return reverse_rubrica.get(user, user)

# =====================
# SUPABASE SAVE
# =====================
def save_response(date, service_name, status):

    supabase.table("responses").upsert({
        "date": date,
        "username": service_name,
        "status": status
    }, on_conflict="date,username").execute()

# =====================
# READ RESPONSES
# =====================
def get_responses(date):

    return supabase.table("responses") \
        .select("*") \
        .eq("date", date) \
        .execute().data

# =====================
# BUILD MESSAGE
# =====================
def build_message(original_text, responses):

    header = original_text.split("\n")[0] + "\n\n"
    msg = header

    for r in responses:
        msg += f"• {r['username']} → {r['status']}\n"

    return msg

# =====================
# WEBHOOK
# =====================
@app.route("/", methods=["POST"])
def webhook():

    data = request.get_json(silent=True)

    if not data or "callback_query" not in data:
        return "ok", 200

    cb = data["callback_query"]

    chat_id = cb["message"]["chat"]["id"]
    msg_id = cb["message"]["message_id"]

    telegram_user = cb["from"].get("username") or str(cb["from"]["id"])
    action, date = cb["data"].split("|")

    service_name = get_service_name(telegram_user)

    print("CLICK:", telegram_user, "→", service_name, action, date, flush=True)

    save_response(date, service_name, action)

    responses = get_responses(date)

    new_text = build_message(cb["message"]["text"], responses)

    requests.post(
        f"https://api.telegram.org/bot{BOT_TOKEN}/editMessageText",
        json={
            "chat_id": chat_id,
            "message_id": msg_id,
            "text": new_text
        }
    )

    requests.post(
        f"https://api.telegram.org/bot{BOT_TOKEN}/answerCallbackQuery",
        data={"callback_query_id": cb["id"], "text": "Salvato ✔"}
    )

    return "ok", 200

# =====================
# START
# =====================
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)