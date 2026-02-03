import os, tempfile, subprocess, requests, threading, json
from flask import Flask, request, jsonify
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google.oauth2 import service_account
from openai import OpenAI

app = Flask(__name__)

# Railway Değişkenlerinden Verileri Alıyoruz
OPENAI_KEY = os.environ.get("OPENAI_API_KEY")
GOOGLE_API_KEY = os.environ.get("GOOGLE_API_KEY")
SERVICE_ACCOUNT_JSON = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS_JSON")
LOGO_URL = "https://pub-10e9a156db6441a8a4692a69c2c8ed4d.r2.dev/logo.png"

client = OpenAI(api_key=OPENAI_KEY)

def process_video_task(file_id, original_name):
    try:
        # 1. Google Drive'dan İndir (Sıfır Make Transferi)
        temp_video = tempfile.NamedTemporaryFile(delete=False, suffix=".mp4")
        drive_url = f"https://www.googleapis.com/drive/v3/files/{file_id}?alt=media&key={GOOGLE_API_KEY}"
        with requests.get(drive_url, stream=True) as r:
            with open(temp_video.name, 'wb') as f:
                for chunk in r.iter_content(chunk_size=8192): f.write(chunk)

        # 2. OpenAI Whisper ile Transkript (Videoyu Dinle)
        audio_path = temp_video.name.replace(".mp4", ".mp3")
        subprocess.run(["ffmpeg", "-y", "-i", temp_video.name, "-vn", "-acodec", "libmp3lame", audio_path], check=True)
        
        with open(audio_path, "rb") as audio_file:
            transcript = client.audio.transcriptions.create(model="whisper-1", file=audio_file).text

        # 3. GPT-4o ile Başlık ve Açıklama Yaz (Diksiyon Eğitmeni Kimliğiyle)
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "system", "content": "Sen Adana Kanalı'nın sahibi, diksiyon eğitmeni Yusuf Koçak'sın. Verilen transkriptten YouTube için etkileyici bir başlık, emoji dolu bir açıklama ve hashtagler üret. JSON formatında 'title' ve 'desc' olarak ver."},
                      {"role": "user", "content": transcript}]
        )
        ai_data = json.loads(response.choices[0].message.content)

        # 4. Logoyu Bas (Videonun Yarısı Kadar, Alt-Orta)
        logo_temp = tempfile.NamedTemporaryFile(delete=False, suffix=".png").name
        with open(logo_temp, "wb") as f: f.write(requests.get(LOGO_URL).content)
        
        output_path = temp_video.name.replace(".mp4", "_final.mp4")
        ffmpeg_cmd = [
            "ffmpeg", "-y", "-i", temp_video.name, "-i", logo_temp,
            "-filter_complex", "[1:v]scale=main_w/2:-1[l];[0:v][l]overlay=(main_w-overlay_w)/2:main_h-overlay_h-150",
            "-preset", "ultrafast", "-c:v", "libx264", "-c:a", "copy", output_path
        ]
        subprocess.run(ffmpeg_cmd, check=True)

        # 5. YouTube'a Yükle
        info = json.loads(SERVICE_ACCOUNT_JSON)
        creds = service_account.Credentials.from_service_account_info(info)
        youtube = build("youtube", "v3", credentials=creds)

        request_body = {
            "snippet": {"title": ai_data['title'], "description": ai_data['desc'], "categoryId": "27"},
            "status": {"privacyStatus": "public"}
        }
        media = MediaFileUpload(output_path, chunksize=-1, resumable=True)
        youtube.videos().insert(part="snippet,status", body=request_body, media_body=media).execute()

        print(f"BAŞARILI: {original_name} YouTube'a yüklendi.")

    except Exception as e:
        print(f"HATA: {str(e)}")

@app.route("/upload", methods=["POST"])
def upload():
    data = request.json
    threading.Thread(target=process_video_task, args=(data['file_id'], data['name'])).start()
    return jsonify({"status": "isleme_alindi"}), 202

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
