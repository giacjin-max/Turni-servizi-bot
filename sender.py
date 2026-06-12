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

SEND_URL = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"

LOG_FILE = "sent_log.json"

# =====================
# ORARIO INVIO
# =====================
now = datetime.now()

weekday = now.weekday()  # lun=0 ... dom=6
hour = now.hour

send = False
message_type = ""

# LUNEDI' SERA
if weekday == 0 and hour >= 18:
    send = True
    message_type = "monday"

# SABATO MATTINA
elif weekday == 5 and hour < 12:
    send = True
    message_type = "saturday"

if not send:
    print("Non è orario di invio")
    exit()

# =====================
# LOAD LOG
# =====================
if os.path.exists(LOG_FILE):
    with open(LOG_FILE, "r") as f:
        sent_log = json.load(f)
else:
    sent_log = {}

today_key = f"{now.strftime('%Y-%m-%d')}_{message_type}"

if sent_log.get(today_key):
    print("Messaggio già inviato")
    exit()

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
    raise Exception("Nessun turno futuro trovato")

riga = future.sort_values("Data").iloc[0]

data_turno = riga["Data"]

# =====================
# TITOLO
# =====================
if message_type == "monday":
    titolo = "📌 Turni della settimana"
else:
    titolo = "🔔 Promemoria turni"

msg = (
    f"{titolo}\n\n"
    f"📅 Domenica {data_turno.strftime('%d/%m/%Y')}\n\n"
)

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

emoji = {
    "Parola": "📖",
    "Adorazione": "🙌🏻",
    "Coro": "🎤",
    "BimbiGiovani": "👦🏻",
    "Piano": "🎹",
    "Bass": "🎸",
    "Chitarra": "🎸",
    "Mix": "🎧",
    "PC": "💻",
    "Porta": "🚪",
    "Pulizia": "🧹",
    "Pulizia sala bimbi": "🧹",
    "Traduzione": "🗣️",
    "Ronda": "🛡️",
}

# =====================
# COSTRUISCI MESSAGGIO
# =====================
for servizio in servizi:

    valore = riga.get(servizio)

    if pd.isna(valore):
        continue

    nomi = [
        x.strip()
        for x in str(valore).replace(";", ",").split(",")
    ]

    utenti = []

    for nome in nomi:

        if nome in users:
            utenti.append(users[nome])
        else:
            utenti.append(nome)

    msg += f"{emoji.get(servizio,'•')} {servizio}\n"
    msg += "\n".join(utenti)
    msg += "\n\n"

# =====================
# BOTTONI
# =====================
keyboard = {
    "inline_keyboard": [
        [
            {
                "text": "✅ OK",
                "callback_data": f"ok|{data_turno.strftime('%Y-%m-%d')}"
            },
            {
                "text": "❌ NON POSSO",
                "callback_data": f"no|{data_turno.strftime('%Y-%m-%d')}"
            }
        ]
    ]
}

# =====================
# INVIO TELEGRAM
# =====================
response = requests.post(
    SEND_URL,
    data={
        "chat_id": CHAT_ID,
        "text": msg,
        "reply_markup": json.dumps(keyboard),
    },
)

print("STATUS:", response.status_code)
print("RISPOSTA:", response.text)

# =====================
# SALVA LOG
# =====================
if response.status_code == 200:

    sent_log[today_key] = {
        "sent_at": now.isoformat(),
        "turno": data_turno.strftime("%Y-%m-%d")
    }

    with open(LOG_FILE, "w") as f:
        json.dump(sent_log, f, indent=2)

    print("Invio registrato")
