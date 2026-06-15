import os
import json
import pandas as pd
import requests
import re

# =====================
# CONFIG
# =====================
BOT_TOKEN = os.environ["BOT_TOKEN"]
CHAT_ID = os.environ["CHAT_ID"]

url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"

# =====================
# CLEANER ROBUSTO
# =====================
def clean(text: str) -> str:
    if not text:
        return ""

    text = str(text)

    # rimuove caratteri invisibili Excel
    text = re.sub(r"[\u200b-\u200f\uFEFF\u00A0]", "", text)

    # normalizza spazi
    text = " ".join(text.split())

    return text.strip().lower()

# =====================
# RUBRICA NORMALIZZATA
# =====================
with open("rubrica.json", "r", encoding="utf-8") as f:
    raw_rubrica = json.load(f)

rubrica = {
    clean(k): v
    for k, v in raw_rubrica.items()
}

# reverse mapping per debug
rubrica_keys = set(rubrica.keys())

def to_username(name: str) -> str:
    key = clean(name)
    return rubrica.get(key, name)

# =====================
# DEBUG MISMATCH
# =====================
def debug_mismatch(excel_names: set):

    missing = []

    for name in excel_names:
        if clean(name) not in rubrica_keys:
            missing.append(name)

    if missing:
        print("\n🚨 MISMATCH RUBRICA DETECTATO:")
        for m in missing:
            print(f"  - {m}")
        print("⚠️ Questi nomi NON sono presenti in rubrica.json\n")
    else:
        print("\n✅ Tutti i nomi Excel sono presenti in rubrica.json\n")

# =====================
# BUILD MESSAGGIO
# =====================
def build_message():

    df = pd.read_excel("turni.xlsx")

    if df.empty:
        return None

    df["Data"] = pd.to_datetime(df["Data"], errors="coerce")
    df = df.dropna(subset=["Data"]).sort_values("Data")

    riga = df.iloc[0]
    date = riga["Data"].strftime("%Y-%m-%d")

    msg = f"📅 TURNI {riga['Data'].strftime('%d/%m/%Y')}\n\n"
    msg += "👉 Premi OK quando hai visto il turno\n\n"

    excel_names = set()

    for col in df.columns:
        if col == "Data":
            continue

        value = riga[col]
        if pd.isna(value):
            continue

        names = str(value).split(",")

        msg += f"• {col}\n"

        for name in names:
            name = clean(name)
            if not name:
                continue

            username = to_username(name)

            msg += f"   {username}\n"

            excel_names.add(name)

        msg += "\n"

    # =====================
    # DEBUG RUN
    # =====================
    debug_mismatch(excel_names)

    msg += "📌 FOOTER\n\n"

    for n in sorted(excel_names):
        msg += f"{n}\n"

    keyboard = {
        "inline_keyboard": [[
            {"text": "✅ OK", "callback_data": f"ok|{date}"}
        ]]
    }

    return msg, date, keyboard

# =====================
# SEND
# =====================
def send():

    result = build_message()
    if not result:
        return

    msg, date, keyboard = result

    res = requests.post(
        url,
        json={
            "chat_id": CHAT_ID,
            "text": msg,
            "reply_markup": keyboard
        }
    )

    print("status:", res.status_code)
    print(res.text)