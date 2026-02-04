import os, boto3, requests, tempfile, threading
from flask import Flask, request, jsonify

app = Flask(__name__)

# R2 Ayarları
R2_ACCESS_KEY = os.environ.get("R2_ACCESS_KEY")
R2_SECRET_KEY = os.environ.get("R2_SECRET_KEY")
R2_BUCKET_NAME = os.environ.get("R2_BUCKET_NAME")
R2_ENDPOINT_URL = os.environ.get("R2_ENDPOINT_URL")
R2_PUBLIC_DOMAIN = os.environ.get("R2_PUBLIC_DOMAIN")

s3 = boto3.client(
    service_name='s3',
    endpoint_url=R2_ENDPOINT_URL,
    aws_access_key_id=R2_ACCESS_KEY,
    aws_secret_access_key=R2_SECRET_KEY,
    region_name='auto'
)

def download_from_drive(file_id, destination):
    URL = "https://drive.google.com/uc?export=download"
    session = requests.Session()
    response = session.get(URL, params={'id': file_id}, stream=True)

    # Google'ın büyük dosya onayını (confirm token) yakala
    for key, value in response.cookies.items():
        if key.startswith('download_warning'):
            params = {'id': file_id, 'confirm': value}
            response = session.get(URL, params=params, stream=True)
            break

    with open(destination, "wb") as f:
        for chunk in response.iter_content(32768):
            if chunk:
                f.write(chunk)

def background_task(file_id, safe_name):
    try:
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".mp4")
        temp_path = temp_file.name
        temp_file.close()

        # 1. Drive'dan Onay Kodlu İndir
        download_from_drive(file_id, temp_path)

        # 2. R2'ye Yükle
        r2_path = f"uploads/{safe_name}"
        s3.upload_file(temp_path, R2_BUCKET_NAME, r2_path, ExtraArgs={'ContentType': 'video/mp4'})

        # 3. Temizlik
        os.unlink(temp_path)
        print(f"Başarıyla yüklendi: {safe_name}")
    except Exception as e:
        print(f"Hata oluştu: {str(e)}")

@app.route("/transfer", methods=["POST"])
def transfer_video():
    data = request.json
    file_id = data.get("file_id")
    file_name = data.get("name", "video.mp4")

    if not file_id:
        return jsonify({"status": "error", "message": "file_id eksik"}), 400

    safe_name = "".join([c if c.isalnum() or c in "._-" else "_" for c in file_name])
    
    # İŞLEMİ ARKA PLANDA BAŞLAT (Make'i bekletme!)
    threading.Thread(target=background_task, args=(file_id, safe_name)).start()

    # MAKE'E ANINDA LİNKİ VER
    base = R2_PUBLIC_DOMAIN.rstrip("/")
    public_url = f"{base}/uploads/{safe_name}"

    return jsonify({
        "status": "processing",
        "video_url": public_url,
        "message": "Dosya arka planda tasiniyor. 1-2 dakika icinde link aktif olacaktir."
    }), 200

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
