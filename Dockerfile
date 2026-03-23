# NVIDIA 官方 CUDA 12.1 + cuDNN 8 image（確認存在於 Docker Hub）
# cuDNN 8 提供 libcudnn_ops_infer.so.8，faster-whisper (ctranslate2) 必要
# CUDA 12.1 與主機 Driver 572 / CUDA 12.8 向下相容
FROM nvidia/cuda:12.1.1-cudnn8-runtime-ubuntu22.04

ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# 安裝 Python 3.11 + 系統依賴
# build-essential：gcc/g++/make，PyAV (av) 編譯 C extension 必要
# pkg-config + ffmpeg dev libs：PyAV 連結 ffmpeg 必要
RUN apt-get update && apt-get install -y \
    python3.11 \
    python3.11-dev \
    python3-pip \
    build-essential \
    ffmpeg \
    git \
    curl \
    libsndfile1 \
    pkg-config \
    libavformat-dev \
    libavcodec-dev \
    libavdevice-dev \
    libavutil-dev \
    libavfilter-dev \
    libswscale-dev \
    libswresample-dev \
    && rm -rf /var/lib/apt/lists/* \
    && ln -sf /usr/bin/python3.11 /usr/bin/python3 \
    && ln -sf /usr/bin/python3 /usr/bin/python

WORKDIR /app

# 先安裝 PyTorch 生態（CUDA 12.1 wheel）
# torchvision 必須在此先裝好，防止 torchmetrics 初次 import 時觸發循環 import
# 必須在 requirements.txt 之前，避免被覆蓋成 CPU 版本
RUN pip install --no-cache-dir --upgrade pip setuptools wheel && \
    pip install --no-cache-dir \
        torch==2.5.1 \
        torchaudio==2.5.1 \
        torchvision==0.20.1 \
        --index-url https://download.pytorch.org/whl/cu121

# 安裝其餘依賴
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 複製應用程式碼
COPY app/ ./app/
COPY config.yml .

# 建立掛載目錄
RUN mkdir -p /input /output

ENTRYPOINT ["python", "app/main.py"]
CMD ["--watch"]
