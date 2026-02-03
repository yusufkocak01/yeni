from flask import Flask, request, jsonify
import tempfile, subprocess, requests, threading, os

app = Flask(__name__)

LOGO_URL = "https://pub-10e9a156db6441a8a4692a69c2c8ed4d.r2.dev/logo.png"
CF_TOKEN = os.environ.get("CF_TOKEN")
CF_ACCOUNT = os.environ.get("CF_ACCOUNT")

def process_and_upload(video_path, name):
    try:
        # 1. Logoyu İndir
        logo_path = tempfile.NamedTemporaryFile(delete=False, suffix=".png").name
        r = requests.get(LOGO_URL)
        with open(logo_path, "wb") as f:
            f.write(r.content)

        # 2. Watermark Bas (Hız öncelikli ayar)
        output_path = video_path.replace(".mp4", "_out.mp4")
        ffmpeg_cmd = [
            "ffmpeg", "-i", video_path, "-i", logo_path,
            "-filter_complex", "[1]scale=iw/2:-1[logo];[0][logo]overlay=(main_w-overlay_w)/2:main_h-overlay_h-80",
            "-preset", "ultrafast", "-codec:a", "copy", output_path
        ]
        subprocess.run(ffmpeg_cmd, check=True)

        # 3. Cloudflare'a Yükle
        url = f"https://api.cloudflare.com/client/v4/accounts/{CF_ACCOUNT}/stream"
        headers = {"Authorization": f"Bearer {CF_TOKEN}"}
        with open(output_path, "rb") as f:
            files = {"file": (name, f, "video/mp4")}
            requests.post(url, headers=headers, files=files)
        
        print(f"BAŞARILI: {name} Cloudflare'a yüklendi.")
    except Exception as e:
        print(f"HATA DETAYI: {str(e)}")

@app.route("/upload", methods=["POST"])
def upload():
    if 'file' not in request.files:
        return jsonify({"status": "error", "message": "Dosya eksik"}), 400

    uploaded_file = request.files['file']
    temp_video = tempfile.NamedTemporaryFile(delete=False, suffix=".mp4")
    uploaded_file.save(temp_video.name)

    # Arka planda çalıştır
    thread = threading.Thread(target=process_and_upload, args=(temp_video.name, uploaded_file.filename))
    thread.start()

    # Make'e hemen cevap ver
    return jsonify({"status": "accepted", "message": "İşlem arka planda başladı."}), 202
