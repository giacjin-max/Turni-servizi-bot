import json
import datetime

now = datetime.datetime.now()

if now.weekday() == 0 and now.hour < 1:

    json.dump({}, open("responses.json","w"))
    json.dump({}, open("reminder_log.json","w"))
    json.dump({"offset":0}, open("offset.json","w"))

    print("Reset settimanale eseguito")
else:
    print("No reset")
