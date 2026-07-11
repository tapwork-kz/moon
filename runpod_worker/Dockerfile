# Используем базовый образ RunPod с предустановленным PyTorch и CUDA
FROM runpod/pytorch:2.1.0-py3.10-cuda11.8.0-devel-ubuntu22.04

# Устанавливаем системные зависимости
RUN apt-get update && apt-get install -y ffmpeg git nano && rm -rf /var/lib/apt/lists/*

# Создаем рабочую директорию
WORKDIR /workspace

# Клонируем официальный FaceFusion
RUN git clone https://github.com/facefusion/facefusion.git

WORKDIR /workspace/facefusion

# Устанавливаем зависимости FaceFusion
RUN python install.py --torch cuda --onnxruntime cuda

# ========================================================
# ОТКЛЮЧЕНИЕ ЦЕНЗУРЫ (NSFW FILTER BYPASS)
# Мы дописываем в конец файла анализатора функции, которые 
# перекрывают оригинальные и всегда разрешают обработку.
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