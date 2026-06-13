from flask import Flask, request
import os
import json
import requests

app = Flask(__name__)

BOT_TOKEN = os.environ["BOT_TOKEN"]

DB_FILE = "responses.json"
RUBRICA_FILE = "rubrica.json"

# =====================
# UTILS JSON
# =====================
def load_json(path):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return {}

def save_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

# =====================
# DB
# =====================
from db import init_db, save_response, get_responses, get_expected

init_db()

# =====================
# RUBRICA
# =====================
rubrica = load_json(RUBRICA_FILE)

def to_name(username):
    username = str(username).lower().replace("@", "")
    for name, u in rubrica.items():
        if str(u).lower().replace("@", "") == username:
            return name
    return username

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
        username = username.lower().replace("@", "").strip()
    else:
        username = str(cb["from"]["id"])

    action, date = cb["data"].split("|")

    db = load_db()

    if date not in db:
        db[date] = {}

    # =====================
    # BLOCCO SE HA GIÀ RISPOSTO
    # =====================
    if username in db[date]:
        requests.post(
            f"https://api.telegram.org/bot{BOT_TOKEN}/answerCallbackQuery",
            data={
                "callback_query_id": cb_id,
                "text": "Hai già risposto 👍"
            }
        )
        return "ok", 200

    # =====================
    # SALVA RISPOSTA
    # =====================
    save_response(date, username, action)

    # =====================
    # CALCOLO STATI
    # =====================
    responses = db[date]

    ok_users = [to_name(u) for u, s in responses.items() if s == "ok"]
    no_users = [to_name(u) for u, s in responses.items() if s != "ok"]

    # =====================
    # LOAD EXPECTED
    # =====================
    expected_file = "expected_users.json"
    try:
        with open(expected_file, "r", encoding="utf-8") as f:
            expected = json.load(f)
        expected_users = set(expected.get(date, []))
    except:
        expected_users = set()

    missing = expected_users - set(responses.keys())

    # =====================
    # TESTO
    # =====================
    status_text = "\n\n📋 RISPOSTE\n\n"

    status_text += "✅ OK:\n"
    status_text += "\n".join(ok_users) if ok_users else "-"

    status_text += "\n\n❌ NON POSSO:\n"
    status_text += "\n".join(no_users) if no_users else "-"

    status_text += f"\n\n⏳ Mancano {len(missing)} risposte"

    # =====================
    # BOTTONI
    # =====================
    if len(missing) == 0:
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
    # UPDATE MESSAGGIO
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
