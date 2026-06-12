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
RUBRICA_FILE = "rubrica.json"


# =====================
# LOAD FILES
# =====================
def load_json(path):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return {}


expected_data = load_json(EXPECTED_FILE)
responses_data = load_json(RESPONSES_FILE)
rubrica = load_json(RUBRICA_FILE)


# =====================
# CONVERT NAME → TAG
# =====================
def to_tag(name):
    return rubrica.get(name, name)


# =====================
# SEND MESSAGE
# =====================
def send_message(text):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    requests.post(url, data={
        "chat_id": CHAT_ID,
        "text": text
    })


# =====================
# MAIN LOGIC
# =====================
for date, expected_users in expected_data.items():

    expected_users = set(expected_users)
    responses = responses_data.get(date, {})

    responded_users = set(responses.keys())
    missing_users = expected_users - responded_users

    # se tutti hanno risposto → skip
    if not missing_users:
        continue

    # =====================
    # COSTRUISCI MESSAGGIO
    # =====================
    msg = f"⏰ REMINDER TURNI {date}\n\n"

    msg += "👉 Mancano ancora le risposte:\n\n"

    for user in missing_users:
        msg += f"• {to_tag(user)}\n"

    msg += "\n⚠️ Rispondi ai turni con i pulsanti nel messaggio"

    send_message(msg)

    print("REMINDER INVIATO:", date)
    print("MANCANO:", len(missing_users))
