FROM pytorch/pytorch:2.5.1-cuda12.4-cudnn9-runtime

ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# 安裝系統依賴
RUN apt-get update && apt-get install -y \
    ffmpeg \
    git \
    curl \
    libsndfile1 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# 先複製 requirements（利用 Docker layer cache 加速重建）
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# 複製應用程式碼
COPY app/ ./app/
COPY config.yml .

# 建立掛載目錄
RUN mkdir -p /input /output

ENTRYPOINT ["python", "app/main.py"]
CMD ["--watch"]
