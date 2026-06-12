from flask import Flask, request
import os
import json
from datetime import datetime
import requests

app = Flask(__name__)

BOT_TOKEN = os.environ["BOT_TOKEN"]

DB_FILE = "responses.json"

# =====================
# LOAD DB
# =====================
if os.path.exists(DB_FILE):
    with open(DB_FILE, "r") as f:
        responses = json.load(f)
else:
    responses = {}

# =====================
# TELEGRAM ANSWER
# =====================
def answer_callback(cb_id, text="✔ Salvato"):
    requests.post(
        f"https://api.telegram.org/bot{BOT_TOKEN}/answerCallbackQuery",
        data={
            "callback_query_id": cb_id,
            "text": text,
            "show_alert": False
        }
    )

# =====================
# WEBHOOK ENDPOINT
# =====================
@app.route("/", methods=["POST"])
def webhook():

    data = request.json

    if "callback_query" not in data:
        return "ok"

    cb = data["callback_query"]
    cb_id = cb["id"]
    user = cb["from"]
    callback_data = cb["data"]

    try:
        action, date = callback_data.split("|")
    except:
        return "ok"

    username = user.get("username")
    user_key = f"@{username}" if username else str(user["id"])

    # =====================
    # SALVA RISPOSTA
    # =====================
    if date not in responses:
        responses[date] = {}

    responses[date][user_key] = {
        "status": action,
        "updated_at": datetime.now().isoformat()
    }

    with open(DB_FILE, "w") as f:
        json.dump(responses, f, indent=2)

    # =====================
    # RISPOSTA IMMEDIATA BOT
    # =====================
    answer_callback(cb_id)

    print(f"{user_key} -> {action}")

    return "ok"


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
