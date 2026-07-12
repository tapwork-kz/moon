# Базовый образ с драйверами CUDA 11.8
FROM runpod/pytorch:2.1.0-py3.10-cuda11.8.0-devel-ubuntu22.04

# 1. Устанавливаем Python 3.11 (жизненно необходим для нового FaceFusion)
RUN apt-get update && apt-get install -y software-properties-common curl ffmpeg git build-essential && \
    add-apt-repository ppa:deadsnakes/ppa -y && \
    apt-get update && \
    apt-get install -y python3.11 python3.11-dev python3.11-distutils && \
    rm -rf /var/lib/apt/lists/*

# 2. Делаем Python 3.11 главным в системе
RUN update-alternatives --install /usr/bin/python python /usr/bin/python3.11 1 && \
    update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.11 1

# 3. Обновляем pip
RUN curl -sS https://bootstrap.pypa.io/get-pip.py | python3.11

WORKDIR /workspace

# Клонируем FaceFusion
RUN git clone https://github.com/facefusion/facefusion.git

WORKDIR /workspace/facefusion

# ========================================================
# ГЛАВНАЯ МАГИЯ: Заставляем pip качать PyTorch строго для CUDA 11.8
# ========================================================
RUN pip install -r requirements.txt --extra-index-url https://download.pytorch.org/whl/cu118 --no-cache-dir

# ========================================================
# ИСПРАВЛЕНИЕ КОНФЛИКТА ВЕРСИЙ ONNX И NUMPY
# ========================================================
RUN pip uninstall -y onnxruntime onnxruntime-gpu numpy && \
    pip install onnxruntime-gpu==1.17.1 numpy==1.26.4 --no-cache-dir

# ========================================================
# ОТКЛЮЧЕНИЕ ЦЕНЗУРЫ
# ========================================================
RUN echo "" >> facefusion/content_analyser.py && \
    echo "# --- BYPASS NSFW ---" >> facefusion/content_analyser.py && \
    echo "def analyse_frame(*args, **kwargs): return False" >> facefusion/content_analyser.py && \
    echo "def analyse_image(*args, **kwargs): return False" >> facefusion/content_analyser.py && \
    echo "def analyse_video(*args, **kwargs): return False" >> facefusion/content_analyser.py

# Устанавливаем библиотеки для воркера
RUN pip install runpod supabase requests

COPY serverless_worker.py /workspace/serverless_worker.py

CMD ["python", "-u", "/workspace/serverless_worker.py"]