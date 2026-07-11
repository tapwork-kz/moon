from supabase import create_client, Client
from app.config import settings

supabase: Client = create_client(settings.supabase_url, settings.supabase_key)

def get_or_create_user(telegram_id: int, username: str | None = None):
    # Ищем пользователя
    user = supabase.table("users").select("*").eq("telegram_id", telegram_id).execute()
    if user.data:
        return user.data[0]
    
    # Если не найден, создаем нового
    new_user = supabase.table("users").insert({
        "telegram_id": telegram_id,
        "username": username
    }).execute()
    return new_user.data[0]

def create_video_record(user_id: str, source_video_url: str):
    video = supabase.table("videos").insert({
        "user_id": user_id,
        "source_video_url": source_video_url,
        "status": "waiting"
    }).execute()
    return video.data[0]

def create_face_record(user_id: str, image_url: str):
    face = supabase.table("faces").insert({
        "user_id": user_id,
        "image_url": image_url
    }).execute()
    return face.data[0]

def create_job_record(video_id: str, face_id: str):
    job = supabase.table("jobs").insert({
        "video_id": video_id,
        "face_id": face_id,
        "gpu_status": "pending"
    }).execute()
    return job.data[0]