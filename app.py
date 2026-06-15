import os
import json
import pandas as pd
import requests
from datetime import datetime
from apscheduler.schedulers.background import BackgroundScheduler

# =====================
# CONFIG
# =====================
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

    if df.empty:
        raise Exception("Excel vuoto: nessun turno trovato")

    df["Data"] = pd.to_datetime(df["Data"])

    # 🔥 FIX: prendi SOLO turni futuri
    now = pd.Timestamp.now()
    future_df = df[df["Data"] >= now].sort_values("Data")

    # STOP se non ci sono turni futuri
    if future_df.empty:
        print("⛔ Nessun turno futuro trovato. Invio interrotto.")
        return None, None, None

    riga = future_df.iloc[0]
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
            if nome:
                msg += f"    {to_tag(nome)}\n"

        msg += "\n"

    keyboard = {
        "inline_keyboard": [[
            {"text": "✅ OK", "callback_data": f"ok|{date}"}
        ]]
    }

    return msg, date, keyboard

# =====================
# INVIO
# =====================
def send():

    msg, date, keyboard = build_message()

    if msg is None:
        return

    print("📤 INVIO TURNI...")

    res = requests.post(
        url,
        data={
            "chat_id": CHAT_ID,
            "text": msg,
            "reply_markup": json.dumps(keyboard)
        }
    )

    print(res.status_code, res.text)

# =====================
# REMINDER (giovedì)
# =====================
def run_reminder():

    df = pd.read_excel("turni.xlsx")
    df["Data"] = pd.to_datetime(df["Data"])

    now = pd.Timestamp.now()
    future_df = df[df["Data"] >= now].sort_values("Data")

    if future_df.empty:
        print("⛔ Nessun turno futuro → reminder non inviato")
        return

    riga = future_df.iloc[0]
    date = riga["Data"].strftime("%Y-%m-%d")

    expected_users = set()

    for col in df.columns:
        if col == "Data":
            continue

        value = riga[col]
        if pd.isna(value):
            continue

        for nome in str(value).replace(";", ",").split(","):
            nome = nome.strip().lower()
            if nome:
                expected_users.add(nome)

    print("📢 Reminder giovedì attivo per:", date, expected_users)

# =====================
# REMINDER SABATO
# =====================
def reminder_sabato():

    msg = (
        "📢 PROMEMORIA SERVIZIO\n\n"
        "Domani c’è il servizio.\n"
        "Controlla i turni e preparati per il tuo incarico."
    )

    requests.post(
        url,
        json={
            "chat_id": CHAT_ID,
            "text": msg
        }
    )

    print("📢 Reminder sabato inviato")

# =====================
# SCHEDULER
# =====================
scheduler = BackgroundScheduler(timezone="Europe/Rome")

scheduler.add_job(
    send,
    "cron",
    day_of_week="mon",
    hour=10,
    minute=0
)

# 🔥 GIOVEDÌ CORRETTO
scheduler.add_job(
    run_reminder,
    "cron",
    day_of_week="thu",
    hour=12,
    minute=40
)

scheduler.add_job(
    reminder_sabato,
    "cron",
    day_of_week="sat",
    hour=10,
    minute=0
)

scheduler.start()

print("🚀 Sender ATTIVO (auto + reminder OK)")