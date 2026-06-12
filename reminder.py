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
    with open(DB_FILE, "r") as f:
        responses = json.load(f)
else:
    responses = {}

# =====================
# LOAD LOG REMINDER
# =====================
if os.path.exists(REMINDER_LOG_FILE):
    with open(REMINDER_LOG_FILE, "r") as f:
        reminder_log = json.load(f)
else:
    reminder_log = {}

# =====================
# LEGGI EXCEL
# =====================
df = pd.read_excel("turni.xlsx")

# Mappa Nome -> Username
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
# TROVA PROSSIMO TURNO
# =====================
turni = df[df["Data"].notna()].copy()

turni["Data"] = pd.to_datetime(turni["Data"])

oggi = pd.Timestamp.now().normalize()

future = turni[turni["Data"] >= oggi]

if future.empty:
    print("Nessun turno futuro trovato")
    exit()

riga = future.sort_values("Data").iloc[0]

date = riga["Data"].strftime("%Y-%m-%d")

# =====================
# INIT LOG DATA
# =====================
if date not in reminder_log:
    reminder_log[date] = {}

# =====================
# SERVIZI
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

# =====================
# PERSONA -> SERVIZI
# =====================
persone_servizi = {}

for servizio in servizi:

    if servizio not in riga:
        continue

    valore = riga[servizio]

    if pd.isna(valore):
        continue

    persone = str(valore).replace(";", ",")

    for nome in persone.split(","):

        nome = nome.strip()

        if not nome:
            continue

        if nome not in persone_servizi:
            persone_servizi[nome] = []

        persone_servizi[nome].append(servizio)

# =====================
# RISPOSTE GIA' FATTE
# =====================
done = responses.get(date, {})

# =====================
# MANCANTI
# =====================
missing = {}

for nome, lista_servizi in persone_servizi.items():

    tag = users.get(nome, nome)

    # non ha risposto
    # e non ha già ricevuto reminder
    if nome not in done and not reminder_log[date].get(tag):

        missing[nome] = lista_servizi

# =====================
# TUTTI HANNO RISPOSTO
# =====================
if not missing:
    print("Nessun reminder necessario")
    exit()

# =====================
# MESSAGGIO
# =====================
msg = (
    f"⏳ Reminder turno del "
    f"{riga['Data'].strftime('%d/%m/%Y')}\n\n"
)

for nome, lista_servizi in missing.items():

    tag = users.get(nome, nome)

    servizi_txt = ", ".join(lista_servizi)

    msg += f"{tag} ({servizi_txt})\n"

# =====================
# INVIO TELEGRAM
# =====================
response = requests.post(
    url,
    data={
        "chat_id": CHAT_ID,
        "text": msg
    }
)

print("STATUS:", response.status_code)
print("RISPOSTA:", response.text)

# =====================
# SALVA LOG REMINDER
# =====================
if response.status_code == 200:

    for nome in missing:

        tag = users.get(nome, nome)

        reminder_log[date][tag] = True

    with open(REMINDER_LOG_FILE, "w") as f:
        json.dump(
            reminder_log,
            f,
            indent=2,
            ensure_ascii=False
        )

    print("Reminder salvato")
