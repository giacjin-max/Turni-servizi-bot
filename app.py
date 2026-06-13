from flask import Flask, request
import os
import json
import requests

app = Flask(__name__)

BOT_TOKEN = os.environ["BOT_TOKEN"]

DB_FILE = "responses.json"
EXPECTED_FILE = "expected_users.json"
RUBRICA_FILE = "rubrica.json"

# =====================
# LOAD DB
# =====================
def load_db():
    try:
        with open(DB_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return {}

def save_db(db):
    try:
        with open(DB_FILE, "w", encoding="utf-8") as f:
            json.dump(db, f, indent=2, ensure_ascii=False)
        print("💾 DB SALVATO:", db, flush=True)
    except Exception as e:
        print("❌ ERRORE SALVATAGGIO DB:", e, flush=True)

# =====================
# LOAD EXPECTED
# =====================
def load_expected(date):
    try:
        with open(EXPECTED_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        return set(data.get(date, []))
    except:
        return set()

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

def to_tag(name):
    name = str(name).strip()
    return rubrica.get(name, name)

# =====================
# WEBHOOK
# =====================
@app.route("/", methods=["POST"])
def webhook():

    data = request.get_json(silent=True)
    print("📩 UPDATE:", json.dumps(data, ensure_ascii=False), flush=True)

    if not data or "callback_query" not in data:
        return "ok", 200

    cb = data["callback_query"]

    cb_id = cb["id"]
    chat_id = cb["message"]["chat"]["id"]
    msg_id = cb["message"]["message_id"]

    # =====================
    # USERNAME NORMALIZZATO (FONDAMENTALE)
    # =====================
    username = cb["from"].get("username")
    if username:
        username = "@" + username.lower().strip().replace("@", "")
    else:
        username = "@" + str(cb["from"]["id"])

    action, date = cb["data"].split("|")

    db = load_db()

    if date not in db:
        db[date] = {}

    # =====================
    # DEBUG INPUT
    # =====================
    print("📅 DATE:", date, flush=True)
    print("👤 USER:", username, flush=True)
    print("⚡ ACTION:", action, flush=True)

    # =====================
    # BLOCCO DOPPIO CLICK
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
    db[date][username] = action
    save_db(db)

    # =====================
    # EXPECTED USERS
    # =====================
    expected_users = load_expected(date)

    responded_users = set(db[date].keys())
    missing = expected_users - responded_users
    remaining = len(missing)

    print("📌 EXPECTED:", expected_users, flush=True)
    print("📌 RESPONDED:", responded_users, flush=True)
    print("📌 MISSING:", missing, flush=True)

    # =====================
    # RISPOSTE
    # =====================
    ok_users = [u for u, s in db[date].items() if s == "ok"]
    no_users = [u for u, s in db[date].items() if s != "ok"]

    status_text = "\n\n📋 RISPOSTE\n\n"
    status_text += "✅ OK:\n" + ("\n".join(ok_users) if ok_users else "-")
    status_text += "\n\n❌ NON POSSO:\n" + ("\n".join(no_users) if no_users else "-")
    status_text += f"\n\n⏳ Mancano {remaining} risposte"

    # =====================
    # BOTTONI
    # =====================
    if remaining == 0:
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
    # POPUP TELEGRAM
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
# HEALTH CHECK
# =====================
@app.route("/", methods=["GET"])
def home():
    return "Webhook attivo", 200

# =====================
# RUN
# =====================
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
