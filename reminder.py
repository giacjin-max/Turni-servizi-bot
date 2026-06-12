import os
import json
import pandas as pd
import requests

# =====================
# CONFIG
# =====================
BOT_TOKEN = os.environ["BOT_TOKEN"]
CHAT_ID = os.environ["CHAT_ID"]

url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"

DB_FILE = "responses.json"
REMINDER_LOG_FILE = "reminder_log.json"

# =====================
# LOAD RISPOSTE
# =====================
if os.path.exists(DB_FILE):
    responses = json.load(open(DB_FILE))
else:
    responses = {}

# =====================
# LOAD REMINDER LOG (ANTI-SPAM)
# =====================
if os.path.exists(REMINDER_LOG_FILE):
    reminder_log = json.load(open(REMINDER_LOG_FILE))
else:
    reminder_log = {}

# =====================
# EXCEL
# =====================
df = pd.read_excel("turni.xlsx")
df = df[df["Data"].notna()].copy()
df["Data"] = pd.to_datetime(df["Data"])

# =====================
# USERS MAP (Nome → @username)
# =====================
users = {}

for _, row in df.iterrows():
    nome = str(row["Nome"]).strip()
    username = row.get("Username Telegram")

    if pd.notna(username):
        username = str(username).strip()
        if not username.startswith("@"):
            username = "@" + username

        users[nome] = username

# =====================
# PROSSIMO TURNO
# =====================
riga = df.sort_values("Data").iloc[0]
date = riga["Data"].strftime("%Y-%m-%d")

# init log data
if date not in reminder_log:
    reminder_log[date] = {}

# =====================
# NOMI SERVIZI
# =====================
servizi = [
    "Parola","Adorazione","Coro","BimbiGiovani","Piano","Bass",
    "Chitarra","Mix","PC","Porta","Pulizia","Pulizia sala bimbi",
    "Traduzione","Ronda"
]

names = []

for s in servizi:
    if s in riga and pd.notna(riga[s]):
        names += str(riga[s]).replace(";", ",").split(",")

names = [n.strip() for n in names]

# =====================
# RISPOSTE GIA FATTE
# =====================
done = responses.get(date, {})

# =====================
# TROVA MANCANTI (NO DUPLICATI REMINDER)
# =====================
missing = []

for n in names:
    tag = users.get(n, n)

    if n not in done and not reminder_log[date].get(tag):
        missing.append(n)

# =====================
# STOP SE TUTTI HANNO RISPOSTO
# =====================
if not missing:
    print("Tutti hanno già risposto 👍")
    exit()

# =====================
# MESSAGGIO
# =====================
msg = "⏳ Reminder: non hanno ancora risposto al turno\n\n"

for n in missing:
    tag = users.get(n, n)
    msg += f"{tag} ({n})\n"

# =====================
# INVIO TELEGRAM
# =====================
requests.post(url, data={
    "chat_id": CHAT_ID,
    "text": msg
})

# =====================
# SALVA ANTI-SPAM
# =====================
for n in missing:
    tag = users.get(n, n)
    reminder_log[date][tag] = True

with open(REMINDER_LOG_FILE, "w") as f:
    json.dump(reminder_log, f, indent=2)

print("Reminder inviato e salvato")