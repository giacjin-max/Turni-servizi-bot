import os
import json
import pandas as pd
import requests
from datetime import datetime

# =====================
# CONFIG
# =====================
BOT_TOKEN = os.environ["BOT_TOKEN"]
CHAT_ID = os.environ["CHAT_ID"]

url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"

# =====================
# ORARIO LOGICA
# =====================
now = datetime.now()
weekday = now.weekday()
hour = now.hour

send = False
prefix = ""

# LUNEDÌ SERA
if weekday == 0 and hour >= 18:
    send = True
    prefix = "📌 Turni settimana"

# SABATO MATTINA
elif weekday == 5 and hour < 12:
    send = True
    prefix = "📅 Reminder weekend"

if not send:
    print("⛔ Fuori orario invio")
    exit()

# =====================
# ANTI-DOPPIONE INVIO
# =====================
LOG_FILE = "sent_log.json"

if os.path.exists(LOG_FILE):
    sent_log = json.load(open(LOG_FILE))
else:
    sent_log = {}

today_key = now.strftime("%Y-%m-%d")

if sent_log.get(today_key):
    print("⛔ Già inviato oggi")
    exit()

# =====================
# EXCEL
# =====================
df = pd.read_excel("turni.xlsx")
df = df[df["Data"].notna()].copy()
df["Data"] = pd.to_datetime(df["Data"])

future = df[df["Data"] >= pd.Timestamp.now().normalize()]

if future.empty:
    print("Nessun turno")
    exit()

riga = future.sort_values("Data").iloc[0]
data_turno = riga["Data"].strftime("%Y-%m-%d")

# =====================
# MESSAGGIO
# =====================
msg = f"{prefix}\n\n📅 Turni Domenica {riga['Data'].strftime('%d/%m/%Y')}\n\n"

servizi = [
    "Parola","Adorazione","Coro","BimbiGiovani","Piano","Bass",
    "Chitarra","Mix","PC","Porta","Pulizia","Pulizia sala bimbi",
    "Traduzione","Ronda"
]

for s in servizi:
    if s in riga and pd.notna(riga[s]):
        msg += f"• {s}: {riga[s]}\n"

# =====================
# BOTTONI
# =====================
keyboard = {
    "inline_keyboard": [
        [
            {"text": "✅ OK", "callback_data": f"ok|{data_turno}"},
            {"text": "❌ NON POSSO", "callback_data": f"no|{data_turno}"}
        ]
    ]
}

# =====================
# INVIO
# =====================
response = requests.post(url, data={
    "chat_id": CHAT_ID,
    "text": msg,
    "reply_markup": json.dumps(keyboard)
})

print(response.text)

# =====================
# SALVA LOG
# =====================
if response.status_code == 200:
    sent_log[today_key] = True
    json.dump(sent_log, open(LOG_FILE, "w"), indent=2)
