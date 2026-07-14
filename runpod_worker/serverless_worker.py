import os
import subprocess
import requests
import uuid
import runpod
from supabase import create_client, Client

# Папки для временных файлов
TEMP_DIR = "/workspace/temp_jobs"
os.makedirs(TEMP_DIR, exist_ok=True)
FF_DIR = "/workspace/facefusion"

def process_job(job):
    job_input = job.get('input', {})
    job_id = job.get('id', 'unknown')
    
    # Получаем секретные ключи из настроек RunPod
    SUPABASE_URL = os.environ.get("SUPABASE_URL")
    SUPABASE_KEY = os.environ.get("SUPABASE_KEY")
    BOT_TOKEN = os.environ.get("BOT_TOKEN")
    
    video_url = job_input.get('video_url')
    face_url = job_input.get('face_url')
    user_id = job_input.get('user_id')
    telegram_id = job_input.get('telegram_id')

    print(f"[{job_id}] 🚀 RunPod Serverless начал обработку!", flush=True)
    
    if not SUPABASE_URL or not SUPABASE_KEY:
        return {"status": "error", "error_message": "Ключи Supabase не найдены в Environment Variables!"}

    supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

    local_video_path = os.path.join(TEMP_DIR, f"{job_id}_video.mp4")
    local_face_path = os.path.join(TEMP_DIR, f"{job_id}_face.jpg")
    local_result_path = os.path.join(TEMP_DIR, f"{job_id}_result.mp4")

    try:
        # --- 1. СКАЧИВАНИЕ ФАЙЛОВ ---
        print(f"[{job_id}] 📥 Скачивание файлов...", flush=True)
        req_video = requests.get(video_url)
        with open(local_video_path, 'wb') as f:
            f.write(req_video.content)
            
        req_face = requests.get(face_url)
        with open(local_face_path, 'wb') as f:
            f.write(req_face.content)

        video_size = os.path.getsize(local_video_path)
        face_size = os.path.getsize(local_face_path)
        
        print(f"[{job_id}] 📦 Размер видео: {video_size} байт. HTTP статус: {req_video.status_code}", flush=True)
        print(f"[{job_id}] 📦 Размер фото: {face_size} байт. HTTP статус: {req_face.status_code}", flush=True)
        
        if video_size < 1000 or face_size < 1000:
            raise Exception(f"Файлы битые или слишком маленькие! Ответ сервера: {req_video.text[:200]}")

        # --- 2. ЗАПУСК FACEFUSION ---
        print(f"[{job_id}] ⚙️ Запуск FaceFusion (CUDA)...", flush=True)
        command = [
            "python", "facefusion.py", "headless-run", 
            "-s", local_face_path, 
            "-t", local_video_path, 
            "-o", local_result_path, 
            "--execution-providers", "cuda",
            "--log-level", "debug"
        ]
        
        # Захватываем системные краши (Segmentation Fault)
        custom_env = os.environ.copy()
        custom_env["PYTHONFAULTHANDLER"] = "1"
        
        process = subprocess.run(command, cwd=FF_DIR, capture_output=True, text=True, env=custom_env)
        
        if process.returncode != 0:
            raise Exception(f"ОШИБКА FACEFUSION:\nSTDERR: {process.stderr}\nSTDOUT: {process.stdout}")

        # --- 3. ВЫГРУЗКА В SUPABASE ---
        print(f"[{job_id}] ☁️ Загрузка результата в облако...", flush=True)
        with open(local_result_path, "rb") as f:
            result_bytes = f.read()
        
        result_cloud_path = f"{user_id}/{uuid.uuid4()}_result.mp4"
        supabase.storage.from_("videos-output").upload(
            path=result_cloud_path, file=result_bytes, file_options={"content-type": "video/mp4", "x-upsert": "true"}
        )
        result_url = supabase.storage.from_("videos-output").get_public_url(result_cloud_path)

        # --- 4. ОТПРАВКА В TELEGRAM ---
        print(f"[{job_id}] ✉️ Отправка в Telegram...", flush=True)
        if BOT_TOKEN:
            requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/sendVideo", data={
                "chat_id": telegram_id,
                "video": result_url,
                "caption": "✨ Готово! Нейросеть успешно обработала видео."
            })

        # --- ОЧИСТКА ---
        os.remove(local_video_path)
        os.remove(local_face_path)
        os.remove(local_result_path)

        return {"status": "success", "result_url": result_url}

    except Exception as e:
        print(f"[{job_id}] ❌ Ошибка выполнения: {e}", flush=True)
        if BOT_TOKEN and telegram_id:
            requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage", data={
                "chat_id": telegram_id,
                "text": "Произошла ошибка при генерации видео. Разработчик уже чинит! 🛠️"
            })
        return {"status": "error", "error_message": str(e)}

if __name__ == "__main__":
    runpod.serverless.start({"handler": process_job})