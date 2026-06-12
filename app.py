from flask import Flask, request
import os
import json
import requests

app = Flask(__name__)

BOT_TOKEN = os.environ["BOT_TOKEN"]

DB_FILE = "responses.json"
EXPECTED_FILE = "expected_users.json"


# =====================
# LOAD/SAVE DB
# =====================
def load_db():
    try:
        with open(DB_FILE, "r") as f:
            return json.load(f)
    except:
        return {}

def save_db(db):
    with open(DB_FILE, "w") as f:
        json.dump(db, f, indent=2)


def load_expected(date):
    try:
        with open(EXPECTED_FILE, "r") as f:
            data = json.load(f)
        return data.get(date, [])
    except:
        return []


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

    # =====================
    # DB
    # =====================
    db = load_db()

    if date not in db:
        db[date] = {}

    # BLOCCA DOPPIO CLICK
    if username in db[date]:
        requests.post(
            f"https://api.telegram.org/bot{BOT_TOKEN}/answerCallbackQuery",
            data={
                "callback_query_id": cb_id,
                "text": "Hai già risposto 👍"
            }
        )
        return "ok", 200

    # SALVA
    db[date][username] = action
    save_db(db)

    # =====================
    # EXPECTED USERS
    # =====================
    expected = load_expected(date)
    total_expected = len(set(expected))
    done = len(db[date])

    # =====================
    # STATUS LIST
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

    remaining = max(total_expected - done, 0)

    status_text += f"\n\n⏳ Mancano {remaining} risposte"

    # =====================
    # CHIUSURA BOTTONI
    # =====================
    keyboard = {
        "inline_keyboard": [
            [
                {"text": "🔒 Risposte chiuse" if remaining == 0 else "✅ OK", "callback_data": f"ok|{date}"},
                {"text": "🔒 Risposte chiuse" if remaining == 0 else "❌ NON POSSO", "callback_data": f"no|{date}"}
            ]
        ]
    }

    if remaining == 0:
        keyboard = {"inline_keyboard": []}

    # =====================
    # EDIT MESSAGGIO
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


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
