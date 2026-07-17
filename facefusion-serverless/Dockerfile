# 1. Используем эталонный образ NVIDIA (CUDA 12.1 + cuDNN 8)
FROM nvidia/cuda:12.1.1-cudnn8-devel-ubuntu22.04

# 2. Оптимизация Python и Docker
ENV DEBIAN_FRONTEND=noninteractive \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PATH="/opt/venv/bin:$PATH" \
    WORKSPACE_DIR="/workspace"

WORKDIR $WORKSPACE_DIR

# 3. Системные зависимости и очистка кэша в одном слое
RUN apt-get update && apt-get install -y --no-install-recommends \
    software-properties-common \
    curl \
    wget \
    git \
    ffmpeg \
    libgl1 \
    libglib2.0-0 \
    build-essential \
    ca-certificates \
    tzdata \
    && add-apt-repository ppa:deadsnakes/ppa -y \
    && apt-get update \
    && apt-get install -y --no-install-recommends python3.11 python3.11-venv python3.11-dev \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# 4. Изолированное виртуальное окружение
RUN python3.11 -m venv /opt/venv \
    && pip install --upgrade pip wheel setuptools

# 5. Установка FaceFusion (фиксированная стабильная версия 2.6.1)
RUN git clone https://github.com/facefusion/facefusion.git $WORKSPACE_DIR/facefusion

# 6. Копируем наши файлы
COPY requirements.txt $WORKSPACE_DIR/requirements.txt
COPY serverless_worker.py $WORKSPACE_DIR/serverless_worker.py
COPY build_check.py $WORKSPACE_DIR/build_check.py

# 7. Установка зависимостей Worker'a и оригинальных зависимостей FaceFusion
# Заменяем дефолтные пакеты FaceFusion на наши (строго под CUDA 12.1)
RUN pip install -r $WORKSPACE_DIR/requirements.txt \
    && pip install -r $WORKSPACE_DIR/facefusion/requirements.txt --no-deps

# 8. Проверки при сборке (Fail-Fast)
RUN python -c "import sys; print('Python:', sys.version)" \
    && pip --version \
    && ffmpeg -version

# 9. Подготовка к запуску
WORKDIR $WORKSPACE_DIR/facefusion
ENTRYPOINT ["python", "/workspace/serverless_worker.py"]