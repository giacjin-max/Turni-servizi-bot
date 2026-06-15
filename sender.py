import os
import json
import pandas as pd
import requests
from supabase import create_client
from apscheduler.schedulers.blocking import BlockingScheduler

# =====================
# CONFIG
# =====================
BOT_TOKEN = os.environ["BOT_TOKEN"]
CHAT_ID = os.environ["CHAT_ID"]

supabase = create_client(
    os.environ["SUPABASE_URL"],
    os.environ["SUPABASE_KEY"]
)

url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"

# =====================
# RUBRICA
# =====================
with open("rubrica.json", "r", encoding="utf-8") as f:
    rubrica = json.load(f)

def to_name(username):
    username = username.lower().replace("@", "")
    return rubrica.get(username, username)

# =====================
# DB
# =====================
def get_responses(date):
    res = supabase.table("responses").select("*").eq("date", date).execute()
    return {r["username"]: r["status"] for r in res.data}

# =====================
# BUILD TURNI
# =====================
def build_turni():

    df = pd.read_excel("turni.xlsx")

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
                msg += f"    {to_name(nome)}\n"

        msg += "\n"

    keyboard = {
        "inline_keyboard": [[
            {"text": "✅ OK", "callback_data": f"ok|{date}"}
        ]]
    }

    return msg, date, expected_users, keyboard

# =====================
# SEND PRINCIPALE
# =====================
def send():

    msg, date, _, keyboard = build_turni()

    res = requests.post(
        url,
        data={
            "chat_id": CHAT_ID,
            "text": msg,
            "reply_markup": json.dumps(keyboard)
        }
    )

    print("SEND STATUS:", res.status_code)
    print("DATE:", date)

# =====================
# REMINDER (SOLO NON RISPOSTI)
# =====================
def reminder():

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
        msg += f"• {to_name(u)}\n"

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

    print("REMINDER INVIATO:", date)

# =====================
# SCHEDULER
# =====================
scheduler = BlockingScheduler()

# 📅 LUNEDÌ: turni
scheduler.add_job(send, "cron", day_of_week="mon", hour=9, minute=0)

# ⏳ GIOVEDÌ: reminder intelligente
scheduler.add_job(reminder, "cron", day_of_week="thu", hour=9, minute=0)

# 📢 SABATO: reminder finale (stesso sistema)
scheduler.add_job(reminder, "cron", day_of_week="sat", hour=10, minute=0)

# =====================
# START
# =====================
if __name__ == "__main__":
    print("🚀 BOT SCHEDULER ATTIVO")
    scheduler.start()