import os
import boto3
import requests
import subprocess
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

def extract_audio(video_path, audio_path):
    subprocess.run([
        "ffmpeg", "-i", video_path,
        "-vn", "-acodec", "mp3",
        audio_path
    ], check=True)

@app.route("/transfer", methods=["POST"])
def transfer_video():
    data = request.json
    file_id = data.get("file_id")
    file_name = data.get("name", "video.mp4")

    safe = "".join(c if c.isalnum() or c in "._-" else "_" for c in file_name)

    video_tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".mp4").name
    audio_tmp = video_tmp.replace(".mp4", ".mp3")

    download_drive(file_id, video_tmp)
    extract_audio(video_tmp, audio_tmp)

    video_key = f"uploads/{safe}"
    audio_key = video_key.replace(".mp4", ".mp3")

    s3.upload_file(video_tmp, R2_BUCKET_NAME, video_key, ExtraArgs={"ContentType": "video/mp4"})
    s3.upload_file(audio_tmp, R2_BUCKET_NAME, audio_key, ExtraArgs={"ContentType": "audio/mpeg"})

    os.unlink(video_tmp)
    os.unlink(audio_tmp)

    base = R2_PUBLIC_DOMAIN.rstrip("/")

    return jsonify({
        "status": "success",
        "video_url": f"{base}/{video_key}",
        "audio_url": f"{base}/{audio_key}"
    }), 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
