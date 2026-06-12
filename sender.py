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

# prossimo turno
riga = df.sort_values("Data").iloc[0]
date = riga["Data"].strftime("%Y-%m-%d")

done = responses.get(date, {})

# =====================
# USERS
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
# SERVIZI
# =====================
servizi = [
    "Parola","Adorazione","Coro","BimbiGiovani","Piano","Bass",
    "Chitarra","Mix","PC","Porta","Pulizia","Pulizia sala bimbi",
    "Traduzione","Ronda",
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
# MESSAGGIO
# =====================
msg = f"📅 TURNI {riga['Data'].strftime('%d/%m/%Y')}\n\n"

for servizio in servizi:

    if servizio not in riga:
        continue

    valore = riga[servizio]

    if pd.isna(valore):
        continue

    nomi = [
        x.strip()
        for x in str(valore).replace(";", ",").split(",")
    ]

    msg += f"{emoji.get(servizio,'•')} {servizio}\n"

    for nome in nomi:

        if not nome:
            continue

        tag = users.get(nome, nome)

        if nome in done:

            status = done[nome]["status"]

            if status == "ok":
                msg += f"   ✅ {tag} (confermato)\n"
            else:
                msg += f"   ❌ {tag} (non disponibile)\n"

        else:
            msg += f"   ⏳ {tag}\n"

    msg += "\n"

# =====================
# BOTTONI GLOBALI (SOLO 2)
# =====================
keyboard = {
    "inline_keyboard": [
        [
            {
                "text": "✅ OK",
                "callback_data": f"ok|{date}"
            },
            {
                "text": "❌ NON POSSO",
                "callback_data": f"no|{date}"
            }
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
print("RISPOSTA:", response.text)
print("Turni inviati con bottoni globali")
