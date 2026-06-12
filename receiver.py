import os
import json
import requests
from datetime import datetime

# =====================
# CONFIG
# =====================
BOT_TOKEN = os.environ["BOT_TOKEN"]

GET_UPDATES_URL = (
    f"https://api.telegram.org/bot{BOT_TOKEN}/getUpdates"
)

ANSWER_CALLBACK_URL = (
    f"https://api.telegram.org/bot{BOT_TOKEN}/answerCallbackQuery"
)

DB_FILE = "responses.json"
OFFSET_FILE = "offset.json"

# =====================
# LOAD RISPOSTE
# =====================
if os.path.exists(DB_FILE):
    with open(DB_FILE, "r") as f:
        responses = json.load(f)
else:
    responses = {}

# =====================
# LOAD OFFSET
# =====================
if os.path.exists(OFFSET_FILE):
    with open(OFFSET_FILE, "r") as f:
        offset_data = json.load(f)

    last_update_id = offset_data.get("offset", 0)

else:
    last_update_id = 0

# =====================
# GET UPDATES
# =====================
resp = requests.get(GET_UPDATES_URL)

data = resp.json()

updates = data.get("result", [])

max_update_id = last_update_id

# =====================
# ELABORA UPDATE
# =====================
for update in updates:

    update_id = update["update_id"]

    if update_id <= last_update_id:
        continue

    max_update_id = max(max_update_id, update_id)

    if "callback_query" not in update:
        continue

    callback = update["callback_query"]

    callback_id = callback["id"]

    user = callback["from"]

    user_id = str(user["id"])

    first_name = user.get("first_name", "")

    username = user.get("username")

    callback_data = callback["data"]

    try:
        action, turno_date = callback_data.split("|")
    except ValueError:
        continue

    if turno_date not in responses:
        responses[turno_date] = {}

    # =====================
    # IDENTIFICAZIONE UTENTE
    # =====================
    if username:
        user_key = f"@{username}"
    else:
        user_key = f"{first_name}_{user_id}"

    # =====================
    # SALVA RISPOSTA
    # =====================
    responses[turno_date][user_key] = {
        "status": action,
        "name": first_name,
        "user_id": user_id,
        "updated_at": datetime.now().isoformat()
    }

    # =====================
    # FEEDBACK TELEGRAM
    # =====================
    testo = (
        "✅ Presenza confermata"
        if action == "ok"
        else "❌ Assenza registrata"
    )

    requests.post(
        ANSWER_CALLBACK_URL,
        data={
            "callback_query_id": callback_id,
            "text": testo,
            "show_alert": False
        }
    )

    print(
        f"{user_key} -> {action} ({turno_date})"
    )

# =====================
# SAVE RISPOSTE
# =====================
with open(DB_FILE, "w") as f:
    json.dump(
        responses,
        f,
        indent=2,
        ensure_ascii=False
    )

# =====================
# SAVE OFFSET
# =====================
with open(OFFSET_FILE, "w") as f:
    json.dump(
        {"offset": max_update_id},
        f,
        indent=2
    )

print("Receiver completato")
