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
# =========================@app.route("/", methods=["POST"])
def webhook():

    data = request.get_json(silent=True)

    if not data:
        data = request.form.to_dict()

    print("INCOMING:", data)

    if "callback_query" not in data:
        return "ok"

    cb = data["callback_query"]

    cb_id = cb["id"]
    user = cb["from"].get("username") or str(cb["from"]["id"])

    raw = cb.get("data", "")

    print("CLICK:", raw)

    return "ok"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
