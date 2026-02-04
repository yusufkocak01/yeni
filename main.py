import os
import boto3
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

@app.route("/upload", methods=["POST"])
def upload():
    file = request.files["file"]
    filename = file.filename

    key = f"uploads/{filename}"

    s3.upload_fileobj(file, R2_BUCKET_NAME, key,
                      ExtraArgs={"ContentType": "video/mp4"})

    url = f"{R2_PUBLIC_DOMAIN.rstrip('/')}/{key}"

    return jsonify({"video_url": url}), 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
