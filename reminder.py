import os
import json
import pandas as pd
import requests

BOT_TOKEN = os.environ["BOT_TOKEN"]
CHAT_ID = os.environ["CHAT_ID"]

url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"

# LOAD
if os.path.exists("responses.json"):
    responses = json.load(open("responses.json"))
else:
    responses = {}

df = pd.read_excel("turni.xlsx")
df = df[df["Data"].notna()]
df["Data"] = pd.to_datetime(df["Data"])

riga = df.sort_values("Data").iloc[0]
date = riga["Data"].strftime("%Y-%m-%d")

# NOMI
servizi = ["Parola","Adorazione","Coro","BimbiGiovani","Piano","Bass",
           "Chitarra","Mix","PC","Porta","Pulizia","Pulizia sala bimbi",
           "Traduzione","Ronda"]

names = []
for s in servizi:
    if s in riga and pd.notna(riga[s]):
        names += str(riga[s]).replace(";", ",").split(",")

names = [n.strip() for n in names]

done = responses.get(date, {})

missing = [n for n in names if n not in done]

if not missing:
    exit()

msg = "⏳ Non hai ancora risposto:\n\n" + "\n".join(missing)

requests.post(url, data={
    "chat_id": CHAT_ID,
    "text": msg
})
