import os
import json
import pandas as pd
import requests
from apscheduler.schedulers.background import BackgroundScheduler

# =====================
# CONFIG
# =====================
BOT_TOKEN = os.environ["BOT_TOKEN"]
CHAT_ID = os.environ["CHAT_ID"]

url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"

# =====================
# RUBRICA (NORMALIZZATA)
# =====================
with open("rubrica.json", "r", encoding="utf-8") as f:
    rubrica = json.load(f)

def normalize(name: str) -> str:
    return str(name).strip().lower()

def to_tag(name: str) -> str:
    """
    Excel name -> Telegram username
    FIX: normalizzazione chiave
    """
    key = normalize(name)
    return rubrica.get(key, name)

# =====================
# BUILD MESSAGGIO
# =====================
def build_message():

    df = pd.read_excel("turni.xlsx")

    if df.empty:
        raise Exception("Excel vuoto")

    df = df[df["Data"].notna()].copy()
    df["Data"] = pd.to_datetime(df["Data"], errors="coerce")
    df = df.dropna(subset=["Data"]).sort_values("Data")

    if df.empty:
        return None

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
            if not nome:
                continue

            tag = to_tag(nome)
            msg += f"    {tag}\n"

        msg += "\n"

    keyboard = {
        "inline_keyboard": [[
            {"text": "✅ OK", "callback_data": f"ok|{date}"}
        ]]
    }

    return msg, date, keyboard

# =====================
# SEND (ROBUSTO)
# =====================
def send():

    result = build_message()
    if not result:
        print("⚠️ Nessun messaggio generato")
        return

    msg, date, keyboard = result

    print("📤 INVIO TURNI...")

    res = requests.post(
        url,
        json={
            "chat_id": CHAT_ID,
            "text": msg,
            "reply_markup": keyboard
        }
    )

    try:
        data = res.json()
    except Exception:
        print("❌ risposta non JSON:", res.text)
        return

    if not data.get("ok"):
        print("❌ Telegram error:", data)
        return

    print("✅ TURNI INVIATI:", date)

# =====================
# SCHEDULER STABILE
# =====================
scheduler = BackgroundScheduler()

scheduler.add_job(send, "cron", day_of_week="mon", hour=9, minute=0)
scheduler.add_job(send, "cron", day_of_week="thu", hour=9, minute=0)
scheduler.add_job(send, "cron", day_of_week="sat", hour=10, minute=0)

scheduler.start()

print("🚀 BOT ATTIVO E STABILE")