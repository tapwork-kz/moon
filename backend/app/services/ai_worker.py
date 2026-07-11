import os
import subprocess
import requests
import uuid
from app.celery_app import celery_app
from app.services.database import supabase
from app.services.storage import storage_service
from app.config import settings

# Папка для временных файлов на сервере с GPU
TEMP_DIR = "/tmp/face_swap_jobs"
os.makedirs(TEMP_DIR, exist_ok=True)

@celery_app.task(name="process_face_swap")
def process_face_swap(job_id: str, video_id: str, face_id: str):
    print(f"[{job_id}] 🚀 Воркер начал реальную задачу!")
    
    try:
        # 1. Получаем ссылки на файлы из базы
        video_record = supabase.table("videos").select("source_video_url, user_id").eq("id", video_id).execute().data[0]
        face_record = supabase.table("faces").select("image_url").eq("id", face_id).execute().data[0]
        user_record = supabase.table("users").select("telegram_id").eq("id", video_record['user_id']).execute().data[0]
        
        telegram_id = user_record['telegram_id']
        source_video_url = video_record['source_video_url']
        face_image_url = face_record['image_url']
        
        # 2. Скачиваем файлы локально
        print(f"[{job_id}] 📥 Скачивание исходников...")
        local_video_path = os.path.join(TEMP_DIR, f"{job_id}_video.mp4")
        local_face_path = os.path.join(TEMP_DIR, f"{job_id}_face.jpg")
        local_result_path = os.path.join(TEMP_DIR, f"{job_id}_result.mp4")
        
        with open(local_video_path, 'wb') as f:
            f.write(requests.get(source_video_url).content)
        with open(local_face_path, 'wb') as f:
            f.write(requests.get(face_image_url).content)
            
        # 3. Запуск FaceFusion (Команда для терминала)
        print(f"[{job_id}] ⚙️ Запуск нейросети FaceFusion...")
        
        # Это стандартная команда запуска FaceFusion в headless режиме (без интерфейса)
        command = [
            "python", "run.py", 
            "-s", local_face_path, 
            "-t", local_video_path, 
            "-o", local_result_path, 
            "--headless"
        ]
        
        # ЗАМЕТКА: Если запустить этот код прямо сейчас в Codespaces, он упадет, 
        # так как FaceFusion здесь не установлен. 
        # Раскомментируй subprocess.run(), когда перенесешь этот код на GPU-сервер.
        
        # subprocess.run(command, check=True) 
        
        # Пока нейросети нет, симулируем создание файла (копируем исходник)
        import shutil
        shutil.copyfile(local_video_path, local_result_path)
        
        # 4. Загружаем результат обратно в Supabase Storage
        print(f"[{job_id}] ☁️ Загрузка результата в облако...")
        with open(local_result_path, "rb") as f:
            result_bytes = f.read()
        
        result_cloud_path = f"{video_record['user_id']}/{uuid.uuid4()}_result.mp4"
        # Вызываем асинхронную функцию синхронно, так как Celery работает в синхронном режиме
        import asyncio
        result_url = asyncio.run(storage_service.upload_file("videos-output", result_cloud_path, result_bytes, "video/mp4"))
        
        # 5. Обновляем БД и отправляем видео пользователю
        supabase.table("jobs").update({"gpu_status": "completed"}).eq("id", job_id).execute()
        supabase.table("videos").update({
            "status": "completed", 
            "result_video_url": result_url
        }).eq("id", video_id).execute()
        
        print(f"[{job_id}] ✅ Готово! Отправляем ответ в Telegram.")
        requests.post(f"https://api.telegram.org/bot{settings.BOT_TOKEN}/sendVideo", data={
            "chat_id": telegram_id,
            "video": result_url,
            "caption": "✨ Твое видео успешно обработано нейросетью!"
        })
        
        # 6. Очистка (Удаляем временные файлы)
        os.remove(local_video_path)
        os.remove(local_face_path)
        os.remove(local_result_path)
        
        return {"status": "success", "job_id": job_id}
        
    except Exception as e:
        print(f"[{job_id}] ❌ Ошибка обработки: {e}")
        supabase.table("jobs").update({"gpu_status": "failed"}).eq("id", job_id).execute()
        requests.post(f"https://api.telegram.org/bot{settings.BOT_TOKEN}/sendMessage", data={
            "chat_id": telegram_id,
            "text": "Произошла ошибка при генерации видео. 😔"
        })
        return {"status": "error", "error": str(e)}