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
# RUBRICA
# =====================
with open("rubrica.json", "r", encoding="utf-8") as f:
    rubrica = json.load(f)

def name_to_username(name: str) -> str:
    return rubrica.get(str(name).strip().lower(), str(name).strip().lower())

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

                # SERVIZI → username con @
                msg += f"    @{username}\n"

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
    # FOOTER (FIX FINALE)
    # =====================
    reverse_rubrica = {v.strip().lower(): k for k, v in rubrica.items()}

    msg += "\n📌 Servizio\n"

    for u in sorted(expected_users):
        msg += f"{u}\n"

    msg += "\n📋 Confermati\n"

    for u in sorted(confirmed_users):
        name = reverse_rubrica.get(u, u)
        msg += f"{name}\n"

    requests.post(
        f"https://api.telegram.org/bot{BOT_TOKEN}/editMessageText",
        json={
            "chat_id": CHAT_ID,
            "message_id": data["result"]["message_id"],
            "text": msg,
            "reply_markup": keyboard
        }
    )

    with open("last_message.json", "w", encoding="utf-8") as f:
        json.dump({
            "chat_id": CHAT_ID,
            "message_id": data["result"]["message_id"],
            "date": date
        }, f, indent=2)

    print("✅ TURNI INVIATI:", date)

# =====================
# REMINDER GIOVEDÌ
# =====================
def run_reminder():

    result = build_message()
    if not result:
        print("❌ Nessun turno")
        return

    _, date, _, expected_users = result

    try:
        res = supabase.table("responses") \
            .select("*") \
            .eq("date", date) \
            .execute()

        confirmed_users = {
            r["username"].strip().lower()
            for r in (res.data or [])
            if r.get("status") == "ok"
        }

    except Exception as e:
        print("Errore Supabase:", e)
        confirmed_users = set()

    pending_users = expected_users - confirmed_users

    msg = "📢 PROMEMORIA SERVIZIO\n\n"

    if not pending_users:
        msg += "✅ Tutti hanno già confermato"
    else:
        msg += "⛔ Non hanno ancora confermato:\n\n"

        for name in sorted(pending_users):
            msg += f"@{name_to_username(name)}\n"

    keyboard = {
        "inline_keyboard": [[
            {
                "text": "✅ OK",
                "callback_data": f"ok|{date}"
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