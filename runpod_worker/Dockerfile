# 1. Используем новейший официальный образ RunPod (Python 3.11 + CUDA 12.4)
FROM runpod/pytorch:2.4.0-py3.11-cuda12.4.1-devel-ubuntu22.04

# 2. Устанавливаем ffmpeg (нужен для работы с видео)
RUN apt-get update && apt-get install -y ffmpeg git curl build-essential && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /workspace

# 3. Скачиваем самую свежую версию FaceFusion
RUN git clone https://github.com/facefusion/facefusion.git

WORKDIR /workspace/facefusion

# 4. Устанавливаем зависимости
RUN pip install -r requirements.txt --no-cache-dir

# ========================================================
# МАГИЯ: Включаем поддержку GPU для CUDA 12!
# Удаляем обычный ONNX и ставим правильный onnxruntime-gpu
# ========================================================
RUN pip uninstall -y onnxruntime onnxruntime-gpu && \
    pip install onnxruntime-gpu --extra-index-url https://aiinfra.pkgs.visualstudio.com/PublicPackages/_packaging/onnxruntime-cuda-12/pypi/simple/ --no-cache-dir

# 5. ОТКЛЮЧЕНИЕ ЦЕНЗУРЫ
RUN echo "" >> facefusion/content_analyser.py && \
    echo "# --- BYPASS NSFW ---" >> facefusion/content_analyser.py && \
    echo "def analyse_frame(*args, **kwargs): return False" >> facefusion/content_analyser.py && \
    echo "def analyse_image(*args, **kwargs): return False" >> facefusion/content_analyser.py && \
    echo "def analyse_video(*args, **kwargs): return False" >> facefusion/content_analyser.py

# 6. Устанавливаем библиотеки для нашего воркера
RUN pip install runpod supabase requests

COPY serverless_worker.py /workspace/serverless_worker.py

CMD ["python", "-u", "/workspace/serverless_worker.py"]