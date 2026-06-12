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
# LOAD DATABASE RISPOSTE
# =====================
if os.path.exists(DB_FILE):
    db = json.load(open(DB_FILE))
else:
    db = {}

# =====================
# LOAD OFFSET (EVITA DUPLICATI UPDATE)
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

    user = cq["from"]["first_name"]
    user_id = cq["from"]["id"]

    data = cq["data"]  # es: ok|2026-01-20

    # =====================
    # PARSING CALLBACK
    # =====================
    try:
        action, date = data.split("|")
    except:
        continue

    if action == "ok":
        status = "ok"
    else:
        status = "no"

    # =====================
    # INIT DATE IN DB
    # =====================
    if date not in db:
        db[date] = {}

    # =====================
    # SALVA RISPOSTA
    # =====================
    db[date][user] = {
        "status": status,
        "time": datetime.now().isoformat(),
        "user_id": user_id
    }

# =====================
# SAVE DB RISPOSTE
# =====================
with open(DB_FILE, "w") as f:
    json.dump(db, f, indent=2)

# =====================
# SAVE OFFSET
# =====================
with open(OFFSET_FILE, "w") as f:
    json.dump({"offset": max_offset}, f, indent=2)

print("Receiver aggiornato")