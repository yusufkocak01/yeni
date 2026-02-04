import os
import boto3
import requests
import tempfile
from flask import Flask, request, jsonify

app = Flask(__name__)

# ENV
R2_ACCESS_KEY = os.environ.get("R2_ACCESS_KEY")
R2_SECRET_KEY = os.environ.get("R2_SECRET_KEY")
R2_BUCKET_NAME = os.environ.get("R2_BUCKET_NAME")
R2_ENDPOINT_URL = os.environ.get("R2_ENDPOINT_URL")
R2_PUBLIC_DOMAIN = os.environ.get("R2_PUBLIC_DOMAIN")

# R2 bağlantısı
s3 = boto3.client(
    service_name='s3',
    endpoint_url=R2_ENDPOINT_URL,
    aws_access_key_id=R2_ACCESS_KEY,
    aws_secret_access_key=R2_SECRET_KEY,
    region_name='auto'
)

# Google Drive büyük dosya indirme (confirm token destekli)
def download_from_drive(file_id, destination):
    URL = "https://drive.google.com/uc?export=download"
    session = requests.Session()

    response = session.get(URL, params={'id': file_id}, stream=True)

    for key, value in response.cookies.items():
        if key.startswith('download_warning'):
            params = {'id': file_id, 'confirm': value}
            response = session.get(URL, params=params, stream=True)
            break

    with open(destination, "wb") as f:
        for chunk in response.iter_content(32768):
            if chunk:
                f.write(chunk)

@app.route("/transfer", methods=["POST"])
def transfer_video():
    data = request.json
    file_id = data.get("file_id")
    file_name = data.get("name", "video.mp4")

    if not file_id:
        return jsonify({"status": "error", "message": "file_id eksik"}), 400

    try:
        # Geçici dosya oluştur
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".mp4")
        temp_path = temp_file.name
        temp_file.close()

        # 1. Drive'dan indir
        download_from_drive(file_id, temp_path)

        # 2. Dosya adını güvenli hale getir
        safe_name = "".join([c if c.isalnum() or c in "._-" else "_" for c in file_name])
        r2_path = f"uploads/{safe_name}"

        # 3. R2'ye yükle
        s3.upload_file(
            temp_path,
            R2_BUCKET_NAME,
            r2_path,
            ExtraArgs={'ContentType': 'video/mp4'}
        )

        # 4. Temp sil
        os.unlink(temp_path)

        # 5. Public URL üret
        base = R2_PUBLIC_DOMAIN.rstrip("/")
        public_url = f"{base}/{r2_path}"

        return jsonify({
            "status": "success",
            "video_url": public_url
        }), 200

    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
