# Использованием проверенный базовый образ с CUDA 11.8
FROM runpod/pytorch:2.1.0-py3.10-cuda11.8.0-devel-ubuntu22.04

# 1. Устанавливаем системные пакеты
RUN apt-get update && apt-get install -y software-properties-common curl ffmpeg git nano build-essential && \
    add-apt-repository ppa:deadsnakes/ppa -y && \
    apt-get update && \
    apt-get install -y python3.11 python3.11-dev python3.11-distutils && \
    rm -rf /var/lib/apt/lists/*

# 2. Делаем Python 3.11 версией по умолчанию
RUN update-alternatives --install /usr/bin/python python /usr/bin/python3.11 1 && \
    update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.11 1

# 3. Pip для Python 3.11
RUN curl -sS https://bootstrap.pypa.io/get-pip.py | python3.11

WORKDIR /workspace

# Клонируем FaceFusion
RUN git clone https://github.com/facefusion/facefusion.git

WORKDIR /workspace/facefusion

# 4. Устанавливаем все пакеты
RUN python -m pip install -r requirements.txt --no-cache-dir

# ========================================================
# ИСПРАВЛЕНИЕ КОНФЛИКТА ВЕРСИЙ: Фиксируем onnxruntime и numpy
# ========================================================
RUN python -m pip uninstall -y onnxruntime onnxruntime-gpu numpy && \
    python -m pip install onnxruntime-gpu==1.17.1 numpy==1.26.4 --no-cache-dir

# ========================================================
# ОТКЛЮЧЕНИЕ ЦЕНЗУРЫ (NSFW FILTER BYPASS)
# ========================================================
RUN echo "" >> facefusion/content_analyser.py && \
    echo "# --- BYPASS NSFW ---" >> facefusion/content_analyser.py && \
    echo "def analyse_frame(*args, **kwargs): return False" >> facefusion/content_analyser.py && \
    echo "def analyse_image(*args, **kwargs): return False" >> facefusion/content_analyser.py && \
    echo "def analyse_video(*args, **kwargs): return False" >> facefusion/content_analyser.py

# Устанавливаем библиотеки для воркера
RUN python -m pip install runpod supabase requests

COPY serverless_worker.py /workspace/serverless_worker.py

CMD ["python", "-u", "/workspace/serverless_worker.py"]