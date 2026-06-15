import os
import json
import pandas as pd
import requests
from datetime import datetime
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
# MASTER MESSAGE
# =====================
def get_master_message():
    try:
        with open("last_message.json", "r") as f:
            return json.load(f)
    except:
        return None

# =====================
# BUILD MESSAGGIO
# =====================
def build_message():
    df = pd.read_excel("turni.xlsx")

    if df.empty:
        raise Exception("Excel vuoto: nessun turno trovato")

    df["Data"] = pd.to_datetime(df["Data"])
    df = df.sort_values("Data")

    today = pd.Timestamp.now()
    future_df = df[df["Data"] >= today]

    if future_df.empty:
        print("⛔ Nessun turno futuro trovato. Invio interrotto.")
        return None

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
# SEND TURNI
# =====================
def send():

    result = build_message()
    if not result:
        return

    msg, date, keyboard = result

    print("📤 INVIO TURNI...")

    res = requests.post(
        url,
        data={
            "chat_id": CHAT_ID,
            "text": msg,
            "reply_markup": json.dumps(keyboard)
        }
    )

    data = res.json()

    if not data.get("ok"):
        raise Exception(f"Telegram error: {data}")

    with open("last_message.json", "w") as f:
        json.dump({
            "chat_id": CHAT_ID,
            "message_id": data["result"]["message_id"],
            "date": date
        }, f)

    print("✅ TURNI INVIATI:", date)

# =====================
# 🔥 FIXED REMINDER GIOVEDÌ (NUOVO COMPORTAMENTO)
# =====================
def run_reminder():

    master = get_master_message()

    if not master:
        print("❌ Nessun messaggio master trovato")
        return

    chat_id = master["chat_id"]
    message_id = master["message_id"]
    date = master["date"]

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

    res = supabase.table("responses").select("*").eq("date", date).execute()

    responded_users = {
        r["username"] for r in res.data if r["status"] == "ok"
    }

    # utenti NON risposti
    missing_users = expected_users - responded_users

    # =====================
    # MESSAGGIO SEMPLICE (COME SABATO + EXTRA)
    # =====================
    text = "📢 PROMEMORIA SERVIZIO\n\n"
    text += "⏳ Non dimenticare di rispondere al turno!\n\n"

    if missing_users:
        text += "❌ NON ANCORA CONFERMATO:\n"
        for u in missing_users:
            text += f"• {to_tag(u)}\n"

    # STESSO IDENTICO BOTTONE
    keyboard = {
        "inline_keyboard": [[
            {"text": "✅ OK", "callback_data": f"ok|{date}"}
        ]]
    }

    requests.post(
        f"https://api.telegram.org/bot{BOT_TOKEN}/editMessageText",
        json={
            "chat_id": chat_id,
            "message_id": message_id,
            "text": text,
            "reply_markup": keyboard
        }
    )

    print("🔄 Reminder giovedì aggiornato")

# =====================
# REMINDER SABATO (UGUALE)
# =====================
def reminder_sabato():

    msg = (
        "📢 PROMEMORIA SERVIZIO\n\n"
        "Domani c’è il servizio.\n"
        "Controlla i turni e preparati."
    )

    requests.post(
        f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
        json={
            "chat_id": CHAT_ID,
            "text": msg
        }
    )

    print("📢 Reminder sabato inviato")