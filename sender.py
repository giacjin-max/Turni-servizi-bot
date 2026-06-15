import os
import json
import pandas as pd
import requests
from apscheduler.schedulers.background import BackgroundScheduler
from supabase import create_client

# =====================
# CONFIG
# =====================
BOT_TOKEN = os.environ["BOT_TOKEN"]
CHAT_ID = os.environ["CHAT_ID"]
SUPABASE_URL = os.environ["SUPABASE_URL"]
SUPABASE_KEY = os.environ["SUPABASE_KEY"]

url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# =====================
# RUBRICA (NO NORMALIZE)
# =====================
with open("rubrica.json", "r", encoding="utf-8") as f:
    rubrica = json.load(f)

def to_tag(name: str) -> str:
    return rubrica.get(name.strip(), name.strip())

# =====================
# BUILD MESSAGGIO
# =====================
def build_message():

    df = pd.read_excel("turni.xlsx")

    if df.empty:
        raise Exception("Excel vuoto")

    df = df[df["Data"].notna()].copy()
    df["Data"] = pd.to_datetime(df["Data"], errors="coerce")
    df = df.dropna(subset=["Data"]).sort_values("Data")

    if df.empty:
        return None

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

    data = res.json()

    if not data.get("ok"):
        print("Errore Telegram:", data)
        return

    print("✅ TURNI INVIATI:", date)

# =====================
# REMINDER GIOVEDÌ (FIXED)
# =====================
def run_reminder():

    msg = (
        "📢 PROMEMORIA SERVIZIO\n\n"
        "Ricordati di rispondere.\n"
    )

    keyboard = {
        "inline_keyboard": [[
            {"text": "✅ OK", "callback_data": "ok|reminder"}
        ]]
    }

    requests.post(
        url,
        json={
            "chat_id": CHAT_ID,
            "text": msg,
            "reply_markup": keyboard
        }
    )

    print("📢 Reminder giovedì inviato")

# =====================
# REMINDER SABATO
# =====================
def reminder_sabato():

    msg = (
        "📢 PROMEMORIA SERVIZIO\n\n"
        "Domani c’è il servizio.\n"
        "Controlla i turni e preparati."
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
scheduler = BackgroundScheduler()

scheduler.add_job(send, "cron", day_of_week="mon", hour=9, minute=0)
scheduler.add_job(run_reminder, "cron", day_of_week="thu", hour=9, minute=0)
scheduler.add_job(reminder_sabato, "cron", day_of_week="sat", hour=10, minute=0)

scheduler.start()

print("🚀 BOT ATTIVO")