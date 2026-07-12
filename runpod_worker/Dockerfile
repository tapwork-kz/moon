# ========================================================
# ПЕРЕХОДИМ НА CUDA 12 (Идеально для новых версий FaceFusion)
# ========================================================
FROM runpod/pytorch:2.2.1-py3.10-cuda12.1.0-devel-ubuntu22.04

RUN apt-get update && apt-get install -y software-properties-common curl ffmpeg git nano build-essential && \
    add-apt-repository ppa:deadsnakes/ppa -y && \
    apt-get update && \
    apt-get install -y python3.11 python3.11-dev python3.11-distutils && \
    rm -rf /var/lib/apt/lists/*

RUN update-alternatives --install /usr/bin/python python /usr/bin/python3.11 1 && \
    update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.11 1

RUN curl -sS https://bootstrap.pypa.io/get-pip.py | python3.11

WORKDIR /workspace

RUN git clone https://github.com/facefusion/facefusion.git

WORKDIR /workspace/facefusion

# Ставим зависимости штатным образом (без костылей onnxruntime!)
RUN python -m pip install -r requirements.txt --no-cache-dir

# ОТКЛЮЧЕНИЕ ЦЕНЗУРЫ (NSFW FILTER BYPASS)
RUN echo "" >> facefusion/content_analyser.py && \
    echo "# --- BYPASS NSFW ---" >> facefusion/content_analyser.py && \
    echo "def analyse_frame(*args, **kwargs): return False" >> facefusion/content_analyser.py && \
    echo "def analyse_image(*args, **kwargs): return False" >> facefusion/content_analyser.py && \
    echo "def analyse_video(*args, **kwargs): return False" >> facefusion/content_analyser.py

RUN python -m pip install runpod supabase requests

COPY serverless_worker.py /workspace/serverless_worker.py

CMD ["python", "-u", "/workspace/serverless_worker.py"]