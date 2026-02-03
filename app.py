from flask import Flask, request, jsonify
import requests
import os

app = Flask(__name__)

CF_ACCOUNT_ID = os.environ.get("CF_ACCOUNT_ID")
CF_API_TOKEN = os.environ.get("CF_API_TOKEN")

@app.route("/upload", methods=["POST"])
def upload():
    if "file" not in request.files:
        return jsonify({"error": "No file provided"}), 400

    file = request.files["file"]

    url = f"https://api.cloudflare.com/client/v4/accounts/{CF_ACCOUNT_ID}/stream"

    headers = {
        "Authorization": f"Bearer {CF_API_TOKEN}"
    }

    files = {
        "file": (file.filename, file.stream, file.mimetype)
    }

    response = requests.post(url, headers=headers, files=files)
    data = response.json()

    if not data.get("success"):
        return jsonify(data), 400

    uid = data["result"]["uid"]
    mp4_url = f"https://videodelivery.net/{uid}/downloads/default.mp4"

    return jsonify({
        "uid": uid,
        "mp4": mp4_url
    })
