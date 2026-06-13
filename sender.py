import os
import json
import pandas as pd
import requests

BOT_TOKEN = os.environ["BOT_TOKEN"]
CHAT_ID = os.environ["CHAT_ID"]

url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"

# =====================
# RUBRICA
# =====================
with open("rubrica.json", "r", encoding="utf-8") as f:
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
msg += "👉 Premi OK quando hai visto il turno\n\n"

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

        msg += f"    {to_tag(nome)}\n"

    msg += "\n"

# =====================
# SOLO TASTO OK
# =====================
keyboard = {
    "inline_keyboard": [[
        {"text": "✅ OK", "callback_data": f"ok|{date}"}
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