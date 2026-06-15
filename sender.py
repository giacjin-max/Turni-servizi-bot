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

url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"

supabase = create_client(
    os.environ["SUPABASE_URL"],
    os.environ["SUPABASE_KEY"]
)

# =====================
# RUBRICA
# =====================
with open("rubrica.json", "r", encoding="utf-8") as f:
    rubrica = json.load(f)

def to_tag(name):
    return rubrica.get(name, name)

# =====================
# GET RISPOSTE
# =====================
def get_responses(date):
    res = supabase.table("responses").select("*").eq("date", date).execute()
    return {r["username"]: r["status"] for r in res.data}

# =====================
# BUILD TURNI
# =====================
def build_turni():

    df = pd.read_excel("turni.xlsx")

    if df.empty:
        return None

    df = df[df["Data"].notna()].copy()
    df["Data"] = pd.to_datetime(df["Data"])
    df = df.sort_values("Data")

    riga = df.iloc[0]
    date = riga["Data"].strftime("%Y-%m-%d")

    msg = f"📅 TURNI {riga['Data'].strftime('%d/%m/%Y')}\n\n"
    msg += "👉 Premi OK quando hai visto il turno\n\n"

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

        msg += f"• {col}\n"

        for nome in str(value).replace(";", ",").split(","):
            nome = nome.strip()
            if nome:
                msg += f"    {to_tag(nome)}\n"

        msg += "\n"

    keyboard = {
        "inline_keyboard": [[
            {"text": "✅ OK", "callback_data": f"ok|{date}"}
        ]]
    }

    return msg, date, expected_users, keyboard

# =====================
# SEND TURNI (LUNEDÌ)
# =====================
def send():

    result = build_turni()
    if not result:
        return

    msg, date, _, keyboard = result

    print("📤 INVIO TURNI...")

    requests.post(
        url,
        json={
            "chat_id": CHAT_ID,
            "text": msg,
            "reply_markup": keyboard
        }
    )

    print("✅ TURNI INVIATI:", date)

# =====================
# REMINDER (GIOVEDÌ)
# =====================
def run_reminder():

    msg, date, expected_users, _ = build_turni()

    responses = get_responses(date)

    responded_users = {
        u for u, s in responses.items() if s == "ok"
    }

    non_responded = expected_users - responded_users

    if not non_responded:
        print("NESSUN REMINDER NECESSARIO")
        return

    msg = "⏳ Reminder: devi ancora confermare:\n\n"

    for u in non_responded:
        msg += f"• {to_tag(u)}\n"

    keyboard = {
        "inline_keyboard": [[
            {"text": "✅ OK", "callback_data": f"ok|{date}"}
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

    print("📨 REMINDER INVIATO:", date)

# =====================
# PROMEMORIA SABATO (DOMANI)
# =====================
def reminder_domani():

    df = pd.read_excel("turni.xlsx")

    if df.empty:
        return

    df = df[df["Data"].notna()].copy()
    df["Data"] = pd.to_datetime(df["Data"])
    df = df.sort_values("Data")

    riga = df.iloc[0]
    date = riga["Data"].strftime("%Y-%m-%d")

    msg = "📢 PROMEMORIA DOMANI:\n\n"
    msg += "Non dimenticare i servizi di domani 👇\n\n"

    all_users = set()

    for col in df.columns:
        if col == "Data":
            continue

        value = riga[col]
        if pd.isna(value):
            continue

        for nome in str(value).replace(";", ",").split(","):
            nome = nome.strip()
            if nome:
                all_users.add(nome)

    msg += "👥 Coinvolti:\n\n"

    for u in all_users:
        msg += f"• {to_tag(u)}\n"

    keyboard = {
        "inline_keyboard": [[
            {"text": "✅ OK", "callback_data": f"ok|{date}"}
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

    print("📢 PROMEMORIA SABATO INVIATO")

# =====================
# SCHEDULER
# =====================
scheduler = BackgroundScheduler()

scheduler.add_job(send, "cron", day_of_week="mon", hour=9, minute=0)
scheduler.add_job(run_reminder, "cron", day_of_week="thu", hour=9, minute=0)
scheduler.add_job(reminder_domani, "cron", day_of_week="sat", hour=10, minute=0)

scheduler.start()

print("🚀 BOT ATTIVO: turni + reminder + promemoria")