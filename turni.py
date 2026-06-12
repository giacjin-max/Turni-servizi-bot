import os
import pandas as pd
import requests
from datetime import datetime

BOT_TOKEN = os.environ["BOT_TOKEN"]
CHAT_ID = os.environ["CHAT_ID"]

df = pd.read_excel("turni.xlsx")

# Dizionario Nome -> Username
users = {}

for _, row in df.iterrows():
    nome = str(row["Nome"]).strip()

    username = row["Username Telegram"]

    if pd.notna(username):
        users[nome] = str(username).strip()

# Trova la prossima domenica
oggi = pd.Timestamp.now().normalize()

turni = df[df["Data"].notna()].copy()

turni["Data"] = pd.to_datetime(turni["Data"])

future = turni[turni["Data"] >= oggi]

if future.empty:
    raise Exception("Nessuna domenica futura trovata")

riga = future.sort_values("Data").iloc[0]

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

msg = f"📅 Turni Domenica {riga['Data'].strftime('%d/%m/%Y')}\n\n"

emoji = {
    "Parola": "📖",
    "Adorazione": "🙏",
    "Coro": "🎤",
    "BimbiGiovani": "👶",
    "Piano": "🎹",
    "Bass": "🎸",
    "Chitarra": "🎸",
    "Mix": "🎚",
    "PC": "💻",
    "Porta": "🚪",
    "Pulizia": "🧹",
    "Pulizia sala bimbi": "🧸",
    "Traduzione": "🌍",
    "Ronda": "🛡",
}

for servizio in servizi:

    valore = riga[servizio]

    if pd.isna(valore):
        continue

    nomi = [x.strip() for x in str(valore).replace(";", ",").split(",")]

    utenti = []

    for nome in nomi:

        if nome in users:
            utenti.append(users[nome])
        else:
            utenti.append(nome)

    msg += f"{emoji.get(servizio,'•')} {servizio}\n"
    msg += "\n".join(utenti)
    msg += "\n\n"

url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"

requests.post(
    url,
    data={
        "chat_id": CHAT_ID,
        "text": msg,
    },
)

print(msg)
