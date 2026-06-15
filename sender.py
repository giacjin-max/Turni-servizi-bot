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

# =====================
# RUBRICA (nome Excel -> @username)
# =====================
with open("rubrica.json", "r", encoding="utf-8") as f:
    rubrica = json.load(f)

def normalize(name: str) -> str:
    return " ".join(str(name).strip().lower().split())

def to_username(name: str) -> str:
    key = normalize(name)
    return rubrica.get(key, name)

# =====================
# BUILD MESSAGGIO
# =====================
def build_message():

    df = pd.read_excel("turni.xlsx")

    if df.empty:
        return None

    df["Data"] = pd.to_datetime(df["Data"], errors="coerce")
    df = df.dropna(subset=["Data"]).sort_values("Data")

    riga = df.iloc[0]
    date = riga["Data"].strftime("%Y-%m-%d")

    msg = f"📅 TURNI {riga['Data'].strftime('%d/%m/%Y')}\n\n"

    footer_names = set()

    # =====================
    # SERVIZI -> USERNAME
    # =====================
    for col in df.columns:
        if col == "Data":
            continue

        value = riga[col]
        if pd.isna(value):
            continue

        names = str(value).split(",")

        msg += f"• {col}\n"

        for name in names:
            name = normalize(name)
            if not name:
                continue

            username = to_username(name)

            msg += f"   {username}\n"

            footer_names.add(name)

        msg += "\n"

    # =====================
    # FOOTER -> NOMI EXCEL
    # =====================
    msg += "📌 FOOTER\n\n"

    for n in sorted(footer_names):
        msg += f"{n}\n"

    keyboard = {
        "inline_keyboard": [[
            {"text": "✅ OK", "callback_data": f"ok|{date}"}
        ]]
    }

    return msg, date, keyboard

# =====================
# SEND
# =====================
def send():

    result = build_message()
    if not result:
        return

    msg, date, keyboard = result

    res = requests.post(
        url,
        json={
            "chat_id": CHAT_ID,
            "text": msg,
            "reply_markup": keyboard
        }
    )

    if res.status_code == 200:
        print("✅ Messaggio inviato:", date)
    else:
        print("❌ Errore Telegram:", res.text)