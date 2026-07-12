# 1. Используем родной, стабильный образ RunPod
FROM runpod/pytorch:2.1.0-py3.10-cuda11.8.0-devel-ubuntu22.04

# 2. Ставим только базовые утилиты
RUN apt-get update && apt-get install -y ffmpeg git curl build-essential && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /workspace

# ========================================================
# ГЛАВНЫЙ ФИКС: Замораживаем стабильную версию FaceFusion!
# Больше никаких сюрпризов от разработчиков
# ========================================================
RUN git clone --branch 2.3.0 https://github.com/facefusion/facefusion.git

WORKDIR /workspace/facefusion

# 3. Ставим родные зависимости именно для этой версии
RUN pip install -r requirements.txt --no-cache-dir

# 4. Перестраховка: гарантируем правильные библиотеки для CUDA 11.8
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

# 5. Устанавливаем библиотеки для нашего воркера
RUN pip install runpod supabase requests

COPY serverless_worker.py /workspace/serverless_worker.py

CMD ["python", "-u", "/workspace/serverless_worker.py"]