import json
import os
import requests

# =====================
# CONFIG
# =====================
BOT_TOKEN = os.environ["BOT_TOKEN"]
CHAT_ID = os.environ["CHAT_ID"]

EXPECTED_FILE = "expected_users.json"
RESPONSES_FILE = "responses.json"

URL = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"

# =====================
# LOAD
# =====================
def load_json(path):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return {}

expected_data = load_json(EXPECTED_FILE)
responses_data = load_json(RESPONSES_FILE)

# =====================
# MAIN LOOP
# =====================
for date, expected_users in expected_data.items():

    expected_users = set(expected_users)
    responses = responses_data.get(date, {})

    responded_users = set(responses.keys())
    missing = expected_users - responded_users

    if not missing:
        continue

    msg = f"⏰ REMINDER TURNI {date}\n\n"
    msg += "👉 Mancano ancora risposte:\n\n"

    for u in missing:
        msg += f"• {u}\n"

    msg += "\n⚠️ Rispondi usando i pulsanti nel messaggio turni"

    requests.post(
        URL,
        data={
            "chat_id": CHAT_ID,
            "text": msg
        }
    )

    print("REMINDER INVIATO:", date)
    print("MANCANO:", len(missing))
