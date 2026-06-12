import json
import os
import requests
import pandas as pd
from datetime import datetime

# =====================
# CONFIG
# =====================
BOT_TOKEN = os.environ["BOT_TOKEN"]
CHAT_ID = os.environ["CHAT_ID"]

URL = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"

RUBRICA_FILE = "rubrica.json"
EXPECTED_FILE = "expected_users.json"
RESPONSES_FILE = "responses.json"


# =====================
# LOAD RUBRICA
# =====================
def load_rubrica():
    try:
        with open(RUBRICA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return {}


rubrica = load_rubrica()


def to_tag(nome):
    nome = str(nome).strip()
    return rubrica.get(nome, nome)


# =====================
# SAVE EXPECTED USERS
# =====================
def save_expected(date, users):
    data = {}

    if os.path.exists(EXPECTED_FILE):
        with open(EXPECTED_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)

    data[date] = list(set(users))

    with open(EXPECTED_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


# =====================
# LOAD EXCEL
# =====================
df = pd.read_excel("turni.xlsx")
df = df[df["Data"].notna()].copy()
df["Data"] = pd.to_datetime(df["Data"])

riga = df.sort_values("Data").iloc[0]
date = riga["Data"].strftime("%Y-%m-%d")


# =====================
# BUILD USERS ATTESI
# =====================
users = set()

for _, row in df.iterrows():

    nome = str(row["Nome"]).strip()

    username = row.get("Username Telegram")

    if pd.notna(username):

        username = str(username).strip()

        if not username.startswith("@"):
            username = "@" + username

        users.add(username.lower())


# salva chi deve rispondere
save_expected(date, list(users))


# =====================
# BUILD MESSAGGIO
# =====================
msg = f"📅 TURNI {riga['Data'].strftime('%d/%m/%Y')}\n\n"

msg += "👉 Rispondi ai turni cliccando i pulsanti\n\n"


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
# MESSAGGIO TURNI
# =====================
for servizio in servizi:

    if servizio not in riga:
        continue

    valore = riga[servizio]

    if pd.isna(valore):
        continue

    nomi = str(valore).replace(";", ",").split(",")

    msg += f"{emoji.get(servizio,'•')} {servizio}\n"

    for nome in nomi:

        nome = nome.strip()
        if not nome:
            continue

        tag = to_tag(nome)

        msg += f"   ⏳ {tag}\n"

    msg += "\n"


# =====================
# BOTTONI
# =====================
keyboard = {
    "inline_keyboard": [
        [
            {"text": "✅ OK", "callback_data": f"ok|{date}"},
            {"text": "❌ NON POSSO", "callback_data": f"no|{date}"}
        ]
    ]
}


# =====================
# INVIO
# =====================
res = requests.post(
    URL,
    data={
        "chat_id": CHAT_ID,
        "text": msg,
        "reply_markup": json.dumps(keyboard)
    }
)

print("STATUS:", res.status_code)
print("TURNI INVIATI")
print("DATA:", date)
print("UTENTI ATTESI:", len(users))
