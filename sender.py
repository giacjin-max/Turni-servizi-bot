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


# =====================
# RUBRICA
# =====================
def load_rubrica():
    try:
        with open(RUBRICA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return {}


rubrica = load_rubrica()


def to_tag(name):
    name = str(name).strip()
    return rubrica.get(name, name)


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
# COSTRUISCI UTENTI ATTESI
# =====================
expected_users = set()


# =====================
# MESSAGGIO
# =====================
msg = f"📅 TURNI {riga['Data'].strftime('%d/%m/%Y')}\n\n"
msg += "👉 Rispondi ai turni cliccando i pulsanti\n\n"


# =====================
# RUOLI (COLONNE EXCEL)
# =====================
for col in df.columns:

    if col == "Data":
        continue

    value = riga[col]

    if pd.isna(value):
        continue

    nomi = str(value).replace(";", ",").split(",")

    msg += f"• {col}\n"

    for nome in nomi:

        nome = nome.strip()

        if not nome:
            continue

        tag = to_tag(nome)

        msg += f"    {tag}\n"

        # salva per reminder / tracking
        expected_users.add(tag.lower())

    msg += "\n"


# =====================
# SALVA EXPECTED USERS
# =====================
save_expected(date, list(expected_users))


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
# INVIO TELEGRAM
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
print("DATA:", date)
print("TURNI INVIATI")
print("UTENTI ATTESI:", len(expected_users))
