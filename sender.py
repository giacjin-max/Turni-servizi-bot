import os
import json
import pandas as pd
import requests
from apscheduler.schedulers.background import BackgroundScheduler

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
# BUILD MESSAGGIO
# =====================
def build_message():
    df = pd.read_excel("turni.xlsx")

    df = df[df["Data"].notna()].copy()
    df["Data"] = pd.to_datetime(df["Data"])
    df = df.sort_values("Data")

    riga = df.iloc[0]
    date = riga["Data"].strftime("%Y-%m-%d")

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

    keyboard = {
        "inline_keyboard": [[
            {"text": "✅ OK", "callback_data": f"ok|{date}"}
        ]]
    }

    return msg, date, keyboard

# =====================
# INVIO (FUNZIONE IMPORTANTE)
# =====================
def send():
    msg, date, keyboard = build_message()

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

# =====================
# SCHEDULER
# =====================
scheduler = BackgroundScheduler()

# 📅 Lunedì
scheduler.add_job(send, "cron", day_of_week="mon", hour=9, minute=0)

# ⏳ Giovedì
scheduler.add_job(send, "cron", day_of_week="thu", hour=9, minute=0)

# 📢 Sabato
scheduler.add_job(send, "cron", day_of_week="sat", hour=10, minute=0)

# =====================
# START SCHEDULER
# =====================
scheduler.start()

print("🚀 Sender attivo (auto + manuale ready)")