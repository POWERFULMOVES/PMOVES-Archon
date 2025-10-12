FROM nvidia/cuda:12.6.2-cudnn-runtime-ubuntu22.04

ENV DEBIAN_FRONTEND=noninteractive \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    python3 \
    python3-pip \
    python3-venv \
    python3-dev \
    ffmpeg \
    ca-certificates \
    git \
    curl \
 && ln -sf /usr/bin/python3 /usr/local/bin/python \
 && ln -sf /usr/bin/pip3 /usr/local/bin/pip \
 && rm -rf /var/lib/apt/lists/*

RUN curl -fsSL -o /tmp/libcudnn8.deb https://developer.download.nvidia.com/compute/cuda/repos/ubuntu2204/x86_64/libcudnn8_8.9.7.29-1+cuda12.2_amd64.deb \
 && curl -fsSL -o /tmp/libcudnn8-dev.deb https://developer.download.nvidia.com/compute/cuda/repos/ubuntu2204/x86_64/libcudnn8-dev_8.9.7.29-1+cuda12.2_amd64.deb \
 && dpkg -i /tmp/libcudnn8.deb /tmp/libcudnn8-dev.deb \
 && rm -f /tmp/libcudnn8.deb /tmp/libcudnn8-dev.deb

# Torch nightly builds include compute capability support for Blackwell GPUs (sm_90+).
RUN python -m pip install --no-cache-dir --upgrade pip \
 && python -m pip install --no-cache-dir --pre torch torchaudio --index-url https://download.pytorch.org/whl/nightly/cu126

COPY pmoves/services/ffmpeg-whisper/requirements.txt ./requirements.txt
RUN python -m pip install --no-cache-dir -r requirements.txt

COPY pmoves/services/common /app/services/common
COPY pmoves/services/ffmpeg-whisper /app

EXPOSE 8078

CMD ["uvicorn","server:app","--host","0.0.0.0","--port","8078"]
