from flask import Flask, request, jsonify
import tempfile, subprocess, requests, threading, os

app = Flask(__name__)

LOGO_URL = "https://pub-10e9a156db6441a8a4692a69c2c8ed4d.r2.dev/logo.png"

CF_TOKEN = os.environ.get("CF_TOKEN")
CF_ACCOUNT = os.environ.get("CF_ACCOUNT")


def upload_to_stream(video_path, name):
    url = f"https://api.cloudflare.com/client/v4/accounts/{CF_ACCOUNT}/stream"
    headers = {
        "Authorization": f"Bearer {CF_TOKEN}"
    }

    with open(video_path, "rb") as f:
        files = {
            "file": (name, f, "video/mp4")
        }
        response = requests.post(url, headers=headers, files=files)
        data = response.json()
        uid = data["result"]["uid"]

        playback = f"https://videodelivery.net/{uid}/manifest/video.m3u8"
        return playback


def process_video(video_path, name):
    logo_path = tempfile.NamedTemporaryFile(delete=False, suffix=".png").name
    r = requests.get(LOGO_URL)
    with open(logo_path, "wb") as f:
        f.write(r.content)

    output_path = video_path.replace(".mp4", "_out.mp4")

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

    stream_url = upload_to_stream(output_path, name)
    print("STREAM URL:", stream_url)
    return stream_url


@app.route("/upload", methods=["POST"])
def upload():
    if 'file' not in request.files:
        return jsonify({"error": "file field missing"}), 400

    uploaded_file = request.files['file']
    name = uploaded_file.filename

    temp_video = tempfile.NamedTemporaryFile(delete=False, suffix=".mp4")
    uploaded_file.save(temp_video.name)

    # watermark + stream upload
    stream_url = process_video(temp_video.name, name)

    return jsonify({"url": stream_url})
