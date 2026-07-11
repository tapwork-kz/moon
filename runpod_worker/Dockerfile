# Используем базовый образ RunPod с предустановленным PyTorch и CUDA
FROM runpod/pytorch:2.1.0-py3.10-cuda11.8.0-devel-ubuntu22.04

# ДОБАВЛЕНО: build-essential и python3-dev для компиляции тяжелых библиотек
RUN apt-get update && apt-get install -y ffmpeg git nano build-essential python3-dev && rm -rf /var/lib/apt/lists/*

WORKDIR /workspace

# Клонируем официальный FaceFusion
RUN git clone https://github.com/facefusion/facefusion.git

WORKDIR /workspace/facefusion

# ДОБАВЛЕНО: Обновляем базовые инструменты Python перед установкой пакетов
RUN pip install --upgrade pip setuptools wheel

# Устанавливаем зависимости
RUN pip install -r requirements.txt --no-cache-dir

# Принудительно ставим GPU-версию onnxruntime
RUN pip uninstall -y onnxruntime onnxruntime-gpu && pip install onnxruntime-gpu --no-cache-dir

# ========================================================
# ОТКЛЮЧЕНИЕ ЦЕНЗУРЫ (NSFW FILTER BYPASS)
RUN echo "\n\n# --- BYPASS NSFW ---" >> facefusion/content_analyser.py && \
    echo "def analyse_frame(*args, **kwargs): return False" >> facefusion/content_analyser.py && \
    echo "def analyse_image(*args, **kwargs): return False" >> facefusion/content_analyser.py && \
    echo "def analyse_video(*args, **kwargs): return False" >> facefusion/content_analyser.py
# ========================================================

# Устанавливаем библиотеки для нашего воркера
RUN pip install runpod supabase requests

# Копируем наш бессерверный скрипт внутрь образа
COPY serverless_worker.py /workspace/serverless_worker.py

# Указываем команду для запуска при старте сервера
CMD ["python", "-u", "/workspace/serverless_worker.py"]