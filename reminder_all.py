import os
import requests

BOT_TOKEN = os.environ["BOT_TOKEN"]
CHAT_ID = os.environ["CHAT_ID"]

requests.post(
    f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
    data={
        "chat_id": CHAT_ID,
        "text": "🔔 Promemoria per il servizio di domani. Controllate i turni e preparatevi per il vostro incarico."
    }
)

print("Reminder generale inviato")
