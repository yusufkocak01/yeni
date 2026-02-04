import os
import boto3
import requests
import tempfile
from flask import Flask, request, jsonify

app = Flask(__name__)

R2_ACCESS_KEY = os.environ.get("R2_ACCESS_KEY")
R2_SECRET_KEY = os.environ.get("R2_SECRET_KEY")
R2_BUCKET_NAME = os.environ.get("R2_BUCKET_NAME")
R2_ENDPOINT_URL = os.environ.get("R2_ENDPOINT_URL")
R2_PUBLIC_DOMAIN = os.environ.get("R2_PUBLIC_DOMAIN")

s3 = boto3.client(
    service_name="s3",
    endpoint_url=R2_ENDPOINT_URL,
    aws_access_key_id=R2_ACCESS_KEY,
    aws_secret_access_key=R2_SECRET_KEY,
    region_name="auto",
)

def download_drive(file_id, path):
    URL = "https://drive.google.com/uc?export=download"
    session = requests.Session()
    r = session.get(URL, params={"id": file_id}, stream=True)

    for k, v in r.cookies.items():
        if k.startswith("download_warning"):
            r = session.get(URL, params={"id": file_id, "confirm": v}, stream=True)
            break

    with open(path, "wb") as f:
        for chunk in r.iter_content(1024 * 1024):
            if chunk:
                f.write(chunk)

@app.route("/transfer", methods=["POST"])
def transfer_video():
    data = request.json
    file_id = data.get("file_id")
    file_name = data.get("name", "video.mp4")

    try:
        safe = "".join(c if c.isalnum() or c in "._-" else "_" for c in file_name)
        r2_key = f"uploads/{safe}"

        tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".mp4")
        tmp_path = tmp.name
        tmp.close()

        # Drive'dan indir
        download_drive(file_id, tmp_path)

        # R2'ye yükle (gerçek mp4)
        s3.upload_file(
            tmp_path,
            R2_BUCKET_NAME,
            r2_key,
            ExtraArgs={"ContentType": "video/mp4"},
        )

        os.unlink(tmp_path)

        url = f"{R2_PUBLIC_DOMAIN.rstrip('/')}/{r2_key}"
        return jsonify({"status": "success", "video_url": url}), 200

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
