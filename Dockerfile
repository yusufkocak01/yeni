FROM python:3.11-slim

RUN apt-get update && apt-get install -y ffmpeg

WORKDIR /app
COPY . .

RUN pip install -r requirements.txt

CMD ["gunicorn", "main:app", "--bind", "0.0.0.0:8000"]
