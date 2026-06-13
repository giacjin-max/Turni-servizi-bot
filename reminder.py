import sqlite3
import requests
import os

BOT_TOKEN = os.environ["BOT_TOKEN"]
CHAT_ID = os.environ["CHAT_ID"]

DB_NAME = "bot.db"

url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"


def get_all_dates():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT DISTINCT date FROM expected")
    rows = c.fetchall()
    conn.close()
    return [r[0] for r in rows]


def get_expected(date):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT user FROM expected WHERE date=?", (date,))
    rows = c.fetchall()
    conn.close()
    return set(r[0] for r in rows)


def get_responses(date):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT user FROM responses WHERE date=?", (date,))
    rows = c.fetchall()
    conn.close()
    return set(r[0] for r in rows)


for date in get_all_dates():

    expected = get_expected(date)
    responses = get_responses(date)

    missing = expected - responses

    if not missing:
        continue

    msg = f"⏰ REMINDER TURNI {date}\n\n"
    msg += "👉 Mancano ancora risposte:\n\n"

    for u in missing:
        msg += f"• {u}\n"

    msg += "\n⚠️ Rispondi ai turni dal messaggio principale"

    requests.post(url, data={
        "chat_id": CHAT_ID,
        "text": msg
    })

    print("REMINDER INVIATO:", date)
