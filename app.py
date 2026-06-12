from flask import Flask, request
import os
import json
import requests

app = Flask(__name__)

BOT_TOKEN = os.environ["BOT_TOKEN"]

DB_FILE = "responses.json"


def load_db():
    try:
        with open(DB_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return {}


def save_db(data):
    with open(DB_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


@app.route("/", methods=["GET"])
def home():
    return "Webhook attivo", 200


@app.route("/", methods=["POST"])
def webhook():

    data = request.get_json(silent=True)

    print(json.dumps(data, ensure_ascii=False), flush=True)

    if not data:
        return "ok", 200

    if "callback_query" not in data:
        return "ok", 200

    cb = data["callback_query"]

    cb_id = cb["id"]

    username = (
        cb["from"].get("username")
        or cb["from"].get("first_name")
        or str(cb["from"]["id"])
    )

    action, date = cb["data"].split("|")

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

    # SALVA RISPOSTA
    db[date][username] = action
    save_db(db)

    # POPUP TELEGRAM
    requests.post(
        f"https://api.telegram.org/bot{BOT_TOKEN}/answerCallbackQuery",
        data={
            "callback_query_id": cb_id,
            "text": f"Registrato: {action.upper()} ✅"
        }
    )

    # COSTRUISCE ELENCHI
    ok_users = []
    no_users = []

    for user, status in db[date].items():

        if status == "ok":
            ok_users.append(f"@{user}")

        elif status == "no":
            no_users.append(f"@{user}")

    status_text = "\n\n📋 RISPOSTE\n\n"

    status_text += "✅ Confermati:\n"

    if ok_users:
        status_text += "\n".join(ok_users)
    else:
        status_text += "-"

    status_text += "\n\n❌ Non disponibili:\n"

    if no_users:
        status_text += "\n".join(no_users)
    else:
        status_text += "-"

    original_text = cb["message"]["text"]

    # EVITA DI AGGIUNGERE PIÙ VOLTE LA SEZIONE RISPOSTE
    if "\n\n📋 RISPOSTE" in original_text:
        original_text = original_text.split("\n\n📋 RISPOSTE")[0]

    requests.post(
        f"https://api.telegram.org/bot{BOT_TOKEN}/editMessageText",
        json={
            "chat_id": cb["message"]["chat"]["id"],
            "message_id": cb["message"]["message_id"],
            "text": original_text + status_text,
            "reply_markup": {
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
        }
    )

    print(
        f"SALVATO -> {username} {action} {date}",
        flush=True
    )

    return "ok", 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
