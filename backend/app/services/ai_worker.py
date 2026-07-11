import requests
from app.services.database import supabase
from app.config import settings

def process_face_swap(job_id: str, video_id: str, face_id: str):
    print(f"[{job_id}] 🚀 Отправка задачи в RunPod Serverless...")
    
    try:
        # 1. Получаем ссылки на файлы и ID из базы
        video_record = supabase.table("videos").select("source_video_url, user_id").eq("id", video_id).execute().data[0]
        face_record = supabase.table("faces").select("image_url").eq("id", face_id).execute().data[0]
        user_record = supabase.table("users").select("telegram_id").eq("id", video_record['user_id']).execute().data[0]
        
        # 2. Формируем секретный запрос для твоего Эндпоинта
        url = f"https://api.runpod.ai/v2/{settings.runpod_endpoint_id}/run"
        headers = {
            "Authorization": f"Bearer {settings.runpod_api_key}",
            "Content-Type": "application/json"
        }
        
        # Эти данные RunPod Serverless передаст в твой Docker-контейнер
        payload = {
            "input": {
                "video_url": video_record['source_video_url'],
                "face_url": face_record['image_url'],
                "user_id": video_record['user_id'],
                "telegram_id": user_record['telegram_id']
            }
        }
        
        # 3. Отправляем команду на запуск видеокарты
        response = requests.post(url, json=payload, headers=headers)
        response_data = response.json()
        
        print(f"[{job_id}] ✅ Сигнал передан в RunPod! ID задачи в облаке: {response_data.get('id')}")
        
        # Обновляем статус в БД, чтобы понимать, что задача ушла в облако
        supabase.table("jobs").update({"gpu_status": "processing_in_cloud"}).eq("id", job_id).execute()
        
        return {"status": "success", "runpod_id": response_data.get("id")}
        
    except Exception as e:
        print(f"[{job_id}] ❌ Ошибка при отправке в RunPod: {e}")
        supabase.table("jobs").update({"gpu_status": "failed"}).eq("id", job_id).execute()
        return {"status": "error", "error": str(e)}