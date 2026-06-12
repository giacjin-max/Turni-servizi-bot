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
# ORARIO
# =====================
now = datetime.now()
weekday = now.weekday()  # lun=0 ... dom=6
hour = now.hour

send = False
mode = "full"
prefix = ""

# =====================
# LOGICA GIORNI
# =====================

# LUNEDÌ SERA → INVIO COMPLETO
if weekday == 0 and hour >= 18:
    send = True
    mode = "full"
    prefix = "📌 Turni settimana"

# SABATO MATTINA → REMINDER GENERALE
elif weekday == 5 and hour < 12:
    send = True
    mode = "full"
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

if sent_log.get(today_key) and mode == "full":
    print("⛔ Già inviato oggi")
    exit()

# =====================
# EXCEL (IMPORTANTE: dd/mm/yyyy)
# =====================
df = pd.read_excel("turni.xlsx")

# ✔ FIX CRITICO PER FORMATO EUROPEO
df["Data"] = pd.to_datetime(df["Data"], dayfirst=True)

future = df[df["Data"] >= pd.Timestamp.now().normalize()]

if future.empty:
    print("Nessun turno trovato")
    exit()

riga = future.sort_values("Data").iloc[0]

# =====================
# FORMATO INTERNO (PER SYSTEM)
# =====================
data_turno = riga["Data"].strftime("%Y-%m-%d")

# =====================
# SERVIZI
# =====================
servizi = [
    "Parola","Adorazione","Coro","BimbiGiovani","Piano","Bass",
    "Chitarra","Mix","PC","Porta","Pulizia","Pulizia sala bimbi",
    "Traduzione","Ronda"
]

# =====================
# MESSAGGIO
# =====================
msg = f"{prefix}\n\n📅 Turni Domenica {riga['Data'].strftime('%d/%m/%Y')}\n\n"

for s in servizi:

    if s not in riga:
        continue

    valore = riga[s]

    if pd.isna(valore):
        continue

    nomi = str(valore).replace(";", ",").split(",")
    nomi = [n.strip() for n in nomi if n.strip()]

    if not nomi:
        continue

    msg += f"• {s}: {', '.join(nomi)}\n"

# =====================
# BOTTONI
# =====================
keyboard = {
    "inline_keyboard": [
        [
            {
                "text": "✅ OK",
                "callback_data": f"ok|{data_turno}"
            },
            {
                "text": "❌ NON POSSO",
                "callback_data": f"no|{data_turno}"
            }
        ]
    ]
}

# =====================
# INVIO TELEGRAM
# =====================
requests.post(url, data={
    "chat_id": CHAT_ID,
    "text": msg,
    "reply_markup": json.dumps(keyboard)
})

# =====================
# SALVA LOG
# =====================
if mode == "full":
    sent_log[today_key] = True
    json.dump(sent_log, open(LOG_FILE, "w"), indent=2)

print("Sender eseguito correttamente")