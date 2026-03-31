import os
from flask import Flask, jsonify

app = Flask(__name__)

@app.route("/")
def home():
    return "Site funcionando 🚀"

@app.route("/saldo")
def saldo():
    return jsonify({"saldo": 500})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))