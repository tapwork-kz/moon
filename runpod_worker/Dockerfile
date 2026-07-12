# 1. Используем родной образ с настроенной CUDA 11.8 и Python 3.10
FROM runpod/pytorch:2.1.0-py3.10-cuda11.8.0-devel-ubuntu22.04

# 2. Ставим только необходимые системные утилиты (без лишнего Python)
RUN apt-get update && apt-get install -y ffmpeg git curl build-essential && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /workspace

# 3. Клонируем оригинальный FaceFusion
RUN git clone https://github.com/facefusion/facefusion.git

WORKDIR /workspace/facefusion

# 4. Устанавливаем оригинальные зависимости
RUN pip install -r requirements.txt --no-cache-dir

# 5. ИСПРАВЛЕНИЕ: Фиксируем совместимые версии под CUDA 11.8
RUN pip uninstall -y onnxruntime onnxruntime-gpu numpy && \
    pip install onnxruntime-gpu==1.17.1 numpy==1.26.4 --no-cache-dir

# 6. ОТКЛЮЧЕНИЕ ЦЕНЗУРЫ (Чистый способ)
RUN echo "" >> facefusion/content_analyser.py && \
    echo "# --- BYPASS NSFW ---" >> facefusion/content_analyser.py && \
    echo "def analyse_frame(*args, **kwargs): return False" >> facefusion/content_analyser.py && \
    echo "def analyse_image(*args, **kwargs): return False" >> facefusion/content_analyser.py && \
    echo "def analyse_video(*args, **kwargs): return False" >> facefusion/content_analyser.py

# 7. Библиотеки для нашего воркера
RUN pip install runpod supabase requests

COPY serverless_worker.py /workspace/serverless_worker.py

CMD ["python", "-u", "/workspace/serverless_worker.py"]