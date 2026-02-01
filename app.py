from flask import Flask, request, send_file
import subprocess
import uuid
import os

app = Flask(__name__)

@app.route("/")
def home():
    return "FFmpeg audio converter is running"

@app.route("/convert", methods=["POST"])
def convert():
    if "file" not in request.files:
        return "No file uploaded", 400

    video = request.files["file"]

    uid = str(uuid.uuid4())
    input_path = f"/tmp/{uid}.mp4"
    output_path = f"/tmp/{uid}.mp3"

    video.save(input_path)

    cmd = [
        "ffmpeg",
        "-i", input_path,
        "-vn",
        "-ar", "44100",
        "-ac", "2",
        "-b:a", "192k",
        output_path
    ]

    subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    return send_file(output_path, as_attachment=True)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=3000)
