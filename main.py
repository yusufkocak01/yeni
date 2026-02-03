from flask import Flask, request, jsonify
import tempfile
import subprocess
import requests
import threading

app = Flask(__name__)

LOGO_URL = "https://pub-10e9a156db6441a8a4692a69c2c8ed4d.r2.dev/logo.png"


def process_video(video_path):
    # Logoyu indir
    logo_path = tempfile.NamedTemporaryFile(delete=False, suffix=".png").name
    r = requests.get(LOGO_URL)
    with open(logo_path, "wb") as f:
        f.write(r.content)

    # Çıktı video yolu
    output_path = video_path.replace(".mp4", "_out.mp4")

    # Logo boyut ve konum ayarı
    ffmpeg_cmd = [
        "ffmpeg",
        "-i", video_path,
        "-i", logo_path,
        "-filter_complex",
        "[1]scale=iw/2:-1[logo];[0][logo]overlay=(main_w-overlay_w)/2:main_h-overlay_h-80",
        "-codec:a", "copy",
        output_path
    ]

    subprocess.run(ffmpeg_cmd)

    print("Video işlendi:", output_path)


@app.route("/upload", methods=["POST"])
def upload():
    if 'file' not in request.files:
        return jsonify({"error": "file field missing"}), 400

    uploaded_file = request.files['file']

    if uploaded_file.filename == '':
        return jsonify({"error": "empty filename"}), 400

    # Geçici videoya kaydet
    temp_video = tempfile.NamedTemporaryFile(delete=False, suffix=".mp4")
    uploaded_file.save(temp_video.name)

    # ffmpeg işlemini arka planda başlat
    threading.Thread(target=process_video, args=(temp_video.name,)).start()

    return jsonify({"status": "processing started"})
