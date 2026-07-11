import os
import subprocess
import requests
import uuid
import runpod
from supabase import create_client, Client

# ================= НАСТРОЙКИ =================
SUPABASE_URL = "https://erjvkdnmfuzdoytoxpol.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImVyanZrZG5tZnV6ZG95dG94cG9sIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc4MzYwMjczMSwiZXhwIjoyMDk5MTc4NzMxfQ.d7Y-U8oY3JswgMFhq4GK027XY5XB80Kn9q2eTK8k68o" # Замени на свой
BOT_TOKEN = "8091794183:AAFNRyezwqE8hHYm26YqFp5cTmQe6d8qRz8"
# =============================================

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
TEMP_DIR = "/workspace/temp_jobs"
os.makedirs(TEMP_DIR, exist_ok=True)
FF_DIR = "/workspace/facefusion"

def upload_file_sync(bucket_name: str, file_path: str, file_bytes: bytes, content_type: str) -> str:
    supabase.storage.from_(bucket_name).upload(
        path=file_path, file=file_bytes, file_options={"content-type": content_type, "x-upsert": "true"}
    )
    return supabase.storage.from_(bucket_name).get_public_url(file_path)

def process_job(job):
    """Эта функция вызывается автоматически серверами RunPod, когда приходит новая задача"""
    job_input = job['input']
    job_id = job['id']
    
    # Данные, которые мы будем передавать из нашего API
    video_url = job_input['video_url']
    face_url = job_input['face_url']
    user_id = job_input['user_id']
    telegram_id = job_input['telegram_id']

    print(f"[{job_id}] 🚀 RunPod Serverless начал обработку!")
    
    local_video_path = os.path.join(TEMP_DIR, f"{job_id}_video.mp4")
    local_face_path = os.path.join(TEMP_DIR, f"{job_id}_face.jpg")
    local_result_path = os.path.join(TEMP_DIR, f"{job_id}_result.mp4")

    try:
        # 1. Скачиваем файлы
        with open(local_video_path, 'wb') as f:
            f.write(requests.get(video_url).content)
        with open(local_face_path, 'wb') as f:
            f.write(requests.get(face_url).content)

        # 2. Запуск FaceFusion (фильтр цензуры уже отключен в Dockerfile)
        command = [
            "python", "facefusion.py", "headless-run", 
            "-s", local_face_path, 
            "-t", local_video_path, 
            "-o", local_result_path, 
            "--execution-providers", "cuda"
        ]
        subprocess.run(command, check=True, cwd=FF_DIR)

        # 3. Выгрузка в Supabase
        with open(local_result_path, "rb") as f:
            result_bytes = f.read()
        
        result_cloud_path = f"{user_id}/{uuid.uuid4()}_result.mp4"
        result_url = upload_file_sync("videos-output", result_cloud_path, result_bytes, "video/mp4")

        # 4. Отправка в Telegram прямо отсюда
        requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/sendVideo", data={
            "chat_id": telegram_id,
            "video": result_url,
            "caption": "✨ Готово! Нейросеть успешно обработала видео."
        })

        # Очистка
        os.remove(local_video_path)
        os.remove(local_face_path)
        os.remove(local_result_path)

        # Возвращаем результат в API
        return {"status": "success", "result_url": result_url}

    except Exception as e:
        print(f"[{job_id}] ❌ Ошибка: {e}")
        requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage", data={
            "chat_id": telegram_id,
            "text": "К сожалению, произошла ошибка при генерации видео. 😔"
        })
        return {"status": "error", "error_message": str(e)}

# Запуск прослушивателя RunPod Serverless
if __name__ == "__main__":
    runpod.serverless.start({"handler": process_job})