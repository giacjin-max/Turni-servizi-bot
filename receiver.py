import os
import json
import requests
from datetime import datetime

# =====================
# CONFIG
# =====================
BOT_TOKEN = os.environ["BOT_TOKEN"]

url = f"https://api.telegram.org/bot{BOT_TOKEN}/getUpdates"

DB_FILE = "responses.json"
OFFSET_FILE = "offset.json"

# =====================
# LOAD DATABASE RISPOSTE
# =====================
if os.path.exists(DB_FILE):
    with open(DB_FILE, "r") as f:
        db = json.load(f)
else:
    db = {}

# =====================
# LOAD OFFSET (ANTI-DOPPIONI TELEGRAM)
# =====================
if os.path.exists(OFFSET_FILE):
    with open(OFFSET_FILE, "r") as f:
        offset_data = json.load(f)
        last_update_id = offset_data.get("offset", 0)
else:
    last_update_id = 0

# =====================
# CHIAMATA TELEGRAM
# =====================
resp = requests.get(url).json()

if "result" not in resp:
    print("Nessun update")
    exit()

updates = resp["result"]

# =====================
# ELABORAZIONE UPDATE
# =====================
max_update_id = last_update_id

for update in updates:

    update_id = update["update_id"]

    # evita duplicati già processati
    if update_id <= last_update_id:
        continue

    max_update_id = max(max_update_id, update_id)

    # solo click bottoni
    if "callback_query" not in update:
        continue

    cq = update["callback_query"]

    user = cq["from"]["first_name"]

    data = cq["data"]  # esempio: ok|2026-01-20

    try:
        action, date = data.split("|")
    except:
        continue

    action = "ok" if action == "ok" else "no"

    # =====================
    # INIT DB DATE
    # =====================
    if date not in db:
        db[date] = {}

    # =====================
    # ANTI-DOPPIONE CLICK
    # =====================
    if user in db[date]:
        print(f"{user} già registrato per {date}")
        continue

    # =====================
    # SALVA RISPOSTA
    # =====================
    db[date][user] = {
        "status": action,
        "timestamp": datetime.now().isoformat()
    }

    print(f"Salvato: {user} -> {action} ({date})")

# =====================
# SALVA DATABASE
# =====================
with open(DB_FILE, "w") as f:
    json.dump(db, f, indent=2)

# =====================
# SALVA OFFSET
# =====================
with open(OFFSET_FILE, "w") as f:
    json.dump({"offset": max_update_id}, f)

print("Receiver aggiornato correttamente")
