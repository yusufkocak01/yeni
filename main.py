import os, boto3, requests, tempfile
from flask import Flask, request, jsonify
from googleapiclient.discovery import build

app = Flask(__name__)

# Ayarlar (Railway Variables kısmına girmelisin)
R2_ACCESS_KEY = os.environ.get("R2_ACCESS_KEY")
R2_SECRET_KEY = os.environ.get("R2_SECRET_KEY")
R2_BUCKET_NAME = os.environ.get("R2_BUCKET_NAME")
R2_ENDPOINT_URL = os.environ.get("R2_ENDPOINT_URL") # https://<hesapid>.r2.cloudflarestorage.com
R2_PUBLIC_DOMAIN = os.environ.get("R2_PUBLIC_DOMAIN") # https://pub-xxx.r2.dev (veya kendi domainin)
GOOGLE_API_KEY = os.environ.get("GOOGLE_API_KEY")

# R2 Bağlantısı
s3 = boto3.client(
    service_name='s3',
    endpoint_url=R2_ENDPOINT_URL,
    aws_access_key_id=R2_ACCESS_KEY,
    aws_secret_access_key=R2_SECRET_KEY,
    region_name='auto'
)

@app.route("/transfer", methods=["POST"])
def transfer_video():
    data = request.json
    file_id = data.get("file_id")
    file_name = data.get("name")

    if not file_id:
        return jsonify({"error": "file_id eksik"}), 400

    try:
        # 1. Drive'dan Geçici Olarak İndir
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".mp4")
        drive_url = f"https://www.googleapis.com/drive/v3/files/{file_id}?alt=media&key={GOOGLE_API_KEY}"
        
        with requests.get(drive_url, stream=True) as r:
            with open(temp_file.name, 'wb') as f:
                for chunk in r.iter_content(chunk_size=8192): f.write(chunk)

        # 2. R2'ye Yükle
        r2_file_path = f"uploads/{file_name}"
        s3.upload_file(temp_file.name, R2_BUCKET_NAME, r2_file_path, ExtraArgs={'ContentType': 'video/mp4'})

        # 3. Geçici Dosyayı Sil ve Linki Dön
        os.unlink(temp_file.name)
        public_url = f"{R2_PUBLIC_DOMAIN}/{r2_file_path}"
        
        return jsonify({"status": "success", "video_url": public_url}), 200

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
