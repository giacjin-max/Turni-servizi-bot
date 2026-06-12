from flask import Flask, request
import os
import requests
import json

app = Flask(__name__)

BOT_TOKEN = os.environ["BOT_TOKEN"]

DB_FILE = "responses.json"


def load_db():
    try:
        with open(DB_FILE, "r") as f:
            return json.load(f)
    except:
        return {}


def save_db(data):
    with open(DB_FILE, "w") as f:
        json.dump(data, f, indent=2)


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
        or str(cb["from"]["id"])
    )

    action, date = cb["data"].split("|")

    db = load_db()

    if date not in db:
        db[date] = {}

    db[date][username] = action

    save_db(db)

    requests.post(
        f"https://api.telegram.org/bot{BOT_TOKEN}/answerCallbackQuery",
        data={
            "callback_query_id": cb_id,
            "text": f"Registrato: {action.upper()} ✅"
        }
    )

    print(
        f"SALVATO -> {username} {action} {date}",
        flush=True
    )

    return "ok", 200


@app.route("/", methods=["GET"])
def home():
    return "Webhook attivo", 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
