import os
import json
import requests
from datetime import datetime

# =====================
# CONFIG
# =====================
BOT_TOKEN = os.environ["BOT_TOKEN"]

get_url = f"https://api.telegram.org/bot{BOT_TOKEN}/getUpdates"

DB_FILE = "responses.json"
OFFSET_FILE = "offset.json"

# =====================
# LOAD DB RISPOSTE
# =====================
if os.path.exists(DB_FILE):
    db = json.load(open(DB_FILE))
else:
    db = {}

# =====================
# LOAD OFFSET (EVITA DUPLICATI)
# =====================
if os.path.exists(OFFSET_FILE):
    last_offset = json.load(open(OFFSET_FILE))["offset"]
else:
    last_offset = 0

# =====================
# FETCH UPDATES
# =====================
resp = requests.get(get_url).json()
updates = resp.get("result", [])

max_offset = last_offset

# =====================
# LOOP UPDATES
# =====================
for u in updates:

    update_id = u["update_id"]

    if update_id <= last_offset:
        continue

    max_offset = max(max_offset, update_id)

    if "callback_query" not in u:
        continue

    cq = u["callback_query"]

    user_id = cq["from"]["id"]
    user_name = cq["from"]["first_name"]

    data = cq["data"]  # ok|2026-06-12

    # =====================
    # PARSING CALLBACK
    # =====================
    try:
        action, date = data.split("|")
    except:
        continue

    status = "ok" if action == "ok" else "no"

    # =====================
    # INIT DATE
    # =====================
    if date not in db:
        db[date] = {}

    # =====================
    # SALVA RISPOSTA
    # =====================
    db[date][user_name] = {
        "status": status,
        "time": datetime.now().isoformat(),
        "user_id": user_id
    }

# =====================
# SALVA DB
# =====================
with open(DB_FILE, "w") as f:
    json.dump(db, f, indent=2)

# =====================
# SALVA OFFSET
# =====================
with open(OFFSET_FILE, "w") as f:
    json.dump({"offset": max_offset}, f, indent=2)

print("Receiver aggiornato")