import os
import requests
import boto3
from flask import Flask, request, jsonify

app = Flask(__name__)

s3 = boto3.client(
    service_name="s3",
    endpoint_url=os.environ.get("R2_ENDPOINT_URL"),
    aws_access_key_id=os.environ.get("R2_ACCESS_KEY"),
    aws_secret_access_key=os.environ.get("R2_SECRET_KEY"),
    region_name="auto",
)

@app.route("/transfer", methods=["POST"])
def transfer():
    data = request.json
    url = data.get("download_url")
    name = data.get("name")

    if not url:
        return jsonify({"error": "no url"}), 400

    r = requests.get(url, stream=True)
    r.raise_for_status()

    key = f"uploads/{name}"

    s3.upload_fileobj(
        r.raw,
        os.environ.get("R2_BUCKET_NAME"),
        key,
        ExtraArgs={"ContentType": "video/mp4"},
    )

    public = f"{os.environ.get('R2_PUBLIC_DOMAIN')}/{key}"

    return jsonify({"video_url": public}), 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
