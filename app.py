from flask import Flask, request
import os
import requests
import json

app = Flask(__name__)

BOT_TOKEN = os.environ["BOT_TOKEN"]

DB_FILE = "responses.json"


# =========================
# LOAD DB
# =========================
def load_db():
    if os.path.exists(DB_FILE):
        with open(DB_FILE, "r") as f:
            return json.load(f)
    return {}


def save_db(db):
    with open(DB_FILE, "w") as f:
        json.dump(db, f, indent=2)


# =========================
# TELEGRAM ANSWER
# =========================
def answer(cb_id, text="Salvato ✔"):
    requests.post(
        f"https://api.telegram.org/bot{BOT_TOKEN}/answerCallbackQuery",
        data={
            "callback_query_id": cb_id,
            "text": text
        }
    )


# =========================
# WEBHOOK
# =========================
@app.route("/", methods=["POST"])
def webhook():

    data = request.get_json()

    # 🔥 DEBUG (QUI)
    print("INCOMING UPDATE:", data)

    if not data:
        return "ok"

    if "callback_query" not in data:
        return "ok"

    cb = data["callback_query"]

    cb_id = cb["id"]
    user = cb["from"].get("username") or str(cb["from"]["id"])

    raw = cb.get("data", "")

    print("CLICK DATA:", raw)  # 🔥 DEBUG

    if "|" not in raw:
        return "ok"

    action, date = raw.split("|", 1)

    db = load_db()

    if date not in db:
        db[date] = {}

    db[date][user] = action

    save_db(db)

    answer(cb_id, f"{action} salvato ✔")

    print(f"SAVED: {user} -> {action} ({date})")

    return "ok"


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
