from flask import Flask, request, jsonify
import tempfile, subprocess, requests, threading, os

app = Flask(__name__)

LOGO_URL = "https://pub-10e9a156db6441a8a4692a69c2c8ed4d.r2.dev/logo.png"

def process_video(video_path):
    logo_path = tempfile.NamedTemporaryFile(delete=False, suffix=".png").name
    r = requests.get(LOGO_URL)
    with open(logo_path, "wb") as f:
        f.write(r.content)

    output_path = video_path.replace(".mp4", "_out.mp4")

    cmd = [
        "ffmpeg",
        "-i", video_path,
        "-i", logo_path,
        "-filter_complex", "overlay=10:10",
        "-codec:a", "copy",
        output_path
    ]
    subprocess.run(cmd)

@app.route("/upload", methods=["POST"])
def upload():
    if 'file' not in request.files:
        return jsonify({"error": "no file"}), 400

    uploaded_file = request.files['file']
    temp_video = tempfile.NamedTemporaryFile(delete=False, suffix=".mp4")
    uploaded_file.save(temp_video.name)

    # ffmpeg’i arka planda başlat
    threading.Thread(target=process_video, args=(temp_video.name,)).start()

    # ANINDA cevap dön
    return jsonify({"status": "processing started"})
