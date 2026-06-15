import os
import json
import pandas as pd
import requests
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
# RUBRICA (nome Excel → username Telegram)
# =====================
with open("rubrica.json", "r", encoding="utf-8") as f:
    rubrica = json.load(f)

def name_to_username(name: str) -> str:
    return rubrica.get(str(name).strip().lower(), str(name).strip().lower())

def username_to_name(username: str) -> str:
    reverse = {v.strip().lower(): k for k, v in rubrica.items()}
    return reverse.get(str(username).strip().lower(), username)

# =====================
# BUILD MESSAGGIO
# =====================
def build_message():

    df = pd.read_excel("turni.xlsx")

    if df.empty:
        return None

    df["Data"] = pd.to_datetime(df["Data"], errors="coerce")
    df = df.dropna(subset=["Data"]).sort_values("Data")

    today = pd.Timestamp.now().normalize()
    future_df = df[df["Data"] >= today]

    if future_df.empty:
        print("⛔ Nessun turno futuro trovato")
        return None

    riga = future_df.iloc[0]
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

        nomi = str(value).replace(";", ",").split(",")

        msg += f"• {col}\n"

        for nome in nomi:
            nome = nome.strip()
            if nome:
                username = name_to_username(nome)
                msg += f"    {username}\n"
                expected_users.add(nome.strip().lower())

        msg += "\n"

    keyboard = {
        "inline_keyboard": [[
            {"text": "✅ OK", "callback_data": f"ok|{date}"}
        ]]
    }

    return msg, date, keyboard, expected_users

# =====================
# SEND TURNI
# =====================
def send():

    result = build_message()
    if not result:
        return

    msg, date, keyboard, expected_users = result

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

    # =====================
    # SUPABASE CONFERMATI
    # =====================
    try:
        res_db = supabase.table("responses") \
            .select("*") \
            .eq("date", date) \
            .execute()

        confirmed_users = {
            r["username"].strip().lower()
            for r in (res_db.data or [])
            if r.get("status") == "ok"
        }

    except Exception as e:
        print("Errore Supabase:", e)
        confirmed_users = set()

    # =====================
    # FOOTER
    # =====================
    msg += "\n📌 Servizio\n"

    for u in sorted(expected_users):
        msg += f"{name_to_username(u)}\n"

    msg += "\n📋 Confermati\n"

    for u in sorted(confirmed_users):
        msg += f"{username_to_name(u)}\n"

    # aggiorna messaggio
    requests.post(
        f"https://api.telegram.org/bot{BOT_TOKEN}/editMessageText",
        json={
            "chat_id": CHAT_ID,
            "message_id": data["result"]["message_id"],
            "text": msg,
            "reply_markup": keyboard
        }
    )

    # salva master
    with open("last_message.json", "w", encoding="utf-8") as f:
        json.dump({
            "chat_id": CHAT_ID,
            "message_id": data["result"]["message_id"],
            "date": date
        }, f, indent=2)

    print("✅ TURNI INVIATI:", date)

# =====================
# 🔥 REMINDER GIOVEDÌ (NON MODIFICATO)
# =====================
def run_reminder():

    msg = (
        "📢 PROMEMORIA SERVIZIO\n\n"
        "Rispondi se non hai ancora confermato."
    )

    keyboard = {
        "inline_keyboard": [[
            {
                "text": "✅ OK",
                "callback_data": "ok|reminder"
            }
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
# REMINDER SABATO (NON MODIFICATO)
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