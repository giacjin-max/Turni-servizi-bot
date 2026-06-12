from flask import Flask, request
import json

app = Flask(__name__)

@app.route("/", methods=["POST"])
def webhook():

    data = request.get_json(silent=True)

    print("UPDATE:", json.dumps(data, ensure_ascii=False), flush=True)

    return "ok", 200

@app.route("/", methods=["GET"])
def home():
    return "Webhook attivo", 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
