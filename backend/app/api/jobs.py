from fastapi import APIRouter
from pydantic import BaseModel
from app.services.database import create_job_record
from app.services.ai_worker import process_face_swap # Импортируем нашу задачу

router = APIRouter(prefix="/jobs", tags=["Jobs"])

class JobCreate(BaseModel):
    video_id: str
    face_id: str

@router.post("/create")
def create_job(job: JobCreate):
    # 1. Создаем запись в таблице jobs в Supabase
    new_job = create_job_record(job.video_id, job.face_id)
    job_id = new_job["id"]
    
    # 2. Отправляем задачу в очередь Celery (функция .delay делает это асинхронно)
    process_face_swap.delay(job_id, job.video_id, job.face_id)
    
    return {"status": "success", "job": new_job, "message": "Задача добавлена в очередь"}