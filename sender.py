import os
import json
import pandas as pd
import requests
from datetime import datetime

BOT_TOKEN = os.environ["BOT_TOKEN"]
CHAT_ID = os.environ["CHAT_ID"]

RUBRICA_FILE = "rubrica.json"

url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"

# =====================
# RUBRICA
# =====================
with open(RUBRICA_FILE, "r", encoding="utf-8") as f:
    rubrica = json.load(f)

def to_tag(name):
    return rubrica.get(name, name)

# =====================
# EXCEL
# =====================
df = pd.read_excel("turni.xlsx")
df = df[df["Data"].notna()].copy()
df["Data"] = pd.to_datetime(df["Data"])
df = df.sort_values("Data")

riga = df.iloc[0]
date = riga["Data"].strftime("%Y-%m-%d")

# =====================
# MESSAGGIO
# =====================
msg = f"📅 TURNI {riga['Data'].strftime('%d/%m/%Y')}\n\n"
msg += "👉 Rispondi ai turni cliccando i pulsanti\n\n"

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

    msg += "\n"

# =====================
# BOTTONI
# =====================
keyboard = {
    "inline_keyboard": [[
        {"text": "✅ OK", "callback_data": f"ok|{date}"},
        {"text": "❌ NON POSSO", "callback_data": f"no|{date}"}
    ]]
}

# =====================
# INVIO
# =====================
res = requests.post(
    url,
    data={
        "chat_id": CHAT_ID,
        "text": msg,
        "reply_markup": json.dumps(keyboard)
    }
)

print("STATUS:", res.status_code)
print("DATA:", date)
print("TURNI INVIATI")