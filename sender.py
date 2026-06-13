import os
import json
import pandas as pd
import sqlite3
import requests

BOT_TOKEN = os.environ["BOT_TOKEN"]
CHAT_ID = os.environ["CHAT_ID"]

DB_NAME = "bot.db"
RUBRICA_FILE = "rubrica.json"

url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"


# =====================
# DB INIT EXPECTED
# =====================
def save_expected(date, users):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()

    for u in users:
        c.execute("INSERT OR IGNORE INTO expected VALUES (?, ?)", (date, u))

    conn.commit()
    conn.close()


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
# EXCEL
# =====================
df = pd.read_excel("turni.xlsx")
df = df[df["Data"].notna()].copy()
df["Data"] = pd.to_datetime(df["Data"])

riga = df.sort_values("Data").iloc[0]
date = riga["Data"].strftime("%Y-%m-%d")

expected_users = set()

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

        expected_users.add(tag.replace("@", "").lower())

    msg += "\n"


# =====================
# SAVE EXPECTED SQLITE
# =====================
save_expected(date, expected_users)


# =====================
# BUTTONS
# =====================
keyboard = {
    "inline_keyboard": [[
        {"text": "✅ OK", "callback_data": f"ok|{date}"},
        {"text": "❌ NON POSSO", "callback_data": f"no|{date}"}
    ]]
}


# =====================
# SEND
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
