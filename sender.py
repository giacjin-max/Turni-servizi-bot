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
# RUBRICA
# =====================
with open("rubrica.json", "r", encoding="utf-8") as f:
    rubrica = json.load(f)
    rubrica_name_to_username = rubrica
    rubrica_username_to_name = {v: k for k, v in rubrica.items()}

def to_username(name: str) -> str:
    return rubrica_name_to_username.get(name.strip(), name.strip())
    
def to_name(username: str) -> str:
    username = username.strip()
    return rubrica_username_to_name.get(username, username)

# =====================
# BUILD MESSAGGIO TURNI
# =====================
def build_message():

    df = pd.read_excel("turni.xlsx")

    if df.empty:
        return None

    df = df[df["Data"].notna()].copy()
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
            if not nome:
                continue

            username = to_username(nome)
            msg += f"    {username}\n"
            expected_users.add(username)

        msg += "\n"

    keyboard = {
        "inline_keyboard": [[
            {"text": "✅ OK", "callback_data": f"ok|{date}"}
        ]]
    }

    return msg, date, keyboard, expected_users, df, riga


# =====================
# SEND TURNI
# =====================
def send():

    result = build_message()
    if not result:
        return

    msg, date, keyboard, expected_users, df, riga = result

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

    message_id = data["result"]["message_id"]

    # =====================
    # SUPABASE CONFERMATI
    # =====================
    try:
        res_db = supabase.table("responses") \
            .select("*") \
            .eq("date", date) \
            .execute()

        confirmed_users = {
            r["username"].strip()
            for r in (res_db.data or [])
            if r.get("status") == "ok"
        }

    except Exception as e:
        print("Errore Supabase:", e)
        confirmed_users = set()

    # =====================
    # FOOTER FIXATO
    # =====================
    footer = "\n📌 Servizio\n\n"

    already_added = set()

    for col in df.columns:
        if col == "Data":
            continue

        value = riga[col]
        if pd.isna(value):
            continue

        nomi = str(value).replace(";", ",").split(",")

        for nome in nomi:
            nome = nome.strip()
            if not nome:
                continue

            if nome in already_added:
                continue

            already_added.add(nome)

            username = to_username(nome)

            if username in confirmed_users:
                footer += f"{nome} 🟢\n"
            else:
                footer += f"{nome}\n"

    msg += footer

    # =====================
    # UPDATE MESSAGGIO
    # =====================
    requests.post(
        f"https://api.telegram.org/bot{BOT_TOKEN}/editMessageText",
        json={
            "chat_id": CHAT_ID,
            "message_id": message_id,
            "text": msg,
            "reply_markup": keyboard
        }
    )

    print("✅ TURNI INVIATI:", date)


# =====================
# REMINDER GIOVEDÌ
# =====================
def run_reminder():

    msg = (
        "📢 PROMEMORIA SERVIZIO\n\n"
        "Ricordati di controllare i turni.\n"
    )

    try:
        df = pd.read_excel("turni.xlsx")

        df = df[df["Data"].notna()].copy()
        df["Data"] = pd.to_datetime(df["Data"], errors="coerce")
        df = df.dropna(subset=["Data"]).sort_values("Data")

        if df.empty:
            return

        today = pd.Timestamp.now().normalize()
        future_df = df[df["Data"] >= today]

        if future_df.empty:
            return

        riga = future_df.iloc[0]
        date = riga["Data"].strftime("%Y-%m-%d")

        expected_users = set()

        for col in df.columns:
            if col == "Data":
                continue

            value = riga[col]
            if pd.isna(value):
                continue

            nomi = str(value).replace(";", ",").split(",")

            for nome in nomi:
                nome = nome.strip()
                if nome:
                    expected_users.add(to_username(nome).strip())

        res = supabase.table("responses") \
            .select("*") \
            .eq("date", date) \
            .execute()

        confirmed_users = {
            r["username"].strip()
            for r in res.data or []
            if r.get("status") == "ok"
        }

        non_risposti = expected_users - confirmed_users

        if non_risposti:
            msg += "\n⛔ Non hanno ancora confermato:\n\n"
            for u in sorted(non_risposti):
                msg += f"{u}\n"
        else:
            msg += "\n✅ Tutti hanno già confermato"

    except Exception as e:
        print("Errore reminder:", e)
        msg += "\n⚠ errore"

    requests.post(
        url,
        json={
            "chat_id": CHAT_ID,
            "text": msg
        }
    )


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