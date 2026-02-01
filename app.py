from flask import Flask, request, send_file
import subprocess, uuid, os

app = Flask(__name__)
LOGO_PATH = "logo.png"

@app.route("/watermark", methods=["POST"])
def watermark():
    video = request.files['video']
    in_file = f"/tmp/{uuid.uuid4()}.mp4"
    out_file = f"/tmp/out_{uuid.uuid4()}.mp4"

    video.save(in_file)

    cmd = [
        "ffmpeg", "-i", in_file, "-i", LOGO_PATH,
        "-filter_complex",
        "[1]format=rgba,colorchannelmixer=aa=0.6[logo];[0][logo]overlay=(main_w-overlay_w)/2:main_h-overlay_h-60",
        "-codec:a", "copy",
        out_file
    ]

    subprocess.run(cmd)

    return send_file(out_file, as_attachment=True)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
