import json
import os
import requests
import pandas as pd
from datetime import datetime

# =====================
# CONFIG
# =====================
BOT_TOKEN = os.environ["BOT_TOKEN"]
CHAT_ID = os.environ["CHAT_ID"]

url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"

# =====================
# FILE EXPECTED USERS
# =====================
EXPECTED_FILE = "expected_users.json"

def save_expected(date, users_list):
    data = {}

    if os.path.exists(EXPECTED_FILE):
        with open(EXPECTED_FILE, "r") as f:
            data = json.load(f)

    # elimina duplicati
    data[date] = list(set(users_list))

    with open(EXPECTED_FILE, "w") as f:
        json.dump(data, f, indent=2)

# =====================
# LOAD RISPOSTE
# =====================
if os.path.exists("responses.json"):
    with open("responses.json", "r") as f:
        responses = json.load(f)
else:
    responses = {}

# =====================
# EXCEL
# =====================
df = pd.read_excel("turni.xlsx")
df = df[df["Data"].notna()].copy()
df["Data"] = pd.to_datetime(df["Data"])

riga = df.sort_values("Data").iloc[0]
date = riga["Data"].strftime("%Y-%m-%d")

done = responses.get(date, {})

# =====================
# USERS + SERVIZI
# =====================
users = []

for _, row in df.iterrows():

    nome = str(row["Nome"]).strip()
    username = row.get("Username Telegram")

    if pd.notna(username):
        username = str(username).strip()
        if not username.startswith("@"):
            username = "@" + username

        users.append(username)

# salva chi deve rispondere
save_expected(date, users)

# =====================
# MESSAGGIO
# =====================
msg = f"📅 TURNI {riga['Data'].strftime('%d/%m/%Y')}\n\n"

msg += "👉 Premi un bottone per confermare\n"

# =====================
# BOTTONI
# =====================
keyboard = {
    "inline_keyboard": [
        [
            {"text": "✅ OK", "callback_data": f"ok|{date}"},
            {"text": "❌ NON POSSO", "callback_data": f"no|{date}"}
        ]
    ]
}

# =====================
# INVIO
# =====================
response = requests.post(
    url,
    data={
        "chat_id": CHAT_ID,
        "text": msg,
        "reply_markup": json.dumps(keyboard)
    }
)

print("STATUS:", response.status_code)
print("Turni inviati + expected_users salvati")
