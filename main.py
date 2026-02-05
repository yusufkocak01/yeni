import subprocess
from openai import OpenAI

client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])

@app.route("/speech", methods=["POST"])
def speech():
    data = request.json
    video_url = data.get("video_url")

    video_file = "/tmp/video.mp4"
    audio_file = "/tmp/audio.mp3"

    # Videoyu indir
    r = requests.get(video_url)
    with open(video_file, "wb") as f:
        f.write(r.content)

    # MP3 çıkar
    subprocess.run([
        "ffmpeg", "-i", video_file,
        "-q:a", "0", "-map", "a",
        audio_file
    ])

    # Whisper'a gönder
    with open(audio_file, "rb") as audio:
        transcript = client.audio.transcriptions.create(
            model="whisper-1",
            file=audio
        )

    return jsonify({"text": transcript.text})
