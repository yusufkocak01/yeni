from flask import Flask, request, jsonify
import tempfile
import subprocess
import requests
import os

app = Flask(__name__)

LOGO_URL = "https://pub-10e9a156db6441a8a4692a69c2c8ed4d.r2.dev/logo.png"

@app.route("/upload", methods=["POST"])
def upload():
    if 'file' not in request.files:
        return jsonify({"error": "file field missing"}), 400

    uploaded_file = request.files['file']

    if uploaded_file.filename == '':
        return jsonify({"error": "empty filename"}), 400

    temp_video = tempfile.NamedTemporaryFile(delete=False, suffix=".mp4")
    uploaded_file.save(temp_video.name)

    logo_path = tempfile.NamedTemporaryFile(delete=False, suffix=".png").name
    r = requests.get(LOGO_URL)
    with open(logo_path, "wb") as f:
        f.write(r.content)

    output_path = tempfile.NamedTemporaryFile(delete=False, suffix=".mp4").name

    cmd = [
        "ffmpeg",
        "-i", temp_video.name,
        "-i", logo_path,
        "-filter_complex", "overlay=10:10",
        "-codec:a", "copy",
        output_path
    ]
    subprocess.run(cmd, check=True)

    return jsonify({"status": "ok"})
