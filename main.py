import os, boto3, requests, tempfile
from flask import Flask, request, jsonify

app = Flask(__name__)

# R2 Ayarları (Railway Variables kısmından çekilir)
R2_ACCESS_KEY = os.environ.get("R2_ACCESS_KEY")
R2_SECRET_KEY = os.environ.get("R2_SECRET_KEY")
R2_BUCKET_NAME = os.environ.get("R2_BUCKET_NAME")
R2_ENDPOINT_URL = os.environ.get("R2_ENDPOINT_URL")
R2_PUBLIC_DOMAIN = os.environ.get("R2_PUBLIC_DOMAIN")

# R2 (S3) Bağlantısı
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
        return jsonify({"status": "error", "message": "file_id eksik"}), 400

    try:
        # 1. Google Drive'dan İndir (Klasör dışarıya açık olduğu için anahtar gerekmez)
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".mp4")
        # Google Drive doğrudan indirme linki formatı
        drive_url = f"https://www.googleapis.com/drive/v3/files/{file_id}?alt=media"
        
        with requests.get(drive_url, stream=True) as r:
            r.raise_for_status()
            with open(temp_file.name, 'wb') as f:
                for chunk in r.iter_content(chunk_size=8192):
                    if chunk: f.write(chunk)

        # 2. R2'ye Yükle
        # Dosya ismini güvenli hale getiriyoruz
        safe_name = "".join([c if c.isalnum() or c in "._-" else "_" for c in file_name])
        r2_file_path = f"uploads/{safe_name}"
        
        s3.upload_file(
            temp_file.name, 
            str(R2_BUCKET_NAME), 
            r2_file_path, 
            ExtraArgs={'ContentType': 'video/mp4'}
        )

        # 3. Geçici Dosyayı Sil
        os.unlink(temp_file.name)

        # 4. Make'e Linki Gönder
        base_url = str(R2_PUBLIC_DOMAIN).rstrip('/')
        public_url = f"{base_url}/{r2_file_path}"
        
        return jsonify({
            "status": "success", 
            "video_url": public_url,
            "file_name": safe_name
        }), 200

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
