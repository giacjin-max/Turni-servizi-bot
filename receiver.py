import os
import json
import requests
from datetime import datetime

# =====================
# CONFIG
# =====================
BOT_TOKEN = os.environ["BOT_TOKEN"]

GET_UPDATES_URL = f"https://api.telegram.org/bot{BOT_TOKEN}/getUpdates"
ANSWER_URL = f"https://api.telegram.org/bot{BOT_TOKEN}/answerCallbackQuery"

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
        offset = json.load(f).get("offset", 0)
else:
    offset = 0

# =====================
# GET UPDATES
# =====================
resp = requests.get(GET_UPDATES_URL, timeout=10)
data = resp.json()

updates = data.get("result", [])

max_offset = offset

# =====================
# LOOP UPDATES
# =====================
for update in updates:

    update_id = update["update_id"]

    if update_id <= offset:
        continue

    max_offset = max(max_offset, update_id)

    if "callback_query" not in update:
        continue

    cb = update["callback_query"]

    cb_id = cb["id"]
    user = cb["from"]

    callback_data = cb["data"]

    # =====================
    # PARSE CALLBACK
    # =====================
    try:
        action, date = callback_data.split("|")
    except:
        continue

    username = user.get("username")
    user_key = f"@{username}" if username else str(user["id"])

    # =====================
    # 1. RISPOSTA IMMEDIATA (CRITICO)
    # =====================
    requests.post(
        ANSWER_URL,
        data={
            "callback_query_id": cb_id,
            "text": "✔ Salvato",
            "show_alert": False
        }
    )

    # =====================
    # 2. SALVATAGGIO RISPOSTA
    # =====================
    if date not in responses:
        responses[date] = {}

    responses[date][user_key] = {
        "status": action,
        "updated_at": datetime.now().isoformat()
    }

    print(f"{user_key} -> {action} ({date})")

# =====================
# SAVE RISPOSTE
# =====================
with open(DB_FILE, "w") as f:
    json.dump(responses, f, indent=2)

# =====================
# SAVE OFFSET
# =====================
with open(OFFSET_FILE, "w") as f:
    json.dump({"offset": max_offset}, f, indent=2)

print("Receiver OK")
