import os
import json
import pandas as pd
import requests
from datetime import datetime, timedelta
from apscheduler.schedulers.background import BackgroundScheduler
from supabase import create_client

# =====================
# CONFIG
# =====================
BOT_TOKEN = os.environ["BOT_TOKEN"]
CHAT_ID = os.environ["CHAT_ID"]

SUPABASE_URL = os.environ["SUPABASE_URL"]
SUPABASE_KEY = os.environ["SUPABASE_KEY"]

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"

# =====================
# RUBRICA
# =====================
with open("rubrica.json", "r", encoding="utf-8") as f:
    rubrica = json.load(f)

def to_tag(name):
    return rubrica.get(name, name)

# =====================
# EXCEL + PROSSIMO TURNO
# =====================
def get_next_shift():
    df = pd.read_excel("turni.xlsx")

    df = df[df["Data"].notna()].copy()
    df["Data"] = pd.to_datetime(df["Data"])
    df = df.sort_values("Data")

    today = datetime.now()

    future = df[df["Data"] >= today]

    if future.empty:
        return None

    return future.iloc[0]

# =====================
# CHECK DUPLICATI
# =====================
def already_sent(date):
    res = supabase.table("sent_logs").select("*").eq("date", date).execute()
    return len(res.data) > 0

def mark_sent(date):
    supabase.table("sent_logs").insert({"date": date}).execute()

# =====================
# BUILD MESSAGGIO
# =====================
def build_message(riga):
    date = riga["Data"].strftime("%Y-%m-%d")

    msg = f"📅 TURNI {riga['Data'].strftime('%d/%m/%Y')}\n\n"
    msg += "👉 Premi OK quando hai visto il turno\n\n"

    for col in riga.index:
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
# INVIO PRINCIPALE
# =====================
def send():
    riga = get_next_shift()

    if riga is None:
        print("❌ Nessun turno futuro")
        return

    date = riga["Data"].strftime("%Y-%m-%d")

    # anti duplicato
    if already_sent(date):
        print("⚠️ Turno già inviato:", date)
        return

    msg, date, keyboard = build_message(riga)

    res = requests.post(
        url,
        data={
            "chat_id": CHAT_ID,
            "text": msg,
            "reply_markup": json.dumps(keyboard)
        }
    )

    mark_sent(date)

    print("🚀 TURNI INVIATI:", date)

# =====================
# REMINDER SOLO NON RISPOSTI
# =====================
def reminder():

    res = supabase.table("responses").select("*").execute()
    responses = res.data

    # qui puoi personalizzare reminder
    msg = "⏳ Reminder: alcuni non hanno ancora risposto ai turni"

    requests.post(
        url,
        data={
            "chat_id": CHAT_ID,
            "text": msg
        }
    )

    print("🔔 REMINDER INVIATO")

# =====================
# SCHEDULER
# =====================
scheduler = BackgroundScheduler()

# 📅 Lunedì → invio turni
scheduler.add_job(send, "cron", day_of_week="mon", hour=9, minute=0)

# ⏳ Giovedì → reminder
scheduler.add_job(reminder, "cron", day_of_week="thu", hour=9, minute=0)

# 📢 Sabato → promemoria
scheduler.add_job(reminder, "cron", day_of_week="sat", hour=10, minute=0)

scheduler.start()

print("🚀 Sender PRO attivo")