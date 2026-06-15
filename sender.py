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

# =====================
# RUBRICA
# =====================
with open("rubrica.json", "r", encoding="utf-8") as f:
    rubrica = json.load(f)

def to_tag(name: str) -> str:
    key = str(name).strip().lower()
    return rubrica.get(key, name)

# =====================
# MASTER MESSAGE (non usata ma mantenuta)
# =====================
def get_master_message():
    try:
        with open("last_message.json", "r") as f:
            return json.load(f)
    except:
        return None

# =====================
# BUILD MESSAGGIO TURNI
# =====================
def build_message():
    try:
        df = pd.read_excel("turni.xlsx")
    except Exception as e:
        print("Errore lettura turni.xlsx:", e)
        return None

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

    try:
        res = requests.post(
            f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
            json={
                "chat_id": CHAT_ID,
                "text": msg,
                "reply_markup": keyboard
            }
        )

        data = res.json()

        if not data.get("ok"):
            raise Exception(f"Telegram error: {data}")

        with open("last_message.json", "w", encoding="utf-8") as f:
            json.dump({
                "chat_id": CHAT_ID,
                "message_id": data["result"]["message_id"],
                "date": date
            }, f, ensure_ascii=False, indent=2)

        print("✅ TURNI INVIATI:", date)

    except Exception as e:
        print("Errore send():", e)

# =====================
# 🔥 REMINDER GIOVEDÌ
# =====================
def run_reminder():
    msg = (
        "📢 PROMEMORIA SERVIZIO\n\n"
        "Rispondere se non hai fatto.\n"
    )

    try:
        df = pd.read_excel("turni.xlsx")
        df["Data"] = pd.to_datetime(df["Data"], errors="coerce")
        df = df.dropna(subset=["Data"]).sort_values("Data")

        if df.empty:
            return

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

        res = supabase.table("responses").select("*").execute()

        responded_users = {
            r["username"].strip().lower()
            for r in (res.data or [])
            if r.get("status") == "ok"
        }

        non_risposti = expected_users - responded_users

        if non_risposti:
            msg += "\nNon hanno ancora confermato:\n\n"
            for u in sorted(non_risposti):
                msg += f"{to_tag(u)}\n"

    except Exception as e:
        print("Errore supabase/reminder:", e)

    keyboard = {
        "inline_keyboard": [[
            {"text": "✅ OK", "callback_data": "ok|reminder"}
        ]]
    }

    try:
        res = requests.post(
            f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
            json={
                "chat_id": CHAT_ID,
                "text": msg,
                "reply_markup": keyboard
            }
        )

        if not res.json().get("ok"):
            print("Errore Telegram reminder:", res.text)

        print("📢 Reminder giovedì inviato")

    except Exception as e:
        print("Errore run_reminder():", e)

# =====================
# REMINDER SABATO
# =====================
def reminder_sabato():
    msg = (
        "📢 PROMEMORIA SERVIZIO\n\n"
        "Domani c’è il servizio.\n"
        "Controlla i turni e preparati."
    )

    try:
        res = requests.post(
            f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
            json={
                "chat_id": CHAT_ID,
                "text": msg
            }
        )

        if not res.json().get("ok"):
            print("Errore Telegram sabato:", res.text)

        print("📢 Reminder sabato inviato")

    except Exception as e:
        print("Errore reminder_sabato:", e)