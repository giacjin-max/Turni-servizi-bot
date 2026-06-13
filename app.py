import os
import json
import requests
import pandas as pd
from flask import Flask, request
from supabase import create_client

app = Flask(__name__)

BOT_TOKEN = os.environ["BOT_TOKEN"]
SUPABASE_URL = os.environ["SUPABASE_URL"]
SUPABASE_KEY = os.environ["SUPABASE_KEY"]

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# =====================
# RUBRICA (telegram → servizio)
# =====================
with open("rubrica.json", "r", encoding="utf-8") as f:
    rubrica = json.load(f)

reverse_rubrica = {
    v.lower().replace("@", ""): k
    for k, v in rubrica.items()
}

def get_service_name(telegram_user):
    user = telegram_user.lower().replace("@", "")
    return reverse_rubrica.get(user, user)

# =====================
# SUPABASE SAVE
# =====================
def save_response(date, service_name):

    supabase.table("responses").upsert({
        "date": date,
        "username": service_name,
        "status": "ok"
    }, on_conflict="date,username").execute()

# =====================
# GET RESPONSES
# =====================
def get_responses(date):

    res = supabase.table("responses") \
        .select("*") \
        .eq("date", date) \
        .execute()

    return res.data

# =====================
# BUILD MESSAGE (Excel base + Supabase overlay)
# =====================
def build_message(riga, status_map):

    msg = f"📅 TURNI {riga['Data'].strftime('%d/%m/%Y')}\n\n"

    for col in riga.index:
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

            if nome in status_map:
                msg += f"    {nome} → OK\n"
            else:
                msg += f"    {nome}\n"

        msg += "\n"

    return msg

# =====================
# WEBHOOK
# =====================
@app.route("/", methods=["POST"])
def webhook():

    data = request.get_json(silent=True)

    if not data or "callback_query" not in data:
        return "ok", 200

    cb = data["callback_query"]

    chat_id = cb["message"]["chat"]["id"]
    msg_id = cb["message"]["message_id"]

    telegram_user = cb["from"].get("username") or str(cb["from"]["id"])
    date = cb["data"].split("|")[1]

    service_name = get_service_name(telegram_user)

    print("CLICK:", telegram_user, "→", service_name, date, flush=True)

    # salva risposta
    save_response(date, service_name)

    # leggi excel (base struttura)
    df = pd.read_excel("turni.xlsx")
    df = df[df["Data"].notna()].copy()
    df["Data"] = pd.to_datetime(df["Data"])
    df = df.sort_values("Data")

    riga = df.iloc[0]

    # leggi supabase
    responses = get_responses(date)

    status_map = {
        r["username"]: r["status"]
        for r in responses
    }

    # costruisci messaggio
    new_text = build_message(riga, status_map)

    # aggiorna telegram
    requests.post(
        f"https://api.telegram.org/bot{BOT_TOKEN}/editMessageText",
        json={
            "chat_id": chat_id,
            "message_id": msg_id,
            "text": new_text
        }
    )

    # risposta click
    requests.post(
        f"https://api.telegram.org/bot{BOT_TOKEN}/answerCallbackQuery",
        data={
            "callback_query_id": cb["id"],
            "text": "OK registrato ✔"
        }
    )

    return "ok", 200

# =======
# test
# =======
@app.route("/test-sender")
def test_sender():
    import os
    os.system("python sender.py")
    return "sender eseguito", 200
    
    
# =====================
# START
# =====================
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)

