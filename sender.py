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
# INVIO PRINCIPALE (FIXED)
# =====================
def send():

    msg, date, keyboard = build_message()

    print("📤 INVIO TURNI IN CORSO...")

    res = requests.post(
        url,
        data={
            "chat_id": CHAT_ID,
            "text": msg,
            "reply_markup": json.dumps(keyboard)
        }
    )

    print("STATUS:", res.status_code)
    print("RESPONSE:", res.text)

    # =====================
    # CHECK ERRORI REALI
    # =====================
    if res.status_code != 200:
        raise Exception(f"Telegram error: {res.text}")

    try:
        data = res.json()
    except:
        raise Exception("Risposta Telegram non valida")

    if not data.get("ok"):
        raise Exception(f"Telegram refused message: {data}")

    print("✅ TURNI INVIATI CORRETTAMENTE:", date)

# =====================
# REMINDER ( SOLO NON RISPOSTI)
# =====================
def run_reminder():

    import pandas as pd

    master = get_master_message()
    if not master:
        print("Nessun messaggio master trovato")
        return

    chat_id = master["chat_id"]
    message_id = master["message_id"]
    date = master["date"]

    # =====================
    # EXCEL
    # =====================
    df = pd.read_excel("turni.xlsx")

    df = df[df["Data"].notna()].copy()
    df["Data"] = pd.to_datetime(df["Data"])
    df = df.sort_values("Data")

    riga = df.iloc[0]

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

    # =====================
    # SUPABASE
    # =====================
    res = supabase.table("responses").select("*").eq("date", date).execute()

    responded_users = {
        r["username"] for r in res.data if r["status"] == "ok"
    }

    # =====================
    # UI AGGIORNATA
    # =====================
    text = "📅 TURNI (AGGIORNATO)\n\n"

    text += "📋 RISPOSTE:\n\n"

    for u in expected_users:

        name = to_tag(u)

        if u in responded_users:
            text += f"🟢 {name}\n"
        else:
            text += f"🔴 {name}\n"

    # =====================
    # UPDATE MESSAGGIO MASTER
    # =====================
    requests.post(
        f"https://api.telegram.org/bot{BOT_TOKEN}/editMessageText",
        json={
            "chat_id": chat_id,
            "message_id": message_id,
            "text": text
        }
    )

    print("🔄 Messaggio master aggiornato (reminder live)")

# =====================
# REMINDER TUTTI
# =====================

def reminder_domani():

    import pandas as pd

    df = pd.read_excel("turni.xlsx")

    if df.empty:
        return

    df = df[df["Data"].notna()].copy()
    df["Data"] = pd.to_datetime(df["Data"])
    df = df.sort_values("Data")

    riga = df.iloc[0]
    date = riga["Data"].strftime("%Y-%m-%d")

    msg = "📢 PROMEMORIA DOMANI:\n\n"
    msg += "Non dimenticare i tuoi servizi per domani 👇\n\n"

    # =====================
    # ESTRAI TUTTI
    # =====================
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

    msg += "👥 Coinvolti:\n"

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

    print("📢 PROMEMORIA DOMENICA INVIATO")
    
# =====================
# SCHEDULER
# =====================
scheduler = BackgroundScheduler()

# 📅 Lunedì
scheduler.add_job(send, "cron", day_of_week="mon", hour=9, minute=0)

# ⏳ Giovedì
scheduler.add_job(run_reminder, "cron", day_of_week="thu", hour=9, minute=0)

# 📢 Sabato
scheduler.add_job(reminder_domani, "cron", day_of_week="sat", hour=10, minute=0)

scheduler.start()

print("🚀 Sender ATTIVO (auto + manuale OK)")