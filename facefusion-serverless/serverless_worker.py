import os
import json
import logging
import subprocess
import tempfile
import shutil
import urllib.request
import urllib.error
from urllib.parse import urlparse
from dataclasses import dataclass
from typing import Dict, Any, Optional

import runpod
import torch
import onnxruntime as ort
import requests

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)s | %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

@dataclass
class JobInput:
    job_id: str
    user_id: str
    source_file_url: str
    face_file_url: str
    output_format: str = "mp4"
    callback_url: Optional[str] = None

class FaceFusionWorker:
    def __init__(self):
        self.facefusion_dir = "/workspace/facefusion"
        self._check_gpu_availability()

    def _check_gpu_availability(self) -> None:
        """Предварительная проверка GPU перед стартом Worker'a."""
        if not torch.cuda.is_available():
            raise RuntimeError("CRITICAL: CUDA is not available on this machine.")
        providers = ort.get_available_providers()
        if 'CUDAExecutionProvider' not in providers:
            raise RuntimeError("CRITICAL: ONNX Runtime CUDA provider is missing.")
        logger.info(f"Worker initialized. GPU: {torch.cuda.get_device_name()}")

    def _validate_input(self, job_input: Dict[str, Any]) -> JobInput:
        """Валидация входящих JSON параметров."""
        required_keys = ["job_id", "user_id", "source_file_url", "face_file_url"]
        for key in required_keys:
            if key not in job_input:
                raise ValueError(f"Missing required parameter: {key}")
        
        return JobInput(
            job_id=str(job_input["job_id"]),
            user_id=str(job_input["user_id"]),
            source_file_url=job_input["source_file_url"],
            face_file_url=job_input["face_file_url"],
            output_format=job_input.get("output_format", "mp4").strip('.'),
            callback_url=job_input.get("callback_url")
        )

    def _download_file(self, url: str, target_path: str) -> None:
        """Скачивание файла с обработкой ошибок и таймаутов."""
        if not urlparse(url).scheme in ("http", "https"):
            raise ValueError(f"Invalid URL schema: {url}")
        try:
            logger.info(f"Downloading file from {url}...")
            # Таймаут 30 секунд для предотвращения зависания
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req, timeout=30) as response, open(target_path, 'wb') as out_file:
                shutil.copyfileobj(response, out_file)
        except urllib.error.URLError as e:
            raise ConnectionError(f"Failed to download {url}: {e}")
        
        if os.path.getsize(target_path) < 1024:
            raise ValueError(f"Downloaded file {url} is too small or corrupted.")

    def _upload_to_storage(self, file_path: str, user_id: str, job_id: str) -> str:
        """
        Загрузка результата в Storage.
        Здесь представлена mock-логика загрузки (например, S3 или Supabase).
        В реальном проекте следует заменить на boto3 / API вызов.
        """
        logger.info("Uploading result to Cloud Storage...")
        # ПРИМЕР: Загрузка через pre-signed URL (должен передаваться в переменных окружения)
        upload_url = os.environ.get("STORAGE_UPLOAD_URL")
        if not upload_url:
            logger.warning("STORAGE_UPLOAD_URL not defined. Returning local path for debug.")
            return f"mock_url_path/{user_id}/{job_id}_result.mp4"

        try:
            with open(file_path, 'rb') as f:
                response = requests.put(upload_url, data=f, timeout=60)
                response.raise_for_status()
            return f"https://storage.yourdomain.com/results/{user_id}/{job_id}_result.mp4"
        except Exception as e:
            raise ConnectionError(f"Storage upload failed: {e}")

    def _run_facefusion(self, source_path: str, face_path: str, output_path: str) -> None:
        """Синхронный запуск процесса FaceFusion с ограничением памяти GPU."""
        logger.info("Starting FaceFusion execution (CUDA)...")
        
        command = [
            "python", "facefusion.py", "headless-run",
            "-s", face_path,
            "-t", source_path,
            "-o", output_path,
            "--execution-providers", "cuda",
            "--video-memory-strategy", "strict",  # Предотвращает OOM Killer
            "--execution-thread-count", "1",      # Стабилизирует CPU
            "--log-level", "info"
        ]

        # Захватываем Segmentation Faults
        env = os.environ.copy()
        env["PYTHONFAULTHANDLER"] = "1"

        process = subprocess.run(
            command, 
            cwd=self.facefusion_dir,
            capture_output=True, 
            text=True, 
            env=env
        )

        if process.returncode != 0:
            logger.error(f"FaceFusion STDERR: {process.stderr}")
            raise RuntimeError(f"FaceFusion processing failed with exit code {process.returncode}")

        if not os.path.exists(output_path) or os.path.getsize(output_path) == 0:
            raise RuntimeError("FaceFusion completed, but output file is missing or empty.")

    def process_job(self, job: Dict[str, Any]) -> Dict[str, Any]:
        """Главный хендлер задачи RunPod."""
        job_id = job.get("id", "unknown")
        raw_input = job.get("input", {})
        temp_dir = tempfile.mkdtemp(prefix=f"job_{job_id}_")
        
        logger.info(f"--- Started processing Job ID: {job_id} ---")

        try:
            # 1. Валидация
            parsed_input = self._validate_input(raw_input)
            
            # Авто-определение типа задачи по расширению
            is_image = parsed_input.source_file_url.lower().endswith(('.png', '.jpg', '.jpeg', '.webp'))
            ext = "jpg" if is_image else "mp4"

            source_path = os.path.join(temp_dir, f"source.{ext}")
            face_path = os.path.join(temp_dir, "face.jpg")
            output_path = os.path.join(temp_dir, f"result.{parsed_input.output_format}")

            # 2. Скачивание
            self._download_file(parsed_input.source_file_url, source_path)
            self._download_file(parsed_input.face_file_url, face_path)

            # 3. Исполнение ИИ
            self._run_facefusion(source_path, face_path, output_path)

            # 4. Загрузка в Storage
            result_url = self._upload_to_storage(output_path, parsed_input.user_id, parsed_input.job_id)

            logger.info(f"✅ Job {job_id} completed successfully.")
            return {
                "status": "success",
                "result_url": result_url,
                "job_type": "image_face_swap" if is_image else "video_face_swap"
            }

        except ValueError as e:
            logger.error(f"Validation Error: {e}")
            return {"status": "error", "error_type": "ValidationError", "message": str(e)}
        except ConnectionError as e:
            logger.error(f"Network Error: {e}")
            return {"status": "error", "error_type": "NetworkError", "message": str(e)}
        except RuntimeError as e:
            logger.error(f"Execution Error: {e}")
            return {"status": "error", "error_type": "GPUExecutionError", "message": str(e)}
        except Exception as e:
            logger.error(f"Unhandled Exception: {e}", exc_info=True)
            return {"status": "error", "error_type": "InternalError", "message": str(e)}
        finally:
            # 5. Гарантированная очистка (даже при ошибках)
            if os.path.exists(temp_dir):
                shutil.rmtree(temp_dir)
                logger.info(f"Cleaned up temporary directory: {temp_dir}")

if __name__ == "__main__":
    worker = FaceFusionWorker()
    runpod.serverless.start({"handler": worker.process_job})