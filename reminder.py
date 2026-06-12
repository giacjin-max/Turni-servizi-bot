import os
import json
import pandas as pd
import requests
from collections import defaultdict

# =====================
# CONFIG
# =====================
BOT_TOKEN = os.environ["BOT_TOKEN"]
CHAT_ID = os.environ["CHAT_ID"]

url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"

DB_FILE = "responses.json"

# =====================
# LOAD RISPOSTE
# =====================
if os.path.exists(DB_FILE):
    responses = json.load(open(DB_FILE))
else:
    responses = {}

# =====================
# EXCEL
# =====================
df = pd.read_excel("turni.xlsx")
df = df[df["Data"].notna()].copy()
df["Data"] = pd.to_datetime(df["Data"])

# =====================
# PROSSIMO TURNO
# =====================
riga = df.sort_values("Data").iloc[0]
date = riga["Data"].strftime("%Y-%m-%d")

done = responses.get(date, {})

# =====================
# SERVIZI
# =====================
servizi = [
    "Parola","Adorazione","Coro","BimbiGiovani","Piano","Bass",
    "Chitarra","Mix","PC","Porta","Pulizia","Pulizia sala bimbi",
    "Traduzione","Ronda"
]

# =====================
# MAPPA PERSONA -> SERVIZI
# =====================
people_to_services = defaultdict(set)

for s in servizi:

    if s not in riga:
        continue

    valore = riga[s]

    # ❌ salta ruoli vuoti
    if pd.isna(valore):
        continue

    valore = str(valore).strip()

    # ❌ salta stringhe vuote
    if valore == "":
        continue

    nomi = valore.replace(";", ",").split(",")

    for n in nomi:
        n = n.strip()

        # ❌ salta nomi vuoti
        if n == "":
            continue

        people_to_services[n].add(s)

# =====================
# TROVA MANCANTI
# =====================
missing = []

for person in people_to_services.keys():
    if person not in done:
        missing.append(person)

# =====================
# STOP SE TUTTI HANNO RISPOSTO
# =====================
if not missing:
    print("Tutti hanno risposto 👍")
    exit()

# =====================
# MESSAGGIO
# =====================
msg = "⏳ Reminder: non hanno ancora risposto al turno\n\n"

for person in missing:

    services = list(people_to_services[person])

    # sicurezza extra
    if not services:
        continue

    msg += f"• {person} ({', '.join(services)})\n"

# =====================
# INVIO TELEGRAM
# =====================
requests.post(url, data={
    "chat_id": CHAT_ID,
    "text": msg
})

print("Reminder inviato")