# 1. Используем стабильный образ (Python 3.11 + CUDA 12.1) - решает конфликт cuDNN!
FROM runpod/pytorch:2.2.1-py3.11-cuda12.1.1-devel-ubuntu22.04

# 2. Устанавливаем системные утилиты
RUN apt-get update && apt-get install -y ffmpeg git curl build-essential && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /workspace

# 3. Клонируем свежий FaceFusion
RUN git clone https://github.com/facefusion/facefusion.git

WORKDIR /workspace/facefusion

# 4. Устанавливаем стандартные зависимости нейросети
RUN pip install -r requirements.txt --no-cache-dir

# ========================================================
# 5. МАГИЯ: Ставим ONNX для CUDA 12.1
# ========================================================
RUN pip uninstall -y onnxruntime onnxruntime-gpu && \
    pip install onnxruntime-gpu --extra-index-url https://aiinfra.pkgs.visualstudio.com/PublicPackages/_packaging/onnxruntime-cuda-12/pypi/simple/ --no-cache-dir

# 6. ОТКЛЮЧЕНИЕ ЦЕНЗУРЫ
RUN echo "" >> facefusion/content_analyser.py && \
    echo "# --- BYPASS NSFW ---" >> facefusion/content_analyser.py && \
    echo "def analyse_frame(*args, **kwargs): return False" >> facefusion/content_analyser.py && \
    echo "def analyse_image(*args, **kwargs): return False" >> facefusion/content_analyser.py && \
    echo "def analyse_video(*args, **kwargs): return False" >> facefusion/content_analyser.py

# 7. Устанавливаем библиотеки для воркера
RUN pip install runpod supabase requests

COPY serverless_worker.py /workspace/serverless_worker.py

CMD ["python", "-u", "/workspace/serverless_worker.py"]