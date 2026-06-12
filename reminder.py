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
# EXCEL (dd/mm/yyyy)
# =====================
df = pd.read_excel("turni.xlsx")

# ✔ IMPORTANTE: formato europeo
df["Data"] = pd.to_datetime(df["Data"], dayfirst=True)

# =====================
# PROSSIMO TURNO
# =====================
future = df[df["Data"] >= pd.Timestamp.now().normalize()]

if future.empty:
    print("Nessun turno trovato")
    exit()

riga = future.sort_values("Data").iloc[0]

date = riga["Data"].strftime("%Y-%m-%d")

done = responses.get(date, {})

# =====================
# MAPPA NOME → USERNAME (col A/B)
# =====================
users = {}

for _, row in df.iterrows():

    nome = str(row.iloc[0]).strip()
    username = row.iloc[1]

    if pd.notna(username):
        username = str(username).strip()

        if not username.startswith("@"):
            username = "@" + username

        users[nome] = username

def display_name(nome):
    return users.get(nome, nome)

# =====================
# SERVIZI
# =====================
servizi = [
    "Parola","Adorazione","Coro","BimbiGiovani","Piano","Bass",
    "Chitarra","Mix","PC","Porta","Pulizia","Pulizia sala bimbi",
    "Traduzione","Ronda"
]

# =====================
# MAPPA PERSONA → SERVIZI
# =====================
people_to_services = defaultdict(set)

for s in servizi:

    if s not in riga:
        continue

    valore = riga[s]

    # ❌ salta vuoti
    if pd.isna(valore):
        continue

    valore = str(valore).strip()

    if valore == "":
        continue

    nomi = valore.replace(";", ",").split(",")

    for n in nomi:

        n = n.strip()

        if not n:
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

    if not services:
        continue

    msg += f"• {display_name(person)} ({', '.join(services)})\n"

# =====================
# INVIO TELEGRAM
# =====================
requests.post(url, data={
    "chat_id": CHAT_ID,
    "text": msg
})

print("Reminder inviato correttamente")