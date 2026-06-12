import os
import json
import requests
from datetime import datetime

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
        offset_data = json.load(f)
        offset = offset_data.get("offset", 0)
else:
    offset = 0

# =====================
# GET UPDATES
# =====================
data = requests.get(GET_UPDATES_URL).json()
updates = data.get("result", [])

max_offset = offset

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

    username = user.get("username")
    user_id = str(user["id"])

    callback_data = cb["data"]

    # =====================
    # PARSE CALLBACK
    # =====================
    try:
        action, date = callback_data.split("|")
    except:
        continue

    user_key = f"@{username}" if username else user_id

    if date not in responses:
        responses[date] = {}

    # =====================
    # SALVA RISPOSTA
    # =====================
    responses[date][user_key] = {
        "status": action,
        "updated_at": datetime.now().isoformat()
    }

    # =====================
    # FEEDBACK BOT
    # =====================
    text = "✅ Salvato" if action == "ok" else "❌ Salvato"

    requests.post(ANSWER_URL, data={
        "callback_query_id": cb_id,
        "text": text,
        "show_alert": False
    })

    print(user_key, action, date)

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
