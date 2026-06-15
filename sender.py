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
def run_reminder():

    master = get_master_message()

    if not master:
        print("❌ Nessun messaggio master trovato")
        return

    date = master["date"]

    # =====================
    # LEGGI TURNO
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
    # RISPOSTE DA SUPABASE
    # =====================
    res = supabase.table("responses") \
        .select("*") \
        .eq("date", date) \
        .execute()

    responded_users = {
        r["username"]
        for r in res.data
        if r["status"] == "ok"
    }

    non_risposti = expected_users - responded_users

    # =====================
    # MESSAGGIO
    # =====================
    msg = "📢 PROMEMORIA RISPOSTA TURNI\n\n"

    if non_risposti:

        msg += "Non hanno ancora confermato:\n\n"

        for u in sorted(non_risposti):
            msg += f"{to_tag(u)}\n"

        msg += "\nPremi il pulsante qui sotto per confermare."

    else:

        msg += "✅ Tutti hanno già confermato."

    # =====================
    # STESSO BOTTONE OK
    # =====================
    keyboard = {
        "inline_keyboard": [[
            {
                "text": "✅ OK",
                "callback_data": f"ok|{date}"
            }
        ]]
    }

    # =====================
    # INVIO MESSAGGIO
    # =====================
    requests.post(
        f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
        json={
            "chat_id": CHAT_ID,
            "text": msg,
            "reply_markup": keyboard
        }
    )

    print("📢 Reminder giovedì inviato")

# =====================
# 🔥 FIXED REMINDER GIOVEDÌ (NUOVO COMPORTAMENTO)
# =====================
def run_reminder():

    master = get_master_message()

    if not master:
        print("❌ Nessun messaggio master trovato")
        return

    date = master["date"]

    msg = (
        "📢 PROMEMORIA RISPOSTA TURNI\n\n"
        "Se non hai ancora confermato la lettura dei turni, "
        "premi il pulsante qui sotto."
    )

    keyboard = {
        "inline_keyboard": [[
            {"text": "✅ OK", "callback_data": f"ok|{date}"}
        ]]
    }

    requests.post(
        f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
        json={
            "chat_id": CHAT_ID,
            "text": msg,
            "reply_markup": keyboard
        }
    )

    print("📢 Reminder giovedì inviato")

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