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

        output_path = video_path.replace(".mp4", "_out.mp4")

        # 2. FFmpeg Komutu (Matematiksel Olarak Düzeltilmiş)
        # scale=main_w/2:-1 -> Logoyu videonun genişliğinin tam yarısına getirir.
        # overlay=(W-w)/2:H-h-150 -> Yatayda orta, dikeyde en alttan 150px yukarı.
        ffmpeg_cmd = [
            "ffmpeg", "-y",
            "-i", video_path,
            "-i", logo_path,
            "-filter_complex", 
            "[1:v]scale=main_w/2:-1[l];[0:v][l]overlay=(main_w-overlay_w)/2:main_h-overlay_h-150:format=auto",
            "-c:v", "libx264",
            "-preset", "ultrafast",
            "-c:a", "copy",
            output_path
        ]
        
        # İşlemi çalıştır ve hataları yakala
        result = subprocess.run(ffmpeg_cmd, capture_output=True, text=True)
        if result.returncode != 0:
            print("FFmpeg Hatası:", result.stderr)
            return

        # 3. Cloudflare'a Yükle
        url = f"https://api.cloudflare.com/client/v4/accounts/{CF_ACCOUNT}/stream"
        headers = {"Authorization": f"Bearer {CF_TOKEN}"}
        with open(output_path, "rb") as f:
            files = {"file": (name, f, "video/mp4")}
            requests.post(url, headers=headers, files=files)
        
        print(f"BAŞARILI: {name} logolu ve doğru boyutlu yüklendi.")
        
    except Exception as e:
        print(f"HATA: {str(e)}")

@app.route("/upload", methods=["POST"])
def upload():
    if 'file' not in request.files:
        return jsonify({"status": "error"}), 400
    uploaded_file = request.files['file']
    temp_video = tempfile.NamedTemporaryFile(delete=False, suffix=".mp4")
    uploaded_file.save(temp_video.name)
    
    threading.Thread(target=process_and_upload, args=(temp_video.name, uploaded_file.filename)).start()
    return jsonify({"status": "accepted"}), 202
