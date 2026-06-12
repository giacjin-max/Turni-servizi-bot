import os
import json
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
# LOAD DATABASE RISPOSTE
# =====================
if os.path.exists("responses.json"):
    with open("responses.json", "r") as f:
        responses = json.load(f)
else:
    responses = {}

# =====================
# LOAD EXCEL TURNI
# =====================
df = pd.read_excel("turni.xlsx")

df = df[df["Data"].notna()].copy()
df["Data"] = pd.to_datetime(df["Data"])

oggi = pd.Timestamp.now().normalize()

future = df[df["Data"] >= oggi]

if future.empty:
    print("Nessun turno futuro")
    exit()

riga = future.sort_values("Data").iloc[0]
data_turno = riga["Data"].strftime("%Y-%m-%d")

# =====================
# CONTROLLO SE ESISTE RISPOSTA
# =====================
risposte_turno = responses.get(data_turno, {})

# =====================
# ESTRAI PERSONE DAL TURN0
# =====================
servizi = [
    "Parola",
    "Adorazione",
    "Coro",
    "BimbiGiovani",
    "Piano",
    "Bass",
    "Chitarra",
    "Mix",
    "PC",
    "Porta",
    "Pulizia",
    "Pulizia sala bimbi",
    "Traduzione",
    "Ronda",
]

tutti_nomi = []

for s in servizi:
    if s in riga and pd.notna(riga[s]):
        nomi = str(riga[s]).replace(";", ",").split(",")
        tutti_nomi.extend([n.strip() for n in nomi])

tutti_nomi = list(set(tutti_nomi))

# =====================
# TROVA MANCANTI
# =====================
mancanti = []

for nome in tutti_nomi:
    if nome not in risposte_turno:
        mancanti.append(nome)

# =====================
# SE TUTTI HANNO RISPOSTO
# =====================
if not mancanti:
    print("Tutti hanno risposto 👍")
    exit()

# =====================
# MESSAGGIO REMINDER
# =====================
msg = f"⏳ Reminder turno {riga['Data'].strftime('%d/%m/%Y')}\n\n"
msg += "Non hanno ancora risposto:\n\n"
msg += "\n".join(mancanti)

# =====================
# INVIO TELEGRAM
# =====================
response = requests.post(url, data={
    "chat_id": CHAT_ID,
    "text": msg
})

print("Reminder inviato")
print(response.text)
