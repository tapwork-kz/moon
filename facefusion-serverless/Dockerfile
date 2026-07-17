# 1. Используем эталонный образ NVIDIA (CUDA 12.1 + cuDNN 8)
FROM nvidia/cuda:12.1.1-cudnn8-devel-ubuntu22.04

# 2. Оптимизация Python и Docker (ЗДЕСЬ ГЛАВНЫЙ ФИКС - УКАЗАТЕЛЬ НА БИБЛИОТЕКИ)
ENV DEBIAN_FRONTEND=noninteractive \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PATH="/opt/venv/bin:$PATH" \
    WORKSPACE_DIR="/workspace" \
    LD_LIBRARY_PATH="/opt/venv/lib/python3.11/site-packages/nvidia/cudnn/lib:/opt/venv/lib/python3.11/site-packages/nvidia/cublas/lib:/usr/local/cuda/lib64:$LD_LIBRARY_PATH"

WORKDIR $WORKSPACE_DIR

# 3. Системные зависимости
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

# 5. Установка FaceFusion
RUN git clone https://github.com/facefusion/facefusion.git $WORKSPACE_DIR/facefusion

# 6. Копируем наши файлы
COPY requirements.txt $WORKSPACE_DIR/requirements.txt
COPY serverless_worker.py $WORKSPACE_DIR/serverless_worker.py
COPY build_check.py $WORKSPACE_DIR/build_check.py

# 7. Установка зависимостей
RUN pip install -r $WORKSPACE_DIR/requirements.txt \
    && pip install -r $WORKSPACE_DIR/facefusion/requirements.txt --no-deps

# 8. Проверки при сборке (Без GPU)
RUN python -c "import sys; print('Python:', sys.version)" \
    && pip --version \
    && ffmpeg -version

# 9. Подготовка к запуску
WORKDIR $WORKSPACE_DIR/facefusion
ENTRYPOINT ["python", "/workspace/serverless_worker.py"]