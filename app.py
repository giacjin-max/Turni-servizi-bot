from flask import Flask, request
import os
import json
import re
import requests
from supabase import create_client
from apscheduler.schedulers.background import BackgroundScheduler

scheduler = BackgroundScheduler()
import sender

app = Flask(__name__)

# =====================
# SCHEDULER
# =====================

scheduler.add_job(
    sender.send,
    "cron",
    day_of_week="mon",
    hour=10,
    minute=00,
    timezone="Europe/Rome"
)

# =====================
# 🔥 GIOVEDÌ FIXATO (SOLO MODIFICA QUI)
# =====================
scheduler.add_job(
    sender.run_reminder,
    "cron",
    day_of_week="mon",
    hour=20,
    minute=15,
    timezone="Europe/Rome"
)

scheduler.add_job(
    sender.reminder_sabato,
    "cron",
    day_of_week="sat",
    hour=10,
    minute=0,
    timezone="Europe/Rome"
)

scheduler.start()
print("=== JOB REGISTRATI ===")

for job in scheduler.get_jobs():
    print(job)
print("🚀 Scheduler attivo")

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

def to_name(username):
    username = username.lower().replace("@", "")
    for nome, tag in rubrica.items():
        if tag.lower().replace("@", "") == username:
            return nome
    return username

# =====================
# UTENTI ATTESI
# =====================
def extract_expected_users(text):
    return set(re.findall(r"@([a-zA-Z0-9_]+)", text.lower()))

# =====================
# SUPABASE
# =====================
def save_response(date, username, status):
    supabase.table("responses").upsert({
        "date": date,
        "username": username,
        "status": status
    }).execute()

def get_responses(date):
    res = supabase.table("responses").select("*").eq("date", date).execute()
    return {r["username"]: r["status"] for r in res.data}

# =====================
# WEBHOOK
# =====================
@app.route("/", methods=["POST"])
def webhook():

    data = request.get_json(silent=True)
    if not data:
        return "ok", 200

    if "message" in data and "text" in data["message"]:

        text = data["message"]["text"]
        chat_id = data["message"]["chat"]["id"]

        if text == "/test":
            requests.post(
                f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
                json={"chat_id": chat_id, "text": "🧪 Bot OK"}
            )
            return "ok", 200

        if text == "/send":
            try:
                import sender
                sender.send()
                msg = "🚀 Turni inviati con successo"
            except Exception as e:
                msg = f"❌ Errore sender:\n{str(e)}"

            requests.post(
                f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
                json={"chat_id": chat_id, "text": msg}
            )
            return "ok", 200

        return "ok", 200

    if "callback_query" not in data:
        return "ok", 200

    cb = data["callback_query"]

    cb_id = cb["id"]
    chat_id = cb["message"]["chat"]["id"]
    msg_id = cb["message"]["message_id"]

    username = cb["from"].get("username") or str(cb["from"]["id"])
    username = username.lower()

    action, date = cb["data"].split("|")

    text_message = cb["message"]["text"]

    expected_users = extract_expected_users(text_message)

    if username not in expected_users:
        requests.post(
            f"https://api.telegram.org/bot{BOT_TOKEN}/answerCallbackQuery",
            data={
                "callback_query_id": cb_id,
                "text": "Non sei assegnato 🚫"
            }
        )
        return "ok", 200

    if action == "noop":
        return "ok", 200

    responses = get_responses(date)

    responded_users = {
        u for u, s in responses.items() if s == "ok"
    }

    if username in responded_users:
        requests.post(
            f"https://api.telegram.org/bot{BOT_TOKEN}/answerCallbackQuery",
            data={
                "callback_query_id": cb_id,
                "text": "Hai già confermato ✔"
            }
        )
        return "ok", 200

    save_response(date, username, action)

    responses = get_responses(date)

    responded_users = {
        u for u, s in responses.items() if s == "ok"
    }

    status_text = "\n\n📋 RISPOSTE\n\n"

    for u in expected_users:
        name = to_name(u)
        if u in responded_users:
            status_text += f"{name} 🟢\n"
        else:
            status_text += f"{name}\n"

    keyboard = {
        "inline_keyboard": [[
            {"text": "✅ OK", "callback_data": f"ok|{date}"}
        ]]
    }

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

    requests.post(
        f"https://api.telegram.org/bot{BOT_TOKEN}/answerCallbackQuery",
        data={"callback_query_id": cb_id, "text": "Salvato ✔"}
    )

    return "ok", 200


@app.route("/", methods=["GET"])
def home():
    return "OK", 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))