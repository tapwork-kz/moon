import os
import subprocess
import requests
import uuid
import runpod
from supabase import create_client, Client

# ================= НАСТРОЙКИ =================
# БЕРЕМ КЛЮЧИ ИЗ ОБЛАКА RUNPOD, А НЕ ИЗ ФАЙЛА!
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")
BOT_TOKEN = os.environ.get("BOT_TOKEN")
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
    job_input = job['input']
    job_id = job['id']
    
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

        # 2. Запуск FaceFusion
        command = [
            "python", "facefusion.py", "headless-run", 
            "-s", local_face_path, 
            "-t", local_video_path, 
            "-o", local_result_path, 
            "--execution-providers", "cuda"
        ]
        
        # ВАЖНО: Захватываем внутренние логи FaceFusion!
        process = subprocess.run(command, cwd=FF_DIR, capture_output=True, text=True)
        
        # Если FaceFusion упал, вызываем ошибку и прикрепляем то, что он написал в консоли
        if process.returncode != 0:
            raise Exception(f"ОШИБКА FACEFUSION:\n{process.stderr}\n{process.stdout}")

        # 3. Выгрузка в Supabase
        with open(local_result_path, "rb") as f:
            result_bytes = f.read()
        
        result_cloud_path = f"{user_id}/{uuid.uuid4()}_result.mp4"
        result_url = upload_file_sync("videos-output", result_cloud_path, result_bytes, "video/mp4")

        # 4. Отправка в Telegram
        requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/sendVideo", data={
            "chat_id": telegram_id,
            "video": result_url,
            "caption": "✨ Готово! Нейросеть успешно обработала видео."
        })

        # Очистка
        os.remove(local_video_path)
        os.remove(local_face_path)
        os.remove(local_result_path)

        return {"status": "success", "result_url": result_url}

    except Exception as e:
        print(f"[{job_id}] ❌ {e}")
        if BOT_TOKEN and telegram_id:
            requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage", data={
                "chat_id": telegram_id,
                "text": "Произошла ошибка при генерации видео. Разработчик уже чинит! 🛠️"
            })
        return {"status": "error", "error_message": str(e)}

if __name__ == "__main__":
    runpod.serverless.start({"handler": process_job})