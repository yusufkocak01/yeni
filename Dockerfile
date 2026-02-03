# 1. Python'un hafif ve güncel bir sürümünü temel al
FROM python:3.10-slim

# 2. Sistem paketlerini güncelle ve FFmpeg'i kur
# (Video işleme için bu adım hayati önem taşıyor)
RUN apt-get update && apt-get install -y \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# 3. Çalışma dizinini oluştur
WORKDIR /app

# 4. Gerekli kütüphanelerin listesini kopyala ve yükle
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 5. Tüm kodları içeri aktar
COPY . .

# 6. Uygulamayı başlat
CMD ["python", "main.py"]
