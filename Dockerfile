FROM python:3.11-slim

RUN apt-get update && \
    apt-get install -y ffmpeg && \
    pip install flask requests gunicorn

WORKDIR /app
COPY . .

CMD gunicorn -b 0.0.0.0:$PORT main:app
