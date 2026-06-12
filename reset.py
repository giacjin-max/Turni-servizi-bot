import json
import os

# =====================
# RESET RISPOSTE
# =====================
with open("responses.json", "w") as f:
    json.dump({}, f)

# =====================
# RESET REMINDER
# =====================
with open("reminder_log.json", "w") as f:
    json.dump({}, f)

# =====================
# RESET OFFSET TELEGRAM
# =====================
with open("offset.json", "w") as f:
    json.dump({"offset": 0}, f)

print("Reset settimana completato")
