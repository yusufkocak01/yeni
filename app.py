from flask import Flask, request, send_file
import subprocess
import uuid
import os

app = Flask(__name__)

LOGO_PATH = "logo.png"


@app.route("/")
def home():
    return "Watermark API çalışıyor"


@app.route("/watermark", methods=["POST"])
def watermark():
    if 'video' not in request.files:
        return "Video dosyası bulunamadı", 400

    video = request.files['video']

    in_file = f"/tmp/{uuid.uuid4()}.mp4"
    out_file = f"/tmp/out_{uuid.uuid4()}.mp4"

    video.save(in_file)

    # HIZLI FFmpeg (Make timeout yemez)
    cmd = [
        "ffmpeg",
        "-y",
        "-i", in_file,
        "-i", LOGO_PATH,
        "-filter_complex",
        "overlay=(main_w-overlay_w)/2:main_h-overlay_h-60",
        "-c:v", "libx264",
        "-preset", "ultrafast",
        "-crf", "28",
        "-c:a", "copy",
        out_file
    ]

    subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    return send_file(out_file, as_attachment=True)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
