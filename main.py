import os
import requests
import boto3
import subprocess
from flask import Flask, request, jsonify
from uuid import uuid4
from openai import OpenAI

app = Flask(__name__)

# OpenAI
client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])

# R2 bağlantısı
s3 = boto3.client(
    "s3",
    endpoint_url=os.environ["R2_ENDPOINT"],
    aws_access_key_id=os.environ["R2_ACCESS_KEY"],
    aws_secret_access_key=os.environ["R2_SECRET_KEY"],
    region_name="auto",
)

BUCKET = os.environ["R2_BUCKET"]
PUBLIC_BASE_URL = os.environ["R2_PUBLIC_URL"]


@app.route("/")
def home():
    return "OK"


# ✅ 1) Dropbox → R2 yükleme
@app.route("/transfer", methods=["POST"])
def transfer():
    data = request.json
    file_url = data.get("file_url")

    if not file_url:
        return jsonify({"error": "file_url missing"}), 400

    filename = f"{uuid4()}.mp4"

    # Dropbox'tan indir
    r = requests.get(file_url, stream=True)

    # R2'ye yükle
    s3.upload_fileobj(
        r.raw,
        BUCKET,
        filename,
        ExtraArgs={"ContentType": "video/mp4"},
    )

    video_url = f"{PUBLIC_BASE_URL}/{filename}"

    return jsonify({"video_url": video_url})


# ✅ 2) Video → MP3 → Whisper → Metin
@app.route("/speech", methods=["POST"])
def speech():
    data = request.json
    video_url = data.get("video_url")

    if not video_url:
        return jsonify({"error": "video_url missing"}), 400

    video_file = "/tmp/video.mp4"
    audio_file = "/tmp/audio.mp3"

    # Videoyu indir
    r = requests.get(video_url)
    with open(video_file, "wb") as f:
        f.write(r.content)

    # MP3 çıkar (ffmpeg)
    subprocess.run(
        ["ffmpeg", "-y", "-i", video_file, "-q:a", "0", "-map", "a", audio_file],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )

    # Whisper'a gönder
    with open(audio_file, "rb") as audio:
        transcript = client.audio.transcriptions.create(
            model="whisper-1",
            file=audio,
        )

    return jsonify({"text": transcript.text})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)

 
