from flask import Flask, request
import os
import json
import requests

app = Flask(__name__)

BOT_TOKEN = os.environ["BOT_TOKEN"]

DB_FILE = "responses.json"


# =====================
# DB
# =====================
def load_db():
    try:
        with open(DB_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return {}


def save_db(db):
    with open(DB_FILE, "w", encoding="utf-8") as f:
        json.dump(db, f, indent=2, ensure_ascii=False)


# =====================
# ESTRAI UTENTI DAL MESSAGGIO TURNI
# =====================
def extract_expected_users(text):
    users = set()

    for line in text.split("\n"):
        if "@" in line:
            for word in line.split():
                if word.startswith("@"):
                    users.add(word.strip())

    return users


# =====================
# WEBHOOK
# =====================
@app.route("/", methods=["POST"])
def webhook():

    data = request.get_json(silent=True)

    print(json.dumps(data, ensure_ascii=False), flush=True)

    if not data or "callback_query" not in data:
        return "ok", 200

    cb = data["callback_query"]

    cb_id = cb["id"]
    chat_id = cb["message"]["chat"]["id"]
    msg_id = cb["message"]["message_id"]

    username = (
        cb["from"].get("username")
        or str(cb["from"]["id"])
    )

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
    # UTENTI ATTESI (DA MESSAGGIO)
    # =====================
    expected_users = extract_expected_users(cb["message"]["text"])
    responded_users = set(db[date].keys())

    remaining = len(expected_users - responded_users)

    # =====================
    # LISTA RISPOSTE
    # =====================
    ok_users = []
    no_users = []

    for user, status in db[date].items():
        if status == "ok":
            ok_users.append("@" + user)
        else:
            no_users.append("@" + user)

    status_text = "\n\n📋 RISPOSTE\n\n"

    status_text += "✅ OK:\n" + ("\n".join(ok_users) if ok_users else "-")
    status_text += "\n\n❌ NON POSSO:\n" + ("\n".join(no_users) if no_users else "-")

    status_text += f"\n\n⏳ Mancano {remaining} risposte"

    # =====================
    # CHIUSURA BOTTONI
    # =====================
    if remaining == 0:
        keyboard = {"inline_keyboard": []}
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


@app.route("/", methods=["GET"])
def home():
    return "Webhook attivo", 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
