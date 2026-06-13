import json
import os
import requests
import pandas as pd

# =====================
# CONFIG
# =====================
BOT_TOKEN = os.environ["BOT_TOKEN"]
CHAT_ID = os.environ["CHAT_ID"]

URL = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"

EXCEL_FILE = "turni.xlsx"
EXPECTED_FILE = "expected_users.json"
RUBRICA_FILE = "rubrica.json"

# =====================
# LOAD RUBRICA
# =====================
def load_rubrica():
    try:
        with open(RUBRICA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return {}

rubrica = load_rubrica()

def to_username(nome):
    nome = str(nome).strip()
    username = rubrica.get(nome)
    if not username:
        return None
    return username.lower().strip()

# =====================
# SAVE EXPECTED USERS
# =====================
def save_expected(date, users):
    try:
        data = {}

        if os.path.exists(EXPECTED_FILE):
            with open(EXPECTED_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)

        data[date] = sorted(list(set(users)))

        with open(EXPECTED_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

        print("💾 EXPECTED SALVATO:", data[date])

    except Exception as e:
        print("❌ ERRORE SAVE EXPECTED:", e)

# =====================
# LOAD EXCEL
# =====================
df = pd.read_excel(EXCEL_FILE)
df = df[df["Data"].notna()].copy()
df["Data"] = pd.to_datetime(df["Data"])

riga = df.sort_values("Data").iloc[0]
date = riga["Data"].strftime("%Y-%m-%d")

# =====================
# BUILD MESSAGE
# =====================
msg = f"📅 TURNI {riga['Data'].strftime('%d/%m/%Y')}\n\n"
msg += "👉 Rispondi ai turni cliccando i pulsanti\n\n"

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

        if username:
            expected_users.add(username)
            msg += f"   {username}\n"
        else:
            msg += f"   {nome} (⚠️ non in rubrica)\n"

    msg += "\n"

# =====================
# SAVE EXPECTED USERS
# =====================
save_expected(date, expected_users)

# =====================
# INLINE KEYBOARD
# =====================
keyboard = {
    "inline_keyboard": [
        [
            {"text": "✅ OK", "callback_data": f"ok|{date}"},
            {"text": "❌ NON POSSO", "callback_data": f"no|{date}"}
        ]
    ]
}

# =====================
# SEND MESSAGE
# =====================
res = requests.post(
    URL,
    data={
        "chat_id": CHAT_ID,
        "text": msg,
        "reply_markup": json.dumps(keyboard)
    }
)

print("STATUS:", res.status_code)
print("DATE:", date)
print("EXPECTED USERS:", len(expected_users))
print("TURNI INVIATI ✔")
