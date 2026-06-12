import os
import json
import requests
from datetime import datetime

BOT_TOKEN = os.environ["BOT_TOKEN"]
url = f"https://api.telegram.org/bot{BOT_TOKEN}/getUpdates"

DB_FILE = "responses.json"
OFFSET_FILE = "offset.json"

# LOAD DB
if os.path.exists(DB_FILE):
    db = json.load(open(DB_FILE))
else:
    db = {}

# LOAD OFFSET
if os.path.exists(OFFSET_FILE):
    last_update = json.load(open(OFFSET_FILE))["offset"]
else:
    last_update = 0

resp = requests.get(url).json()
updates = resp.get("result", [])

max_update = last_update

for u in updates:

    if u["update_id"] <= last_update:
        continue

    max_update = max(max_update, u["update_id"])

    if "callback_query" not in u:
        continue

    cq = u["callback_query"]

    user = cq["from"]["first_name"]
    data = cq["data"]

    action, date = data.split("|")
    action = "ok" if action == "ok" else "no"

    if date not in db:
        db[date] = {}

    if user in db[date]:
        continue

    db[date][user] = {
        "status": action,
        "time": datetime.now().isoformat()
    }

json.dump(db, open(DB_FILE, "w"), indent=2)
json.dump({"offset": max_update}, open(OFFSET_FILE, "w"), indent=2)
