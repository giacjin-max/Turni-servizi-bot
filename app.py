from flask import Flask, request
import os
import json
import requests

app = Flask(name)

BOT_TOKEN = os.environ[“BOT_TOKEN”]

DB_FILE = “responses.json”
RUBRICA_FILE = “rubrica.json”
EXPECTED_FILE = “expected_users.json”

=====================

LOAD DB

=====================

def load_db():
try:
with open(DB_FILE, “r”, encoding=“utf-8”) as f:
return json.load(f)
except:
return {}

def save_db(db):
with open(DB_FILE, “w”, encoding=“utf-8”) as f:
json.dump(db, f, indent=2, ensure_ascii=False)

=====================

RUBRICA

=====================

def load_rubrica():
try:
with open(RUBRICA_FILE, “r”, encoding=“utf-8”) as f:
return json.load(f)
except:
return {}

rubrica = load_rubrica()

=====================

WEBHOOK

=====================

@app.route(”/”, methods=[“POST”])
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
    username = "@" + username.lower()
else:
    username = "@" + str(cb["from"]["id"])
action, date = cb["data"].split("|")
db = load_db()
if date not in db:
    db[date] = {}
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
# UTENTI ATTESI
# =====================
try:
    with open(EXPECTED_FILE, "r", encoding="utf-8") as f:
        expected = json.load(f)
    expected_users = set(expected.get(date, []))
except:
    expected_users = set()
# =====================
# UTENTI CHE HANNO RISPOSTO
# =====================
responded_users = set(db[date].keys())
remaining = len(expected_users - responded_users)
print("EXPECTED:", expected_users)
print("RESPONDED:", responded_users)
print("MISSING:", expected_users - responded_users)
# =====================
# COSTRUISCI STATO
# =====================
ok_users = []
no_users = []
for user, status in db[date].items():
    if status == "ok":
        ok_users.append(user)
    else:
        no_users.append(user)
status_text = "\n\n📋 RISPOSTE\n\n"
status_text += "✅ OK:\n"
status_text += "\n".join(sorted(ok_users)) if ok_users else "-"
status_text += "\n\n❌ NON POSSO:\n"
status_text += "\n".join(sorted(no_users)) if no_users else "-"
status_text += f"\n\n⏳ Mancano {remaining} risposte"
# =====================
# BOTTONI
# =====================
if remaining == 0:
    keyboard = {
        "inline_keyboard": []
    }
    status_text += "\n\n🔒 Risposte chiuse"
else:
    keyboard = {
        "inline_keyboard": [
            [
                {
                    "text": "✅ OK",
                    "callback_data": f"ok|{date}"
                },
                {
                    "text": "❌ NON POSSO",
                    "callback_data": f"no|{date}"
                }
            ]
        ]
    }
# =====================
# TESTO ORIGINALE
# =====================
original = cb["message"]["text"]
if "\n\n📋 RISPOSTE" in original:
    original = original.split("\n\n📋 RISPOSTE")[0]
# =====================
# AGGIORNA MESSAGGIO
# =====================
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

@app.route(”/”, methods=[“GET”])
def home():
return “Webhook attivo”, 200

if name == “main”:
app.run(
host=“0.0.0.0”,
port=int(os.environ.get(“PORT”, 5000))
)