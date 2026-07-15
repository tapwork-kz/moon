# 1. Используем официальный эталонный образ NVIDIA (CUDA 11.8 + cuDNN 8)
FROM nvidia/cuda:11.8.0-cudnn8-devel-ubuntu22.04

# Отключаем окна подтверждения при установке Linux-пакетов
ENV DEBIAN_FRONTEND=noninteractive

# 2. Устанавливаем системные утилиты и Python 3.11
RUN apt-get update && apt-get install -y software-properties-common curl ffmpeg git build-essential && \
    add-apt-repository ppa:deadsnakes/ppa -y && \
    apt-get update && \
    apt-get install -y python3.11 python3.11-dev python3.11-distutils && \
    rm -rf /var/lib/apt/lists/*

# 3. Делаем Python 3.11 версией по умолчанию в системе
RUN update-alternatives --install /usr/bin/python python /usr/bin/python3.11 1 && \
    update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.11 1 && \
    curl -sS https://bootstrap.pypa.io/get-pip.py | python3.11

WORKDIR /workspace

# 4. Клонируем свежий FaceFusion
RUN git clone https://github.com/facefusion/facefusion.git

WORKDIR /workspace/facefusion

# 5. Устанавливаем зависимости FaceFusion
RUN pip install -r requirements.txt --no-cache-dir

# ========================================================
# 6. ГЛАВНАЯ МАГИЯ: Жестко связываем ИИ с нашими драйверами
# Ставим версии PyTorch и ONNX строго под CUDA 11.8
# ========================================================
RUN pip uninstall -y torch torchvision torchaudio onnxruntime onnxruntime-gpu && \
    pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118 --no-cache-dir && \
    pip install onnxruntime-gpu==1.18.1 --no-cache-dir

# 7. ОТКЛЮЧЕНИЕ ЦЕНЗУРЫ
RUN echo "" >> facefusion/content_analyser.py && \
    echo "# --- BYPASS NSFW ---" >> facefusion/content_analyser.py && \
    echo "def analyse_frame(*args, **kwargs): return False" >> facefusion/content_analyser.py && \
    echo "def analyse_image(*args, **kwargs): return False" >> facefusion/content_analyser.py && \
    echo "def analyse_video(*args, **kwargs): return False" >> facefusion/content_analyser.py

# 8. Устанавливаем библиотеки для нашего воркера
RUN pip install runpod supabase requests

COPY serverless_worker.py /workspace/serverless_worker.py

# Запуск
CMD ["python", "-u", "/workspace/serverless_worker.py"]