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
# CARICA EXCEL
# =====================
df = pd.read_excel("turni.xlsx")

# Dizionario Nome -> Username Telegram
users = {}

for _, row in df.iterrows():
    nome = str(row["Nome"]).strip()
    username = row.get("Username Telegram")

    if pd.notna(username):
        users[nome] = str(username).strip()

# =====================
# TROVA PROSSIMO TURNO
# =====================
oggi = pd.Timestamp.now().normalize()

turni = df[df["Data"].notna()].copy()
turni["Data"] = pd.to_datetime(turni["Data"])

future = turni[turni["Data"] >= oggi]

if future.empty:
    raise Exception("Nessun turno futuro trovato")

riga = future.sort_values("Data").iloc[0]

data_turno = riga["Data"]

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
    "Ronda": "🛡",
}

# =====================
# COSTRUZIONE MESSAGGIO
# =====================
msg = f"📅 Turni Domenica {data_turno.strftime('%d/%m/%Y')}\n\n"

for servizio in servizi:
    valore = riga.get(servizio)

    if pd.isna(valore):
        continue

    nomi = [x.strip() for x in str(valore).replace(";", ",").split(",")]

    utenti = []
    for nome in nomi:
        if nome in users:
            utenti.append(f"@{users[nome]}")
        else:
            utenti.append(nome)

    msg += f"{emoji.get(servizio,'•')} {servizio}\n"
    msg += "\n".join(utenti)
    msg += "\n\n"

# =====================
# BOTTONI TELEGRAM
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
# INVIO
# =====================
response = requests.post(url, data={
    "chat_id": CHAT_ID,
    "text": msg,
    "reply_markup": json.dumps(keyboard)
})

# =====================
# DEBUG
# =====================
print("STATUS:", response.status_code)
print("RISPOSTA:", response.text)
print("\nMESSAGGIO:\n", msg)
